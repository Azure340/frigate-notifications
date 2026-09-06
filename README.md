# Frigate Review Notification Blueprint

A three-phase Frigate 0.18 review notification blueprint for Home Assistant.

- **Version:** 2026-09-06 (date-based versioning — the version is the release date)
- **Requires:** Frigate 0.18+, Frigate integration (MQTT `frigate/reviews`), MQTT broker, HA companion app
- **License:** MIT — see [LICENSE](LICENSE). Heavily rewritten from SgtBatten's Frigate Notifications blueprint — thanks for the inspiration.

## What it does

- **Phase 1:** instant `<Label> detected` + snapshot (audible) as soon as a review's severity matches the selected boxes (`alert` / `detection`).
- **Phase 2 (silent in-place updates, stable notification tag = review id):**
  - Event end → swaps the snapshot for the triggering detection's own preview GIF (`event_preview.gif`). The end update listens for the GenAI message during the delay window so the AI title/summary arrives together with the GIF.
  - Sub-label changes → refresh the message.
- **GenAI safety net:** a dedicated MQTT trigger re-asserts the AI title/summary `genai_send_delay` seconds after Frigate publishes it (covers late summaries / HA restarts).
- Configurable: notification icon, Android channel, sound, cooldown, alert-once, click action, action buttons (Clip / Snapshot / Silence 30 min), multiple `notify.` targets.

## Changes in 2026-09-06

- Removed the Review/Event GIF choice — the event-end GIF is always the triggering detection's own `event_preview.gif`.
- Added **Notification Icon (Optional - Android)** (`notification_icon`): a fixed `mdi:` name or a template; the default matches the detected object (person → `mdi:account`, cat → `mdi:cat`, dog → `mdi:dog`, car → `mdi:car`, package/amazon → `mdi:package-variant`, else `mdi:cctv`).

## Install

1. Copy `frigate_review_notification.yaml` into `/config/blueprints/automation/Frigate0.18/` (any subfolder under `blueprints/automation/` works).
2. Developer Tools → YAML → **Reload automations**.
3. Settings → Automations → Create from blueprint, one automation per camera.

## History

- **2026-09-06:** Event GIF hardcoded; Android notification icon added; switched to date-based versioning.
- **Earlier (Sep 2026):** GenAI delivery timing fixes — AI title arrives with the end-GIF update; delayed re-assertion kept as a safety net.
