# Codex Prompt Template — VPD Air Auto V2

Kopiere den folgenden Prompt 1:1 in Codex, wenn die Umsetzung von V2 gestartet werden soll.

---

## Prompt für Codex

You are working in the GitHub repository `binoalien/vpd_air_auto`.

Your task is to refactor the integration from its current V1 architecture toward V2 using the implementation plan in:

- `docs/V2_IMPLEMENTATION_PLAN.md`

Read that file first and treat it as the authoritative implementation guide.

## High-level objective

Refactor `vpd_air_auto` into a V2 architecture that will support:

- global defaults
- per-area overrides
- per-device overrides
- later support for optional source overrides

This is **not** a rewrite from scratch.
It must be an **incremental, test-driven refactor** that preserves working V1 behavior during the transition.

## Critical constraints

1. Do **not** change the existing unique ID scheme for entities.
2. Do **not** do a big-bang rewrite.
3. Do **not** mix massive architecture, migration, and UI changes into one step.
4. Keep the repository passing:
   - `ruff check .`
   - `pylint custom_components/vpd_air_auto tests`
   - `pytest --cov=custom_components.vpd_air_auto --cov-report=term-missing`
5. Prefer small, reviewable commits / PR-sized changes.
6. Preserve current public behavior unless the implementation plan explicitly says otherwise.
7. Use the plan document as the source of truth when making tradeoffs.

## Execution strategy

Follow the phases from `docs/V2_IMPLEMENTATION_PLAN.md`.

Start with **PR 1 only**.
Do not skip ahead to policy resolution, migrations, or config flow redesign until the earlier structural work is done.

## Immediate task: PR 1

Implement only the first planned step:

1. Add `custom_components/vpd_air_auto/domain/enums.py`
2. Add `custom_components/vpd_air_auto/domain/sensor_definitions.py`
3. Add `tests/test_sensor_definitions.py`
4. Keep the implementation compatible with the current codebase
5. Do **not** introduce policy-layer behavior yet
6. Do **not** redesign config flows yet
7. Do **not** modify unique ID behavior

## Expected output for this run

Produce a minimal, focused change set for PR 1 that:

- introduces `SensorKind` as a central enum
- introduces declarative sensor definitions for all current derived sensor types
- adds focused tests for those definitions
- does not yet require broad rewrites across the repository

## Working style

- First inspect the existing relevant files before editing:
  - `custom_components/vpd_air_auto/const.py`
  - `custom_components/vpd_air_auto/sensor.py`
  - `custom_components/vpd_air_auto/models.py`
  - `custom_components/vpd_air_auto/calculations.py`
  - existing sensor tests
- Then implement the smallest correct change that aligns with the V2 plan.
- Prefer backward-compatible helpers and imports where useful.
- If you need transitional code to keep V1 behavior stable, add it.

## Deliverable format

At the end of the run, provide:

1. A concise summary of what changed
2. The exact files added/modified
3. Any follow-up work needed for PR 2
4. Validation status for lint/tests if run

## Important

Do not attempt the full V2 in one run.
Only execute the first planned slice unless explicitly instructed to continue.

---

## Kürzere Variante für schnelle Codex-Läufe

You are in `binoalien/vpd_air_auto`.

Read `docs/V2_IMPLEMENTATION_PLAN.md` first.

Implement only **PR 1** from that plan:
- add `domain/enums.py`
- add `domain/sensor_definitions.py`
- add `tests/test_sensor_definitions.py`

Constraints:
- no unique ID changes
- no big-bang rewrite
- no policy layer yet
- no config flow redesign yet
- keep V1 behavior stable
- keep changes small and reviewable

At the end, summarize changed files and what PR 2 should do next.
