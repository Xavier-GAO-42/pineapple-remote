# Post-MVP Optimization Notes

The MVP remains intentionally small and has no background process, database, server,
or WeChat protocol integration. These are follow-up candidates, not blockers:

1. Validate DOM selectors against the authorized official File Helper page after
   login and retain small selector diagnostics in local debug logs.
2. Improve web message identity if the DOM exposes a stable message identifier or
   timestamp, especially for identical commands after profile/session renewal.
3. Package or document a browser-runtime fallback when Microsoft Edge is unavailable,
   without adding screenshots, OCR, clipboard collection, or desktop-WeChat scanning.
4. Evaluate a separate opt-in launcher mode only if starting an inactive agent from
   WeChat becomes a requirement; keep it outside the agent-active bridge.
5. Consider an optional per-session challenge phrase if users later need protection
   against commands sent from another device already logged into their WeChat account.
