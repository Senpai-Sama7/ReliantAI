# ClearDesk Design Directive

## Aesthetic Direction
Premium operational intelligence. Bloomberg Terminal meets Linear.app. Expensive without being decorative. "Software a hedge fund would build internally and never release publicly."

## Typography
- Headings: "Clash Display" or "Syne" (Google Fonts)
- Body/UI: "DM Sans"
- Numbers/data: "JetBrains Mono"
- Aggressive size contrast — hero numbers 48px+, labels 11px
- Use `font-display: swap` to prevent FOUT

## Color System
- Background: #0A0A0F
- Surface: #111118
- Border: #1E1E2E
- Text primary: #F0F0F5
- Text secondary: #6B6B80
- Accent: #00FF94 — MAX 3 elements per screen. When tempted to use it, use text-secondary instead.
- Danger: #FF4444
- Warning: #FFB800

## Layout
- Dark left sidebar, 240px fixed
- Main content: generous padding (48px)
- Card grid: 16px gap
- Cards: bg #111118, border 1px solid #1E2030, border-radius 8px (NOT 16px — reads cheap)
- NO box shadows — use borders instead

## Motion
- Page load: staggered fade-up on cards, animation-delay increments of 80ms
- Hover: border color shift + subtle translateY(-2px), nothing more
- NO bounce, NO elastic, NO decorative spinning
- NO counting-up number animations — numbers just appear (operational tool, not demo toy)

## Data Tables
- Compact row height (40px), no zebra striping
- Subtle bottom borders only
- Header text: 11px uppercase tracking-wide in text-secondary

## Empty/Loading States
- Empty: single line text-secondary, no illustrations, no emoji
- Loading: subtle pulse on card skeletons, same surface color with 5% opacity shift

## Anti-Patterns (DO NOT USE)
- No gradients on text
- No glassmorphism
- No icons without meaning
- No decorative elements
- No rounded-2xl (cheap look)
- No default Tailwind card shadows
- Restraint: every element earns its place. Empty space is intentional.
