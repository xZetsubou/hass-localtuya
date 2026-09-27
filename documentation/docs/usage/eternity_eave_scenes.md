# Enbrighten Eternity Eave factory scenes (local DP 106)

This opt-in scene profile is for Enbrighten Eternity Eave Lights, **not** all
Tuya lights in the generic `dj` category. The factory scene catalog was
captured from the Smart Life app and is shipped in
`custom_components/localtuya/scene_profiles/eternity_eave.csv`. Local scene
selection requires no Tuya cloud account or periodic synchronization.

For an existing LocalTuya light, leave its Boolean power DP set to 20, set
**Scene** to the device's mode DP (106 on the tested model), and set
**Scene profile** to **Enbrighten Eternity Eave Lights (DP 106)**. The factory
scenes then appear as effects on that light entity. For example:

```yaml
- action: light.turn_on
  target:
    entity_id: light.eave_lights
  data:
    effect: Halloween
```

Selecting a scene sends its captured default DP 106 value (including default
speed and brightness) to the light locally. The current effect is identified
by its mode prefix, even if speed or brightness is subsequently changed in
the vendor app. An unmapped mode, including DIY patterns, is not labeled as a
factory scene. The device must be powered and connected for control.

The CSV contains `name,default,speed`: `default` is the full captured mode
value and `speed` records whether Smart Life allows adjusting that scene's
speed. This profile only implements factory scene selection, not speed or
brightness sliders. Factory mode strings observed on the tested device have
12 hex characters: four identifying the scene, four for speed, and four for
brightness. Other firmware could differ. Additional entries should be based
on observed values, not inferred from adjacent scene numbers.
