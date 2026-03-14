[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
![Maintenance](https://img.shields.io/maintenance/yes/2026.svg)

# hass-centrometal-boiler

Home Assistant custom component integration for Centrometal Boiler System (with CM WiFi-Box).

To visualize boiler display as card use https://github.com/9a4gl/lovelace-centrometal-boiler-card card.

## About

This is a fork of [hass-centrometal-boiler](https://github.com/9a4gl/hass-centrometal-boiler) by Tihomir Heidelberg, maintained by [Internetdivisor](https://github.com/Internetdivisor) with full PelTec II Lambda support and critical bug fixes.

## Supported devices

- **PelTec II Lambda** (`peltec2`) ← added in this fork
- PelTec-lambda, PelTec (`peltec`)
- CentroPlus + Cm Pelet-set (`cmpelet`)
- BioTec-L (`biotec`)
- BioTec-Plus / Morvan GMX EASY (`biopl`)
- EKO-CK P + Cm Pelet-set
- Compact variants

## Critical fix for all users

All sensors and switches were silently freezing at startup values and never updating from websocket pushes. This affected every device type. Fixed. Also fixes issue #21 (circuit switches always showing OFF).

See [CHANGELOG.md](CHANGELOG.md) for full details.

## Installation

Requires Home Assistant 2024.11.2 or newer.

### Manual installation

```bash
cd /config
git clone https://github.com/Internetdivisor/hass-centrometal-boiler-V2.git
mkdir -p custom_components
cd custom_components
ln -s ../hass-centrometal-boiler-V2/custom_components/centrometal_boiler
```

### HACS (custom repository)

1. HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/Internetdivisor/hass-centrometal-boiler-V2` as type **Integration**
3. Install "Centrometal Boiler System" and restart Home Assistant

## Configuration

Settings → Integrations → Add Integration → search "Centrometal Boiler System" → enter your web-boiler.com e-mail and password.

## Services

`centrometal_boiler.turn` — Start or stop the boiler.

## Debugging

```yaml
logger:
  default: info
  logs:
    custom_components.centrometal_boiler: debug
    centrometal_web_boiler: debug
```
