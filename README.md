# hass-peltec

Home Assistant custom component integration for Centrometal PelTec System

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

### Important

This project is in early development stage, better not try to use it yet.
