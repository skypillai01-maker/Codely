# design.md: Design System & UI/UX Rules

## 1. Color Palette (Exact Hex Codes)
| Name | Hex Code | Usage |
|------|---------|-------|
| Primary Background | #343541 | Main chat area background |
| Secondary Background | #202123 | Sidebar background |
| Accent Green | #19c37d | Primary button, active indicator |
| Accent Green Hover | #10a556 | Hover state for accent green |
| Border Color | #343541 | Dividers, borders |
| Border Light | #565869 | Light borders (new chat button) |
| Text Primary | #ffffff | Main text |
| Text Secondary | #8e8ea0 | Muted text, previews |

## 2. Typography
- **Body Font**: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif (system stack, no custom fonts)
- **Font Sizes (px)**:
  - Base: 14px (buttons, thread names)
  - Muted: 12px (previews, small text)

## 3. Spacing & Layout Rules
- **Sidebar Width**: 300px fixed
- **Border Radius**: 5px for buttons, 4px for small elements (thread icon)
- **Padding (px)**:
  - Sidebar header/footer: 15px
  - Buttons: 12px 15px
  - Thread items: 12px 15px
  - Thread list: 10px vertical
- **Gaps (px)**:
  - Button/icon gap: 10px
  - Thread actions gap: 5px

## 4. UI/UX Behavior Rules
- **Hover States**: All interactive elements have smooth hover transitions (0.2s duration)
- **Active Threads**: Active thread has left border in accent green (#19c37d), and uses primary background color (#343541)
- **Hidden Actions**: Thread actions are hidden by default (opacity:0), appear on hover (opacity:1, 0.2s transition)
- **Overflow Handling**: Long thread names/previews use text-overflow: ellipsis, white-space: nowrap
- **Responsive**: Viewport meta tag set to width=device-width, initial-scale=1.0
