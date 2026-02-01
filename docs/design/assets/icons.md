# 🌿 Prakruti Icon Guidelines

> **Icon Library**: Lucide Icons (https://lucide.dev)
> **Version**: Latest
> **Style**: Consistent 24x24 stroke icons

---

## 🎯 Icon Philosophy

Prakruti uses **Lucide Icons** for consistency and accessibility. Icons should feel:
- **Natural** — Organic, not mechanical
- **Clear** — Instantly recognizable
- **Consistent** — Same stroke width and style

---

## 🌾 Agriculture-Specific Icons

### Crops & Plants
| Icon | Name | Usage |
|------|------|-------|
| 🌱 | `Sprout` | New germplasm, seedlings |
| 🌿 | `Leaf` | Plant health, vegetation |
| 🌾 | `Wheat` | Cereals, grain crops |
| 🌻 | `Flower` | Flowering stage |
| 🌳 | `TreeDeciduous` | Perennial crops |
| 🍃 | `Clover` | Legumes, cover crops |

### Field Operations
| Icon | Name | Usage |
|------|------|-------|
| 📍 | `MapPin` | Field locations |
| 🗺️ | `Map` | Field maps |
| 📐 | `Grid3x3` | Plot layouts |
| 🚜 | `Tractor` | Field equipment |
| 💧 | `Droplets` | Irrigation |
| ☀️ | `Sun` | Weather, solar |

### Breeding & Genetics
| Icon | Name | Usage |
|------|------|-------|
| 🧬 | `Dna` | Genomics, genetics |
| 🔬 | `Microscope` | Lab work |
| 🧪 | `TestTube` | Testing, analysis |
| 📊 | `BarChart3` | Statistics |
| 🎯 | `Target` | Selection |
| 🔗 | `Link` | Crosses, relationships |

### Seed Bank
| Icon | Name | Usage |
|------|------|-------|
| 📦 | `Package` | Seed lots |
| 🏛️ | `Building` | Vaults |
| ❄️ | `Snowflake` | Cryopreservation |
| 🌡️ | `Thermometer` | Temperature |
| 💨 | `Wind` | Humidity |
| 🔒 | `Lock` | Security |

### Data & Analysis
| Icon | Name | Usage |
|------|------|-------|
| 📈 | `TrendingUp` | Progress, growth |
| 📉 | `TrendingDown` | Decline |
| 📊 | `PieChart` | Distribution |
| 📋 | `ClipboardList` | Observations |
| 🔍 | `Search` | Search |
| 📁 | `Folder` | Collections |

---

## 🎨 Icon Colors

Use Prakruti semantic colors for icons:

```tsx
// Success/Growth
<Sprout className="text-prakruti-patta" />

// Warning/Attention
<AlertTriangle className="text-prakruti-narangi" />

// Error/Danger
<XCircle className="text-prakruti-laal" />

// Info/Neutral
<Info className="text-prakruti-neela" />

// Premium/Important
<Star className="text-prakruti-sona" />

// Earth/Grounded
<Mountain className="text-prakruti-mitti" />
```

---

## 📏 Icon Sizes

| Size | Class | Usage |
|------|-------|-------|
| 16px | `w-4 h-4` | Inline, badges |
| 20px | `w-5 h-5` | Buttons, inputs |
| 24px | `w-6 h-6` | Default, navigation |
| 32px | `w-8 h-8` | Cards, headers |
| 48px | `w-12 h-12` | Empty states |

---

## ✅ Do's and Don'ts

### ✅ Do
- Use consistent stroke width (2px default)
- Align icons to pixel grid
- Use semantic colors
- Add aria-labels for accessibility
- Use `aria-hidden="true"` for decorative icons

### ❌ Don't
- Mix icon libraries
- Use filled icons (stick to stroke)
- Make icons too small (<16px)
- Use icons without labels in navigation
- Rely solely on color for meaning

---

## 🔧 Implementation

```tsx
import { Sprout, Leaf, Wheat } from 'lucide-react';

// Basic usage
<Sprout className="w-6 h-6 text-prakruti-patta" />

// With accessibility
<button aria-label="Add new germplasm">
  <Sprout className="w-5 h-5" aria-hidden="true" />
  <span>New Germplasm</span>
</button>

// Decorative icon
<div className="flex items-center gap-2">
  <Leaf className="w-4 h-4 text-prakruti-patta" aria-hidden="true" />
  <span>Plant Health</span>
</div>
```

---

## 📚 Full Icon Reference

See the complete Lucide icon library at: https://lucide.dev/icons

**Recommended categories for Bijmantra:**
- Nature & Weather
- Science & Technology
- Charts & Data
- Files & Folders
- Navigation & Actions

---

> **"Agriculture is our Culture."**
> 
> Icons should reflect the natural, grounded essence of agricultural work.
