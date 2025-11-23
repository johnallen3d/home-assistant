# Home Assistant

## Access

### Network

via tailscale, hostname: `homeassistant`

### SSH

```bash
ssh root@homeassistant
```

### CLI

accessible via SSH

```bash
ssh root@homeassistant "ha --help"
```

## Scripts

- `./extract_config.sh` - downloads YAML config files (automations, scenes, configuration)
- `./inventory.sh` - generates device/entity inventory reports
