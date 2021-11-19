[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
![Maintenance](https://img.shields.io/maintenance/yes/2021.svg)

# hass-peltec

Home Assistant custom component integration for Centrometal PelTec System with CM WiFi-Box.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## About

This component is originally based on
https://github.com/9a4gl/py-peltec

The integration / component is created to support Centrometal PelTec System with CM WiFi-Box in Home Assistant.

## Installation

Requires Home Assistant core-2021.11.3 or newer.

### Installation through HACS

If you have not yet installed HACS, go get it at https://hacs.xyz/ and walk through the installation and configuration.

Use "https://github.com/9a4gl/hass-peltec" as URL for a new HACS custom repository.

Then find the Centrometal PelTec System integration in HACS and install it.

Install the new integration through *Configuration -> Integrations* in HA (see below).

### Manual installation

Copy the sub-path `/hass-peltec/custom_components/peltec` of this repo into the path `/config/custom_components/peltec` of your HA installation.

Alternatively use the following commands within an SSH shell into your HA system.
Do NOT try to execute these commands directly your PC on a mounted HA file system. The resulting symlink would be broken for the HA file system.
```
cd /config
git clone https://github.com/9a4gl/hass-peltec.git

# if folder custom_components does not yet exist:
mkdir custom_components

cd custom_components
ln -s ../hass-peltec/custom_components/peltec
```

## Configuration

### Home Assistant

Setup under Integrations in Home Assistant, search for "Centrometal PelTec System". You need to enter e-mail and password.

Even though this integration can be installed and configured via the Home Assistant GUI (uses config flow), you might have to restart Home Assistant to get it working.

## Supported devices

The following devices are supported, other may work with CM WiFi-Box.

* Pel-Tec (12–96 kW) (lambda)

## Services

`paltec.turn`
Start or stop the bolier..

## Changelog

### 0.0.1
- TODO

## Development

### Debugging

To enable debug logging for this integration and related libraries you
can control this in your Home Assistant `configuration.yaml`
file. Example:

```
logger:
  default: info
  logs:
    custom_components.peltec: debug
    peltec: debug
```

After a restart detailed log entries will appear in `/config/home-assistant.log`.
