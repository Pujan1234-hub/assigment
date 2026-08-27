#!/usr/bin/env python3
import html
import json
import re
import sys
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

HOME = "https://www.nepalpolice.gov.np/"
OUT = Path("data/floodsafe-police.json")
UA = "FloodSafe-Nepal/1.0 (+public-safety bulletin checker)"
DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

DISTRICTS = [
    ("Rasuwa", "रसुवा", r"रसुवामा"),
    ("Nuwakot", "नुवाकोट", r"नुवाकोटमा"),
    ("Dhading", "धादिङ", r"धादिङमा"),
    ("Chitwan", "चितवन", r"चितवनमा"),
    ("Gorkha", "गोरखा", r"गोरखामा"),
    ("Tanahun", "तनहुँ", r"तनहुँमा"),
    ("Nawalparasi East", "नवलपरासी पूर्व", r"नवलपरासी\s+पूर्वमा"),
    ("Nawalparasi West", "नवलपरासी पश्चिम", r"नवलपरासी\s+पश्चिम(?:मा)?"),
]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.buf = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.href = dict(attrs).get("href")
            self.buf = []

    def handle_data(self, data):
        if self.href is not None:
            self.buf.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.href is not None:
            self.links.append((self.href, " ".join(self.buf).strip()))
            self.href = None
            self.buf = []


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def clean_text(raw: str) -> str:
    p = TextParser()
    p.feed(raw)
    s = html.unescape(" ".join(p.parts))
    s = s.replace("पश्‍चिम", "पश्चिम").replace("पश्‍चिम", "पश्चिम").replace("\u200d", "").replace("\u200c", "")
    return re.sub(r"\s+", " ", s).strip()


def np_num(s: str) -> int:
    s = re.sub(r"[^०-९0-9सयहजार]+", " ", s).strip().translate(DIGITS)
    if not s:
        raise ValueError("empty Nepali number")
    toks = s.split()
    if "हजार" in toks:
        i = toks.index("हजार")
        left = int(toks[i - 1]) if i else 1
        rest = np_num(" ".join(toks[i + 1:])) if toks[i + 1:] else 0
        return left * 1000 + rest
    if "सय" in toks:
        i = toks.index("सय")
        left = int(toks[i - 1]) if i else 1
        rest = int("".join(t for t in toks[i + 1:] if t.isdigit()) or "0")
        return left * 100 + rest
    nums = [t for t in toks if t.isdigit()]
    if not nums:
        raise ValueError(f"cannot parse Nepali number: {s!r}")
    return int("".join(nums))


def latest_bulletin_url(home_html: str) -> str:
    p = LinkParser()
    p.feed(home_html)
    candidates = []
    for href, text in p.links:
        if "रसुवा बाढी" not in text or "मृत्यु" not in text:
            continue
        m = re.search(r"/news/(\d+)/?", href or "")
        if not m:
            continue
        url = href if href.startswith("http") else urllib.request.urljoin(HOME, href)
        candidates.append((int(m.group(1)), url))
    if not candidates:
        raise RuntimeError("No Rasuwa flood fatality bulletin found on Nepal Police homepage")
    return max(candidates)[1]


def parse_bulletin(url: str, raw: str) -> dict:
    text = clean_text(raw)
    if "रसुवा बाढी" not in text or "जनाको मृत्यु" not in text:
        raise RuntimeError("Candidate page is not a Rasuwa flood fatality bulletin")

    # Keep extraction inside the current article's district paragraph. Nepal Police
    # pages can contain older/related headlines elsewhere in the same HTML.
    body_m = re.search(
        r"जसमध्ये\s+(.*?)\s+गरी\s+[०-९0-9\sसयहजार]+?\s+जनाको शव फेला परेको छ",
        text,
    )
    if not body_m:
        raise RuntimeError("Could not isolate current bulletin district paragraph")
    district_text = body_m.group(1)

    # Date/time/total are read from the text immediately before that district paragraph.
    prefix = text[: body_m.start()]
    date_hits = re.findall(r"(२०[०-९0-9]{2}-[०-९0-9]{2}-[०-९0-9]{2})", prefix)
    time_hits = re.findall(r"([०-९0-9]{1,2})\s*:\s*([०-९0-9]{2})\s*बजे", prefix)
    total_hits = re.findall(r"सम्म\s+([०-९0-9\sसयहजार]+?)\s+जनाको मृत्यु", prefix)
    if not (date_hits and time_hits and total_hits):
        raise RuntimeError("Could not parse bulletin date/time/total")

    bs = date_hits[-1].translate(DIGITS)
    hh = int(time_hits[-1][0].translate(DIGITS))
    mm = int(time_hits[-1][1].translate(DIGITS))
    total = np_num(total_hits[-1])

    districts = []
    for en, ne, label in DISTRICTS:
        m = re.search(
            label + r"\s+([०-९0-9\sसयहजार]+?)(?=\s*(?:जना)?\s*(?:,|र\s+|$))",
            district_text,
        )
        if not m:
            raise RuntimeError(f"Could not parse district count: {ne}; paragraph={district_text}")
        districts.append({"name": en, "name_ne": ne, "deaths": np_num(m.group(1))})

    district_sum = sum(x["deaths"] for x in districts)
    if district_sum != total:
        raise RuntimeError(
            f"Safety validation failed: district sum {district_sum} != published total {total}; parsed={districts}"
        )

    now_np = datetime.now(ZoneInfo("Asia/Kathmandu"))
    iso = now_np.replace(hour=hh, minute=mm, second=0, microsecond=0).isoformat()
    return {
        "source": "Nepal Police",
        "source_url": url,
        "event": "Rasuwa flood",
        "event_ne": "रसुवा बाढी",
        "cause": "Flood",
        "cause_ne": "बाढी",
        "total_deaths": total,
        "official_update_bs": bs,
        "official_update_time": f"{hh:02d}:{mm:02d} NPT",
        "official_update_iso": iso,
        "districts": districts,
        "status": "verified",
        "note": "Automatically synced from the latest Nepal Police Rasuwa flood bulletin. Time is Nepal Time (NPT, UTC+05:45). Data is written only when every district count is parsed and the district sum exactly matches the published total."
    }


def main() -> int:
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    url = latest_bulletin_url(fetch(HOME))
    data = parse_bulletin(url, fetch(url))

    old_url = old.get("source_url", "")
    old_total = old.get("total_deaths")
    old_time = old.get("official_update_time")
    if old_url == data["source_url"] and old_total == data["total_deaths"] and old_time == data["official_update_time"]:
        print(f"No newer verified bulletin: {data['total_deaths']} at {data['official_update_time']}")
        return 0

    # Never move backwards on the same event.
    if isinstance(old_total, int) and data["total_deaths"] < old_total:
        raise RuntimeError(f"Refusing rollback from {old_total} to {data['total_deaths']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated verified bulletin: {data['total_deaths']} at {data['official_update_time']} -> {data['source_url']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FloodSafe police sync failed safely: {e}", file=sys.stderr)
        raise
