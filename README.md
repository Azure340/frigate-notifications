# Frigate Review Notification Blueprint

A three-phase Frigate 0.18 review notification blueprint for Home Assistant.

- **Version:** 2026-09-24b (date-based; `b` marks a same-day follow-up)
- **Requires:** Frigate 0.18+, Frigate integration (MQTT `frigate/reviews`), MQTT broker, HA companion app
- **License:** MIT — see [LICENSE](LICENSE). Heavily rewritten from SgtBatten's Frigate Notifications blueprint — thanks for the inspiration.

## What it does

- **Phase 1:** instant '<Label> detected' + snapshot (audible) as soon as a review's severity matches the selected boxes (`alert` / `detection`).
- **Phase 2 (silent in-place updates, stable notification tag = review id):**
  - Event end → swaps the snapshot for the Frigate review-scoped preview GIF (`review_preview.gif`, keyed by the review id), regardless of review duration. The end update listens for the GenAI message during the delay window so the AI title/summary arrives together with the GIF.
  - Sub-label changes → refresh the message.
- **GenAI safety net:** a dedicated MQTT trigger re-asserts the AI title/summary `genai_send_delay` seconds after Frigate publishes it (covers late summaries / HA restarts).
- Configurable: notification icon, Android channel, sound, cooldown, alert-once, click action, action buttons (Clip / Snapshot / Silence 30 min with optional presence-gated re-enable), multiple `notify.` targets.

## How media URLs work (verified against Frigate's HA notification proxy)

The proxy has separate URL forms for tracked-object media and review media:

- `…/api/frigate/notifications/{event_id}/snapshot.jpg` → tracked-object snapshot
- `…/api/frigate/notifications/{event_id}/event_preview.gif` → tracked-object GIF
- `…/api/frigate/notifications/{event_id}/clip.mp4` → tracked-object clip
- `…/api/frigate/notifications/{review_id}/review_preview.gif` → review-scoped GIF

The initial snapshot and the explicit Clip/Snapshot action links remain event-keyed and use the newest event id from `data.detections | max`. End-of-review and GenAI GIF updates use the review id with `review_preview.gif`, so their media is tied to the same review as the notification tag. Do not use a review id with an event-keyed endpoint (or an event id with the review GIF endpoint).

For multiple Frigate instances, the `client_id` input accepts the MQTT client ID with or without surrounding slashes; the blueprint normalizes the path segment. Leave it blank for a single instance.

### Notification proxy access

The Frigate integration's notification media proxy is deliberately unauthenticated so mobile devices can fetch pushed media. Keep it enabled only when you use it, and choose `notification_proxy_expire_after_seconds` deliberately: `0` means media URLs never expire. A finite expiry is evaluated from the timestamp prefix of the event/review ID, so allow for long review durations as well as the period users may need to open an old notification.

## Changes in 2026-09-24

- **Review-scoped GIF for every review duration.** End-of-review and GenAI GIF updates now use `review_preview.gif` keyed by the review id, rather than switching to the newest detection's event GIF after 180 seconds. Event ids are not mapped to the review's object labels, so selecting the newest event could attach media for a different detection. Initial snapshots and Clip/Snapshot actions remain event-keyed.

## Changes in 2026-09-24b

- **Current metadata now describes the review-scoped GIF.** Updated the blueprint summary to match the deployed `review_preview.gif` behavior; earlier dated notes remain historical.
- **Multi-instance URL normalization:** `client_id` can be entered with or without slashes.
- **Canonical event links:** Clip actions now use `/notifications/{event_id}/clip.mp4` without the unused camera segment.
- **`final_update` is consistent:** when disabled, the GenAI safety-net refresh keeps the snapshot rather than reattaching a GIF.
- **GenAI safety-net timing:** default raised from 10 to 20 seconds, five seconds after the default 15-second GIF delay, matching the documented ordering.
- **Notification proxy security:** Home Assistant's `notification_proxy_expire_after_seconds` is set to 86400 (24 hours) on the audited instance; `0` means no expiry.

## Changes in 2026-09-18

- **The Silence re-enable guard now actually works (bugfix).** The presence guard added in 2026-09-15 never took effect. The two inputs were declared under `blueprint.input` but were never mapped into the blueprint's top-level `variables:` block, so the guard template referenced **undefined Jinja variables** (`silence_reenable_entity` / `silence_reenable_state`). Automations render undefined variables non-strictly: HA logs `Template variable warning: 'silence_reenable_entity' is undefined when rendering …` and treats the value as falsy — so `not silence_reenable_entity` evaluated **true**, the `or` short-circuited, and `automation.turn_on` ran unconditionally on every silence expiry. Net effect was exactly the pre-2026-09-15 behavior — a Silence that expired while everyone was home re-enabled the automation — plus a template warning in the log each time it happened.
  - Both inputs are now mapped into `variables:`: `silence_reenable_entity: !input silence_reenable_entity` and `silence_reenable_state: !input silence_reenable_state`. Every other input was already mapped this way; only these two were missing, so no bare `!input`-derived name was in scope for the guard.
  - The check no longer relies on undefined-value semantics (blank guard is handled explicitly instead of via a falsy undefined):
    ```jinja
    {{ silence_reenable_entity == '' or is_state(silence_reenable_entity, silence_reenable_state) }}
    ```
  - Blank guard = unchanged behavior (always re-enable after 30 minutes). A configured guard is now genuinely evaluated once, at the moment the delay expires.
  - Why this slipped through the 2026-09-15 verification: anything that renders strictly (the template editor / Developer Tools) raises `UndefinedError` for these variables, while the automation path only logged a *warning* and carried on. A template test in isolation therefore can't prove the wiring — the only reliable check is the logbook/trace of a real silence expiry.
  - Re-import the blueprint with **overwrite** (or reload automations after editing the installed file) so the existing automations pick up the fix.

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

- **2026-09-24:** All end-of-review and GenAI GIFs use the review-scoped `review_preview.gif`, keyed to the notification review id; snapshots and action links remain event-keyed.
- **2026-09-24b:** Metadata/media docs corrected; client-id paths normalized; clip URL canonicalized; `final_update` now also governs GenAI GIF attachment; GenAI delay default aligned to follow the GIF delay.
- **2026-09-18:** Silence re-enable guard inputs wired into the blueprint's `variables:` block — they were declared but undefined, so the guard was a no-op and every silence expiry logged a template warning; the check is now `guard == '' or is_state(guard, state)`.
- **2026-09-15:** Silence re-enable gated by an optional presence guard entity/state (single check at delay expiry; blank = previous behavior).
- **2026-09-09:** Review-scoped preview GIF for short reviews (≤ 180 s); wait-loop re-resolves the media id per payload.
- **2026-09-08:** Media pinned to the newest detection (`max`); GenAI safety-net severity/age gating; GIF delay default 15s.
- **2026-09-07b:** Media id pinned per review so snapshot/GIF/clip are identical across Phase-1, end-GIF and GenAI safety-net updates.
- **2026-09-07:** Exit-loop fix (no lingering after end when Phase 1 wasn't sent); camera_raws guard; removed `genai_timeout` and redundant loop GenAI capture; media URL contract documented.
- **2026-09-06:** Event GIF hardcoded; Android notification icon added; switched to date-based versioning.
- **Earlier (Sep 2026):** GenAI delivery timing fixes — AI title arrives with the end-GIF update; delayed re-assertion kept as a safety net.
