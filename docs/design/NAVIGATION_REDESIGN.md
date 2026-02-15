# Navigation Redesign Proposal

## Problem Statement

The current vertical navigation bar has become cluttered with 11+ divisions and 100+ items. Users are overwhelmed and can't find what they need quickly.

## Proposed Solution: Customizable Dock + Spotlight

Inspired by macOS Dock + Spotlight, Windows Start Menu, and modern productivity apps like Notion/Linear.

### Core Concepts

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  [Search ⌘K]                    [🔔] [👤] [⚙️]     │  ← Top Bar
├─────────────────────────────────────────────────────────────┤
│ ┌──────┐                                                    │
│ │ 🏠   │  Main Content Area                                │
│ │ 🌱   │                                                    │
│ │ 🧬   │                                                    │
│ │ 🌾   │                                                    │
│ │ ──── │  (Dock: User's pinned favorites)                  │
│ │ 📊   │                                                    │
│ │ ⚙️   │                                                    │
│ │      │                                                    │
│ │ [+]  │  ← Add to Dock                                    │
│ └──────┘                                                    │
└─────────────────────────────────────────────────────────────┘
```

### 1. The Dock (Left Sidebar)

A slim, icon-only sidebar with user's **pinned favorites**:

- **Default pins**: Dashboard, Programs, Germplasm, Trials, Settings
- **User customizable**: Drag to reorder, right-click to unpin
- **Hover tooltip**: Shows name
- **Click**: Goes to that module
- **[+] button**: Opens module browser to add more

**Benefits**:
- Clean, minimal interface
- User controls what they see
- Different users can have different workflows
- Scales to any number of modules

### 2. Spotlight / Command Palette (⌘K)

The **primary navigation method** for power users:

- Press `⌘K` anywhere
- Type to search: "germplasm", "create trial", "settings"
- Shows recent items, suggested actions
- Keyboard-first navigation

**Already exists** - just needs to be promoted as primary nav method.

### 3. Module Browser (App Launcher)

Accessed via [+] button or `⌘ Space`:

```
┌─────────────────────────────────────────────────────────────┐
│  Browse Modules                                    [×]      │
├─────────────────────────────────────────────────────────────┤
│  [Search modules...]                                        │
│                                                             │
│  ★ PINNED                                                   │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                          │
│  │ 🏠  │ │ 🌱  │ │ 📊  │ │ ⚙️  │                          │
│  │Dash │ │Plant│ │Stats│ │Set  │                          │
│  └─────┘ └─────┘ └─────┘ └─────┘                          │
│                                                             │
│  BREEDING                                                   │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                  │
│  │Prog │ │Trial│ │Study│ │Germ │ │Cross│                  │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                  │
│                                                             │
│  GENOMICS                                                   │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                          │
│  │Vari │ │Allel│ │GWAS │ │GS   │                          │
│  └─────┘ └─────┘ └─────┘ └─────┘                          │
│                                                             │
│  SEED OPERATIONS                                            │
│  ...                                                        │
└─────────────────────────────────────────────────────────────┘
```

### 4. Contextual Sub-Navigation

When inside a module, show relevant sub-pages:

```
┌──────────────────────────────────────────────────────────────┐
│ Plant Sciences                                               │
│ ┌────────┬────────┬────────┬────────┬────────┐              │
│ │Programs│ Trials │ Studies│Germplsm│ Crosses│              │
│ └────────┴────────┴────────┴────────┴────────┘              │
│                                                              │
│ [Main content for selected sub-page]                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Dock Foundation (MVP)
- [ ] Create `Dock.tsx` component (icon-only sidebar)
- [ ] Add pin/unpin functionality with localStorage persistence
- [ ] Default pins for new users
- [ ] Tooltip on hover

### Phase 2: Module Browser
- [ ] Create `ModuleBrowser.tsx` (grid of all modules)
- [ ] Categorized view
- [ ] Search within browser
- [ ] Click to navigate, right-click to pin

### Phase 3: Enhanced Command Palette
- [ ] Add "recent" section
- [ ] Add "suggested actions" based on context
- [ ] Improve search ranking

### Phase 4: User Preferences
- [ ] Save dock configuration to user profile (backend)
- [ ] Role-based default configurations
- [ ] Import/export dock settings

---

## Alternative Approaches Considered

### A. Mega Menu (Rejected)
- Hover to show large dropdown with all options
- **Problem**: Still overwhelming, not customizable

### B. Hamburger Menu (Rejected)
- Hide everything behind ☰
- **Problem**: Extra click for everything, poor discoverability

### C. Tab-based (Rejected)
- Horizontal tabs for divisions
- **Problem**: Doesn't scale, takes horizontal space

### D. Ribbon (Rejected)
- Microsoft Office style ribbon
- **Problem**: Complex, takes vertical space

---

## User Personas & Default Docks

### Breeder (Default)
```
🏠 Dashboard
🌱 Programs
🧪 Trials
🌾 Germplasm
✂️ Crosses
📊 Statistics
⚙️ Settings
```

### Seed Company
```
🏠 Dashboard
📦 Seed Lots
🔬 Quality Gate
🚚 Dispatch
📋 Traceability
📊 Reports
⚙️ Settings
```

### Researcher
```
🏠 Dashboard
🧬 Genomics
📊 Analytics
🔬 GWAS
📈 G×E Analysis
📚 Knowledge
⚙️ Settings
```

### Lab Technician
```
🏠 Dashboard
🧪 Samples
🔬 Testing
📋 Certificates
📦 Inventory
⚙️ Settings
```

---

## Decision Required

**Option A**: Full Dock implementation (2-3 days)
- Complete redesign with all features above

**Option B**: Quick Win - Collapsible Sidebar (1 day)
- Keep current structure but add collapse/expand
- Add "favorites" section at top

**Option C**: Hybrid (1-2 days)
- Add Dock alongside existing nav
- Users can choose which to use

**Recommendation**: Start with **Option C** (Hybrid) to test the concept without breaking existing workflows, then migrate to full Dock if users prefer it.

---

## Questions for Decision

1. Should dock be on left (macOS style) or bottom (Windows taskbar)?
2. Should we support multiple "workspaces" (saved dock configurations)?
3. Should dock auto-hide on small screens?
4. Should we show notification badges on dock icons?
