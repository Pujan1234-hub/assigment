from pathlib import Path

ROOT = Path(__file__).resolve().parent
path = ROOT / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/RainAlertWorker.java'
text = path.read_text(encoding='utf-8')

# Normalize any older 3h/4h weather digest build to the locked 2-hour user requirement.
text = text.replace('roughly every 3 hours', 'roughly every 2 hours')
text = text.replace('roughly every 4 hours', 'roughly every 2 hours')
text = text.replace('WEATHER_DIGEST_INTERVAL_MS = 3L * 60L * 60L * 1000L',
                    'WEATHER_DIGEST_INTERVAL_MS = 2L * 60L * 60L * 1000L')
text = text.replace('WEATHER_DIGEST_INTERVAL_MS = 4L * 60L * 60L * 1000L',
                    'WEATHER_DIGEST_INTERVAL_MS = 2L * 60L * 60L * 1000L')
text = text.replace('smart_weather_updates_v1', 'smart_weather_updates_v3')
text = text.replace('smart_weather_updates_v2', 'smart_weather_updates_v3')
text = text.replace('"last_weather_digest_at"', '"last_weather_digest_v3_at"')
text = text.replace('"last_weather_digest_v2_at"', '"last_weather_digest_v3_at"')
text = text.replace('आगामी ३ घण्टामा वर्षाको सम्भावना', 'आगामी २ घण्टामा वर्षाको सम्भावना')
text = text.replace('आगामी ४ घण्टामा वर्षाको सम्भावना', 'आगामी २ घण्टामा वर्षाको सम्भावना')
text = text.replace('३ घण्टाको मौसम अपडेट', '२ घण्टाको मौसम अपडेट')
text = text.replace('४ घण्टाको मौसम अपडेट', '२ घण्टाको मौसम अपडेट')
text = text.replace('३ घण्टापछि करिब ', '२ घण्टापछि करिब ')
text = text.replace('४ घण्टापछि करिब ', '२ घण्टापछि करिब ')
text = text.replace('now.plusHours(3).plusMinutes(30)', 'now.plusHours(2).plusMinutes(30)')
text = text.replace('now.plusHours(4).plusMinutes(30)', 'now.plusHours(2).plusMinutes(30)')
text = text.replace('3-hour forecast', '2-hour forecast')
text = text.replace('4-hour forecast', '2-hour forecast')
text = text.replace('A 4-hour general weather digest', 'A 2-hour general weather digest')

required = [
    'WEATHER_DIGEST_INTERVAL_MS = 2L * 60L * 60L * 1000L',
    'smart_weather_updates_v3',
    'last_weather_digest_v3_at',
]
for marker in required:
    if marker not in text:
        raise SystemExit('Two-hour weather patch missing: ' + marker)

path.write_text(text, encoding='utf-8')
print('FloodSafe 2-hour weather notification policy applied')
