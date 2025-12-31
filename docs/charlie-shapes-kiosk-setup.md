# Charlie Shapes Kiosk Mode Setup

A dedicated Nanoleaf Shapes dashboard for Charlie with kiosk mode enabled for non-admin users.

## Dashboard Details

- **Name:** Shapes
- **URL path:** `/charlie-shapes/shapes`
- **Sidebar:** Visible to all users

## Kiosk Mode Implementation

Uses the [kiosk-mode HACS integration](https://github.com/NemesisRE/kiosk-mode) to hide sidebar and header for non-admin users.

**Configuration** (in dashboard config root):
```yaml
kiosk_mode:
  non_admin_settings:
    hide_sidebar: true
    hide_header: true
```

### How It Works

- **Admin users:** See full UI (sidebar, header, navigation)
- **Non-admin users (Charlie):** See only the dashboard content, no navigation

### Requirements

1. Charlie must be a non-admin user in Home Assistant
2. kiosk-mode HACS integration must be installed

## Dashboard Features

- **Shapes tile** - Toggle on/off with brightness slider
- **17 Effect buttons** in 3-column grid:
  - Beatdrop, Blaze, Cocoa Beach, Cotton Candy
  - Date Night, Hip Hop, Hot Sauce, Jungle
  - Lightscape, Morning Sky, Northern Lights, Pop Rocks
  - Prism, Sonic Sunset, Starlight, Sundown, Waterfall

## Troubleshooting

**Kiosk mode not working:**
- Verify kiosk-mode is installed in HACS
- Clear browser cache / force refresh
- Confirm user is non-admin (Settings > People > Users)

**Admin needs to temporarily disable kiosk:**
- Add `?disable_km` to the URL

## Notes

- The original "Charlie" dashboard remains unchanged for admin use
- The companion app does NOT have native kiosk mode - this is a dashboard-level feature via the HACS integration
