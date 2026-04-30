---
name: ReliantAI Nexus
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#e2bfb0'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#a98a7c'
  outline-variant: '#594136'
  surface-tint: '#ffb692'
  primary: '#ffb692'
  on-primary: '#552000'
  primary-container: '#ff6e00'
  on-primary-container: '#582100'
  inverse-primary: '#9f4200'
  secondary: '#bcc7de'
  on-secondary: '#263143'
  secondary-container: '#3e495d'
  on-secondary-container: '#aeb9d0'
  tertiary: '#bec6e0'
  on-tertiary: '#283044'
  tertiary-container: '#929ab2'
  on-tertiary-container: '#2a3246'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdbcb'
  primary-fixed-dim: '#ffb692'
  on-primary-fixed: '#341100'
  on-primary-fixed-variant: '#793100'
  secondary-fixed: '#d8e3fb'
  secondary-fixed-dim: '#bcc7de'
  on-secondary-fixed: '#111c2d'
  on-secondary-fixed-variant: '#3c475a'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  headline-xl:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  safe-margin: 20px
  gutter: 12px
---

## Brand & Style

The design system is engineered for a high-stakes, data-driven environment where precision and reliability are paramount. It targets professional operators and decision-makers who require rapid insights from complex data sets. 

The aesthetic is a blend of **Corporate Modern** and **High-Tech Minimalism**. It utilizes a dark-mode foundation to reduce eye strain during prolonged analysis, punctuated by high-energy brand colors that signal action and importance. The interface should feel like a high-end command center: authoritative, responsive, and technologically advanced. By balancing deep slate backgrounds with clean white surfaces and vibrant orange accents, the system evokes a sense of "secure innovation."

## Colors

The color palette is optimized for a dark-themed mobile experience, ensuring high contrast for critical information.

- **Primary (Vibrant Orange):** Reserved for primary actions, critical alerts, and key brand moments. It represents energy and the "spark" of AI intelligence.
- **Secondary/Tertiary (Deep Slate):** Used for background layering and container surfaces. These deep blues and greys provide a sophisticated, professional backdrop that allows data to stand out.
- **Neutral:** A range of mid-tone greys used for secondary text, borders, and inactive states to maintain a clear visual hierarchy.
- **Surface (Clean White):** Used sparingly for high-priority card surfaces or data visualization backgrounds where maximum legibility is required.

Functional colors should follow standard patterns: Green for growth/success, Red for risk/error, and Blue for informational highlights.

## Typography

This design system employs a dual-font strategy to balance technical edge with functional clarity.

**Space Grotesk** is used for headings. Its geometric, slightly futuristic construction reinforces the AI-driven, high-tech nature of the brand. It should always be used in bold weights to create a strong visual anchor on the screen.

**Inter** is the workhorse for all body text, data points, and UI labels. It is chosen for its exceptional readability on mobile screens and its neutral, systematic feel. 

For data-heavy views (analytics and lead lists), use `label-md` with uppercase styling to categorize data types clearly without overwhelming the user.

## Layout & Spacing

The layout philosophy follows a **Fluid Grid** model optimized for mobile viewport density. 

- **Margins:** A standard safe margin of 20px is applied to the left and right of all screens.
- **Hierarchy:** Use vertical spacing to group related information. Elements within a card should use `sm` (8px) or `md` (16px) spacing, while sections of the app should be separated by `xl` (32px) to provide "breathing room" in data-dense environments.
- **Rhythm:** An 8px linear scale ensures consistency across all components and spacing values.
- **Lead Management Views:** Use a compressed vertical rhythm (`sm` spacing between list items) to maximize the amount of information visible at once, ensuring efficiency for the user.

## Elevation & Depth

This design system uses **Tonal Layering** combined with **Ambient Shadows** to create a sense of depth and focus.

- **Base Layer:** The deepest background color (`#020617`).
- **Surface Layer:** Secondary containers (`#1E293B`) create the first level of elevation. These are used for grouped content or navigation bars.
- **Priority Layer:** White or primary-tinted cards that appear to "float" above the background. These use subtle, highly diffused shadows (e.g., `0px 4px 20px rgba(0, 0, 0, 0.4)`) to suggest they are interactable.
- **Visual Cues:** High-tech "glow" effects (low-opacity orange shadows) may be used behind primary buttons or active AI-processing indicators to signal activity and importance.

## Shapes

The shape language is defined by **Balanced Roundedness**. A radius of 8px to 12px (Level 2) is used across most components to soften the high-tech aesthetic, making the professional tool feel accessible and modern.

- **Standard Elements:** Buttons, input fields, and small chips use a 0.5rem (8px) radius.
- **Large Containers:** Cards and modal sheets use a 1rem (16px) radius for a more prominent, distinct appearance.
- **Interactive Feedback:** Selection states should mirror the container's corner radius exactly to maintain a clean, aligned silhouette.

## Components

### Buttons
Primary buttons use the Vibrant Orange background with white text, utilizing a bold Inter font. Secondary buttons should be "ghost" style with a slate border or a subtle slate fill to remain subordinate to the primary action.

### Cards
Cards are the primary vehicle for lead management and analytics. They should have a subtle 1px border (`#334155`) to define their boundaries against the dark background. Use a white background for high-priority metrics to make them "pop."

### Chips/Tags
Used for lead status (e.g., "New," "In Progress," "Qualified"). These should be pill-shaped with low-opacity background tints of functional colors (green, orange, red) to keep the UI clean but informative.

### Input Fields
Inputs should have a dark slate background with a subtle border. Upon focus, the border should transition to the Vibrant Orange to provide clear visual feedback.

### Data Visualization
Charts and graphs should use the primary orange for the most important data line/bar, while neutral greys or secondary blues are used for comparison data. Ensure all lines have a minimum weight of 2px for visibility on mobile.

### List Items
For lead management, list items should be high-density. Use `body-sm` for secondary metadata and `headline-md` or `body-lg` (bold) for the lead name to establish clear hierarchy.
