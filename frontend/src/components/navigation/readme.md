# Mahasarthi Navigation System

This directory contains the components for **Mahasarthi** ("The Great Charioteer"), the central navigation system for the BijMantra platform.

## Core Components

| Component                   | Description                                                                                                                                        |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`Mahasarthi.tsx`**        | The main controller component. Orchestrates the Sidebar, Dock, Search, and Strata components based on responsive state.                            |
| **`MahasarthiSidebar.tsx`** | The visual sidebar container featuring the signature diagonal "slashed" edge design. Handles collapse/expand animations and mobile swipe gestures. |
| **`MahasarthiNav.tsx`**     | Adaptor component that integrates the Mahasarthi system into the application's layout.                                                             |
| **`MahasarthiDock.tsx`**    | **Desktop**: Vertical icon-only strip for pinned/recent apps.`<br>`**Mobile**: Bottom tab bar navigation.                                          |
| **`MahasarthiStrata.tsx`**  | The "Start Menu" / App Launcher overlay. Provides a folder-based view of all available modules and divisions ("Web-OS" style).                     |
| **`MahasarthiSearch.tsx`**  | Global Command Palette (`Cmd+K`). Supports fuzzy search for pages, quick actions, and navigation.                                                  |
| **`MahasarthiKshetra.tsx`** | **Workspace Switcher**. The dropdown menu allows users to switch between major functional domains (Breeding, Seed Ops, Research, etc.).            |

## Helper Components

| Component                       | Description                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------ |
| **`MahasarthiBreadcrumbs.tsx`** | Context-aware breadcrumb trails ensuring user orientation within the "Navigation Gravity" model. |
| **`ContextualTabs.tsx`**        | Horizontal secondary navigation bar showing sections within the current active Division.         |
| **`StrataFolder.tsx`**          | UI component used by *MahasarthiStrata* to render grid grids of folders and app icons.           |
| **`QuickActionFAB.tsx`**        | Mobile-only Floating Action Button for high-frequency field tasks (Scan, Photo, Collect).        |

## Architecture Notes

- **Navigation Gravity**: The system follows a hierarchy of Workspace > Division > Section > Page.
- **Responsive Design**:
  - **Desktop**: Vertical Sidebar + Dock.
  - **Mobile**: Bottom Tab Bar + Full-screen Strata Overlay.
- **State Management**: Uses `dockStore` for pinned/recent items and `workspaceStore` for active context.
