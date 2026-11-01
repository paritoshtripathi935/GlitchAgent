# GlitchAgent design system

Terminal-adjacent and precise: near-black surfaces, one signal-green accent for actions and live state. Tokens live in `src/index.css`; components use only the Tailwind names in the token tables below (`bg-surface`, `text-muted`, `border-line-strong`, `text-h2`…). A component that hard-codes a hex value or a pixel font size is a bug.

This file was produced by running the `ui-design` plugin: `color-palette` (with `color-system`, `dark-mode-design`), `type-system` (with `typography-scale`, `visual-hierarchy`, `spacing-system`, `layout-grid`, `responsive-design`) and `responsive-audit`. Neither app has charts, so `data-visualization` did not apply.

## Color

### Tonal scales
Use these when you need a new tint, for example a badge background. Semantic tokens are picked from or near these scales.

| | 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 | 950 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Signal green | `#effcf5` | `#e0f9eb` | `#c1f4d8` | `#9eeec2` | `#6ee5a3` | `#3ddc84` | `#32b46c` | `#278d54` | `#1d6a3f` | `#154b2d` | `#0c2c1a` |
| Neutral | `#f3f4f5` | `#e7e8eb` | `#d0d2d6` | `#b5b8c0` | `#9095a0` | `#6b7280` | `#585d69` | `#444952` | `#33373d` | `#24272c` | `#15171a` |

### Semantic tokens

| Token (Tailwind) | Role | Dark | Light |
|---|---|---|---|
| `bg` | Page background | `#08090b` | `#f5f6f3` |
| `surface` | Sidebars, cards, composer | `#0e1013` | `#ffffff` |
| `raised` | Inputs, nested cards | `#14171c` | `#eff1ed` |
| `hover` | Hover/selected rows | `#1b1f26` | `#e5e8e2` |
| `line` | Dividers (decorative) | `#262b33` | `#d7dbd3` |
| `line-strong` | Input edges (≥3:1) | `#676b70` | `#81837f` |
| `fg` | Primary text | `#eef1f4` | `#0f1411` |
| `muted` | Secondary text | `#a3acb7` | `#4b544e` |
| `dim` | Metadata, timestamps | `#838c97` | `#5c655f` |
| `accent` | Primary action, active state, links | `#3ddc84` | `#0b763e` |
| `ink` | Text on accent | `#04130a` | `#ffffff` |
| `success` | Done states | `#3ddc84` | `#0b763e` |
| `warn` | Running / pending | `#fbbf24` | `#975600` |
| `danger` | Errors, destructive | `#f87171` | `#c42828` |
| `info` | Informational | `#60a5fa` | `#1d4ed8` |

Tint backgrounds for status come from opacity (`bg-danger/10`), not extra tokens.

### Contrast matrix (WCAG 2.1)

Minimum ratio of each foreground against `bg`, `surface`, `raised` and `hover`. AA needs 4.5 for text and 3.0 for UI boundaries.

| Foreground | Dark (min) | Light (min) | Status |
|---|---|---|---|
| `text` | 14.6 | 15.0 | ✅ AA |
| `muted` | 7.2 | 6.3 | ✅ AA |
| `dim` | 4.9 | 4.9 | ✅ AA |
| `accent` | 9.3 | 4.6 | ✅ AA |
| `success` | 9.3 | 4.6 | ✅ AA |
| `warn` | 9.9 | 4.7 | ✅ AA |
| `danger` | 6.0 | 4.6 | ✅ AA |
| `info` | 6.5 | 5.4 | ✅ AA |
| `border-strong` | 3.1 | 3.1 | ✅ AA (UI) |
| `ink` on `accent` | 10.7 | 5.7 | ✅ AA |

Status is never shown by color alone: badges carry a text label, and missing wiki links are dashed as well as dimmed.

### Dark mode

- Both themes are first-class. With no saved choice the app follows `prefers-color-scheme`; the toggle saves a choice to `localStorage`, and an inline script in `index.html` applies it before first paint, so there is no flash.
- Elevation in dark mode comes from lighter surfaces (`bg` → `surface` → `raised` → `hover`), not shadows.
- Text is off-white rather than `#fff`. The accent is a deeper shade in light mode so it still reaches ≥4.6:1.

## Typography

Fonts: Space Grotesk (display) · Inter (UI/body) · JetBrains Mono (commands, actions).

The scale is a major third (×1.25) from 16px. Every line height is a multiple of 4px, which puts text on the baseline grid.

| Class | Size / line | Tracking | Use |
|---|---|---|---|
| `text-display` | 56 / 64 | −0.02em | Landing hero (≥640px) |
| `text-h1` | 40 / 48 | −0.02em | Hero on phones; section titles (≥768px); note title (≥640px) |
| `text-h2` | 32 / 40 | −0.02em | Page titles; section titles on phones |
| `text-h3` | 24 / 32 | −0.01em | Card and modal headings |
| `text-sub` | 20 / 28 | 0 | Lead paragraphs, wordmark |
| `text-body` | 16 / 24 | 0 | Body copy (minimum for reading text) |
| `text-small` | 14 / 20 | 0 | UI chrome: buttons, nav, rows, inputs |
| `text-caption` | 12 / 16 | 0 (wider when uppercase) | Metadata, timestamps, eyebrows |

- Weights: 400 for body, 500 for UI emphasis, 600 for headings and buttons. Don't go above 600 except in the logo.
- Uppercase labels use `tracking-wider` (0.05em).
- Long-form paragraphs use `leading-7` (28px).
- Measure: landing copy is capped at `max-w-xl`. The console is capped at `max-w-3xl`; there is no long-form reading text.

## Spacing

The base unit is 4px. The scale in use is 2, 4, 8, 12, 16, 24, 32, 48, 64 and 96px (Tailwind `0.5`, `1`, `2`, `3`, `4`, `6`, `8`, `12`, `16`, `24`). Don't use other values.

| Intent | Steps |
|---|---|
| Inline (icon ↔ label) | 4–8 |
| Inset (buttons, inputs) | 12–16 horizontal, controlled by height |
| Stack inside a component | 8–16 |
| Between groups | 24–48 |
| Landing sections | 96 vertical |

## Layout grid and breakpoints

- **Breakpoints:** Tailwind defaults: `sm` 640, `md` 768, `lg` 1024, `xl` 1280.
- **Landing:** contained in `max-w-6xl` (1152px), with 16px margins on phones and 24px from `sm`. The hero is 1 column on phones and 2 from `lg`; feature grids go 1 → 2 → 3 columns.
- **App:** sidebar plus content from `md` (232px rail); on phones the rail becomes a top bar with icons only. Content uses 16px gutters, 32px from `sm`.
- **Touch:** interactive controls are at least 44px tall on coarse pointers (`pointer-coarse:h-11`) and at least 24px with a mouse.

## Responsive audit (2026-11-01)

Measured in the browser at 375, 768 and 1440px. Phones were emulated with touch, so `pointer: coarse` applies.

| Check | Result |
|---|---|
| Horizontal overflow | None at any width. **Fixed:** the app top bar was 384px wide at 375px; the wordmark now hides below `md`. |
| Touch targets (coarse) | All ≥44px. **Fixed:** "+ Add context" (16px), the empty-history link (20px) and the icon buttons (36px). |
| Pointer targets (fine) | All ≥24px. **Fixed:** landing nav links (20px → 36px). |
| Smallest text | 12px (captions) |
| Line length | 32 / 54 / 47 characters at 375 / 768 / 1440px |

**Known gaps:** none open.
