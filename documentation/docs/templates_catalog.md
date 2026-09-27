# Device Templates Catalog

Browse community-contributed device templates for LocalTuya. Use these templates to quickly configure your Tuya devices without manual DP mapping.

!!! tip "How to use a template"
    1. Download the YAML file and place it in `custom_components/localtuya/templates/`
    2. Restart Home Assistant
    3. When adding a new device, select **Use saved template** in the config flow
    4. Choose the template from the list

    Want to contribute your own? See the [Contributing Guide](contributing_templates.md).

---

## Available Templates

| Device | Brand | Category | Models |
|---|---|---|---|
| [HTW Smart Plus Water Heater](devices/htw_smart_water_heater.md) | HTW | :material-water-boiler: Water Heater | HTW-TV-030SMPLUS, HTW-TV-050SMPLUS, HTW-TV-080SMPLUS, HTW-TV-100SMPLUS |

---

## Adding Your Template to This Page

When you [contribute a template](contributing_templates.md), please also update this page in your Pull Request:

1. Create a new markdown file in `docs/devices/` for your device
2. Add a row to the **Available Templates** table above with the device name linking to your page
