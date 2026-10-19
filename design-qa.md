# Deep Blue Local Skin QA, 2026-10-19

final result: passed

## Material Badge Right Inset, 2026-10-20

After PR18 the user requested less trailing space and explicitly reused the
previously authorized browser. Installed Safari measures all 4,316 current
material rows before editing: the largest badge/gap/full-amount combination is
102.1333px (Inquisitor Core, x0.015), inside the existing 112px group. Minimum
frame clearance is 20.8594px. One product declaration, 8px left padding inside
that border-box group, moves all contents right without changing the parent
tracks, slider positions, amount format or vertical alignment.

An independent full rerun of the same 16 viewports below renders 25,888 record
views / 69,056 rows. Amount text is checked both against its own box (including
potential ellipsis clipping) and its material row. Badge alignment, visible
text, slider alignment, 72x23 capsules and page bounds all pass, with no captured
runtime errors. The group stays 112px at every size; minimum frame clearance
is 12.8594px, exactly 8px less than baseline, still safely inside the frame.
The longest current amount remains complete, not abbreviated or reduced.

The first AX read during the batch timed out and reset CUA after 30 seconds;
the Safari page continued and saved all 16 successful reports. Progress was
read from the result file, then native CUA reconnected. Final desktop/390px
screenshots were reviewed; the shifted phone badge opens the correct mineral
dialog and Escape restores focus. Existing Safari-only / non-iPhone-hardware
and non-DevTools-console limitations still apply. No settings or dependencies
were changed. Final build and production verification are in the handoff.

## Material Location Column Alignment

The latest correction left-aligns each manufacturing material's mineral badge
at the existing amount-column start instead of moving it with the amount's
right edge. Product code changes only two declarations: `.material-side` gets
`min-width:112px` and `justify-content:flex-start`. The 8px internal gap, parent
tracks, typography, quantities, sliders, quality formulas and dialogs remain.
The column can still grow for future content rather than clipping it.

Actual installed Safari independently renders all 1,618 manufacturing records /
4,316 material rows at 16 sizes: 320x568, 360x640, 375x667, 390x844,
620/621/880/881/1100/1101/1264/1320/1321x793, 1920x1080, 2560x1440 and
3440x1440. All 69,056 row checks pass: badge starts align across each list,
visible text stays within its row, quality sliders share position/width and
capsules stay 72x23. Both mineral/no-location labels are covered; the largest
current side group is 112px. No captured runtime errors or page overflow.
An initial harness false positive included an invisible positioned input hint;
visible-text checking now excludes hidden/transparent text, not visible faults.

Native CUA opens/closes Torite from the aligned desktop badge. Inputting 750
sets the slider to 750 and recoil effects to 80% / 0.8x; a native range click
sets 655 in both controls and 87.60% / 0.876x. At 390px the badge opens the
mineral dialog, Stanton filtering updates results, its signal opens, and two
Escape presses close the signal/dialog in order and return focus to the badge.
Desktop/phone screenshots were opened and reviewed. Browser skill is absent;
the user requires existing Safari only. Fixed desktop Safari viewports are not
iPhone hardware/touch/keyboard evidence, nor a DevTools console audit. Runtime
capture and screenshot checks found no relevant overlay/blank screen.

175 Python / 42 Node tests, syntax/diff and offline blueprint/mining pairing
pass. Build/candidate byte matching and exact-client production release gates
are recorded in the required handoff; local QA alone is not deployment proof.
No application JS, data, production HTML, refresh workflow or dependency changes.

## Both Units Retained (Latest)

The user's next correction explicitly retains the first scale/unit. Both sides
now show complete whole-万 abbreviations, `21万km/s -> 23万km/s`, with separate
full original titles. No shared/omitted first suffix or space inside the compact
number/unit; complete full-value formatting is unchanged. Only compact change
indicators reserve 8ch horizontally, preventing short/long percentages from
switching wrap points. No fixed taller heights or font reductions are added.

The full targeted Safari matrix reran independently: 14 viewports, 1,638 states,
6,426 card-bound/height checks and 1,400 repeated range input events pass, with
no captured runtime error/page overflow and complete integer/title checks.
The screenshot's 1264px quantum card remains one line / 27px; 320px and 1101px
narrow cards naturally use 38px across the tested states, rather than dropping
units to claim every size is one line. All other tested widths use 27px. Native
750 entry and the final desktop screenshot confirm both units and +9.98%.
Earlier shared-unit screenshots/results below are superseded, not final proof.
Existing Safari/phone-hardware limitations and scoped data guarantees remain.

## Shared-Unit Trial (Superseded)

PR15 (48189a9) passed the production gate, but the user correctly pointed out
that its label still sat above the numbers. The latest correction supersedes
the stage-one policy below: compare full text against the natural one-line
height, not against the original two-line baseline. Only large values that
wrap use whole 万, rounded half away from zero (20.983万 -> 21万), with each
full original value/unit retained in its hover title. Both sides share the
final scale/unit only when both qualify. Only compact cards tighten horizontal
gaps to 6px between label/values and 2px within values. No new fixed/minimum
height, smaller fonts, overflow hiding, formula or percentage changes.

Installed Safari independently reran the same 14 viewports and targeted
13-record / nine-quality matrix: 1,638 states, 6,426 card-bound/height checks,
1,400 range input events, complete titles and integer-compact checks pass.
VK-00's quantum card is now 27px in all 14 sizes, including 1264px, with label
and values together. Slider/scroll/focus remain stable, with no captured runtime
error or page overflow. Early 320px VK-00 and Allegro negative-percentage edges
were caught and fixed by sharing scale/unit and scoped horizontal spacing.
Native UI entry to 750 and actual desktop/390px screenshots were reviewed.
The exact result stays 230,775.57 km/s / +9.98%, displayed as 23万 only when
needed. This is a new run, not reuse of stage-one evidence. Existing browser
and phone-hardware limitations below still apply. Production identifiers and
final health status are recorded in the required handoff.

## Stage-One Compact Values (Superseded)

The taller fixed two-row trial in PR13 was rejected and reverted by PR14.
Its old matrix is not evidence for this replacement. The restored baseline is
22ffc45 (same source tree as c0a43e4). The new flow is VK-00 -> change Tungsten
quality -> keep the original card/section height and slider/scroll position.

Only absolute quality-summary values >=10,000 receive a full-value title and
optional compact text. An invisible, out-of-flow clone compares current full
text with the original Q500/no-change natural height at the same card width.
Only an extra line triggers 万, up to three decimals or two if still necessary
(the Allegro 1920px boundary). Resizing can restore full text. The original
flex card CSS, font sizes, padding and natural baseline height remain intact;
normal values, relative percentages, tasks/materials/signals and formulas are
unchanged. At 1264px VK-00 stays 114px overall / 38px quantum card, not 56px.

Actual installed Safari 26.6.2: 14 fixed CSS viewports, 320x568, 375x667,
390x844, 620/621/880/881/1100/1101/1264/1321x793, 1920x1080, 2560x1440 and
3440x1440. Thirteen targeted long-value/label/many-effect records per viewport,
nine qualities for a slot affecting a large metric: 1,638 states / 6,426 card
bounds and baseline-height checks pass. Another 1,400 actual range input events
on VK-00 preserve range position, detail/page scrolling and focus, with no
captured error/unhandledrejection or horizontal page overflow. This is targeted
large-value coverage, not every item/quality/slot. A diagnostic changing all
slots together also found an unrelated small relative-percentage wrap at
320px; that is intentionally outside the user's final oversized-number scope.

Native Safari numeric entry to 750 shows the real 230,775.57 km/s / +9.98%.
At 1264px it becomes 23.078万 km/s; at 390px the full value fits and remains full.
Both screenshots were opened and visually reviewed. Browser skill is absent;
the user's installed-Safari-only constraint is retained, with no browser
download or setting changes. No framework overlay/blank page was visible.
Runtime error capture is not a DevTools console audit; fixed Safari iframes
are not iPhone hardware, touch, soft-keyboard or browser-bar evidence.

175 Python / 42 Node tests, syntax and diff checks pass before release; build,
candidate-byte comparison, exact blueprint/mining pairing and production gate
must also pass. Temporary harness files remain outside deployable source/dist.
Release identifiers and final production verification are recorded in the
required project handoff rather than treating a local pass as deployment.

## Result Header Match

Following the Safari fix, the user requested that the left `item name/spec` and
source headings match the right detail label's size/color, then explicitly
authorized safe deployment after all checks. Only `.result-head` changes from
12px / translucent cyan to 14px / `var(--cyan)`; item names, geometry and data
remain unchanged. A regression test asserts the shared label size/color and
existing minimum height; the older 12px expectation is updated for this request.

Actual Safari checks both modes at 320/390/620/621/880/881/1100/1101/1320/1321/
1920/2560/3440/3840px: 28 states, equal 14px/rgb(126,221,242) labels, unchanged
36px header, full text inside each cell, no horizontal overflow, unchanged
21px item names/30px detail title. Desktop screenshot 13 and an actual native
320x568 select/result-click screenshot 14 were visually opened; the phone header
is complete and readable. This is a focused header delta, not another full
material/task matrix. Earlier Safari scope/limits below still apply.

174 Python tests, 40 Node tests, syntax/diff, build and blueprint/mining validation
pass. Built CSS c7ad53ec405a is byte-identical to the Safari candidate. JS and
data revisions are unchanged. Prior Safari release PR #11 / b750832 passed the
exact EdgeOne health gate with CSS 754f0d027d20 before this separate header delta.
Its production verification is not substituted for the new release's health gate.

## Actual Safari Follow-Up

The user requested Safari/mobile checks and explicitly chose the installed
Safari only. Safari 26.6.2 was operated through native CUA in a separate private
window. No browser download, dependency install, Safari setting/developer-mode
change or Wikelo coordination occurred. The flow under test was material quality
input -> plan editing/scrolling -> expanded task sources -> task dialog/close.

### Finding, Fixed

At 375x667, TH-01's Aluminum `minimum quality 600` phrase extended 2.49 CSS px
past its material-name column (text right 214.4739, column right 211.9844).
The existing inline no-wrap span did not move as a whole in this Safari case.
Adding only `display: inline-block` makes the phrase wrap atomically. The text
now ends at 136.1012 inside the column; the row grows naturally by 18px. Original
fonts, complete text, all thresholds including 0/1, data and formulas remain.
The regression test locks the inline-block/no-wrap pair without width/font fixes.

### Final Scope And Evidence

- Actual Safari rendered an isolated byte-matched site copy in same-origin fixed CSS viewports. The harness asserts each iframe's real innerWidth/innerHeight; it does not substitute Chromium, fake UA rendering or a recreated UI. Test HTML/bridge/server stay outside source and public dist.
- Twelve bounded batches passed: 320x568, 360x640, 375x667, 390x844, 393x852, 414x896, 430x932, 568x320, 667x375, 844x390, 1024x768 and 1264x793. Each covers 47 selected records, including all 17 recipes with minimum quality above 1, longest material/source titles, largest source lists/material sets, and 16 complex/long task dialogs.
- Final totals: 1,620 material rows, 1,296 quality controls, 14,316 task-source rows, 48 plan scenarios and 192 task dialogs. Empty, missing-ID, two-item and 100 longest-name items x 9999 plans retain their true text/cell bounds. Capsule dimensions, inner outline removal, slider synchronization, tooltip bounds, page overflow, dialog head/body/footer separation and unobstructed close buttons pass. No captured application error or unhandled rejection; domain records unchanged.
- Earlier exhaustive baseline checks passed 320/360 then caught the 375px bug. A later exhaustive rerun was stopped after native window-control timeouts; the user closed only the hung QA window. Final results above are the completed focused batches, not a claim that all 1,618 recipes and 672 tasks passed all twelve sizes. Smaller batches completed without that tool blockage.
- Native UI interaction at 390px: type quality 1000/Tab -> slider 1000 and coefficient 1.2x; type plan quantity 9999/Tab -> plus disabled, 10,002 pieces and material totals update; scroll to plan bottom -> totals/footer remain readable; Escape closes plan. Open a real source from the 125-task list -> expand requirements -> close button returns focus to its original source. Screenshots were saved and visually opened.
- Evidence: `/tmp/gvy-safari-audit-20261019/result.json`, `result-before.json`, `minimum-before.json`, `minimum-after.json`, and actual native captures `/tmp/gvy-safari-01-desktop-20261019.png` through `12-task-final-20261019.png`. Retain the original full-window images when providing focused screenshot crops.
- 173 Python tests, 40 standalone Node tests, syntax, diff, build and offline version-pair checks pass. Built CSS 754f0d027d20 is byte-equal to the final Safari-tested candidate; JS 2bc5ce5932cd and data-0f6906d31548ddd6 are unchanged. Latest stable LIVE still 4.10.2-live.12913470; data/timestamps, app JS, public HTML, scripts and workflows have no changes. Pre-fix healthy main/checkpoint is 230ca01, with an integrity-checked source archive retained for scoped rollback. Exact-client-URL production verification is required before reporting deployment. Full originals, result JSON and the isolated harness are also retained under `.git/visual-previews/safari-native-20261019/`, never shipped.

This is desktop Safari's real narrow-viewport CSS rendering and native input,
not iPhone hardware/iOS browser chrome, safe-area, touch, soft-keyboard or system
text-zoom verification. Safari DevTools was not enabled, so runtime error capture
is not a claim of an exhaustive developer-console warning audit. Browser plugin
skill was not listed; the existing-Safari-only direction takes precedence over
installing a separate Playwright WebKit runtime.

## Release Authorization

After the local corrections and audit below, the user explicitly authorized safe
deployment after final checks. This supersedes historical local-only notes for
this reviewed batch. The release preserves the verified production data and
requires exact-client-URL EdgeOne health verification; Git push is not deployment
proof. No further Wikelo coordination is requested; that site is separately
deployed. Final production revision and verification are recorded in the project
handoff after publishing.

## Latest Full-Site Audit And Refinements

The user requested a whole-site audit, explicitly authorized direct fixes, then
requested the Wikelo-style site footer and removal of nested numeric focus
frames. These are scoped corrections to the hierarchy below, not a new theme,
layout redesign or deployment authorization.

### Findings, Fixed

1. The left results panel's opaque sticky header covered the shared parent inset rim, unlike the right detail. The header now paints the common narrow `--shadow-panel-rim` itself, with no exterior header shadow or dimension change. Actual IAB before/after crop confirms the correction.
2. Search/default-quality text was hard to read. Flat-fill composite contrast changes from 2.94 to 5.41 and 3.99 to 5.97 respectively; default quality remains gray and unconfirmed, edited quality remains cyan. These token calculations are not a claim of complete accessibility compliance.
3. Empty favorites/search/filter states all said `暂无蓝图 / 无`. Existing empty-state structure now reports the actual reason; filters, selected IDs, data and favorites are unchanged.
4. Opening all seven dropdowns reproduced horizontal clipping at 320/390px and an 820px tablet. A first phone-only alignment trial was insufficient. The final helper measures the actual natural-width menu and applies only a horizontal offset, retaining an 8px viewport margin on click, keyboard opening and resize. No filter-grid change, label shrinking or option-width change.
5. The requested footer now blends into the canvas like the user's Wikelo reference, with a thin separator and the same filing icon dimensions. The audit also found a narrow-screen implicit grid/nowrap contribution extending footer children beyond their panel. A shrinkable grid track and normal filing wrapping correct it; existing legal text, URLs, logos and dialog footers are retained.
6. Global focus styling added a rectangle inside the quality capsule. The analogous plan quantity field had the same problem. Both inner numeric inputs now have no outline/shadow; the outer capsule/stepper retains clear focus-within feedback. Standalone search/share fields and normal keyboard indicators are not globally disabled. Six viewport sizes and fresh touch testing verify this.

### Current Evidence And Scope

- Fresh numbered steps `gvy-full-audit-01` through `17` capture main/filter, expanded detail/quality, task sources and rewards, filled/empty plan, empty/filled favorites, share fallback, mineral/signal, dismantle, footer and responsive views. They were saved and opened during this audit, not borrowed from a prior run. Corrections have separate `gvy-full-audit-final-*` evidence. Scripts, before source archive, failure evidence and captures are retained in `.git/visual-previews/deep-blue-full-audit-20261019/`.
- Exact original navy source remains `exec-aa8ec7b3-2baa-4210-a4ba-6cb77e570476.png`, normalized from 1672x941 to 1280x720. `gvy-full-audit-source-final-20261019.png` puts it beside the final actual IAB capture (1280x720 CSS/DPR2; screenshot API returns 1280x720). Both pages show craft VK-00/no filters/default quality/collapsed base attributes. Full-view and focused `gvy-full-audit-rim-before-after-20261019.png` were opened and reviewed. Independent Chromium uses DPR1; no screenshot recoloring or monitor-calibration claim.
- The new footer reference is the user's `截屏2026-10-19 12.09.44.png`. Its actual Wikelo footer CSS was read only, not edited here. Main blueprint panel widths/layout remain authoritative, rather than expanding the whole site to match a differently cropped reference. Focus-removal reference is the user's `截屏2026-10-19 12.26.57.png`; final quality/quantity screenshots show one outer field boundary only.
- Fidelity: existing typography, name sizes, colors, material names, content and logos remain unchanged except the requested footer's readable mobile filing style. All 397 non-paint CSSOM rules outside the explicit footer/menu-offset/inner-focus exceptions match. The 14-size/42-state snapshots match outside the requested footer and its natural page-height contribution. Five prior hierarchy roles and approved hover/selected colors remain unchanged. Broad gradients, generated mock geometry drift and screenshot density differences remain intentional exclusions. No outstanding actionable P0/P1/P2 remains in this scope; user style acceptance is separate.

### Verification

- Final matrix: 27 viewport sizes, 320 through 3840px, including 360/375/414 phones, 768/820/834/1024 tablets, both sides of existing breakpoints, 2K/ultrawide, 760x320 and 1100x420 short windows. All 189 menu openings, actual header children, main panels, plan bounds, footer children and complete filing links pass. Search/empty/reset, empty favorites, simulated 503/retry and missing-blueprint states pass. The simulated failure is an intentional separate QA context, not a production outage.
- This audit reran all 4316 material rows / 3718 quality controls at 13 widths (56108 / 48334 checks), and all 7476 source rows at seven widths (52332), including specification/type ordering, text bounds and slider equality/alignment. It also reran all 672 tasks / 37 minerals at nine sizes (6048 / 333 dialogs) and all 531 signal associations at nine sizes (4779 layers, 58834 visible-trigger hit checks). No overlap, hidden neighbor signal, domain-data mutation or text-bound failure. Later scoped menu/focus/footer corrections have their dedicated final matrix/focus and geometry checks; do not imply every exhaustive content pass was repeated after every last paint declaration.
- Final served port 8002 rechecks 18 sizes x four plan scenarios, three real 50/22/28 cells, 4px row spacing, no table pseudos, text bounds and elevation. Five-size/20 checks preserve the three unframed text exclusions plus task-source hover. Six-size numeric focus and fresh 390px touch check both wrapper feedback and inner outline removal; standalone search focus remains visible. Header/actions/share/favorite/add-plan focus restoration passes 80 cases at ten widths. Ten pointer targets retain distinct approved states without resizing.
- 172 Python tests (including Node subprocess coverage), standalone 40 Node tests, JS syntax, offline blueprint/mining pair, build and diff checks pass. No relevant application error/warning in normal flows. Browser plugin/skill absent; the requested frontend-testing-debugging/audit skills use the user's explicitly authorized existing independent Playwright, plus actual IAB checks. Physical Safari/iOS/QQ, real OS text zoom and full assistive-technology compliance remain unverified.
- QA harness corrections: normalize disposable favorites/plan badges across origins before geometry comparisons, allow only the requested footer's natural page-height delta, and compare share links to the actual candidate origin rather than hard-coded 8002. These fixture failures were investigated and rerun; they were not hidden as product regressions or used to widen layout exceptions.
- Final local CSS `de4648290200`, JS `2bc5ce5932cd`; data `data-0f6906d31548ddd6`, exact LIVE/counts and 05:12 timestamp unchanged. Only UI paint, menu-boundary presentation and empty-result copy change; no domain calculations, minima, refresh scripts, workflows or schedules change. Pre-audit checkpoint `4425164` and full source/dist backups remain. No push, PR, workflow dispatch, data refresh or deployment.

### Audit Steps

1. Main, filters and all menus: passed, viewport clipping fixed.
2. Craft/dismantle, attributes/materials and task sources: passed, readable placeholders and shared rim fixed.
3. Task/mineral/signal dialogs: passed, compact widths and height-first behavior retained.
4. Plan/favorites/share/empty/retry: passed, clearer empty reasons and scoped numeric focus fixed.
5. Site footer: passed, requested style and narrow-screen wrapping implemented.
6. Responsive, pointer, keyboard and touch: passed within the tested Chromium/IAB scope; physical-browser limits above remain.

## Latest Semantic Hierarchy Audit

The user stopped the flat-unification trial, then explicitly requested an audit
before repainting: same-role surfaces must match, different roles must retain
depth. The trial was never installed on port 8002. This section supersedes the
older depth-pass palette below. This is local technical QA, not final user style
approval or permission to deploy.

### Findings And Corrections

- [P2, fixed] Same-level primary panels differed: top/filter #06233e, detail/dialog #061c32 and structural headers #071d33. Fresh main/plan/task/mineral/dismantle captures plus computed styles confirmed the mismatch. They now share the approved right-detail #061c32 token.
- [P2, fixed] Repeated cards differed (#071e35 rows versus #0b2338 quality effects), and the stopped trial would have flattened all rows into the main panel. All repeated data cards now share distinct #0b243b with the existing raised-card shadow; quality-effect cells join that same role.
- [P2, fixed] Nested task-source groups used a row surface and reward pools used a control surface. They now share the existing recessed #031321 group role with quality-results groups. Source-row hover feedback remains explicitly enabled.
- [P2, fixed] The higher-specificity `.material-quality .quality-number` retained legacy RGBA and overrode the common opaque field token. Its original scoped declaration now uses #031321. No input or quality mechanism changed.

| Role | Components | Normal Fill |
| --- | --- | --- |
| Primary | Top/summary/filter, results/detail, plan/task/mineral shells and structural heads/feet | #061c32 |
| Raised data card | Results, materials, base/quality cells, plan items/material cells, reward rows, mineral entries, dismantled outputs | #0b243b |
| Recessed group | Quality-effects section, task-source section, reward pools | #031321 |
| Compact control | Normal buttons, filter triggers, specification chips, unselected system buttons | #061e33 |
| Inset field | Search/quality fields, stepper, modifier chips, small inset capsules | #031321 |
| Interaction | Existing hover / selected, plus original semantic gold/cyan exceptions | #1b455f / #164f68 |

Roles describe component function, not arbitrary DOM depth. Recessed groups and
fields deliberately share the inset token. Transparent plain-text targets remain
transparent; semantic badges, gold commands and accent-selected buttons are not
forced into resting content colors. The page canvas/footer remain unchanged.

### Evidence And Fidelity

- Source visual truth: `/Users/bindox/.codex/generated_images/019ec6a8-7788-76e3-ae3c-ae7a03b52189/exec-aa8ec7b3-2baa-4210-a4ba-6cb77e570476.png`, 1672 x 941 normalized to 1280 x 720. Route is manufacturing VK-00, no filters, collapsed base attributes/default quality. IAB uses 1280 x 720 CSS/DPR 2, screenshot API returns 1280 x 720; independent Chromium uses DPR 1. Actual IAB favorites 1/plan 0 remain unchanged; isolated Chromium uses disposable QA state.
- Before captures `gvy-hierarchy-01-main-before-20261019.png` through `06-dismantle-before` were opened before edits. After detail/plan/task/mineral/dismantle desktop and 390px captures were opened as well. Evidence and scripts are retained in `.git/visual-previews/deep-blue-hierarchy-20261019/`.
- Full-view `gvy-hierarchy-source-final-iab-20261019.png` puts source left/final IAB right; `gvy-hierarchy-before-after-iab-20261019.png` puts actual pre-pass IAB left/final right, both 2560 x 720. Focused `gvy-hierarchy-source-before-final-focused-20261019.png` compares corresponding filter/control regions source/before/final left-to-right, 1200 x 140. All were opened together and reviewed; screenshots are not recolored.
- Colors/elevation: same-role panels now agree, card/group depth remains visible, opaque uniform fills avoid the rejected blotchy shading. This is intentionally not pixel-identical to the generated concept's gradients; latest explicit role/deep-base choices and existing geometry override mock drift. No unresolved actionable P0/P1/P2 remains within this paint-only scope; user art-direction acceptance remains pending.
- Typography: existing fonts/fallbacks, sizes, weights, line heights, wrapping and white/mint/muted/semantic foregrounds unchanged. Layout: all 405 non-paint CSSOM rules plus 14-size/42-state geometry snapshots match the real pre-pass baseline exactly. Radii, responsive tracks, widths and spacing are unchanged. Unlike the preceding pass, some scoped component paint rules now change; do not claim everything outside :root is byte-identical.
- Assets: existing real logos, crops, dimensions and icons retained, no generated substitutes or new dependencies. Copy/content: HTML/JS/data unchanged; quality minima, grouping/formulas, per-item time placement and labels untouched.

### Verification

- Five sizes (320/390/1920/2560/3440), 25 main/plan/task/mineral/dismantle states assert 1235 actual component backgrounds against their assigned role, including the scoped quality field. All opaque/untextured. The same checks also pass against the final served 8002 build, not only the isolated candidate.
- 18 sizes from 320 to 3840 verify panels and actual header descendants, no page overflow, manufacturing/dismantling, filter open/Escape, search/empty/reset, keyboard plan and mineral/task close, hover signal bridge/Escape and fresh 390px touch neighboring-signal/plan flows. No relevant application error/warning or blank/error overlay. IAB final console is clear.
- 18 sizes x four plan scenarios pass real 50/22/28 cell proportions, text bounds, 4px spacing, inset rims and outer bounds. Five-size/20 targeted checks retain the three unframed text exclusions and task-source hover. Ten representative pointer targets change state without resizing; selection remains distinct, and touch-selected results stay visible without hover.
- 167 Python tests (including Node subprocess coverage), standalone 38 Node tests, JS syntax, offline blueprint/mining pair, whitespace checks and isolated/final builds pass. Browser plugin/skill absent; user-authorized existing independent Playwright is used, no new dependency installed. Physical iOS/Safari/QQ and the earlier exhaustive all-content audits were not rerun in this paint-only pass.
- Local CSS `48e40718b2c0`, JS `b085889e5719`, data `data-0f6906d31548ddd6`; exact LIVE, record counts and 05:12 timestamp unchanged. Original full backups and checkpoint `checkpoint/deep-blue-before-unify-20261019` at `4c0ea08` remain. No push, PR, workflow, refresh or deployment. Recovery is a normal scoped revert of this hierarchy commit.

### Checklist

1. Fresh screenshots/computed-style role audit completed before editing.
2. Role-specific paint corrected in isolated 8003; geometry and interaction gates passed.
3. Revised source/candidate plus actual source/IAB full and focused comparisons reviewed.
4. Final 8002 role checks and user-storage-preserving IAB capture passed; preview retained.

## Latest Navy Depth Pass

User review found the preceding candidate pale/gray-blue compared with the
selected concept. The comparison is reopened; the earlier pass below is not
proof of color acceptance. This pass fixes that P2 finding with deeper uniform
normal fills and lower-alpha blue rather than whitish rim light. The candidate
was checked on isolated port 8003 before replacing port 8002. This is local
technical/design acceptance, not final user style approval or deployment.

### Evidence And Findings

- Exact source remains `/Users/bindox/.codex/generated_images/019ec6a8-7788-76e3-ae3c-ae7a03b52189/exec-aa8ec7b3-2baa-4210-a4ba-6cb77e570476.png` (1672 x 941), normalized to 1280 x 720 for comparison. IAB actual route is VK-00/manufacturing/no filters/collapsed attributes/default quality, at 1280 x 720 CSS pixels, DPR 2; screenshot API returns 1280 x 720. Independent Chromium uses DPR 1. No screenshot was recolored. Output PNGs have no embedded ICC; RGB samples below describe the captured image, not monitor calibration or a guaranteed cross-browser literal CSS-to-pixel mapping.
- `.git/visual-previews/deep-blue-depth-20261019/` retains the before image, isolated candidate, final served IAB/Chromium captures and QA scripts. `gvy-blue-depth-source-final-20261019.png` combines source left/final right at 2560 x 720; `gvy-blue-depth-before-after-20261019.png` combines actual old/new IAB pages at the same dimensions. Both were opened and reviewed. The final user-origin captures keep favorites 1/plan 0 unchanged.
- Focused comparison `gvy-blue-depth-focused-20261019.png` is 1200 x 140, source/old/new left-to-right, corresponding filter/control crops. Earlier combined comparison found overly pale panel cores and neutral rim light (P2), not an acceptable deviation. Final primary core is #06233e, main #061c32, row #071e35; rim uses blue RGB(93,174,235) at 0.3 rather than whitish RGB(171,217,250) at 0.4. Actual IAB 32 x 8 empty-panel patch changes uniformly from RGB(20,40,65) to RGB(14,34,59), with no blotching. The sampled edge at (400,200) changes from RGB(38,67,99) to RGB(19,48,80).
- Intentional remaining source differences: the user's uniform-fill requirement excludes the concept's broad uneven gradients; existing page geometry, font sizes and true logo remain authoritative. Do not copy the mock's typography/layout drift to make this color-only pass appear pixel-identical. No actionable P0/P1/P2 remains within this color correction; art-direction preference still belongs to the user.

### Fidelity And Verification

- Typography: exact original fonts, sizes, weights, line heights and wrapping. Spacing/layout: all 405 non-paint CSSOM rules and 14 sizes / 42 main, plan and mineral geometry snapshots match the pre-pass baseline. Every byte outside :root is unchanged, so this pass adds no selectors, frames, spacing or component behavior.
- Color: darker opaque constant fills and blue edge light, no new gradients/filters/textures. Approved hover/selected colors and every semantic foreground token are unchanged. Normal foreground-token contrast remains at least 5.25:1 on the checked navy normal/hover/selected fills, excluding disabled/placeholder and dark-on-accent states.
- Assets: real logos, dimensions and crop unchanged; no new images/icons/dependencies. Copy/content: HTML, JS, both public snapshots, qualities, quantities, mission sources and cancelled unit-time move unchanged.
- 18 widths from 320 to 3840px verify panel/real-header-control bounds, opaque untextured surfaces, craft/dismantle, search-empty/reset, filter/Escape, keyboard plan, mineral hover/Escape, exact task opening and 390px touch mineral-neighbor/plan interactions. No application errors/warnings. IAB final console is also clear.
- 18 sizes x four plan scenarios pass actual 50/22/28 columns, cell text bounds, 4px spacing, rims and viewport bounds. Five sizes / 20 targeted checks confirm material-name/base-attribute/source-expand text still has no added frame and task-source hover stays explicitly enabled.
- 165 Python tests (including 38 Node), standalone 38 Node, JS syntax, offline blueprint/mining pair, build and diff checks pass. Browser plugin/skill unavailable; existing independent Playwright uses the user's prior explicit approval. Physical iOS/Safari/QQ remain untested; earlier full-content audits are not claimed as rerun.
- Final local CSS `6ad5fcc42258`; JS `b085889e5719` and data `data-0f6906d31548ddd6` unchanged. Source/dist historical backups and checkpoint `checkpoint/deep-blue-before-depth-20261019` at `786f079` remain. No push, PR, workflow, data refresh or deployment; normal scoped revert is the rollback path.

### Checklist

1. Pre-color checkpoint and original source/dist backups retained.
2. Actual IAB source/old/new full and focused comparison reviewed after correction.
3. Geometry, targeted feedback, responsive interactions and tests passed.
4. Final local preview restored to port 8002 with user storage unchanged.

## Previous Repair And State Contrast

This section supersedes the preceding checkpoint's acceptance below. This remains
local technical/design QA, not final user style approval or deployment authority.

- [P1, fixed] The decorative `tr::before` trial disrupted table layout: names moved into the middle and amounts wrapped outside the right edge. Restored the verified three-cell table immediately, then tested the replacement in an isolated build on port 8003. The final implementation adds no generated table content: exterior shadow stays on the row, the continuous inset rim is painted on its three opaque cells. Column widths, padding, fonts and row height remain unchanged.
- [P1, fixed] Hover and selection had almost the same fill. Results now use different hover/selected fills, a clear hover outline and a persistent 3px cyan inset selected marker. Filter selections stay solid cyan, open signals become gold-filled, and gold command hover is distinct from the filled active state. Keyboard focus is independently outlined. Hover adds no dimensions or new hit targets; touch selection remains visible without hover.
- [P2, fixed] Earlier whole-panel brightening flattened the depth. The revised darker cores use only a narrow continuous edge rim and exterior/contact shadows. Joined header/summary has no second top rim at its center seam. Body fills remain opaque and uniform, not the concept's blotchy gradients.
- [P2, fixed] The broad hover treatment unnecessarily framed material names, base attributes and source-expand summaries. After a too-broad color-only rollback, the user explicitly asked to restore the preceding stronger state treatment, remove only those unwanted boxes and KEEP task-source feedback. The final exclusions are scoped to those three plain-text surfaces, not the rest of the site. Their hover backgrounds stay transparent, shadows/added outlines stay none; five widths verify these exclusions plus the retained blue task-source fill/rim. `gvy-rim-unframed-{width}-20261019.png` records the final targeted correction.

Source visual truth remains `/Users/bindox/.codex/generated_images/019ec6a8-7788-76e3-ae3c-ae7a03b52189/exec-aa8ec7b3-2baa-4210-a4ba-6cb77e570476.png`.
New evidence is in `.git/visual-previews/deep-blue-rim-polish-20261019/evidence/`:
`gvy-rim-final-source-candidate-20261019.png` combines the same 1280 x 720
source/candidate state into 2560 x 720; `gvy-rim-final-filter-focus-20261019.png`
is a 520 x 104 source-left/candidate-right edge/control comparison. Both were
opened together and reviewed. Source 1672 x 941 is normalized to 1280 x 720;
implementation is 1280 x 720 CSS pixels at density 1, manufacturing VK-00,
default quality, collapsed attributes and independent QA storage. The mock's
different text metrics/geometry, favorite count and uneven shading remain
intentional exclusions, not instructions to change the existing layout.

Additional opened evidence: `gvy-rim-states-list-focus-20261019.png` shows normal,
selected and hovered rows together; `gvy-rim-plan-390-20261019.png` and
`gvy-rim-plan-fixed-20261019.png` show the repaired phone/desktop table.
`gvy-rim-first-plan-20261019.png` is failed evidence only, never the deliverable.
Final port-8002 proof `gvy-final-targeted-feedback-20261019.png` combines the
unframed base-attribute/material/expand text and the explicitly retained framed
task-source hover. `gvy-final-targeted-plan-20261019.png` rechecks the repaired
three columns against the final served CSS, not only the isolated candidate.

Five fidelity surfaces: typography/fallbacks/weights and complete wrapping stay
unchanged; spacing/layout/columns/radii match the preceding verified checkpoint;
color/elevation now has distinct interaction states and uniform panel bodies;
all real logos/assets are unchanged with no additions; HTML/JS/data/copy and
quality/unit-time/total-time semantics are unchanged. A 32 x 8 empty panel sample
is uniformly RGB(11,42,67). The checked normal foreground tokens have minimum
contrast 5.25:1 on normal/hover/selected navy fills; this excludes placeholders,
disabled controls and dark text on filled accent buttons.

Verification for this iteration:

- Exact baseline geometry and fonts at 14 sizes / 42 main, plan and mineral states; non-paint CSS matches after excluding explicitly requested focus outlines and normalizing declaration order. Baseline 404 rules, candidate 405 including the new focus-only rule.
- 18 sizes from 320 to 3840px, four plan scenarios each: empty, unavailable ID, two real items and 100 items at quantity 9999. Actual three-cell 50/22/28 widths, text bounds, 4px spacing, backgrounds/rims, row/window bounds and unchanged data pass. A further six sizes including 760 x 320 short-window stress all 1618 planned rows at quantity 9999 and their five resulting material groups; this does not claim every possible material choice was covered.
- Whole-page 18-size panel/header-descendant/overflow checks, craft/dismantle, filter open/Escape, search-empty/reset, keyboard plan open/close, mineral hover bridge/Escape, task open/close and fresh 390px touch mineral/neighbor/plan flows pass. Ten representative hover targets and persistent selected states are checked with real pointer actions; their geometry stays constant. No relevant application console warnings/errors.
- 164 Python tests including 38 Node tests, standalone 38 Node tests, JavaScript syntax, isolated build, offline paired-snapshot validation and whitespace checks pass. Latest CSS is `ff6753101cc7`; JS `b085889e5719` and data `data-0f6906d31548ddd6` are unchanged. No production check is claimed for this unpublished build.
- Browser plugin/skill unavailable; the user-approved existing independent Playwright Chromium is used, without dependency installation or user storage changes. Physical iOS/Safari/QQ remain untested. Earlier exhaustive source/material/task content runs below were not repeated in full for these paint-only edits.

The pre-refinement checkpoint `checkpoint/deep-blue-before-rim-polish-20261019`
and earlier source/dist backups remain. Experimental builds must stay isolated
until rendered verification, so another failed paint trial cannot overwrite the
user's preview. Final preview remains on port 8002; no push or deployment.

## Previous Verified Checkpoint

Latest user corrections are implemented and rechecked: originally unframed
primary regions receive the shared raised treatment; header/summary align with
the other panels; actual header controls fit at both breakpoint sides; plan
material rows share the reward-list elevation. This is local technical/design QA,
not user approval of the final art direction or authorization to publish.

## Scope And Authority

This is a local preview only. No push, PR, workflow dispatch, data refresh or
deployment is authorized for this batch. Historical release authorizations below
do not apply. The latest user-approved specification is uniform navy surfaces
with floating exterior shadows, while preserving the current production layout,
templates, typography and behavior. The cancelled unit-time move stays cancelled.

## Comparison Evidence

- Source visual truth: `/Users/bindox/.codex/generated_images/019ec6a8-7788-76e3-ae3c-ae7a03b52189/exec-aa8ec7b3-2baa-4210-a4ba-6cb77e570476.png` (1672 x 941 pixels). The robot ship card at `.git/visual-references/bot-ship-card-shadow-only-20261019.png` is an exterior-shadow reference only, not an asset/layout/palette source.
- Implementation: `http://127.0.0.1:8002/#blueprint=33be7f1a-3f75-4627-bb8b-88e6d6b42f4e&mode=craft`, VK-00, manufacturing, no filters, base attributes collapsed, default quality. CSS `fd42e6d833b0`; unchanged JS `b085889e5719` and data `data-0f6906d31548ddd6`.
- Evidence directory: `.git/visual-previews/deep-blue-20261019/` (local, not shipped). Main capture `gvy-deep-blue-after-1280-20261019.png`: viewport and screenshot 1280 x 720 CSS/device pixels, density 1. The concept was normalized from 1672 x 941 to the same 1280 x 720 comparison frame; its subpixel aspect-ratio difference is negligible, not a font/layout measurement source.
- Actual combined full-view input: `gvy-deep-blue-source-candidate-20261019.png`, 2560 x 720, source left/candidate right. Actual combined focused input: `gvy-deep-blue-focused-comparison-20261019.png`, 2560 x 380, corresponding filter/list/detail regions. Both were opened and reviewed together, not inferred from separate views.
- `gvy-deep-blue-before-after-20261019.png` compares the real production baseline against the candidate at identical viewport, route, content and independent QA storage. The concept's favorite count is 1 versus QA's 0; no user storage was changed. Generated geometry/text differences are intentional exclusions: the existing real page is authoritative for layout, fonts, exact labels and assets.
- Additional opened evidence: `gvy-deep-blue-detail-390-20261019.png`, `gvy-deep-blue-main-3440-20261019.png`, final `gvy-deep-blue-plan-card-20261019.png`, `gvy-deep-blue-task-card-20261019.png`, `gvy-deep-blue-mineral-card-20261019.png`. Other captures cover 320/1920/2560, filter-open, signal-open and keyboard-focus states. An early ultrawide capture had a transient compositing artifact after rapid resizing; a two-animation-frame recapture and DOM hit-testing confirmed one header/shell and correct content, with no product edit required.
- Material-row focused comparison: `gvy-deep-blue-material-row-comparison-20261019.png`, source reward-list screenshot left (1618 x 550 normalized to 809 x 275), actual plan table right (684 x 206 crop at density 1). Shared fill/highlight/shadow is the target; retaining the plan's three columns, 13px names and original contents is intentional, not a request to copy the reward list's two-column layout or smaller typography.

## Findings And Fidelity

- No actionable P0/P1/P2 issue remains in the inspected local candidate. The first pass was incomplete: the user identified a P1 omission in primary elevation and later a P2 header edge mismatch. These are fixes, not intentional deviations. See comparison history below; the earlier pass must not be used as proof of final acceptance.
- Fonts/typography: original system/Inter fallback chain, weights, sizes, line heights, letter spacing and wrapping retained. Detail 30px, result/plan names 21px white, material names 18px mint; muted metadata and original disabled/placeholder treatment remain. No generated lettering or robot typography was copied.
- Spacing/layout rhythm: final 404 non-paint CSSOM entries match the original 401 after an explicit allowlist for header/summary insets, outer corners, header track sizing and three material-row presentation rules. Across 14 widths/42 states, 29,260 snapshot values were inspected; fonts stay unchanged, main/mineral geometry outside the header correction and its natural height offset has maximum difference 0. Plan numeric geometry is intentionally not compared to the old contiguous table: the new separated rows are checked independently in 72 bounded-content scenarios at 18 sizes. Compact dialog widths, existing columns and control targets remain.
- Colors/tokens: solid opaque navy surfaces, continuous 1px highlights, stronger shared exterior/contact shadows, beveled control edges and recessed inputs. The structural page wrapper is transparent, leaving independent main panels visible. The concept's uneven gradients were intentionally removed per user correction. All main panel computed background images are `none`, opacity 1. A 256-pixel empty filter-panel sample is uniformly RGB(16,47,72). Normal white/muted/gold/cyan/mint/task-type/source text tokens have minimum measured contrast 6.27:1 against the final tested normal/hover panel fills; this is not a claim about disabled or placeholder text.
- Image quality/assets: existing real Star Citizen/GVY logos retain their exact files, dimensions and crop; no SVG/CSS substitute, generated logo, stock imagery, new asset or dependency. The bot card's image, watermark and grid are not imported. No decorative textures or blurry panel fills.
- Copy/content: application HTML/JS/data are unchanged. Real record names, exact source types/systems, quantities, quality thresholds, mission pools and unit/total time semantics retain the approved presentation and calculations. No mock labels or explanatory design copy leaked into the app.
- States/accessibility: selected/hover controls remain distinct, search/filter/empty states work, keyboard Tab/Shift+Tab yields the native visible focus outline, plan Enter/Escape works, quality fresh typing/keyboard/click synchronize, mineral hover bridge and signal-first Escape work. Touch-enabled 390px Chromium can open minerals, directly select a neighboring signal, close, and open/close the plan.

## Verification

- Final whole-page widths: 320, 390, 620, 621, 720, 721, 880, 881, 1100, 1101, 1320, 1321, 1366, 1440, 1920, 2560, 3440, 3840; short-window dialogs additionally 760 x 320 and 1100 x 420. Main panel edges and every actual header action fit, not merely their parent containers. No finite test suite proves every possible physical screen.
- First-pass exhaustive dialogs at nine sizes render every 672 tasks and 37 minerals: 6,048 task dialogs and 333 mineral dialogs, expanded content/text bounds, accessible body/footer and no unnecessary width growth. Final header/shared-color corrections do not change task/mineral geometry; final pointer/keyboard/touch checks reopen their actual surfaces. No raw-data mutation or application warnings/errors.
- Thirteen material widths render all 1,618 recipes: 56,108 material rows and 48,334 quality controls. Names/metadata/amounts stay inside their columns, sliders are equal-length within each list, modifiers share their left edge, explicit minima above 1 stay visible and hidden 1 values remain in the data. No application warnings/errors.
- Seven widths also render all 1,618 details and 52,332 task-source rows, checking exact type/system order, distinct text colors, text bounds and adjacent-row separation. Actual task links open/close their exact dialog. These content checks preceded the final color-only strengthening; main content geometry remains unchanged.
- Final plan-specific checks: 18 sizes x four scenarios (empty, unavailable ID, two real items and 100 items at quantity 9999). Material rows retain three columns, full text, shared background/shadow and 4px separation; dialogs stay bounded. No raw-data mutation or application warnings/errors.
- 161 Python tests including 38 Node tests, standalone 38 Node tests, JS syntax, build, diff checks and offline blueprint/mining version-pair validation pass. The historical contiguous-table assertion was updated to the explicitly requested separated-row style; business behavior assertions remain. No HTML/JS/data/workflow diff.
- Browser plugin/skill unavailable; existing independent Playwright Chromium was used under the user's explicit all-size approval. The user-facing in-app tab is refreshed and preserved without changing favorites or plan. Physical iOS, Safari and QQ browser are not tested.

## Implementation Checklist

1. Before-change source/dist/handoff backup and checkpoint retained; archive integrity and hashes checked.
2. Paint-only CSS, shared surface/shadow roles and scoped regression tests complete.
3. Combined visual comparison, responsive geometry, content and interaction checks complete.
4. Local branch/checkpoint and handoff saved; preview remains available. No publication performed.

## Comparison History

1. Initial local pass had subtle shadows but retained the unframed header/summary and surrounding page card. The user correctly reported missing primary elevation (P1). Evidence retained under `iteration-1/`. Added the joined opaque raised header, shared dialog/control roles and continuous edge treatment; subsequent user review requested more faithful depth, so the old wrapper paint was removed and shared edge/contact/ambient shadows strengthened without gradients.
2. User screenshot `截屏2026-10-19 10.06.13.png` identified the header's left edge extending beyond other panels (P2). The original header had no side margin, unlike filter/workbench. Added their exact responsive inset to header/summary. Descendant checks then found a phone and 1101px version pill crossing the surface despite its parent fitting (P2). Header tracks now reserve actual action minima and let search flex, with no changed navigation or breakpoint. Final 18-size edge/control checks and same-state captures pass.
3. During header-band review, a square filter-heading fill covered rounded corners (P2). Removed that child fill, using the parent's uniform surface; menus remain unclipped. Resized screenshots also required two animation frames before capture to avoid transient compositor duplication; this was capture stabilization, not a product change.
4. User requested plan material rows to match the task reward-row effect. Retained the existing 50/22/28 percent table columns and values, adding shared row fill/elevation, 4px gaps and 4px row corners. Final 72 plan scenarios and screenshots pass. No unit-time move, quality unification or calculation changes.

## Historical QA Reports

The reports below are history, not authority to deploy this local skin candidate.

## Reviewed Release Candidate, 2026-10-19

- The user has now authorized review and safe deployment. Earlier local-only statements below describe historical checkpoints, not a continuing publication ban.
- Ten code checkpoints were picked onto the production baseline; four local preview-data commits were excluded. The candidate data comes from successful cloud preparation run `39166743008`, head `81d6eb60d9fefdd99c5f6747c74faafe84c738b0`, with a verified 14-day backup matching all six original production inputs. Preparation skipped publishing and production-health steps by design.
- Candidate revision `data-0f6906d31548ddd6`, exact stable LIVE `4.10.2-live.12913470`: 1618 blueprint records, 672 tasks, 37 materials, 36 located, 603 location associations and 531 signal associations. Recipe numeric values match the production baseline. Reviewed preview records, reward gameplay fields, item metrics and mineral contents are unchanged; six reward items gained Chinese fallback names.
- 137 Python tests (including 29 Node checks), standalone Node checks, JavaScript syntax, YAML parsing, diff checks, build and paired-version validation pass. Full candidate rendering at 320/390/1920/2560/3440 checks all 1618 manufacturing and 1596 dismantling records without text overflow or quality-capsule sizing errors; all 672 task dialogs pass at 390px, including the newly translated reward names.
- Pointer, keyboard and touch-enabled Chromium checks cover quality limits/fresh typing, clipboard-denied sharing, missing IDs, plan persistence/quantity scaling, independent 17/7 pools, signal opening/dismissal/filter/template/resize cleanup and focus restoration. Browser plugin/skill not available; existing Playwright used under prior explicit authorization. No dependencies were installed; physical iOS, QQ and Safari remain untested.
- Candidate evidence: `/tmp/gvy-release-desktop.png`, `/tmp/gvy-release-mobile.png`, `/tmp/gvy-primary-quality-1920-20261019.png`, `/tmp/gvy-mineral-popover-touch-390-20261019.png`. Formal deployment acceptance is recorded in the required external handoff after merge; preparation or localhost success alone is not production proof.
- Signal-button occlusion remains explicitly deferred. No trigger-avoidance placement or count-based table is introduced by this release.

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
- Runtime screenshots and temporary QA harnesses live outside the site and are not production assets. The local-only acceptance below is historical; publication now follows the reviewed cloud-candidate procedure above and separate formal-domain verification.
