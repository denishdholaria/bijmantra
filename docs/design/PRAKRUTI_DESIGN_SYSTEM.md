# 🌿 Prakruti Design Language/System (प्रकृति)

> **"Agriculture is our Culture."**
> — Wisdom passed through generations

---

## Philosophy

**Prakruti** (प्रकृति) means "Nature" in Sanskrit — the inherent disposition, the original essence, the way things naturally are. In Indian philosophy, Prakruti represents the primal creative force from which all forms emerge.

The Prakruti Design System is Bijmantra's original design language, created specifically for agricultural research software. It follows nature's principles — organic growth, seasonal cycles, and the timeless patterns that govern life itself.

### Why "Prakruti"?

- **Nature as Teacher** — Design patterns inspired by natural forms and growth
- **Inherent Essence** — Captures the true nature of agricultural work
- **Sanskrit Heritage** — Aligns with Bijmantra's naming (SWAYAM, PRAHARI, RAKSHAKA)
- **Universal Principle** — Nature's design works everywhere, for everyone
- **Timeless** — Natural patterns never go out of style

---

## Core Principles

### 1. 🌱 Rooted (जड़)

**Grounded, stable, trustworthy.**

Like a tree with deep roots, Bijmantra's interface should feel stable and reliable. Users trust us with years of research data — our design must reflect that trustworthiness.

**Implementation:**

- Solid, consistent foundations
- Predictable navigation patterns
- No surprising UI changes
- Earthy, grounded color palette

### 2. 🌿 Growing (बढ़ता)

**Progressive, alive, evolving.**

Agriculture is about growth. Our interface should feel alive — not static like a spreadsheet, but organic like a growing plant.

**Implementation:**

- Subtle growth-inspired animations
- Progressive disclosure of complexity
- Interfaces that evolve with user expertise
- Celebration of milestones and progress

### 3. 🔧 Practical (व्यावहारिक)

**Works in the field, not just the office.**

Our users aren't in air-conditioned offices. They're in greenhouses, fields, and labs. Design must work everywhere.

**Implementation:**

- High contrast for outdoor visibility
- Large touch targets for gloved hands
- Offline-first architecture
- Fast load times on slow connections

### 4. 🔬 Scientific (वैज्ञानिक)

**Data-driven, precise, credible.**

Bijmantra serves scientists. Our design must respect the precision and rigor of scientific work.

**Implementation:**

- Clear data visualization
- Proper typography hierarchy
- Accurate representations (no misleading charts)
- Citation and source attribution

### 5. 🤝 Inclusive (समावेशी)

**Works for everyone, everywhere.**

From PhD researchers to field technicians, from India to Iowa, from desktop to mobile — Bijmantra must work for all.

**Implementation:**

- WCAG 2.1 AA accessibility compliance
- Multilingual-ready typography
- Low-bandwidth optimizations
- Support for assistive technologies

---

## Design Tokens

### Color Palette

Our colors are drawn from the agricultural landscape — soil, leaves, harvest, sky.

#### Primary Colors

| Token                      | Name        | Hindi                   | Hex         | Usage                     |
| -------------------------- | ----------- | ----------------------- | ----------- | ------------------------- |
| `--prakruti-mitti`       | Earth       | मिट्टी            | `#8B5A2B` | Primary brand, headers    |
| `--prakruti-mitti-light` | Light Earth | हल्की मिट्टी | `#D4A574` | Hover states, accents     |
| `--prakruti-mitti-dark`  | Dark Earth  | गहरी मिट्टी   | `#5D3A1A` | Text on light backgrounds |

#### Secondary Colors

| Token                      | Name       | Hindi               | Hex         | Usage                   |
| -------------------------- | ---------- | ------------------- | ----------- | ----------------------- |
| `--prakruti-patta`       | Leaf       | पत्ता          | `#2D5A27` | Success, growth, nature |
| `--prakruti-patta-light` | Young Leaf | नया पत्ता   | `#4A9B3F` | Interactive elements    |
| `--prakruti-patta-pale`  | Pale Leaf  | फीका पत्ता | `#E8F5E9` | Success backgrounds     |

#### Accent Colors

| Token                      | Name       | Hindi               | Hex         | Usage                          |
| -------------------------- | ---------- | ------------------- | ----------- | ------------------------------ |
| `--prakruti-sona`        | Gold       | सोना            | `#D4A012` | Harvest, achievements, premium |
| `--prakruti-sona-light`  | Light Gold | हल्का सोना | `#F5D742` | Highlights, badges             |
| `--prakruti-neela`       | Sky        | नीला            | `#1E6091` | Links, information             |
| `--prakruti-neela-light` | Light Sky  | हल्का नीला | `#E3F2FD` | Info backgrounds               |

#### Semantic Colors

| Token                        | Name         | Hindi                   | Hex         | Usage                       |
| ---------------------------- | ------------ | ----------------------- | ----------- | --------------------------- |
| `--prakruti-laal`          | Red          | लाल                  | `#C62828` | Errors, destructive actions |
| `--prakruti-laal-light`    | Light Red    | हल्का लाल       | `#FFEBEE` | Error backgrounds           |
| `--prakruti-narangi`       | Orange       | नारंगी            | `#E65100` | Warnings, attention         |
| `--prakruti-narangi-light` | Light Orange | हल्का नारंगी | `#FFF3E0` | Warning backgrounds         |

#### Neutral Colors

| Token                    | Name     | Hindi  | Hex         | Usage              |
| ------------------------ | -------- | ------ | ----------- | ------------------ |
| `--prakruti-dhool-50`  | Dust 50  | धूल | `#FAFAF8` | Page backgrounds   |
| `--prakruti-dhool-100` | Dust 100 | धूल | `#F5F5F0` | Card backgrounds   |
| `--prakruti-dhool-200` | Dust 200 | धूल | `#E8E8E0` | Borders, dividers  |
| `--prakruti-dhool-300` | Dust 300 | धूल | `#D4D4C8` | Disabled states    |
| `--prakruti-dhool-400` | Dust 400 | धूल | `#A8A898` | Placeholder text   |
| `--prakruti-dhool-500` | Dust 500 | धूल | `#787868` | Secondary text     |
| `--prakruti-dhool-600` | Dust 600 | धूल | `#585848` | Body text          |
| `--prakruti-dhool-700` | Dust 700 | धूल | `#383830` | Headings           |
| `--prakruti-dhool-800` | Dust 800 | धूल | `#282820` | Primary text       |
| `--prakruti-dhool-900` | Dust 900 | धूल | `#181810` | High contrast text |

#### Dark Mode Colors

Dark mode uses inverted neutrals with adjusted saturation to maintain warmth.

| Token                         | Light Mode  | Dark Mode   |
| ----------------------------- | ----------- | ----------- |
| `--prakruti-bg-primary`     | `#FAFAF8` | `#1A1A18` |
| `--prakruti-bg-secondary`   | `#F5F5F0` | `#242420` |
| `--prakruti-bg-tertiary`    | `#E8E8E0` | `#2E2E28` |
| `--prakruti-text-primary`   | `#282820` | `#F5F5F0` |
| `--prakruti-text-secondary` | `#585848` | `#A8A898` |
| `--prakruti-border`         | `#E8E8E0` | `#383830` |

---

## Typography

### Font Stack

```css
/* Primary: System fonts optimized for readability */
--prakruti-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                   'Noto Sans', 'Liberation Sans', sans-serif, 
                   'Apple Color Emoji', 'Segoe UI Emoji';

/* Monospace: For data, codes, and scientific notation */
--prakruti-font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Monaco, 
                   'Cascadia Code', Consolas, monospace;

/* Display: For large headings and marketing (optional) */
--prakruti-font-display: 'Cal Sans', 'DM Sans', var(--prakruti-font-sans);
```

### Type Scale

Based on a 1.25 ratio (Major Third) for harmonious scaling.

| Token                    | Size            | Line Height | Weight | Usage                    |
| ------------------------ | --------------- | ----------- | ------ | ------------------------ |
| `--prakruti-text-xs`   | 12px / 0.75rem  | 1.5         | 400    | Captions, labels         |
| `--prakruti-text-sm`   | 14px / 0.875rem | 1.5         | 400    | Secondary text, metadata |
| `--prakruti-text-base` | 16px / 1rem     | 1.6         | 400    | Body text                |
| `--prakruti-text-lg`   | 18px / 1.125rem | 1.5         | 400    | Lead paragraphs          |
| `--prakruti-text-xl`   | 20px / 1.25rem  | 1.4         | 500    | Card titles              |
| `--prakruti-text-2xl`  | 24px / 1.5rem   | 1.3         | 600    | Section headings         |
| `--prakruti-text-3xl`  | 30px / 1.875rem | 1.25        | 700    | Page titles              |
| `--prakruti-text-4xl`  | 36px / 2.25rem  | 1.2         | 700    | Hero headings            |
| `--prakruti-text-5xl`  | 48px / 3rem     | 1.1         | 800    | Display headings         |

### Font Weights

| Token                         | Weight | Usage            |
| ----------------------------- | ------ | ---------------- |
| `--prakruti-font-normal`    | 400    | Body text        |
| `--prakruti-font-medium`    | 500    | Emphasis, labels |
| `--prakruti-font-semibold`  | 600    | Subheadings      |
| `--prakruti-font-bold`      | 700    | Headings         |
| `--prakruti-font-extrabold` | 800    | Display, hero    |

### Scientific Typography

For scientific content, we use specific conventions:

- **Gene names**: Italic (`*OsGW2*` → *OsGW2*)
- **Species names**: Italic (`*Oryza sativa*`)
- **Numbers**: Tabular figures for alignment
- **Units**: Thin space between number and unit (`42 kg/ha`)
- **Subscripts/Superscripts**: Proper HTML tags, not fake styling

---

## Spacing System

Based on a 4px base unit for precise alignment.

| Token                   | Value | Usage                        |
| ----------------------- | ----- | ---------------------------- |
| `--prakruti-space-0`  | 0     | Reset                        |
| `--prakruti-space-1`  | 4px   | Tight spacing, icon gaps     |
| `--prakruti-space-2`  | 8px   | Related elements             |
| `--prakruti-space-3`  | 12px  | Form element padding         |
| `--prakruti-space-4`  | 16px  | Standard padding             |
| `--prakruti-space-5`  | 20px  | Card padding (mobile)        |
| `--prakruti-space-6`  | 24px  | Card padding (desktop)       |
| `--prakruti-space-8`  | 32px  | Section spacing              |
| `--prakruti-space-10` | 40px  | Large section spacing        |
| `--prakruti-space-12` | 48px  | Page section gaps            |
| `--prakruti-space-16` | 64px  | Major section breaks         |
| `--prakruti-space-20` | 80px  | Hero spacing                 |
| `--prakruti-space-24` | 96px  | Page margins (large screens) |

---

## Border Radius

Organic, rounded corners inspired by natural forms — not harsh rectangles, not perfect circles.

| Token                      | Value  | Usage                            |
| -------------------------- | ------ | -------------------------------- |
| `--prakruti-radius-none` | 0      | Sharp edges (rare)               |
| `--prakruti-radius-sm`   | 4px    | Small elements, badges           |
| `--prakruti-radius-md`   | 8px    | Buttons, inputs                  |
| `--prakruti-radius-lg`   | 12px   | Cards, modals                    |
| `--prakruti-radius-xl`   | 16px   | Large cards, panels              |
| `--prakruti-radius-2xl`  | 24px   | Hero cards, feature sections     |
| `--prakruti-radius-full` | 9999px | Pills, avatars, circular buttons |

---

## Shadows

Soft, natural shadows that suggest depth without harshness.

```css
/* Elevation levels */
--prakruti-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--prakruti-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.07), 
                  0 2px 4px -2px rgb(0 0 0 / 0.07);
--prakruti-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.08), 
                  0 4px 6px -4px rgb(0 0 0 / 0.08);
--prakruti-shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.08), 
                  0 8px 10px -6px rgb(0 0 0 / 0.08);
--prakruti-shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.15);

/* Colored shadows for emphasis */
--prakruti-shadow-patta: 0 4px 14px 0 rgb(45 90 39 / 0.25);
--prakruti-shadow-sona: 0 4px 14px 0 rgb(212 160 18 / 0.25);
--prakruti-shadow-mitti: 0 4px 14px 0 rgb(139 90 43 / 0.25);
```

---

## Motion & Animation

### Principles

1. **Purposeful** — Animation should communicate, not decorate
2. **Natural** — Inspired by organic growth, not mechanical bounce
3. **Respectful** — Honor `prefers-reduced-motion` preferences
4. **Fast** — Users shouldn't wait for animations

### Timing Functions

```css
/* Natural easing - like a leaf falling */
--prakruti-ease-natural: cubic-bezier(0.4, 0, 0.2, 1);

/* Growth easing - starts slow, accelerates */
--prakruti-ease-grow: cubic-bezier(0.0, 0, 0.2, 1);

/* Settle easing - quick start, gentle end */
--prakruti-ease-settle: cubic-bezier(0.4, 0, 0, 1);

/* Spring easing - slight overshoot */
--prakruti-ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

### Duration Scale

| Token                           | Duration | Usage                 |
| ------------------------------- | -------- | --------------------- |
| `--prakruti-duration-instant` | 50ms     | Micro-interactions    |
| `--prakruti-duration-fast`    | 150ms    | Hover states, toggles |
| `--prakruti-duration-normal`  | 250ms    | Standard transitions  |
| `--prakruti-duration-slow`    | 400ms    | Complex animations    |
| `--prakruti-duration-slower`  | 600ms    | Page transitions      |

### Animation Patterns

**Growth Animation** — For elements appearing:

```css
@keyframes prakruti-grow {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
```

**Sprout Animation** — For success states:

```css
@keyframes prakruti-sprout {
  0% { transform: scale(0) rotate(-45deg); }
  50% { transform: scale(1.2) rotate(0deg); }
  100% { transform: scale(1) rotate(0deg); }
}
```

**Sway Animation** — For loading states:

```css
@keyframes prakruti-sway {
  0%, 100% { transform: rotate(-3deg); }
  50% { transform: rotate(3deg); }
}
```

---

## Multi-Platform Design

### Breakpoints

| Token                     | Width  | Target Devices                     |
| ------------------------- | ------ | ---------------------------------- |
| `--prakruti-screen-xs`  | 320px  | Small phones                       |
| `--prakruti-screen-sm`  | 480px  | Large phones                       |
| `--prakruti-screen-md`  | 768px  | Tablets (portrait)                 |
| `--prakruti-screen-lg`  | 1024px | Tablets (landscape), small laptops |
| `--prakruti-screen-xl`  | 1280px | Desktops                           |
| `--prakruti-screen-2xl` | 1536px | Large monitors                     |

### Platform-Specific Guidelines

#### 📱 Mobile Phone (320px - 767px)

**Context:** Field workers, quick data entry, one-handed use

**Design Priorities:**

- Touch targets minimum 44×44px (48×48px preferred)
- Bottom navigation for thumb reach
- Swipe gestures for common actions
- Offline-first with sync indicators
- High contrast for outdoor visibility
- Minimal typing — use pickers, scanners, voice

**Layout:**

- Single column layouts
- Full-width cards
- Sticky headers with essential actions
- Bottom sheets instead of modals
- Floating action button for primary action

**Typography:**

- Base font: 16px (prevents iOS zoom)
- Minimum readable: 14px
- Touch labels: 16px+

**Navigation:**

- Bottom tab bar (5 items max)
- Hamburger menu for secondary items
- Swipe-back gesture support
- Pull-to-refresh for lists

#### 📱 Tablet (768px - 1023px)

**Context:** Lab work, field tablets, data review

**Design Priorities:**

- Support both orientations
- Split-view for master-detail patterns
- Larger touch targets for gloved hands
- Keyboard support when docked
- Multi-column forms

**Layout:**

- 2-column layouts in landscape
- Sidebar navigation (collapsible)
- Cards in 2-column grid
- Modals instead of full-page transitions

**Typography:**

- Base font: 16px
- Comfortable reading width: 65-75 characters

**Navigation:**

- Collapsible sidebar
- Breadcrumbs for deep navigation
- Tab bars for section switching

#### 💻 Desktop (1024px+)

**Context:** Office work, data analysis, report generation

**Design Priorities:**

- Keyboard shortcuts for power users
- Dense information display
- Multi-panel layouts
- Hover states and tooltips
- Drag-and-drop interactions

**Layout:**

- Persistent sidebar navigation
- 3-column layouts for complex views
- Data tables with sorting/filtering
- Resizable panels
- Maximum content width: 1440px

**Typography:**

- Base font: 16px
- Data tables: 14px acceptable
- Generous line height for long reading

**Navigation:**

- Persistent sidebar (240-280px)
- Command palette (⌘K)
- Keyboard shortcuts
- Breadcrumbs always visible

---

## Component Guidelines

### Buttons

**Hierarchy:**

1. **Primary** — Main action, one per view (`--prakruti-patta` background)
2. **Secondary** — Supporting actions (outlined)
3. **Tertiary** — Low-emphasis actions (text only)
4. **Destructive** — Dangerous actions (`--prakruti-laal`)

**Sizes:**

| Size   | Height | Padding   | Font | Usage                   |
| ------ | ------ | --------- | ---- | ----------------------- |
| `sm` | 32px   | 12px 16px | 14px | Compact UIs, tables     |
| `md` | 40px   | 12px 20px | 14px | Default                 |
| `lg` | 48px   | 16px 24px | 16px | Primary actions, mobile |
| `xl` | 56px   | 20px 32px | 18px | Hero CTAs               |

**States:**

- Default → Hover → Active → Focus → Disabled
- Loading state with spinner
- Success state with checkmark (brief)

### Cards

**Anatomy:**

```
┌─────────────────────────────────┐
│ [Icon]  Title            [Menu] │  ← Header (optional)
├─────────────────────────────────┤
│                                 │
│         Content Area            │  ← Body
│                                 │
├─────────────────────────────────┤
│ [Secondary]        [Primary →]  │  ← Footer (optional)
└─────────────────────────────────┘
```

**Variants:**

- **Elevated** — Shadow, white background (default)
- **Outlined** — Border, transparent background
- **Filled** — Colored background (for emphasis)
- **Interactive** — Hover state, clickable

### Forms

**Input Fields:**

- Label always visible (no placeholder-only labels)
- Helper text below for guidance
- Error messages replace helper text
- Required indicator: asterisk after label
- Character count for limited fields

**Layout:**

- Single column on mobile
- 2 columns on tablet/desktop for related fields
- Group related fields with fieldset
- Progressive disclosure for advanced options

**Validation:**

- Validate on blur, not on every keystroke
- Show success state for valid fields
- Inline errors, not toast notifications
- Summarize errors at form top for accessibility

### Data Tables

**Features:**

- Sortable columns (click header)
- Filterable (search + column filters)
- Selectable rows (checkbox)
- Pagination or infinite scroll
- Column resizing (desktop)
- Row actions (hover menu or last column)

**Density:**

| Density     | Row Height | Usage                     |
| ----------- | ---------- | ------------------------- |
| Compact     | 40px       | Data-heavy views, experts |
| Default     | 52px       | Standard usage            |
| Comfortable | 64px       | Touch devices, beginners  |

**Empty States:**

- Illustration + message
- Clear call-to-action
- Never just blank space

### Navigation

**Sidebar:**

- Width: 240px (expanded), 64px (collapsed)
- Grouped by workspace/module
- Active state clearly visible
- Collapse button at bottom
- User menu at bottom

**Breadcrumbs:**

- Always show current location
- Truncate middle items on mobile
- Home icon for root
- Separator: chevron (›)

**Tabs:**

- Underline style (not boxed)
- Active tab: bold + underline
- Scrollable on mobile
- Icons optional (left of label)

---

## Iconography

### Style Guidelines

- **Stroke weight:** 1.5px (consistent with Lucide)
- **Corner radius:** 2px for sharp corners
- **Size grid:** 24×24px base, scale to 16, 20, 32, 48
- **Style:** Outlined (not filled) for UI icons
- **Filled variants:** For selected/active states

### Icon Sizes

| Size   | Pixels | Usage                     |
| ------ | ------ | ------------------------- |
| `xs` | 16px   | Inline with text, badges  |
| `sm` | 20px   | Buttons, form elements    |
| `md` | 24px   | Default, navigation       |
| `lg` | 32px   | Empty states, features    |
| `xl` | 48px   | Hero sections, onboarding |

### Agricultural Icons (Custom)

Beyond standard Lucide icons, Bijmantra needs custom agricultural iconography:

| Icon | Name        | Usage                  |
| ---- | ----------- | ---------------------- |
| 🌾   | Wheat/Grain | Breeding, germplasm    |
| 🌱   | Seedling    | Growth, new items      |
| 🧬   | DNA Helix   | Genomics, molecular    |
| 🔬   | Microscope  | Research, analysis     |
| 📊   | Chart       | Analytics, data        |
| 🌡️ | Thermometer | Environment, sensors   |
| 💧   | Water Drop  | Irrigation, moisture   |
| ☀️ | Sun         | Solar, photoperiod     |
| 🏛️ | Vault       | Gene bank, storage     |
| 📦   | Package     | Seed lots, inventory   |
| 🚚   | Truck       | Dispatch, logistics    |
| 🏷️ | Tag         | Labels, barcodes       |
| 📋   | Clipboard   | Field book, data entry |
| 🗺️ | Map         | Field map, locations   |

---

## Data Visualization

### Color Palette for Charts

**Categorical (up to 8 categories):**

```
1. #2D5A27 (Patta - Green)
2. #1E6091 (Neela - Blue)
3. #D4A012 (Sona - Gold)
4. #8B5A2B (Mitti - Brown)
5. #7B1FA2 (Purple)
6. #00838F (Teal)
7. #C62828 (Laal - Red)
8. #5D4037 (Dark Brown)
```

**Sequential (single hue, low to high):**

- Green: `#E8F5E9` → `#1B5E20`
- Blue: `#E3F2FD` → `#0D47A1`
- Gold: `#FFF8E1` → `#FF8F00`

**Diverging (negative to positive):**

- Red → White → Green: `#C62828` → `#FFFFFF` → `#2D5A27`

### Chart Types

| Data Type       | Recommended Chart                     |
| --------------- | ------------------------------------- |
| Comparison      | Bar chart (horizontal for many items) |
| Trend over time | Line chart                            |
| Part of whole   | Donut chart (not pie)                 |
| Distribution    | Histogram, box plot                   |
| Correlation     | Scatter plot                          |
| Geographic      | Choropleth map                        |
| Hierarchy       | Treemap                               |
| Flow            | Sankey diagram                        |

### Chart Guidelines

1. **Always include:**

   - Clear title
   - Axis labels with units
   - Legend (if multiple series)
   - Data source attribution
2. **Avoid:**

   - 3D effects
   - Excessive grid lines
   - Truncated axes (unless clearly marked)
   - More than 7 colors in one chart
3. **Accessibility:**

   - Don't rely on color alone
   - Use patterns/shapes as secondary encoding
   - Provide data table alternative
   - Sufficient contrast (4.5:1 minimum)

---

## Accessibility

### WCAG 2.1 AA Compliance

Bijmantra must meet WCAG 2.1 Level AA standards.

#### Color Contrast

| Element                         | Minimum Ratio |
| ------------------------------- | ------------- |
| Normal text                     | 4.5:1         |
| Large text (18px+ or 14px bold) | 3:1           |
| UI components                   | 3:1           |
| Focus indicators                | 3:1           |

#### Keyboard Navigation

- All interactive elements focusable via Tab
- Logical focus order (left-to-right, top-to-bottom)
- Visible focus indicators (2px outline minimum)
- Skip links for main content
- No keyboard traps

#### Screen Readers

- Semantic HTML elements
- ARIA labels for icons and complex widgets
- Live regions for dynamic content
- Proper heading hierarchy (h1 → h2 → h3)
- Alt text for all images

#### Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

#### Touch Targets

- Minimum size: 44×44px
- Recommended size: 48×48px
- Spacing between targets: 8px minimum

---

## Writing Guidelines

### Voice & Tone

**Voice (consistent):**

- Knowledgeable but not condescending
- Supportive, like a helpful colleague
- Scientific but accessible
- Respectful of expertise

**Tone (varies by context):**

| Context       | Tone                  |
| ------------- | --------------------- |
| Onboarding    | Warm, encouraging     |
| Data entry    | Clear, efficient      |
| Errors        | Calm, helpful         |
| Success       | Celebratory (briefly) |
| Documentation | Thorough, precise     |

### UI Text Guidelines

**Buttons:**

- Use verbs: "Save", "Create", "Export"
- Be specific: "Save Trial" not just "Save"
- Avoid "Click here" or "Submit"

**Labels:**

- Use sentence case: "Germplasm name"
- Be concise: "Name" not "Please enter the name"
- Include units: "Weight (kg)"

**Error Messages:**

- Say what went wrong
- Say how to fix it
- Don't blame the user

```
❌ "Invalid input"
✅ "Please enter a valid date (DD/MM/YYYY)"

❌ "Error 500"
✅ "Something went wrong. Please try again or contact support."
```

**Empty States:**

- Explain what would be here
- Provide action to populate
- Use friendly illustration

```
No trials yet

Trials help you organize field experiments.
Create your first trial to get started.

[+ Create Trial]
```

### Terminology

Use consistent terms throughout the application:

| Preferred   | Avoid                                |
| ----------- | ------------------------------------ |
| Germplasm   | Accession (unless gene bank context) |
| Trial       | Experiment (unless research context) |
| Observation | Measurement, Reading                 |
| Trait       | Variable, Character                  |
| Location    | Site, Field                          |
| Program     | Project (for breeding programs)      |

---

## Field-Ready Design

### Outdoor Visibility

**High Contrast Mode:**

- Increase contrast ratios to 7:1+
- Bolder fonts
- Larger touch targets
- Reduced color reliance

**Sunlight Readability:**

- Avoid pure white backgrounds (use warm off-white)
- Dark text on light backgrounds preferred
- No thin fonts
- No low-contrast placeholder text

### Offline Support

**Visual Indicators:**

- Persistent offline banner (non-intrusive)
- Sync status in header
- Pending changes badge
- Last synced timestamp

**Offline-First Patterns:**

- Optimistic UI updates
- Queue actions for sync
- Clear conflict resolution
- Local data persistence

### Low Bandwidth

**Performance Targets:**

| Metric                   | Target            |
| ------------------------ | ----------------- |
| First Contentful Paint   | < 1.5s            |
| Time to Interactive      | < 3s              |
| Largest Contentful Paint | < 2.5s            |
| Total Page Weight        | < 500KB (initial) |

**Optimization Strategies:**

- Lazy load images
- Code splitting by route
- Service worker caching
- Compressed assets (gzip/brotli)
- Skeleton loading states

### Gloved Hands

For users wearing work gloves:

- Touch targets: 56×56px minimum
- Spacing between targets: 16px
- Avoid swipe-only interactions
- Provide button alternatives

---

## Implementation

### CSS Custom Properties

```css
:root {
  /* Colors */
  --prakruti-mitti: #8B5A2B;
  --prakruti-patta: #2D5A27;
  --prakruti-sona: #D4A012;
  --prakruti-neela: #1E6091;
  --prakruti-laal: #C62828;
  
  /* Typography */
  --prakruti-font-sans: 'Inter', system-ui, sans-serif;
  --prakruti-font-mono: 'JetBrains Mono', monospace;
  
  /* Spacing */
  --prakruti-space-unit: 4px;
  
  /* Radius */
  --prakruti-radius-md: 8px;
  --prakruti-radius-lg: 12px;
  
  /* Shadows */
  --prakruti-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.07);
  
  /* Transitions */
  --prakruti-ease-natural: cubic-bezier(0.4, 0, 0.2, 1);
  --prakruti-duration-normal: 250ms;
}
```

### Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        khet: {
          mitti: { DEFAULT: '#8B5A2B', light: '#D4A574', dark: '#5D3A1A' },
          patta: { DEFAULT: '#2D5A27', light: '#4A9B3F', pale: '#E8F5E9' },
          sona: { DEFAULT: '#D4A012', light: '#F5D742' },
          neela: { DEFAULT: '#1E6091', light: '#E3F2FD' },
          laal: { DEFAULT: '#C62828', light: '#FFEBEE' },
          dhool: {
            50: '#FAFAF8', 100: '#F5F5F0', 200: '#E8E8E0',
            300: '#D4D4C8', 400: '#A8A898', 500: '#787868',
            600: '#585848', 700: '#383830', 800: '#282820', 900: '#181810'
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'khet': '12px',
      },
      transitionTimingFunction: {
        'khet': 'cubic-bezier(0.4, 0, 0.2, 1)',
      }
    }
  }
}
```

---

## Resources

### Design Files

- Figma Component Library: `[To be created]`
- Icon Set: `[To be created]`
- Illustration Library: `[To be created]`

### References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Inclusive Design Principles](https://inclusivedesignprinciples.org/)
- [Material Design](https://material.io/) — For accessibility patterns
- [Apple HIG](https://developer.apple.com/design/) — For quality benchmarks

---

## Changelog

| Version | Date         | Changes                                   |
| ------- | ------------ | ----------------------------------------- |
| 1.0.0   | Dec 26, 2025 | Initial release — Prakruti Design System |

---

> **"Agriculture is our Culture."**
>
> Prakruti — following nature's design.
> This design system honors the farmers, scientists, and researchers who feed the world.
> Every pixel is planted with purpose. Every interaction grows from nature.
>
> 🌿 *Bijmantra Design Team*
