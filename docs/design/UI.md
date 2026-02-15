# 🌱 Bijmantra UI/UX Blueprint — Revised December 2025

A comprehensive UI/UX strategy for Bijmantra: a BrAPI v2.1-compatible plant breeding PWA with **251+ pages**, **11 modules**, and **multi-engine compute** (Python, Rust/WASM, Fortran).

> **Last Updated**: December 11, 2025  
> **Status**: 98% Complete — Camera integration, i18n with RTL support added

---

## 📦 Current Tech Stack (Production)

| Layer              | Technology               | Purpose                              | Status |
| ------------------ | ------------------------ | ------------------------------------ | ------ |
| **UI Components**  | shadcn/ui + Radix UI     | Accessible, composable primitives    | ✅     |
| **Styling**        | Tailwind CSS 3.4+        | Utility-first CSS with design tokens | ✅     |
| **Charts**         | Recharts + ECharts       | Declarative + high-performance viz   | ✅     |
| **State**          | Zustand + TanStack Query | Client & server state management     | ✅     |
| **Forms**          | React Hook Form + Zod    | Performant forms with validation     | ✅     |
| **Offline**        | Dexie.js + Workbox       | IndexedDB + Service Worker           | ✅     |
| **Icons**          | Lucide React             | Modern icon set                      | ✅     |
| **Virtual Scroll** | @tanstack/react-virtual  | 100K+ row performance                | ✅     |

> [!IMPORTANT]
> The codebase uses **shadcn/ui + Tailwind CSS**, not Ant Design/Mantine/Chakra UI. All improvements must align with this stack.

---

## 🎯 Key UI/UX Improvement Areas

### 1. Data-Dense Scientific Interfaces

| Problem                                                    | Solution                                                  | Status    |
| ---------------------------------------------------------- | --------------------------------------------------------- | --------- |
| Genomic datasets (100K+ markers) overwhelm standard tables | Virtual scrolling with `@tanstack/react-virtual`          | ✅ Done   |
| Complex multi-trait visualizations                         | Upgrade to **ECharts** for heatmaps, PCA, large scatter   | ✅ Done   |
| Field layouts need spatial awareness                       | Leaflet already integrated—add interactive plot selection | ✅ Done   |
| Pedigree trees lack depth navigation                       | Implement zoomable D3-based pedigree with GEDCOM export   | ✅ Done   |

**Completed Components:**
- `VirtualDataGrid.tsx` — 100K+ row virtual scrolling with sticky headers
- `HeatmapChart.tsx` — ECharts heatmap for correlation matrices
- `ScatterPlot.tsx` — WebGL scatter for PCA (100K+ points)
- `CorrelationMatrix.tsx` — Trait correlation with significance
- `TraitRadar.tsx` — Multi-trait comparison radar chart
- `PedigreeViewer.tsx` — Interactive SVG pedigree with zoom/pan/export
- `SpatialFieldPlot.tsx` — Click-to-record field layout grid
- `KinshipNetwork.tsx` — Force-directed kinship graph
- `AMMIBiplot.tsx` — G×E biplot visualization

### 2. Mobile-First Field Data Collection

| Current Gap                          | Enhancement                                                    | Status    |
| ------------------------------------ | -------------------------------------------------------------- | --------- |
| Forms not optimized for gloved hands | Larger touch targets (min 48px), swipe gestures                | ✅ Done   |
| Camera integration is basic          | Add crop detection overlay, auto-focus hints                   | ✅ Done   |
| Offline sync UI is minimal           | Real-time sync queue visualization with conflict resolution UI | ✅ Done   |
| No voice input                       | Integrate with Veena AI for voice-controlled data entry        | ✅ Done   |

**Completed Components:**
- `useFieldMode.ts` — Hook with settings persistence, haptic feedback
- `FieldModeToggle.tsx` — Toggle with settings popover
- `field-mode.css` — WCAG AAA high contrast, 48px touch targets
- `FieldNumberInput.tsx` — Large +/- buttons, long-press support
- `FieldPlotNavigator.tsx` — Swipe gestures, keyboard nav
- `SyncStatusPanel.tsx` — Sync queue visualization
- `ConflictResolutionDialog.tsx` — Side-by-side conflict resolution
- `SyncIndicator.tsx` — Compact navbar indicator
- `VeenaVoiceInput.tsx` — Voice-to-text using Web Speech API

### 3. Accessibility & Internationalization

| Issue                        | Fix                                         | Status    |
| ---------------------------- | ------------------------------------------- | --------- |
| Contrast ratios inconsistent | Enforce WCAG AAA (7:1) for field conditions | ✅ Done   |
| RTL languages unsupported    | Add `dir="rtl"` support for Hindi, Arabic   | ✅ Done   |
| Screen reader navigation     | ARIA landmarks on all major sections        | 🟢 Partial |
| Colorblind-safe palettes     | Provide alternative chart color schemes     | ✅ Done   |

**Completed:**
- `field-mode.css` — WCAG AAA 7:1 contrast ratio
- `useColorScheme.ts` — Colorblind-safe Okabe-Ito palette
- `design-tokens.css` — Accessible color tokens

### 4. Information Architecture Refinements

| Feature                  | Description                        | Status    |
| ------------------------ | ---------------------------------- | --------- |
| Command Palette (⌘K)     | Jump to any entity                 | ✅ Done   |
| Recent Items Widget      | Last 10 accessed items             | ✅ Done   |
| Contextual Actions       | Right-click/long-press menus       | ✅ Done   |
| Breadcrumb + Quick Switch| Change context without leaving     | ✅ Done   |
| Favorites/Pinned Items   | User-defined shortcuts             | ✅ Done   |

---

## 🎨 Design System Refinements

### Color Token Improvements — ✅ DONE

Created `frontend/src/styles/design-tokens.css`:
- Status colors (success, warning, error, info)
- Scientific data colors (8 categorical)
- Colorblind-safe palette (Okabe-Ito)
- Sequential scales (blue, green)
- Diverging scales (red-white-green)
- Genotype colors (AA, AB, BB, missing)
- Density mode variables

### Typography Scale — ✅ DONE

Created `frontend/src/styles/typography.css`:
- `.text-data-mono` — Tabular numbers for data
- `.text-section-header` — Section titles
- `.text-table-header` — Uppercase table headers
- `.text-data-value` — Numeric values
- `.text-data-label` — Muted labels
- `.text-metric` — Large dashboard numbers
- `.text-scientific` — Scientific notation
- `.text-gene` — Italic gene names
- `.text-accession` — Accession numbers

### Spacing & Density Controls — ✅ DONE

Created `frontend/src/hooks/useDensity.ts`:
- `compact` — 4px base, power users
- `comfortable` — 8px base (default)
- `spacious` — 12px base, accessibility

---

## 🔧 Component Library Extensions

### High-Priority New Components

| Component            | Use Case                                  | Status    |
| -------------------- | ----------------------------------------- | --------- |
| `<VirtualDataGrid>`  | Genotyping marker tables, allele matrices | ✅ Done   |
| `<PedigreeViewer>`   | Interactive pedigree with zoom/pan        | ✅ Done   |
| `<SpatialFieldPlot>` | Click-to-record field layout              | ✅ Done   |
| `<TraitRadar>`       | Multi-trait comparison for selections     | ✅ Done   |
| `<TimelineActivity>` | Breeding program milestones               | ✅ Done   |
| `<SyncStatusBadge>`  | Offline-aware entity indicators           | ✅ Done   |
| `<VeenaVoiceInput>`  | Voice-to-text for field entry             | ✅ Done   |

### Existing Component Upgrades

| Component        | Enhancement                                            | Status    |
| ---------------- | ------------------------------------------------------ | --------- |
| `CommandPalette` | Add entity-specific actions (create, clone, archive)   | 🟡 Medium |
| `DataPanel`      | Virtual scrolling, column pinning, export to CSV/Excel | ✅ Done   |
| `Modal`          | Nested modals support, sheet variant for mobile        | 🟢 Partial |
| `LocationMap`    | Plot-level selection, GeoJSON import, GPS tracking     | 🟡 Medium |
| `ContextMenu`    | Right-click/long-press entity actions                  | ✅ Done   |

---

## 📊 Visualization Implementation Plan

### Phase 1: Core Data Viz — ✅ COMPLETE

| Task                      | Package             | Status    |
| ------------------------- | ------------------- | --------- |
| Add ECharts React wrapper | `echarts-for-react` | ✅ Done   |
| Allele frequency heatmap  | ECharts             | ✅ Done   |
| PCA scatter (10K+ points) | ECharts GL          | ✅ Done   |
| Trait correlation matrix  | ECharts heatmap     | ✅ Done   |
| Trait radar chart         | Recharts            | ✅ Done   |

### Phase 2: Specialized Scientific Viz — ✅ COMPLETE

| Task                     | Package                      | Status    |
| ------------------------ | ---------------------------- | --------- |
| Pedigree tree (DAG)      | Custom SVG with zoom/pan     | ✅ Done   |
| Kinship network graph    | ECharts force graph          | ✅ Done   |
| AMMI biplot (G×E)        | Custom ECharts               | ✅ Done   |

### Phase 3: Real-time & Streaming (Q3 2025)

| Task                    | Package               | Status    |
| ----------------------- | --------------------- | --------- |
| Live sensor data charts | ECharts + polling     | ✅ Done   |
| WASM compute progress   | Custom canvas         | 🟢 Low    |
| Field map GPS tracking  | Leaflet + geolocation | 🟢 Low    |

---

## 🌐 Offline-First UX Patterns — ✅ COMPLETE

### Sync Status Communication — ✅ DONE

Implemented in `frontend/src/components/sync/`:
- `SyncStatusPanel.tsx` — Full sync queue visualization
- `SyncIndicator.tsx` — Compact navbar indicator
- `SyncStatusBadge.tsx` — Per-entity sync status

### Conflict Resolution UI — ✅ DONE

Implemented `ConflictResolutionDialog.tsx`:
- Side-by-side version comparison
- Field-level conflict highlighting
- Keep Local / Keep Server / Merge options

---

## 🎤 Veena AI Integration Points

| Integration                 | Description                                                 | Status    |
| --------------------------- | ----------------------------------------------------------- | --------- |
| **Voice Data Entry**        | "Record trait value 185.5 for plot A-15"                    | 🟡 Medium |
| **Natural Language Search** | "Show me all germplasm with rust resistance above 7"        | 🟡 Medium |
| **Contextual Help**         | Veena explains current page/feature on request              | ✅ Done   |
| **Analysis Suggestions**    | "Based on your trial data, consider running GBLUP analysis" | 🟡 Medium |
| **Report Generation**       | "Generate a summary report for trial XYZ"                   | 🟡 Medium |

---

## ✅ Implementation Summary

### ✅ Completed (December 2025)

1. **ECharts integration** — HeatmapChart, ScatterPlot, CorrelationMatrix
2. **Virtual scrolling** — VirtualDataGrid with 100K+ row support
3. **Mobile touch targets** — Field mode with 48px min targets
4. **WCAG AAA contrast** — field-mode.css with 7:1 ratio
5. **Offline conflict resolution UI** — Full sync panel + conflict dialog
6. **Design tokens** — Color, typography, spacing systems
7. **Colorblind-safe palettes** — useColorScheme hook
8. **Density modes** — useDensity hook (compact/comfortable/spacious)
9. **TraitRadar** — Multi-trait comparison chart
10. **TimelineActivity** — Milestone timeline component
11. **SyncStatusBadge** — Per-entity sync indicator
12. **FavoritesPanel** — User-defined shortcuts with persistence
13. **VeenaVoiceInput** — Voice-to-text using Web Speech API
14. **PedigreeViewer** — Interactive SVG pedigree with zoom/pan/export
15. **SpatialFieldPlot** — Click-to-record field layout grid
16. **KinshipNetwork** — Force-directed kinship graph (ECharts)
17. **AMMIBiplot** — G×E biplot visualization
18. **DashboardGrid** — Drag-and-drop widget framework
19. **LiveSensorChart** — Real-time streaming chart with ECharts
20. **ContextMenu** — Right-click/long-press entity actions
21. **EntityContextMenu** — Entity-specific contextual actions
22. **CameraCapture** — Full camera integration with overlays
23. **PlantVisionAnalyzer** — AI disease/growth stage detection
24. **i18n System** — 7 languages with RTL support
25. **LanguageSelector** — Multi-variant language picker
26. **RTL Styles** — Complete RTL layout support

### 🟡 In Progress / Planned

1. TensorFlow.js model training for real disease detection
2. WASM compilation for Rust genomics modules

---

## 📐 Summary: Design Principles

1. **Data-Dense yet Scannable** — Scientific rigor with visual hierarchy
2. **Offline-First Always** — Every interaction must work without network
3. **Touch-Friendly by Default** — Field conditions are the primary context
4. **Progressive Disclosure** — Simple by default, powerful when needed
5. **Accessible & Inclusive** — WCAG AAA, colorblind-safe, multi-language

---

**ॐ श्री गणेशाय नमः** 🙏

_Building tools that empower breeders, researchers, and farmers worldwide._
