# Frigate Review Notification Blueprint

A three-phase Frigate 0.18 review notification blueprint for Home Assistant.

- **Version:** 2026-09-07 (date-based versioning — the version is the release date)
- **Requires:** Frigate 0.18+, Frigate integration (MQTT `frigate/reviews`), MQTT broker, HA companion app
- **License:** MIT — see [LICENSE](LICENSE). Heavily rewritten from SgtBatten's Frigate Notifications blueprint — thanks for the inspiration.

## What it does

- **Phase 1:** instant '<Label> detected' + snapshot (audible) as soon as a review's severity matches the selected boxes (`alert` / `detection`).
- **Phase 2 (silent in-place updates, stable notification tag = review id):**
  - Event end → swaps the snapshot for the triggering detection's own preview GIF (`event_preview.gif`). The end update listens for the GenAI message during the delay window so the AI title/summary arrives together with the GIF.
  - Sub-label changes → refresh the message.
- **GenAI safety net:** a dedicated MQTT trigger re-asserts the AI title/summary `genai_send_delay` seconds after Frigate publishes it (covers late summaries / HA restarts).
- Configurable: notification icon, Android channel, sound, cooldown, alert-once, click action, action buttons (Clip / Snapshot / Silence 30 min), multiple `notify.` targets.

## How media URLs work (verified against the HA integration proxy)

The notification proxy (`frigate-hass-integration` `views.py`) is **event-keyed**:

- `…/api/frigate/notifications/{event_id}/snapshot.jpg` → `api/events/{event_id}/snapshot.jpg`
- `…/api/frigate/notifications/{event_id}/event_preview.gif` → `api/events/{event_id}/preview.gif`
- `…/api/frigate/notifications/{event_id}/{camera}/clip.mp4` → `api/events/{event_id}/clip.mp4`

So snapshots/GIF/clip links use the **triggering event id** (`data.detections[0]`), while the notification **tag** (update identity) uses the **review id**. Do not swap these — a review id in a media path 404s.

## Changes in 2026-09-07

- **Loop no longer lingers after event end when Phase 1 never fired.** Previously a severity-mismatched review (e.g. `detection` on an alert-only automation) kept the run alive for the full `wait_timeout`; the run now exits as soon as the review ends.
- **Camera guard:** conditions now require a resolvable camera list (`camera_raws`), so a renamed/missing camera entity can't silently leave the automation blind (no traces, no errors).
- **Removed unused `genai_timeout` input** (was "for compatibility"; nothing referenced it).
- **Removed redundant loop-level GenAI capture.** AI summaries are delivered by the end-window listener (glued to the GIF) and the delayed re-assertion safety net — the mid-loop capture was dead weight. Edge case: if a GenAI summary is published *mid-review* (before end) outside the end-window, it now arrives via the safety-net update instead of riding the GIF update.
- **Media URLs unchanged** — verified correct against the integration proxy (see above).

## Changes in 2026-09-06

- Removed the Review/Event GIF choice — the event-end GIF is always the triggering detection's own `event_preview.gif`.
- Added **Notification Icon (Optional - Android)** (`notification_icon`): a fixed `mdi:` name or a template; the default matches the detected object (person → `mdi:account`, cat → `mdi:cat`, dog → `mdi:dog`, car → `mdi:car`, package/amazon → `mdi:package-variant`, else `mdi:cctv`).

## Install

1. Copy `frigate_review_notification.yaml` into `/config/blueprints/automation/Frigate0.18/` (any subfolder under `blueprints/automation/` works).
2. Developer Tools → YAML → **Reload automations**.
3. Settings → Automations → Create from blueprint, one automation per camera.

## History

- **2026-09-07:** Exit-loop fix (no lingering after end when Phase 1 wasn't sent); camera_raws guard; removed `genai_timeout` and redundant loop GenAI capture; media URL contract documented.
- **2026-09-06:** Event GIF hardcoded; Android notification icon added; switched to date-based versioning.
- **Earlier (Sep 2026):** GenAI delivery timing fixes — AI title arrives with the end-GIF update; delayed re-assertion kept as a safety net.