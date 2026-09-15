# Frigate Review Notification Blueprint

A three-phase Frigate 0.18 review notification blueprint for Home Assistant.

- **Version:** 2026-09-15 (date-based versioning — the version is the release date)
- **Requires:** Frigate 0.18+, Frigate integration (MQTT `frigate/reviews`), MQTT broker, HA companion app
- **License:** MIT — see [LICENSE](LICENSE). Heavily rewritten from SgtBatten's Frigate Notifications blueprint — thanks for the inspiration.

## What it does

- **Phase 1:** instant '<Label> detected' + snapshot (audible) as soon as a review's severity matches the selected boxes (`alert` / `detection`).
- **Phase 2 (silent in-place updates, stable notification tag = review id):**
  - Event end → swaps the snapshot for the preview GIF. The end update listens for the GenAI message during the delay window so the AI title/summary arrives together with the GIF.
  - Sub-label changes → refresh the message.
- **GenAI safety net:** a dedicated MQTT trigger re-asserts the AI title/summary `genai_send_delay` seconds after Frigate publishes it (covers late summaries / HA restarts).
- Configurable: notification icon, Android channel, sound, cooldown, alert-once, click action, action buttons (Clip / Snapshot / Silence 30 min with optional presence-gated re-enable), multiple `notify.` targets.

## How media URLs work (verified against the HA integration proxy)

The notification proxy (`frigate-hass-integration` `views.py`) is **event-keyed**:

- `…/api/frigate/notifications/{event_id}/snapshot.jpg` → `api/events/{event_id}/snapshot.jpg`
- `…/api/frigate/notifications/{event_id}/event_preview.gif` → `api/events/{event_id}/preview.gif`
- `…/api/frigate/notifications/{event_id}/{camera}/clip.mp4` → `api/events/{event_id}/clip.mp4`

So snapshots/GIF/clip links use the **triggering event id**, while the notification **tag** (update identity) uses the **review id**. Do not swap these — a review id in a media path 404s.

**Which event id?** The MOST RECENT detection in the review — resolved as `data.detections | max` (event ids string-compare by their epoch prefix, so the maximum is the newest activation). This is deliberate: for long-lived reviews (an object staying in view, e.g. a car parked for hours) the departure review bundles the still-open old event id alongside newer ones, and anchoring media to the oldest event made end/departure updates show the arrival. A review's detection list can also grow or reorder between the `new`/`end`/`genai` messages, so the `max` resolution keeps snapshot, GIF and clip consistent across every update of the same review (Phase 1, end-GIF update, and GenAI safety net).

## Changes in 2026-09-15

- **Silence re-enable is now presence-aware (optional).** The Silence button previously re-enabled the automation unconditionally after its 30-minute delay — so a Silence that expired shortly after someone got home resurrected the notification automation while everyone was present. Two new optional inputs gate that re-enable: **Silence re-enable guard entity** (`silence_reenable_entity`) and **Silence re-enable guard state** (`silence_reenable_state`, default `off`). When the guard entity is set, the automation is only turned back on if the guard entity's state equals the guard state at the moment the delay expires (single check, no re-check loop; a missing/unresolvable guard entity fails safe = stays off). For a scene-managed automation, select `binary_sensor.household_status` with guard state `off`, so an expiry while home leaves the automation off until the away scene turns it back on. Guard left blank = previous behavior; existing automations keep the old behavior until the guard is set on them.

## Changes in 2026-09-09

- **Review-scoped preview GIF for short reviews.** End-of-review and GenAI media now use the REVIEW-scoped `review_preview.gif` (keyed by the review id) when the review is short (≤ 180 s from start to end), falling back to the newest event's `event_preview.gif` for long-lived reviews. Root cause of stale departure media on long-parked vehicles: Frigate keeps ONE tracked event open the whole time an object stays in view, the departure review bundles that old event id, and the event preview endpoint hard-caps the GIF at the first 20 seconds of the event — so departure updates rendered the arrival. The main run's wait-loop also re-resolves the media id from each incoming payload's detections (`max`).

## Changes in 2026-09-08

- **Stale media anchoring fixed.** Media is pinned to the review's MOST RECENT detection (`data.detections | max` instead of `min`): a review whose detections span a long period (car parked in view for hours) previously anchored snapshot/GIF/clip to the FIRST event, so end/departure updates showed the arrival media.
- **GenAI safety net gated.** The safety-net run now requires the review's severity to match 'Trigger on (severity)' AND the review to be less than 15 minutes past its end (or start, if still open), so stale reviews can no longer resurrect as new notifications hours later and detection-only reviews no longer notify on alert-only automations.
- Default 'Delay before GIF update' raised from 5s to 15s.

## Changes in 2026-09-07b

- **Media id pinned per review.** `id` is now resolved from the review's detection list (see 2026-09-08 for the final `max` resolution) instead of the first list entry (`detections[0]`), so Phase 1, end-GIF and GenAI safety-net updates of the same review reference the identical event.

## Changes in 2026-09-07

- **Loop no longer lingers after event end when Phase 1 never fired.** Previously a severity-mismatched review (e.g. `detection` on an alert-only automation) kept the run alive for the full `wait_timeout`; the run now exits as soon as the review ends.
- **Camera guard:** conditions now require a resolvable camera list (`camera_raws`), so a renamed/missing camera entity can't silently leave the automation blind (no traces, no errors).
- **Removed unused `genai_timeout` input** (was "for compatibility"; nothing referenced it).
- **Removed redundant loop-level GenAI capture.** AI summaries are delivered by the end-window listener (glued to the GIF) and the delayed re-assertion safety net — the mid-loop capture was dead weight. Edge case: if a GenAI summary is published *mid-review* (before end) outside the end-window, it now arrives via the safety-net update instead of riding the GIF update.

## Changes in 2026-09-06

- Removed the Review/Event GIF choice — the event-end GIF is always the triggering detection's own `event_preview.gif`.
- Added **Notification Icon (Optional - Android)** (`notification_icon`): a fixed `mdi:` name or a template; the default matches the detected object (person → `mdi:account`, cat → `mdi:cat`, dog → `mdi:dog`, car → `mdi:car`, package/amazon → `mdi:package-variant`, else `mdi:cctv`).

## Install

1. Copy `frigate_review_notification.yaml` into `/config/blueprints/automation/Frigate0.18/` (any subfolder under `blueprints/automation/` works), or import from the raw URL and re-import after each update.
2. Developer Tools → YAML → **Reload automations**.
3. Settings → Automations → Create from blueprint, one automation per camera.

## History

- **2026-09-15:** Silence re-enable gated by an optional presence guard entity/state (single check at delay expiry; blank = previous behavior).
- **2026-09-09:** Review-scoped preview GIF for short reviews (≤ 180 s); wait-loop re-resolves the media id per payload.
- **2026-09-08:** Media pinned to the newest detection (`max`); GenAI safety-net severity/age gating; GIF delay default 15s.
- **2026-09-07b:** Media id pinned per review so snapshot/GIF/clip are identical across Phase-1, end-GIF and GenAI safety-net updates.
- **2026-09-07:** Exit-loop fix (no lingering after end when Phase 1 wasn't sent); camera_raws guard; removed `genai_timeout` and redundant loop GenAI capture; media URL contract documented.
- **2026-09-06:** Event GIF hardcoded; Android notification icon added; switched to date-based versioning.
- **Earlier (Sep 2026):** GenAI delivery timing fixes — AI title arrives with the end-GIF update; delayed re-assertion kept as a safety net.
