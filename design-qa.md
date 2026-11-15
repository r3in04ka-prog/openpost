# Desktop redesign QA

Source: user-supplied `codex-clipboard-4533e056-f825-4da3-b693-e29e580edf22.png` (749 × 458).
Implementation: `release/preview-final-design.png`, captured on Windows from commit e17b9ff.
Comparison: `release/design-comparison-final.png` (source and implementation in a single image).
Viewport: 960 × 620 Tk content pixels, desktop demo, first letter selected, dark theme.
Normalization: the photographed source's application region (26,14)-(728,440) was cropped and scaled to 960 × 583; implementation is a native 960 × 620 capture. This is a native desktop redesign, not a browser prototype. Windows title bars, photographed frame and macOS traffic lights are outside scope.

## Findings and iterations

- Initial 0.2.0 capture: missing navigation icons, excessive message-row height, clipped clinic photograph and empty search hint (P2).
- Added licensed Lucide icons and neutral sender markers; reduced message row heights to show all six demo messages; resized the demo photograph and simplified its text block; added an explicit empty-search hint.
- Final combined comparison: the search hint is visible, six messages fit, the reading text is complete and the photograph fits above the reply action. Main columns and persistent controls are visible at the minimum viewport.

## Fidelity surfaces

- Typography: Segoe UI, compact 11–14 px list text, 17 px bold reading title. A Windows font substitution and slightly different density from the photographed source are expected. No text overlaps in the capture.
- Spacing: three-column shell, rounded compose button, compact message cards and rounded paper reader. Native window geometry replaces the photographed device frame. Content and controls fit at 960 × 620.
- Colors: charcoal #1c1e20, sidebar #222426, rose #edb4c2, selected card #634b55, paper #f7f4f2. Warm palette and dark/light balance follow the source.
- Images: generated clinic photograph follows the blush/beige architectural direction. Neutral Lucide sender icons replace contact portraits because this version has no contact-photo integration. No invented Gmail/iCloud/Outlook accounts or logos are displayed. The demo photograph is explicitly synthetic and never substituted into a real letter.
- Copy: Russian compose, search, inbox, filters and reply controls. Unsupported folders are subdued and explain their limits on click. Only one real account is supported. Unread/snooze/draft controls from the reference are intentionally omitted because those features are absent.

The full-view comparison is readable at native size; no further focused crop was required for this small desktop surface.

## Interaction verification

Windows GUI smoke tests cover loading/selecting demo letters, searching to empty and back, marking important, filtering important/newsletters/people and opening the connection dialog. Mail tests verify MIME parsing, recipient/header validation, IMAP read-only/PEEK, SMTP TLS and partial-recipient refusal. The release job additionally installs the packaged executable, checks its window opens, closes it and verifies uninstallation. No live mailbox credentials are used. Browser console checks do not apply to Tk.

## Follow-up polish

- P3: contact portraits and richer email imagery require separate contact/HTML integration.
- P3: unified multi-account navigation needs actual account management before showing multiple provider rows.
- P3: native background lacks the photographed reference's translucent material and soft outer shadow.

final result: passed
