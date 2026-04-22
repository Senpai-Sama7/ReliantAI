# Progressive Luxury Email Architecture — v2.0
## Production Bible: Enhanced & Corrected

---

## CRITICAL CORRECTIONS TO COMMON IMPLEMENTATIONS

Before the guide: five bugs found in standard "premium email" templates that silently break in production.

### Bug 1 — Accordion `display:none` on inputs (breaks `:checked` in Apple Mail 16.x)
❌ Wrong:
```html
<input type="checkbox" id="faq1" style="display: none;">
```
✅ Correct — visually hidden without removing from accessibility tree or blocking `:checked`:
```html
<input type="checkbox" id="faq1" style="
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;">
```
The `display:none` approach removes the element from CSS selector targeting in several Apple Mail
versions. The position/opacity approach preserves pseudo-class reactivity.

### Bug 2 — Accordion `max-height` transition requires same-scope CSS declaration
❌ Wrong — transition on inline style, state change in `<style>` tag won't reliably trigger:
```html
<div style="max-height: 0; transition: max-height 0.5s ease;">
<style>#faq1:checked + div { max-height: 500px; }</style>
```
✅ Correct — keep both the base state AND transition declaration in the same `<style>` block:
```css
/* In <style> tag */
.acc-body {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: max-height 0.65s cubic-bezier(0.16, 1, 0.3, 1),
              opacity 0.4s ease;
}
#faq-1:checked ~ .acc-body { max-height: 300px; opacity: 1; }
```

### Bug 3 — VML `<v:textbox>` in hero sections needs `mso-fit-shape-to-text:true`
Without this, Outlook clips the VML box to its declared pixel height
and cuts off dynamic content.
```xml
<!-- CORRECT -->
<v:textbox style="mso-fit-shape-to-text:true" inset="32px,72px,32px,64px">
```

### Bug 4 — CSS Custom Properties not supported in Outlook (Windows)
Outlook's rendering engine (Word HTML engine) has zero support for
`var(--token)`. Every Outlook override must use literal values in an
MSO-conditional `<style>` block. Failing to do this means Outlook
renders completely unstyled elements.

### Bug 5 — AMP for Email deprecation status
Google significantly reduced AMP email support in 2023. Do NOT build
primary email flows on AMP. Use CSS-only interactivity for broad
coverage. AMP is viable only as an optional enhancement layer for
confirmed Gmail Web audiences with AMP pre-registration.

---

## PHASE 1 — DESIGN TOKEN ARCHITECTURE

### Complete Token System

Tokens defined at `:root` level for Tier 1/2 clients. Literal values
repeated in MSO conditional block for Tier 3 (Outlook).

```css
:root {
  /* ── Palette ──────────────────────────────────────────── */
  --void:        #0A0905;    /* Deepest background */
  --deep:        #141210;    /* Elevated background */
  --surface:     #1E1B16;    /* Card surfaces */
  --raised:      #2A2620;    /* Highest surface */
  --divider:     rgba(201, 168, 76, 0.12);

  --paper:       #F4EFE6;    /* Primary text — warm white */
  --paper-dim:   #C8BEA8;    /* Secondary text */
  --paper-muted: #7A7268;    /* Tertiary text */
  --paper-ghost: #3A3630;    /* Disabled */

  --gold:        #C9A84C;    /* Primary accent */
  --gold-bright: #E5C76E;    /* Hover/active accent */
  --gold-dim:    #8B6B28;    /* Subdued accent */
  --gold-glow:   rgba(201, 168, 76, 0.18);

  /* ── Typography ──────────────────────────────────────── */
  /* Email-safe stack: web font → quality fallback → universal fallback */
  --font-serif: 'Cormorant Garamond', 'EB Garamond', Georgia,
                'Times New Roman', Times, serif;
  --font-sans:  'Source Sans 3', 'Optima', 'Gill Sans MT',
                'Trebuchet MS', Verdana, Geneva, sans-serif;

  /* ── Spacing (8pt grid) ──────────────────────────────── */
  --sp-4:  16px;   --sp-6:  24px;   --sp-8:  32px;
  --sp-10: 40px;   --sp-12: 48px;   --sp-16: 64px;
  --sp-20: 80px;

  /* ── Motion ──────────────────────────────────────────── */
  --ease-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-back: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

### JSON Export (Figma Variables / Style Dictionary)
```json
{
  "color": {
    "void":        { "value": "#0A0905", "type": "color" },
    "gold":        { "value": "#C9A84C", "type": "color" },
    "paper":       { "value": "#F4EFE6", "type": "color" },
    "email-safe-gray": { "value": "#333333", "type": "color",
                         "description": "Outlook-safe fallback for all dark text" }
  },
  "spacing": {
    "base":   { "value": "8px", "type": "sizing" },
    "content-pad": { "value": "32px", "type": "sizing",
                     "mobile": "20px" }
  },
  "typography": {
    "display": {
      "fontFamily": { "value": "{font-serif}" },
      "fontSize":   { "value": "56px", "mobile": "38px" },
      "fontWeight": { "value": "300" },
      "lineHeight": { "value": "1.04" },
      "letterSpacing": { "value": "-0.025em" }
    },
    "eyebrow": {
      "fontFamily": { "value": "{font-sans}" },
      "fontSize":   { "value": "10px" },
      "fontWeight": { "value": "600" },
      "letterSpacing": { "value": "0.22em" },
      "textTransform": { "value": "uppercase" }
    }
  }
}
```

---

## PHASE 2 — TECHNICAL STACK

### Progressive Enhancement Matrix (Complete)

| Feature               | Tier 1: Apple/iOS/Samsung | Tier 2: Gmail/Yahoo/Outlook.com | Tier 3: Outlook Win |
|-----------------------|---------------------------|---------------------------------|---------------------|
| **Layout engine**     | Flexbox + CSS Grid        | Table + CSS (Gmail strips flex) | Pure tables         |
| **Custom fonts**      | Google Fonts via `<link>` | System font fallback            | MSO font stack only |
| **CSS custom props**  | Full support              | Full support (stripped Gmail)   | ❌ Literal values   |
| **CSS animations**    | Full: keyframes, delays   | ❌ Static                       | ❌ Static           |
| **Hover states**      | ✅ `transition`, `:hover` | ❌ Stripped                     | ❌ Stripped         |
| **CSS Grid**          | ✅ Full                   | ❌ Tables required              | ❌ Tables required  |
| **Dark mode**         | `prefers-color-scheme`    | `[data-ogsc]` + `[data-ogsb]`  | ❌ Force-light       |
| **VML backgrounds**   | N/A (uses CSS gradient)   | N/A                             | ✅ Required         |
| **Bulletproof button**| CSS `<a>` with padding    | CSS `<a>` with padding         | VML `<v:roundrect>` |
| **CSS `position`**    | ✅ All values             | Partial (absolute risky)       | ❌ Static only      |
| **`border-radius`**   | ✅                        | ✅ Gmail                       | ❌ Use `arcsize`    |
| **Image `object-fit`**| ✅                        | ✅ Modern clients               | ❌ Needs height fix  |
| **`<picture>` + srcset**| ✅                       | ❌ Stripped                     | ❌ Not supported    |
| **SVG images**        | ✅                        | Gmail strips inline SVG        | ❌ Use PNG          |
| **WebP images**       | ✅                        | ✅ Gmail                       | ❌ Use JPG fallback  |
| **Interactivity**     | CSS checkbox/radio hack   | ❌ Stripped                     | ❌ Stripped          |
| **AMP for Email**     | ❌ Not supported          | ⚠️ Partial (pre-reg required) | ❌                  |
| **`mso-hide: all`**   | Ignored (shows content)   | Ignored (shows content)        | ✅ Hides content    |

---

## PHASE 3 — THE COMPLETE HTML DOCUMENT SKELETON

Every structural element explained:

```html
<!DOCTYPE html>
<html lang="en" dir="ltr"
  xmlns:v="urn:schemas-microsoft-com:vml"
  xmlns:o="urn:schemas-microsoft-com:office:office">
<!--
  xmlns:v — Required for VML (Vector Markup Language), which is how
  Outlook renders background images, gradient fills, and rounded buttons.
  Without this namespace declaration, ALL VML in the document silently fails.
  
  xmlns:o — Required for Office-specific XML elements like
  <o:OfficeDocumentSettings> which controls Outlook's rendering DPI.
-->
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  
  <!--
    x-apple-disable-message-reformatting:
    Prevents Apple Mail on iOS from resizing and repositioning your
    email to fit the screen width. Without this, narrow emails get
    auto-scaled in unpredictable ways.
  -->
  <meta name="x-apple-disable-message-reformatting">
  
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  
  <!--
    format-detection:
    Prevents iOS, Android, and some desktop clients from automatically
    converting phone numbers, dates, addresses, emails, and URLs into
    tappable links (which override your styling with blue underlines).
  -->
  <meta name="format-detection" content="telephone=no, date=no, address=no, email=no, url=no">
  
  <!--
    color-scheme declarations:
    Tell supporting clients this email handles both color schemes.
    Without this, Gmail and some iOS versions may auto-invert your
    colors thinking you haven't considered dark mode.
  -->
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:AllowPNG/>
        <!--
          PixelsPerInch: Forces Outlook to render at 96dpi instead of
          its default auto-scaling. Without this, Outlook may render
          images and layout at incorrect sizes based on display resolution.
        -->
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  
  <!-- Web fonts: only load in clients that support them -->
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400&family=Source+Sans+3:wght@300;400;600&display=swap" rel="stylesheet">

</head>
```

### The Platform-Specific Link Targeting Triad
```css
/* 1. iOS / Apple Mail — kills blue data-detector links */
a[x-apple-data-detectors] {
  color: inherit !important;
  text-decoration: none !important;
  font-size: inherit !important;
  font-family: inherit !important;
  font-weight: inherit !important;
  line-height: inherit !important;
}

/* 2. Gmail — "u + #body" is the selector Gmail uses for its wrapper div.
   This targets only Gmail-rendered content and prevents their
   auto-resize override for text in forwarded email threads. */
u + #body a {
  color: inherit;
  text-decoration: none;
}

/* 3. Samsung Mail — Samsung Mail injects its own link targets */
#MessageViewBody a {
  color: inherit;
  text-decoration: none;
}
```

---

## PHASE 4 — BULLETPROOF COMPONENTS

### Bulletproof CTA Button (All Three Tiers)

The critical pattern: VML `<v:roundrect>` for Outlook wrapped in
MSO conditionals, with standard `<a>` for everyone else. Both
reference the same href. Both display the same text.

```html
<!-- Solid filled button -->
<!--[if mso]>
<v:roundrect
  xmlns:v="urn:schemas-microsoft-com:vml"
  xmlns:w="urn:schemas-microsoft-com:office:word"
  href="https://example.com"
  style="height:52px; v-text-anchor:middle; width:220px;"
  arcsize="4%"
  stroke="f"
  fillcolor="#C9A84C">
  <w:anchorlock/>
  <center style="font-family:'Trebuchet MS',sans-serif;font-size:11px;font-weight:600;letter-spacing:0.2em;text-transform:uppercase;color:#0A0905;">
    View Collection
  </center>
</v:roundrect>
<![endif]-->

<!--[if !mso]><!-->
<a href="https://example.com" style="
  display: inline-block;
  background-color: #C9A84C;
  color: #0A0905;
  font-family: 'Source Sans 3', 'Trebuchet MS', sans-serif;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  text-decoration: none;
  padding: 17px 38px;
  border-radius: 2px;
  line-height: 1;
  mso-line-height-rule: exactly;">
  View Collection
</a>
<!--<![endif]-->
```

### Ghost/Outlined Button (Tier 3 VML with stroke)

```html
<!--[if mso]>
<v:roundrect
  xmlns:v="urn:schemas-microsoft-com:vml"
  xmlns:w="urn:schemas-microsoft-com:office:word"
  href="https://example.com"
  style="height:52px; v-text-anchor:middle; width:208px;"
  arcsize="4%"
  stroke="t"
  strokecolor="#C9A84C"
  strokeweight="1pt"
  fill="f">
  <w:anchorlock/>
  <center style="font-family:'Trebuchet MS',sans-serif;font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;">
    Book Appointment
  </center>
</v:roundrect>
<![endif]-->
<!--[if !mso]><!-->
<a href="https://example.com" style="
  display: inline-block;
  border: 1px solid #C9A84C;
  color: #C9A84C;
  font-family: 'Trebuchet MS', sans-serif;
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  text-decoration: none;
  padding: 17px 36px;
  line-height: 1;">
  Book Appointment
</a>
<!--<![endif]-->
```

### VML Background Image (Bulletproof)

The ONLY way to get background images in Outlook Windows:

```html
<!--[if mso]>
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<v:rect xmlns:v="urn:schemas-microsoft-com:vml"
        fill="true" stroke="false"
        style="width:600px; height:400px;">
  <!-- Gradient fill -->
  <v:fill type="gradient"
          color="#0A0905"
          color2="#2A2620"
          angle="135"
          focus="50%" />
  <!-- OR: Image fill -->
  <!--
  <v:fill type="frame"
          src="https://example.com/hero-bg.jpg"
          color="#0A0905" />
  -->
  <v:textbox style="mso-fit-shape-to-text:true" inset="32px,64px,32px,56px">
<![endif]-->

<div style="background: linear-gradient(135deg, #0A0905, #2A2620); padding: 64px 32px;">
  <!-- Content here renders in both Outlook (inside VML textbox) 
       and modern clients (inside the div) -->
  <h1 style="color: #F4EFE6;">...</h1>
</div>

<!--[if mso]>
  </v:textbox>
</v:rect>
</td>
</tr>
</table>
<![endif]-->
```

---

## PHASE 5 — DARK MODE: COMPLETE FOUR-VECTOR IMPLEMENTATION

### Vector Coverage Map

```
Email Client              Dark Mode Vector              CSS Selector
─────────────────────     ──────────────────────────    ────────────────────────────────
Apple Mail (macOS 13+)    prefers-color-scheme: dark    @media (prefers-color-scheme: dark)
iOS Mail (16+)            prefers-color-scheme: dark    @media (prefers-color-scheme: dark)
Outlook Mac (2019+)       prefers-color-scheme: dark    @media (prefers-color-scheme: dark)
Samsung Mail (11+)        prefers-color-scheme: dark    @media (prefers-color-scheme: dark)
Thunderbird               prefers-color-scheme: dark    @media (prefers-color-scheme: dark)
Gmail Web (Chrome DM)     Gmail data attribute          [data-ogsc]
Gmail Web (Firefox DM)    Gmail data attribute          [data-ogsc]
Gmail Android             Gmail data attribute          [data-gmail-darkreader]
Outlook.com (DM)          Microsoft data attribute      [data-ogsb]
Yahoo Mail                ❌ No reliable targeting       Force-test light mode elements
Outlook Win               ❌ No dark mode support        Force-light via mso-background
```

### Complete Dark Mode CSS Block

```css
/* ── Vector 1: Native dark mode ─────────────────────────────── */
@media (prefers-color-scheme: dark) {
  body,
  .outer-table { background-color: #0A0905 !important; }

  .bg-surface  { background-color: #1E1B16 !important; }
  .bg-deep     { background-color: #141210 !important; }

  .text-primary   { color: #F4EFE6 !important; }
  .text-secondary { color: #C8BEA8 !important; }
  .text-accent    { color: #C9A84C !important; }

  /* Invert light-mode-only content */
  .lm-only { display: none !important; max-height: 0 !important; overflow: hidden !important; }
  .dm-only { display: block !important; }

  /* Prevent Gmail from re-inverting our intentionally dark elements */
  .dm-preserve { background-color: #1E1B16 !important; }
}

/* ── Vector 2: Gmail Web ─────────────────────────────────────── */
[data-ogsc] body,
[data-ogsc] .outer-table { background-color: #0A0905 !important; }
[data-ogsc] .bg-surface  { background-color: #1E1B16 !important; }
[data-ogsc] .text-primary   { color: #F4EFE6 !important; }
[data-ogsc] .text-secondary { color: #C8BEA8 !important; }
[data-ogsc] .text-accent    { color: #C9A84C !important; }
[data-ogsc] .lm-only { display: none !important; }
[data-ogsc] .dm-only { display: block !important; }

/* ── Vector 3: Gmail Android ─────────────────────────────────── */
[data-gmail-darkreader] body    { background-color: #0A0905 !important; }
[data-gmail-darkreader] .bg-surface { background-color: #1E1B16 !important; }
[data-gmail-darkreader] .text-primary { color: #F4EFE6 !important; }
[data-gmail-darkreader] .text-accent  { color: #C9A84C !important; }

/* ── Vector 4: Outlook.com / Hotmail ────────────────────────── */
[data-ogsb] body        { background-color: #0A0905 !important; }
[data-ogsb] .bg-surface { background-color: #1E1B16 !important; }
[data-ogsb] .text-primary { color: #F4EFE6 !important; }
```

### Dark Mode Image Swap Strategy

For logos/images that need different versions in light vs dark:

```html
<!-- Light mode image (hidden in dark mode) -->
<img class="lm-only" src="logo-dark.png" alt="Brand Logo" width="120"
  style="display:block;">

<!-- Dark mode image (hidden in light mode by default, shown via DM CSS) -->
<img class="dm-only" src="logo-light.png" alt="Brand Logo" width="120"
  style="display:none; max-height:0; overflow:hidden;">

<!-- CSS (in media query + data-ogsc selectors) -->
/* @media (prefers-color-scheme: dark) { */
  .lm-only { display: none !important; max-height: 0 !important; }
  .dm-only { display: block !important; max-height: none !important; }
/* } */
```

---

## PHASE 6 — ANIMATION SYSTEM

### Timing Architecture

Use staggered `animation-delay` with `animation-fill-mode: both` to
reveal content sequentially. `both` means:
- Before animation starts: element sits at `from` state (invisible/translated)
- After animation ends: element locks to `to` state (visible/in-place)

This prevents flash of unstyled content while ensuring non-animating
clients (Gmail, Outlook) just see the fully-rendered final state.

```css
@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(28px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Stagger system — increment delays for sequential reveals */
.anim-0 { animation: fadeUp 0.9s cubic-bezier(0.16,1,0.3,1) 0.00s both; }
.anim-1 { animation: fadeUp 0.9s cubic-bezier(0.16,1,0.3,1) 0.12s both; }
.anim-2 { animation: fadeUp 0.9s cubic-bezier(0.16,1,0.3,1) 0.26s both; }
.anim-3 { animation: fadeUp 0.9s cubic-bezier(0.16,1,0.3,1) 0.42s both; }
.anim-4 { animation: fadeUp 0.9s cubic-bezier(0.16,1,0.3,1) 0.58s both; }

/* Scale-in rule animation */
@keyframes scaleX-in {
  from { transform: scaleX(0); transform-origin: left center; }
  to   { transform: scaleX(1); transform-origin: left center; }
}
.anim-rule { animation: scaleX-in 0.7s cubic-bezier(0.16,1,0.3,1) 0.35s both; }

/* Continuous gold shimmer on CTA */
@keyframes gold-shimmer {
  0%   { background-position: -400% center; }
  100% { background-position:  400% center; }
}
.shimmer-gold {
  background: linear-gradient(
    105deg,
    #8B6B28 0%,
    #C9A84C 35%,
    #E5C76E 50%,
    #C9A84C 65%,
    #8B6B28 100%
  );
  background-size: 400% 100%;
  animation: gold-shimmer 3.5s linear infinite;
}
```

### Easing Curve Reference

```
Standard      cubic-bezier(0.4, 0, 0.2, 1)   — Material Design standard
Expo out      cubic-bezier(0.16, 1, 0.3, 1)   — Snappy deceleration, premium feel
Back out      cubic-bezier(0.34, 1.56, 0.64, 1) — Spring overshoot, playful
Circ in-out   cubic-bezier(0.85, 0, 0.15, 1)  — Circular, dramatic
```

---

## PHASE 7 — RESPONSIVE SYSTEM

### Mobile-First Grid Collapse

```css
/* ── Base: two-column flexbox ──────────────────────── */
.grid-2col {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.grid-2col .col {
  flex: 1;
  min-width: 240px;
  max-width: 260px;
}

/* ── Mobile: full-width stacked ──────────────────────── */
@media only screen and (max-width: 620px) {
  .grid-2col .col {
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
  }
  .grid-2col .col + .col {
    margin-top: 24px !important;
  }
}
```

### Outlook Grid (MSO Conditional Tables)

Flex doesn't render in Outlook. Wrap the entire grid in an MSO ghost table:

```html
<!--[if mso]>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="536">
<tr>
<td width="260" valign="top" style="padding-right:16px;">
<![endif]-->

<!-- First column content -->
<div class="col">...</div>

<!--[if mso]>
</td>
<td width="260" valign="top">
<![endif]-->

<!-- Second column content -->
<div class="col">...</div>

<!--[if mso]>
</td>
</tr>
</table>
<![endif]-->
```

---

## PHASE 8 — RETINA / HIRES IMAGE STRATEGY

Email clients don't support `<picture>` or `srcset`. The workaround
is to serve 2x images at the desired display size via `width` attribute:

```html
<!-- 
  Image is physically 520px wide (2x of 260px display width)
  width="260" constrains it to correct display size
  High-DPI screens render at full 520px resolution → crisp
  Standard screens scale down → still looks fine
-->
<img
  src="https://example.com/product-hero@2x.jpg"
  width="260"
  alt="Product name and description"
  style="
    width: 100%;
    max-width: 260px;
    height: auto;
    display: block;
    border: 0;">
```

For full-width images (600px container):
- Serve at 1200px width (2x)
- Set `width="600"` and `max-width: 600px`
- Use `height` attribute only if you need to constrain height (e.g., cropped hero)

---

## PHASE 9 — PREHEADER TEXT ENGINEERING

The preheader (preview text) is the ~150 characters inbox clients
display after the subject line. It's arguably as important as the
subject line for open rates.

### Complete Implementation

```html
<!-- Place immediately after <body> tag, before everything else -->
<div style="
  display: none;
  max-height: 0;
  max-width: 0;
  overflow: hidden;
  opacity: 0;
  font-size: 1px;
  line-height: 1px;
  mso-hide: all;"
  aria-hidden="true">
  
  Your compelling preview text goes here — ideally 85–100 characters.
  
  <!--
    The invisible characters that follow fill Gmail's 150-char
    preview window to prevent body text bleed-through.
    
    &#8199; = FIGURE SPACE (invisible but counts toward character limit)
    &#847;  = COMBINING GRAPHEME JOINER (zero-width, prevents rendering)
    
    Together they form non-printing, non-rendering characters that
    occupy the remaining ~50 characters of preview space.
    
    Number needed: approximately (150 - preview_text_length) characters,
    each "&#8199;&#847;" counts as ~1.5 characters in most clients.
    Use 50+ pairs to be safe.
  -->
  &#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;
</div>
```

---

## PHASE 10 — DELIVERABILITY & AUTHENTICATION

### Authentication Stack (Required for Inbox Delivery)

```
Record Type    DNS Entry                      Purpose
───────────    ─────────────────────────────  ──────────────────────────────────
SPF            TXT @ "v=spf1 include:..."     Authorizes sending servers
DKIM           TXT selector._domainkey        Cryptographic signature per email
DMARC          TXT _dmarc                     Policy: what to do with failures
BIMI           TXT default._bimi             Shows brand logo in inbox (Gmail)
```

### DMARC Policy Progression

Start permissive, tighten as you validate:

```dns
; Phase 1: Monitor only (no enforcement, collect reports)
v=DMARC1; p=none; rua=mailto:dmarc-reports@yourdomain.com; ruf=mailto:dmarc-forensics@yourdomain.com; fo=1;

; Phase 2: Quarantine (unauth goes to spam)
v=DMARC1; p=quarantine; pct=25; rua=mailto:dmarc-reports@yourdomain.com;

; Phase 3: Full reject (required for BIMI)
v=DMARC1; p=reject; rua=mailto:dmarc-reports@yourdomain.com; aspf=s; adkim=s;
```

### BIMI (Brand Indicators for Message Identification)

Displays your brand logo next to the email in Gmail and Apple Mail:

```dns
; Requires p=quarantine or p=reject DMARC
; SVG must be Tiny PS (Tiny Portable/Secure) format — not standard SVG
default._bimi.yourdomain.com TXT "v=BIMI1; l=https://yourdomain.com/logo.svg; a=https://yourdomain.com/bimi-cert.pem"
```

---

## PHASE 11 — REACT EMAIL COMPONENT SYSTEM

Corrected React Email implementation (using proper component API):

```tsx
// components/email/tokens.ts
export const tokens = {
  color: {
    void:    '#0A0905',
    gold:    '#C9A84C',
    paper:   '#F4EFE6',
    dim:     '#C8BEA8',
    surface: '#1E1B16',
  },
  font: {
    serif:  'Georgia, "Times New Roman", Times, serif',
    sans:   '"Trebuchet MS", Verdana, Geneva, sans-serif',
    // Web font string for non-Outlook clients:
    serifFull: '"Cormorant Garamond", Georgia, "Times New Roman", serif',
    sansFull:  '"Source Sans 3", "Trebuchet MS", Verdana, sans-serif',
  },
  space: {
    sm: '16px', md: '24px', lg: '40px', xl: '64px'
  }
} as const;

// components/email/BulletproofButton.tsx
import { Link } from '@react-email/components';
import { tokens } from './tokens';

interface BulletproofButtonProps {
  href: string;
  children: React.ReactNode;
  variant?: 'solid' | 'outline';
  width?: number;
}

export const BulletproofButton = ({
  href,
  children,
  variant = 'solid',
  width = 220,
}: BulletproofButtonProps) => {
  const isSolid = variant === 'solid';

  return (
    <>
      {/* Outlook VML button — rendered via dangerouslySetInnerHTML
          because React Email doesn't have a VML primitive */}
      <div
        dangerouslySetInnerHTML={{
          __html: `
            <!--[if mso]>
            <v:roundrect
              xmlns:v="urn:schemas-microsoft-com:vml"
              xmlns:w="urn:schemas-microsoft-com:office:word"
              href="${href}"
              style="height:52px;v-text-anchor:middle;width:${width}px;"
              arcsize="4%"
              ${isSolid
                ? `stroke="f" fillcolor="${tokens.color.gold}"`
                : `stroke="t" strokecolor="${tokens.color.gold}" strokeweight="1pt" fill="f"`
              }>
              <w:anchorlock/>
              <center style="font-family:${tokens.font.sans};font-size:11px;font-weight:600;letter-spacing:0.22em;text-transform:uppercase;color:${isSolid ? tokens.color.void : tokens.color.gold};">
                ${children}
              </center>
            </v:roundrect>
            <![endif]-->
          `
        }}
      />
      {/* Modern clients: standard anchor */}
      <Link
        href={href}
        style={{
          display: 'inline-block',
          backgroundColor: isSolid ? tokens.color.gold : 'transparent',
          border: isSolid ? 'none' : `1px solid ${tokens.color.gold}`,
          color: isSolid ? tokens.color.void : tokens.color.gold,
          fontFamily: tokens.font.sansFull,
          fontSize: '11px',
          fontWeight: 600,
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          textDecoration: 'none',
          padding: '17px 38px',
          borderRadius: '2px',
          lineHeight: '1',
        }}
      >
        {children}
      </Link>
    </>
  );
};

// components/email/HeroSection.tsx
import { Section, Text, Heading } from '@react-email/components';
import { tokens } from './tokens';
import { BulletproofButton } from './BulletproofButton';

interface HeroSectionProps {
  eyebrow: string;
  headline: string;
  body: string;
  ctaText: string;
  ctaHref: string;
}

export const HeroSection = ({
  eyebrow,
  headline,
  body,
  ctaText,
  ctaHref,
}: HeroSectionProps) => (
  <Section
    style={{
      padding: '72px 32px 64px',
      background: `linear-gradient(138deg, ${tokens.color.void} 0%, #1E1B16 60%, #2A2620 100%)`,
    }}
  >
    {/* Eyebrow */}
    <Text
      style={{
        fontFamily: tokens.font.sansFull,
        fontSize: '10px',
        fontWeight: 600,
        letterSpacing: '0.24em',
        textTransform: 'uppercase',
        color: tokens.color.gold,
        margin: '0 0 18px 0',
        lineHeight: '1',
      }}
    >
      {eyebrow}
    </Text>

    {/* Horizontal rule */}
    <div
      style={{
        width: '44px',
        height: '1px',
        background: `linear-gradient(90deg, ${tokens.color.gold}, #E5C76E)`,
        marginBottom: '28px',
      }}
    />

    {/* Headline */}
    <Heading
      as="h1"
      style={{
        fontFamily: tokens.font.serifFull,
        fontSize: '52px',
        fontWeight: 300,
        lineHeight: '1.06',
        letterSpacing: '-0.025em',
        color: tokens.color.paper,
        margin: '0 0 22px 0',
      }}
    >
      {headline}
    </Heading>

    {/* Body */}
    <Text
      style={{
        fontFamily: tokens.font.sansFull,
        fontSize: '15px',
        fontWeight: 300,
        lineHeight: '1.78',
        color: tokens.color.dim,
        margin: '0 0 36px 0',
        maxWidth: '380px',
      }}
    >
      {body}
    </Text>

    <BulletproofButton href={ctaHref}>{ctaText}</BulletproofButton>
  </Section>
);
```

---

## PHASE 12 — BUILD PIPELINE & WORKFLOW

### Production Build Steps

```bash
# 1. Lint your HTML (catches unclosed tags, attribute errors)
npm install -g htmlhint
htmlhint email.html

# 2. CSS inliner — Gmail strips <style> blocks, requires inline styles
# Use Juice for reliable inlining:
npx juice --web-resources-images false email.html email-inlined.html

# 3. Image optimization
# Serve images via CDN. Optimal settings:
# - Hero images: JPG at quality 82, max 1200px wide (2x)
# - Product images: JPG at quality 85, max 560px wide (2x)
# - Logos: PNG with alpha, or SVG (converted to PNG for Outlook)

# 4. Image hosting
# CRITICAL: Images must be hosted on a public URL.
# Never use local/relative paths in emails.
# CDN: Cloudflare Images, Imgix, or Cloudinary recommended.

# 5. Validate HTML structure
# Use https://validator.w3.org/nu/ with HTML email doctype

# 6. Multi-client test (required before every send)
# Litmus: 90+ email clients rendered as screenshots
# Email on Acid: Similar, better Outlook coverage
# Testi.at: Free limited option

# 7. Spam score check
# Mail-Tester.com: Send test → get score
# SpamAssassin CLI: spamassassin -t < email.html
# Target: score above 7/10

# 8. Send API (production)
# SendGrid: Superior deliverability, excellent analytics
# AWS SES: Lowest cost at scale, requires more ops setup
# Postmark: Best for transactional, excellent reputation
# Resend: Modern DX, good for developer workflows
```

### Pre-Send Checklist

```
AUTHENTICATION
  [ ] SPF record validated (mxtoolbox.com/spf.aspx)
  [ ] DKIM signing active — send to mail-tester.com, verify pass
  [ ] DMARC policy in place (p=quarantine minimum)
  [ ] BIMI configured if brand logo display desired
  [ ] Custom tracking domain (email.yourdomain.com, not ESP's domain)

CONTENT
  [ ] Preheader text filled (test renders in 5+ clients)
  [ ] All images have descriptive alt text (WCAG 2.1 Level AA)
  [ ] Image-to-text ratio: approximately 40% images, 60% text
  [ ] All links tested (href values, UTM parameters populated)
  [ ] Unsubscribe link present and functional (CAN-SPAM / GDPR required)
  [ ] Physical mailing address in footer (CAN-SPAM required)
  [ ] View-in-browser link present

RENDERING
  [ ] Tested in: Apple Mail, iOS Mail, Gmail Web, Gmail Android,
      Outlook 2016/2019/365, Samsung Mail, Yahoo Mail
  [ ] Dark mode tested in Apple Mail and Gmail
  [ ] Mobile layout verified (iPhone 14/15 at 390px width)
  [ ] Images load correctly (test with images disabled)
  [ ] Fonts render with correct fallback when web fonts blocked
  [ ] CTA buttons render and link correctly in all clients

ACCESSIBILITY
  [ ] `<html lang="en">` set
  [ ] All decorative images: `role="presentation"` or `alt=""`
  [ ] All content images: descriptive alt text
  [ ] Layout tables: `role="presentation"` on every table
  [ ] Color contrast: minimum 4.5:1 for body text
  [ ] Link text is descriptive (not "click here")

PERFORMANCE
  [ ] Total email weight under 102KB (Gmail clips above this)
  [ ] All images under 200KB individually
  [ ] No base64-encoded images in HTML (massively inflates size)
  [ ] Lazy loading on below-fold images

COMPLIANCE
  [ ] Subject line not deceptive
  [ ] From name/address consistent with brand
  [ ] Unsubscribe processes within 10 business days (CAN-SPAM)
  [ ] Personal data handling compliant with GDPR if EU recipients
```

---

## ULTIMATE ARCHITECTURE SUMMARY

```
Figma Design (600px email frame, auto-layout, design tokens)
  ↓
Token Export (Style Dictionary / Figma Variables → JSON)
  ↓
React Email Components (type-safe, bulletproof, token-driven)
  ↓ juice (CSS inliner)
Three output variants:
  ├─ /dist/apple.html      — Full CSS, animations, web fonts
  ├─ /dist/gmail.html      — Inlined CSS, table fallbacks, system fonts
  └─ /dist/outlook.html    — VML enhanced, MSO conditionals, fixed widths
  ↓
Litmus / Email on Acid (80+ client screenshot matrix)
  ↓
Mail-Tester.com (spam score + auth validation)
  ↓
SendGrid / AWS SES API — DKIM signing, multipart/alternative envelope
  ↓
Post-send: open rate, click-to-open rate, unsubscribe rate monitoring
  ↓
Iteration: A/B test subject + preheader, CTA placement, image ratio
```

**The definitive principle:** An email isn't a document — it's a
negotiation between your intent and twelve different rendering engines.
Win that negotiation by designing explicitly for each tier while
sharing a single visual identity across all of them.
