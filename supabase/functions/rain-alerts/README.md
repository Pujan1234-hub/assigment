# FloodSafe opt-in rain alerts

GPS runs only after the location button is pressed and while the page is visible.
The Nepal map remains closed until its explicit open button is pressed. GPS is
shown separately from river gauges; its accuracy and last-fix time remain visible.

Rain timing is an **estimate**, not an observation or a guaranteed warning.
Open-Meteo's 15-minute amounts cover the preceding interval. In Nepal these are
interpolated hourly forecasts, not local radar nowcasts. Start/end ranges and
the source timezone are displayed. Missing or stale data cannot trigger an alert.

The browser refreshes forecasts every five minutes and retries failures after a
minute. The notification-only service worker does not cache application files or
river data. Existing news, river and human-impact feeds are unchanged.

## Background push

Users explicitly opt in through the rain-notification button and browser prompt.
The last approximate 1-km area and push subscription are retained for seven days,
renewed while the app is used. Closed-app alerts use that last area, not live GPS.
Turning off unsubscribes the browser and attempts immediate server deletion;
server records otherwise expire automatically. No precise GPS history is stored.

An authenticated minute cron checks the forecast cache; cache refresh is every
ten minutes, up to five areas per tick. Initial free-tier limits are 500 active
subscriptions and 50 distinct areas. Delivery is best effort and may be delayed
by forecast cadence, connectivity, browser/OS restrictions or push providers.
Only a forecast onset in the next 15 minutes is eligible; it expires at onset.
Duplicate events are suppressed, with bounded retries and a 30-minute cooldown.

Private tables have RLS and no anonymous grants. Per-subscription random
capabilities are stored as hashes. VAPID and scheduler signing keys stay in Vault;
only the VAPID public key is returned to browsers. JWT verification is disabled
because subscription operations and scheduler ticks use these separate credentials.

## Verification

Run `node --test tests/gps-rain.test.cjs tests/floodsafe-refresh.test.cjs tests/river-sync-latency.test.cjs`
from the repository root. The candidate/deployed browser workflow additionally
checks mobile UI, marker initialization, independent feed refresh and closed-map
reload behavior. On a real phone: enable location, open the map, enable rain
notifications, then press **Test notification**. Provider acceptance alone does
not prove that the OS displayed a notification. No account is required.
