# Mineral Dialog Local Design QA

final result: passed

## Latest Compacting Override

- Scope: remove all visible cluster-configuration rows and let the signal layer size itself to its contents. Actual count/value pairs, shared per-rock rules, the gold capsule style and one smaller bottom note remain unchanged.
- The user explicitly withdrew the signal-button occlusion work. The trial side/height-avoidance code and its regression test were manually removed. `mineralSignalBounds` matches the prior checkpoint; this report does not claim that button occlusion is fixed. It is a known deferred issue outside this acceptance scope.
- Current desktop evidence: `/tmp/gvy-mineral-trigger-clear-desktop-20261019.png`; focused signal evidence: `/tmp/gvy-mineral-trigger-clear-signal-20261019.png`. The temporary harness/file name reflects an earlier trial, not a claim of trigger-clearance verification. The final run no longer asserts trigger overlap; it checks the requested compacting and normal boundaries.
- 37 minerals at 320/390/620/621/880/1920/2560/3440px: 4248 signal instances and 11216 capsules render without the removed text, table columns, row resizing, horizontal overflow or viewport escape. Data serialization is unchanged; hover transition, pointer exit and keyboard Escape pass with no relevant console warnings/errors.
- At 1920px the real cached signals naturally measure 222-360px wide and 136-198px tall. These are measurements, not hardcoded sizes. The original 360/400 maximums remain. Current syntax/build/version-pair checks, 136 Python tests and 29 Node subtests pass.
- Earlier sections below describe the previous visual checkpoint; visible configuration rows in those reference images are superseded by the latest written request. The old gold capsule references remain the style target, not permission to restore removed copy.

## Visual Truth

- Outer layout: `/Users/bindox/.codex/generated_images/019ec6a8-7788-76e3-ae3c-ae7a03b52189/exec-a052bc2c-ee77-4f08-8463-4321a4f6a40a.png`.
- Latest inner-popover override: `/var/folders/rd/5vqxbv0522j_08nn62qj_bhr0000gn/T/TemporaryItems/NSIRD_screencaptureui_uiVOGF/截屏2026-10-19 04.25.16.png`.
- Latest note-placement override: `/var/folders/rd/5vqxbv0522j_08nn62qj_bhr0000gn/T/TemporaryItems/NSIRD_screencaptureui_KHG93h/截屏2026-10-19 04.32.37.png`: one smaller disclaimer at the bottom, not repeated per group.
- User explicitly rejected count-based table columns after approving the combined outer layout. The latest screenshot governs the popover: gold capsules, wrapping values, cluster configuration underneath. Do not restore the intermediate table.
- Local URL: `http://127.0.0.1:8002/`. No deployment, account connection or dependency installation.

## Evidence And Normalization

- Full comparison: source and `/tmp/gvy-mineral-final-reference-scale-20261019.png` were opened together in the same comparison input, with Copper / All systems / Pyro I signals open.
- Source outer image: 1448 x 1086 pixels, no authoritative CSS/DPR metadata. Its roughly 1216-pixel dialog width corresponds to the existing 760 CSS-pixel frame at an inferred 1.6 scale.
- Implementation: 905 x 679 CSS viewport, deviceScaleFactor 1.6, 1448 x 1086 screenshot; dialog 760 CSS pixels wide. This aligns frame scale without changing the existing site's fonts to mimic a raster mock.
- Focused comparison: the capsule-style user screenshot (570 x 370, cropped context, unknown capture scale) and `/tmp/gvy-mineral-final-signal-20261019.png` (1.6 DPR, 360 CSS-pixel popover) were opened together. Compare the approximately 520-pixel source frame after width normalization, not the surrounding clipped location list. The final note-placement override intentionally shortens the content; no exact pixel-identity claim is made from the source's unknown scale.
- Desktop: `/tmp/gvy-mineral-final-desktop-20261019.png`, dialog crop from 1920 x 1080 at DPR 1.
- Phone: `/tmp/gvy-mineral-popover-touch-390-20261019.png`, 390 x 844, touch-enabled Chromium at DPR 1.

## Findings And Comparison History

1. Initial combined layout used the selected mock's count-column table. The user subsequently overrode that part. Removed the table and its responsive CSS; restored gold numeric capsules and an ordered cluster-configuration line. Latest focused and full-view evidence shows no count-generated columns.
2. Keyboard review found that focus needed a route into the popover's controls. Added Tab from the trigger to its close control, then to the scrollable signal region; Shift+Tab and Escape restore the trigger, and leaving the signal region closes it. Verified in the browser at 390 and 1920 pixels.
3. The first stress harness opened a synthetic popup before the search debounce completed, then mistook the expected detail rerender for a signal-scroll failure. Event/stack instrumentation identified `applyFilters -> renderDetail -> closeMineralInfo`; the harness now waits for actual filtered results and resize frames. It passes without suppressing the app's normal rerender cleanup. This was not a proven internal-scroll regression. Focus-out cleanup was also narrowed to events originating within the signal region.
4. Touch resize validation initially checked before the resize event was delivered. It now waits for the expected hidden state rather than assuming synchronous event delivery.
5. The user found per-group mixed-deposit disclaimers visually repetitive. Consolidated them into one 10px note after all signal groups, while retaining each group's cluster configuration. Added a regression assertion for a single note after the final configuration and recaptured the final state.
6. The user then removed the redundant 舰采矿体 heading prefix. Single-mode popovers now show only primary/secondary relationships; genuinely mixed-mode locations retain compact mode labels to distinguish readings, never the verbose mineral-body suffix. Tests protect both cases.

No actionable P0/P1/P2 visual or interaction findings remain within the tested scope.

## Fidelity Surfaces

- Typography: existing site family, original 22px dialog heading and 12px location labels retained; signal values are readable 12px bold tabular digits, without viewport-based font scaling. Labels and long parent paths wrap. No font files or global typography changed.
- Spacing/layout: compact two-line location entries, two columns above 620px and one at/below it; equal-width separate star-system buttons; content-driven dialog height with a viewport cap. Gold popover does not resize location rows and is clamped inside the dialog/viewport. All named locations remain present, so the real list is longer than the generated mock; templates follow it rather than replacing actual entries.
- Colors/tokens: inherited dark mineral surface, cyan systems, white names and gold signal emphasis. Capsules use the existing orange token with dark digits, matching the latest screenshot's treatment.
- Assets/image quality: no product images, illustrations or logos occur in this surface. Existing application close controls and modal treatment are retained; generated screenshots are references, not rasterized UI or data sources.
- Copy/data: verified bilingual places, known parent paths, searched primary first, explicit secondary-material relationship, actual count order and shared per-rock semantics retained. One smaller bottom note avoids repeated disclaimers. Generated misspellings/duplicate rows are not copied. Added non-exact template label; no coordinates or signals invented.

## Verification

- 136 Python tests, including the frontend wrapper; 29 standalone Node tests.
- JavaScript syntax, diff whitespace, build and offline blueprint/mining version-pair validation pass.
- 37 minerals at 320/390/620/621/880/1920/2560/3440px: 296 dialogs and 4248 signal open/close cases, including text-bound checks, no failures. The 531 entries per size are material/location associations, not distinct exact physical mines.
- Real pointer tests: button-only hover, moving into the popover, leaving both regions, clicking then leaving despite retained mouse focus, filtering and close controls. Keyboard Enter/Space, Tab/Shift+Tab, Escape priority and modal focus/scroll restoration pass.
- Touch simulation: tap toggle, outside/close dismissal, one layer only, filter/template collapse and resize cleanup pass.
- Synthetic stress only: 60 capsules at 320/390/1920/2560/3440px wrap into 20/15/14/14/14 lines; popup widths remain 280/350/360/360/360px and height is capped at 400px with internal scrolling. Location-list scrolling dismisses the layer; internal popup scrolling does not. Synthetic values were never written into snapshots.
- Page identity/nonblank content, no framework error overlay, no relevant console warnings/errors, screenshots and target-flow interactions pass. Cached mineral data serializes identically before/after.
- Browser plugin/skill not available; existing local Playwright Chromium used with explicit user permission. Physical iOS, Safari and QQ browser are not tested.

## Follow-Up Polish

- The mock's decorative anchor pointer and divider are not introduced into the inherited UI. The active signal border and anchored placement identify the owner without adding custom-drawn assets. This does not block the approved interaction.
- Runtime screenshots and temporary QA harnesses live outside the site and are not production assets. The code is a local-only checkpoint awaiting user inspection, not a production release.
