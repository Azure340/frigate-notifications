# Changelog

New entries are added at the top. Entries dated 2026-09-06 through 2026-10-31 live in the `Changes in ...` sections of [README.md](README.md) and are unchanged.

## 2026-11-12 - documentation only, blueprint file unchanged

`frigate_review_notification.yaml` is byte-identical to the 2026-10-31 build. Nothing in the automation logic changed. This entry records configuration that is now known to be required, plus Home Assistant Companion (Android) behaviour measured against a live install, so the dead ends are not retried.

### `base_url` must be filled in, or the Clip and Snapshot buttons cannot work

The Companion app only accepts a tapped notification link that resolves to a **Home Assistant frontend page**. The distinction is the whole problem:

| `base_url` | Link the blueprint emits | What the app does | Result |
|---|---|---|---|
| blank (the old default) | `/api/frigate/notifications/<id>/snapshot.jpg` | resolves it against the app's own server URL and navigates its **frontend webview** | the JPEG or MP4 never runs the frontend, so the external-bus handshake never completes and the tap fails after 10 s with `ExternalBusTimeout`, shown as a generic connection-timeout page |
| set to your external URL | `https://<your HA URL>/api/frigate/notifications/<id>/snapshot.jpg` | `UrlUtil.isAbsoluteUrl` matches, so the app builds an `ACTION_VIEW` intent and hands it to Android | the phone's default browser opens the snapshot or plays the clip; works from anywhere as long as that URL is the one the phone uses remotely |

This is the app's own dispatch logic, not a heuristic: relative paths go to the webview, absolute `http(s)` links go to the system. The notification **body tap** (`clickAction`) was always a frontend path, which is why it never failed the way the buttons did.

The notification `image` and the review `attachment` are unaffected either way: the app fetches them with its own HTTP client, outside the webview, so relative media paths there are correct and should be left alone.

### Why the `intent://` variant was dropped

Wrapping the same address as an Android intent URI (`intent://<host>/api/.../snapshot.jpg#Intent;scheme=https;end`) also reaches the system, because the app parses it with `Intent.parseUri`. It worked, but it hardcoded one cloud hostname into ten places in the shared blueprint file, and a parse failure falls back to opening the app's home page silently. The plain absolute URL takes the identical route with no special syntax, so the hostname lives in each automation's `base_url` input instead of in the file.

### Two routes that cannot work - do not re-propose them

- **Links to the Frigate host itself** (`https://<frigate>/api/events/<id>/snapshot.jpg`). This only helps if that host is reachable from the phone. Where the Frigate vhost exists for Home Assistant's internal proxy only (LAN-only DNS, no public exposure), the links fail for every phone away from home, while the Home Assistant proxy path keeps working through remote access.
- **In-app playback of one specific event via a media-browser deep link.** The addressable form is `/media-browser/browser/<encoded media_content_type,media_content_id>`, and it works when typed into a desktop browser. It cannot work from a notification tap on Android: the app decodes `%2F` escapes while resolving a relative link, so one segment becomes several and Home Assistant is handed the bare event id, which it rejects with `Invalid media source URI`. Every media-source id contains slashes, so no encoding or double-encoding trick avoids this.

### Measured media behaviour, for expectations

All figures are unauthenticated requests through the Home Assistant proxy over a cloud relay URL:

- `snapshot.jpg` - 56 to 60 KB, 0.14 to 0.16 s.
- `review_preview.gif` / `event_preview.gif` - 134 to 276 KB, about 0.2 s.
- `clip.mp4` - **bounded and fast for short events** (a 10 s alert: 11.4 MB in 0.68 s), but for an object that stays in view the endpoint streams continuously: chunked, no `Content-Length`, `Range` ignored (answered with `200`, not `206`), and `HEAD` returns 405. One long-running event streamed 379 MB in 12 s without ending. So the Clip button is a fine quick look at a normal alert and a very large download for a parked vehicle; the review GIF is the safe option, and bounded, seekable playback belongs in the Frigate panel, which streams.

### Configuration applied on the reference instance

- `base_url` set to the Nabu Casa relay address on all six Frigate automations (per-automation input, not in the blueprint file).
- Frigate integration option `notification_proxy_expire_after_seconds` changed from `0` (never expire) to `86400` (24 h), because these media URLs require no login and the buttons now place them in a browser, with the history and sync that implies. Expiry is evaluated from the timestamp prefix of the event or review id, so it must also cover the gap between an event starting and someone tapping the notification: that is why one hour was rejected in favour of 24, given reviews that stay open for hours.
