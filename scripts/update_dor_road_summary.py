#!/usr/bin/env python3
import html
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL='https://navigate.dor.gov.np/app/dashboard'
OUT=Path('data/dor-road-summary.json')
UA='FloodSafe-Nepal/1.0 (+road status checker)'


def fetch():
    req=urllib.request.Request(URL,headers={'User-Agent':UA,'Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=25) as r:
        return r.read().decode('utf-8','replace')


def text(raw):
    s=re.sub(r'<script\b[^>]*>.*?</script>',' ',raw,flags=re.I|re.S)
    s=re.sub(r'<style\b[^>]*>.*?</style>',' ',s,flags=re.I|re.S)
    s=re.sub(r'<[^>]+>',' ',s)
    return re.sub(r'\s+',' ',html.unescape(s)).strip()


def pick(t,label):
    patterns=[
        rf'{re.escape(label)}\s*(\d+)',
        rf'(\d+)\s*{re.escape(label)}',
    ]
    for p in patterns:
        m=re.search(p,t,re.I)
        if m:return int(m.group(1))
    raise RuntimeError(f'Could not parse {label}')


def main():
    t=text(fetch())
    data={
      'source':'Department of Roads NAVIGATE',
      'source_url':URL,
      'total':pick(t,'Total'),
      'closed':pick(t,'Closed Roads'),
      'opened':pick(t,'Opened Roads'),
      'partially_opened':pick(t,'Partially Opened Roads'),
      'checked_at':datetime.now(timezone.utc).isoformat(),
      'status':'official_summary'
    }
    if data['closed']+data['opened']+data['partially_opened']>data['total']+2:
        raise RuntimeError('DoR summary failed sanity check')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    old=json.loads(OUT.read_text()) if OUT.exists() else {}
    same=all(old.get(k)==data.get(k) for k in ['total','closed','opened','partially_opened'])
    if same:
        print('No road summary change')
        return
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Updated',data)

if __name__=='__main__':main()
