# shadcn/ui Integration

## Overview
Successfully integrated shadcn/ui component library into the Bijmantra frontend application.

## Components Installed

### Core Components
- **Button** - Accessible button component with variants (default, outline, ghost, etc.)
- **Card** - Container component with header, content, and footer sections
- **Dialog** - Modal dialog component
- **Alert Dialog** - Confirmation dialog for destructive actions
- **Input** - Form input component
- **Label** - Form label component
- **Textarea** - Multi-line text input
- **Select** - Dropdown select component
- **Badge** - Status and tag badges
- **Separator** - Visual divider
- **Skeleton** - Loading placeholder
- **Table** - Data table components
- **Dropdown Menu** - Context and action menus

## Configuration

### Tailwind Config
- Style: **New York** (Recommended)
- Base Color: **Neutral**
- CSS Variables: Configured in `src/index.css`

### Theme Variables
```css
--background: Light/dark background
--foreground: Text color
--primary: Primary brand color
--secondary: Secondary color
--muted: Muted text/backgrounds
--accent: Accent color
--destructive: Error/danger color
--border: Border color
--input: Input border color
--ring: Focus ring color
--radius: Border radius (0.5rem)
```

## Updated Components

### 1. ConfirmDialog
- Migrated from custom Modal to shadcn AlertDialog
- Improved accessibility
- Consistent styling with design system

### 2. Programs Page
- Using shadcn Button for actions
- Using shadcn Card for container
- Using shadcn Skeleton for loading states
- Pagination buttons use Button component

### 3. ProgramForm
- Using shadcn Card with CardHeader
- Using shadcn Input for text fields
- Using shadcn Textarea for multi-line input
- Using shadcn Label for form labels
- Using shadcn Button for submit/cancel actions

## Benefits

1. **Accessibility** - All components follow WAI-ARIA guidelines
2. **Consistency** - Unified design system across the app
3. **Customization** - Easy to customize via Tailwind classes
4. **Type Safety** - Full TypeScript support
5. **Copy-Paste** - Components are copied into your codebase (not a dependency)
6. **Composability** - Build complex UIs from simple primitives

## Next Steps

### Recommended Migrations
1. **Trials Page** - Update to use shadcn components
2. **Studies Page** - Update to use shadcn components
3. **Locations Page** - Update to use shadcn components
4. **Dashboard** - Update stat cards to use shadcn Card
5. **Forms** - Migrate all forms to use shadcn form components

### Additional Components to Add
- **Form** - Form validation with react-hook-form integration
- **Toast** - Notification system
- **Popover** - Floating content
- **Tooltip** - Hover information
- **Tabs** - Tabbed interfaces
- **Sheet** - Slide-out panels
- **Command** - Command palette
- **Data Table** - Advanced table with sorting, filtering, pagination

## Usage Examples

### Button
```tsx
import { Button } from '@/components/ui/button'

<Button>Click me</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button size="sm">Small</Button>
```

### Card
```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    Content goes here
  </CardContent>
</Card>
```

### Input with Label
```tsx
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

<div className="space-y-2">
  <Label htmlFor="email">Email</Label>
  <Input id="email" type="email" placeholder="Enter email" />
</div>
```

## Resources
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Component Examples](https://ui.shadcn.com/examples)
- [Themes](https://ui.shadcn.com/themes)
