# Ember Mug 2 Integration Troubleshooting

## Error

```
Failed setup, will retry: An error occurred updating CM19/CM21M: e=BleakError('Service Discovery has not been performed yet')
```

## Current Status

- **Integration:** ember_mug v1.3.0 (via HACS)
- **State:** `setup_retry` - continuously failing
- **Home Assistant:** 2025.12.3

## Analysis

This is a **Bluetooth Low Energy (BLE) issue** where the integration successfully connects to the mug but fails to complete the GATT service discovery phase.

Logs confirm the pattern:
```
[ember_mug.mug] Failed to subscribe to state attr: [org.bluez.Error.NotConnected] Not Connected
```

## Root Causes (from GitHub issues)

### 1. ESPHome Bluetooth Proxy Bug (Issue #78)

There's a **known regression** in ESPHome 2025.6.0+ that breaks Ember Mug connectivity. Users report downgrading ESPHome to 2025.5.x fixes the issue.

- https://github.com/sopelj/hass-ember-mug-component/issues/78

### 2. Cached Services Stale Data (Issue #77)

BlueZ caches GATT services, but if the cache becomes stale or corrupted, connections succeed but service discovery fails.

- https://github.com/sopelj/hass-ember-mug-component/issues/77

### 3. BLE Connection Race Condition

The mug connects but disconnects before service discovery completes (seen as `le-connection-abort-by-local` in logs).

## Recommended Fixes

### 1. Check Bluetooth proxy setup

Determine whether you're using an ESPHome Bluetooth proxy or native Bluetooth.

### 2. Clean re-pairing sequence

```
a) Remove the mug from HA completely (delete the integration entry)
b) Forget/unpair the mug from your phone's Ember app temporarily
c) Put mug in pairing mode (tap bottom until LED blinks blue)
d) Re-add through HA
```

### 3. If using ESPHome proxy, downgrade to 2025.5.2

Issue #78 explicitly confirms this fixes the problem.

### 4. Clear BlueZ cache (if using native Bluetooth)

```bash
# SSH into HA OS
bluetoothctl
remove <MAC_ADDRESS>  # Remove cached pairing
exit
```

### 5. Try native Bluetooth instead of proxy

If you have Bluetooth on your HA hardware, try disabling/removing the ESPHome proxy temporarily to rule it out.

## Questions to Answer

1. Are you using an ESPHome Bluetooth proxy, or the built-in Bluetooth on your HA server?
2. If ESPHome proxy, what version is it running?
3. Is the mug currently paired to your phone's Ember app? (BLE devices can typically only maintain one active connection)

## Related GitHub Issues

- [#78 - Can't connect when proxy updated to ESPHome 2025.6.0](https://github.com/sopelj/hass-ember-mug-component/issues/78) - **external problem** label
- [#77 - Unable to connect new mug, Stuck on "Failed setup"](https://github.com/sopelj/hass-ember-mug-component/issues/77) - **connection issue** label
- [#79 - BleakNotFoundError](https://github.com/sopelj/hass-ember-mug-component/issues/79) - similar symptoms
