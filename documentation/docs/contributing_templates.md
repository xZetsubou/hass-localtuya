# Contributing Device Templates

Templates are YAML files in `custom_components/localtuya/templates/` that describe a device's entity configuration. Users can import them when adding a new device instead of configuring entities manually.

For existing templates, see the [Templates Catalog](templates_catalog.md).

---

## Creating a Template

### Export from a configured device (Recommended) { #export }

1. Go to **Settings → Devices & Services → LocalTuya → Configure**
2. Select **Reconfigure existing device**
3. Choose the device you want to export
4. Check **Save entity configuration as template**
5. Submit

The template will be saved to `custom_components/localtuya/templates/`.

### Write YAML manually

You can write a template by hand. See the example below and the [Templates Catalog](templates_catalog.md) for reference.

!!! warning "There is no validation for manually written templates. Double-check your DP IDs and platform settings."

example "2-Gang Switch template"

```yaml
- switch:
    id: "1"
    friendly_name: "Switch 1"
    entity_category: None
    is_passive_entity: false
    platform: "switch"

- switch:
    id: "2"
    friendly_name: "Switch 2"
    entity_category: None
    is_passive_entity: false
    platform: "switch"
```

## File Naming

Lowercase, underscore-separated. Include device type and optionally brand/model:

- `2g_switch.yaml`
- `zemismart_curtain_motor.yaml`
- `rgbw_bulb_music.yaml`

---

## Submitting a Pull Request

1. **Fork** the [repository](https://github.com/xZetsubou/hass-localtuya){target="_blank"}
2. Add your template YAML to `custom_components/localtuya/templates/`
3. Create a device markdown file in `documentation/docs/devices/` (see existing files for format)
4. Add a row to the **Available Templates** table in `templates_catalog.md` linking to your device page
5. Open a PR with: device name/model, category, entities included, and protocol version

### Before submitting

- Template tested — re-import it on a clean device to confirm it works
- No sensitive data (`local_key`, `device_id`, `ip`) in the file
- Friendly names are generic (e.g., "Switch 1" not "My Kitchen Light")
- Catalog page updated

!!! danger "Never share your `local_key` or `device_id` publicly."

!!! info "Templates load at HA startup. A restart is required after adding a new file."
