# FloodSafe Nepal V25 security baseline

V25 is a public, read-only web/PWA client. It intentionally contains no private API keys, admin credentials, write-capable tokens, or user passwords.

## Client controls

- Pages use a restrictive Content Security Policy and self-hosted JavaScript.
- Dynamic official-source text is rendered as text, not inserted as executable HTML.
- Fetch requests are restricted in `app.js` to same-origin content and an explicit host allowlist.
- External links use `noopener noreferrer` and no-referrer behavior.
- Forms, objects and embedded executable content are disabled by CSP.
- Public-source failures are treated as unavailable/unconfirmed data, never inferred as safe conditions.
- Missing/fatality figures from different authorities are shown with source/scope instead of silently merged.

## Production requirements before very large scale

A static client cannot provide a guarantee of being unhackable. A production backend should add a CDN/WAF, server-side allowlists, rate limiting, DDoS controls, dependency integrity/pinning, central cache/gateway, audit logging, security monitoring, automated dependency scanning and periodic penetration/load tests. Secrets must remain server-side only.
