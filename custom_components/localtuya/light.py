"""Platform to locally control Tuya-based light devices."""

import base64
import logging
import textwrap
import homeassistant.util.color as color_util
import voluptuous as vol

from dataclasses import dataclass
from functools import partial
from homeassistant.helpers import selector
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    DOMAIN,
    LightEntityFeature,
    ColorMode,
    LightEntity,
)
from homeassistant.const import CONF_BRIGHTNESS, CONF_COLOR_TEMP, CONF_SCENE

from .config_flow import col_to_select
from .entity import LocalTuyaEntity, async_setup_entry
from .const import (
    CONF_BRIGHTNESS_LOWER,
    CONF_BRIGHTNESS_UPPER,
    CONF_COLOR,
    CONF_COLOR_MODE,
    CONF_COLOR_MODE_SET,
    CONF_COLOR_TEMP_MAX_KELVIN,
    CONF_COLOR_TEMP_MIN_KELVIN,
    CONF_COLOR_TEMP_REVERSE,
    CONF_MUSIC_MODE,
    CONF_SCENE_VALUES,
    CONF_WRITE_ONLY,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_MIN_KELVIN = 2700  # MIRED 370
DEFAULT_MAX_KELVIN = 6500  # MIRED 153

DEFAULT_COLOR_TEMP_REVERSE = False

DEFAULT_LOWER_BRIGHTNESS = 29
DEFAULT_UPPER_BRIGHTNESS = 1000

MODE_MANUAL = "manual"
MODE_COLOR = "colour"
MODE_MUSIC = "music"
MODE_SCENE = "scene"
MODE_WHITE = "white"

SCENE_MUSIC = "Music"

MODES_SET = {"Colour, Music, Scene and White": 0, "Manual, Music, Scene and White": 1}

# https://developer.tuya.com/en/docs/iot/dj?id=K9i5ql3v98hn3#title-10-scene_data
SCENE_LIST_RGBW_255 = {
    "Night": "bd76000168ffff",
    "Read": "fffcf70168ffff",
    "Meeting": "cf38000168ffff",
    "Leasure": "3855b40168ffff",
    "Scenario 1": "scene_1",
    "Scenario 2": "scene_2",
    "Scenario 3": "scene_3",
    "Scenario 4": "scene_4",
}

# https://developer.tuya.com/en/docs/iot/dj?id=K9i5ql3v98hn3#title-11-scene_data_v2
SCENE_LIST_RGBW_1000 = {
    "Night": "000e0d0000000000000000c80000",
    "Read": "010e0d0000000000000003e801f4",
    "Meeting": "020e0d0000000000000003e803e8",
    "Leasure": "030e0d0000000000000001f401f4",
    "Soft": "04464602007803e803e800000000464602007803e8000a00000000",
    "Rainbow": "05464601000003e803e800000000464601007803e803e80000000046460100f003e803"
    + "e800000000",
    "Shine": "06464601000003e803e800000000464601007803e803e80000000046460100f003e803e8"
    + "00000000",
    "Beautiful": "07464602000003e803e800000000464602007803e803e80000000046460200f003e8"
    + "03e800000000464602003d03e803e80000000046460200ae03e803e800000000464602011303e80"
    + "3e800000000",
}
SCENE_LIST_RGB_1000 = {
    "Night": "000e0d00002e03e802cc00000000",
    "Read": "010e0d000084000003e800000000",
    "Working": "020e0d00001403e803e800000000",
    "Leisure": "030e0d0000e80383031c00000000",
    "Soft": "04464602007803e803e800000000464602007803e8000a00000000",
    "Colorful": "05464601000003e803e800000000464601007803e803e80000000046460100f003e80"
    + "3e800000000464601003d03e803e80000000046460100ae03e803e800000000464601011303e803"
    + "e800000000",
    "Dazzling": "06464601000003e803e800000000464601007803e803e80000000046460100f003e80"
    + "3e800000000",
    "Gorgeous": "07464602000003e803e800000000464602007803e803e80000000046460200f003e803e8"
    + "00000000464602003d03e803e80000000046460200ae03e803e800000000464602011303e803e80"
    + "0000000",
}

# BASE64-encoded 1-byte numbers.
# Other numbers up to 0x10 were tested to no avail.
SCENE_LIST_RGBW_BLE = {
    "Good Night": "AA==", # 00
    "Leisure":    "Aw==", # 01
    "Gorgeous":   "Bw==", # 07
    "Dream":      "HA==", # 1C
    "Sunflower":  "GA==", # 18
    "Grassland":  "BA==", # 04
}

@dataclass(frozen=True)
class Mode:
    color: str = MODE_COLOR
    music: str = MODE_MUSIC
    scene: str = MODE_SCENE
    white: str = MODE_WHITE

    def as_list(self) -> list:
        return [self.color, self.music, self.scene, self.white]

    def as_dict(self) -> dict[str, str]:
        default = {"Default": self.white}
        return {**default, "Mode Color": self.color, "Mode Scene": self.scene}


MAP_MODE_SET = {0: Mode(), 1: Mode(color=MODE_MANUAL)}


def map_range(value, from_lower, from_upper, to_lower=0, to_upper=255, reverse=False):
    """Map a value in one range to another."""
    if reverse:
        value = from_upper - value + from_lower
    mapped = value * to_upper / from_upper
    return min(max(round(mapped), to_lower), to_upper)


def flow_schema(dps):
    """Return schema used in config flow."""
    return {
        vol.Optional(CONF_BRIGHTNESS): col_to_select(dps, is_dps=True),
        vol.Optional(CONF_COLOR_TEMP): col_to_select(dps, is_dps=True),
        vol.Optional(CONF_BRIGHTNESS_LOWER, default=DEFAULT_LOWER_BRIGHTNESS): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=10000)
        ),
        vol.Optional(CONF_BRIGHTNESS_UPPER, default=DEFAULT_UPPER_BRIGHTNESS): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=10000)
        ),
        vol.Optional(CONF_COLOR_MODE): col_to_select(dps, is_dps=True),
        vol.Required(CONF_COLOR_MODE_SET, default="0"): col_to_select(MODES_SET),
        vol.Optional(CONF_COLOR): col_to_select(dps, is_dps=True),
        vol.Optional(CONF_COLOR_TEMP_MIN_KELVIN, default=DEFAULT_MIN_KELVIN): vol.All(
            vol.Coerce(int), vol.Range(min=1500, max=8000)
        ),
        vol.Optional(CONF_COLOR_TEMP_MAX_KELVIN, default=DEFAULT_MAX_KELVIN): vol.All(
            vol.Coerce(int), vol.Range(min=1500, max=8000)
        ),
        vol.Optional(CONF_COLOR_TEMP_REVERSE, default=DEFAULT_COLOR_TEMP_REVERSE): bool,
        vol.Optional(CONF_SCENE): col_to_select(dps, is_dps=True),
        vol.Optional(CONF_SCENE_VALUES, default={}): selector.ObjectSelector(),
        vol.Optional(CONF_MUSIC_MODE, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_WRITE_ONLY, default=False): selector.BooleanSelector(),
    }


class LocalTuyaLight(LocalTuyaEntity, LightEntity):
    """Representation of a Tuya light."""

    def __init__(
        self,
        device,
        config_entry,
        lightid,
        **kwargs,
    ):
        """Initialize the Tuya light."""
        super().__init__(device, config_entry, lightid, _LOGGER, **kwargs)
        # Light is an active device (mains powered). It should be able
        # to respond at any time. But Tuya BLE bulbs are write-only.
        self._write_only = self._config.get(CONF_WRITE_ONLY, False)
        if self._write_only:
            self._device.write_only = self._write_only

        self._state = None
        self._color_temp = None
        self._lower_brightness = int(
            self._config.get(CONF_BRIGHTNESS_LOWER, DEFAULT_LOWER_BRIGHTNESS)
        )
        self._upper_brightness = int(
            self._config.get(CONF_BRIGHTNESS_UPPER, DEFAULT_UPPER_BRIGHTNESS)
        )
        self._brightness = None if not self._write_only else self._upper_brightness
        self._upper_color_temp = self._upper_brightness
        self._min_kelvin = int(
            self._config.get(CONF_COLOR_TEMP_MIN_KELVIN, DEFAULT_MIN_KELVIN)
        )
        self._max_kelvin = int(
            self._config.get(CONF_COLOR_TEMP_MAX_KELVIN, DEFAULT_MAX_KELVIN)
        )
        self._color_temp_reverse = self._config.get(
            CONF_COLOR_TEMP_REVERSE, DEFAULT_COLOR_TEMP_REVERSE
        )
        self._modes = MAP_MODE_SET[int(self._config.get(CONF_COLOR_MODE_SET, 0))]
        self._hs = None
        self._effect = None
        self._effect_list = []
        self._scenes = {}

        if self.has_config(CONF_SCENE):
            if self.has_config(CONF_SCENE_VALUES) and len(self._config.get(CONF_SCENE_VALUES)):
                values_list = list(self._config.get(CONF_SCENE_VALUES))
                values_name = list(self._config.get(CONF_SCENE_VALUES).values())
                self._scenes = dict(zip(values_name, values_list))
            elif self._write_only: # BLE bulbs
                self._scenes = SCENE_LIST_RGBW_BLE
            elif int(self._config.get(CONF_SCENE)) < 20:
                self._scenes = SCENE_LIST_RGBW_255
            elif self._config.get(CONF_BRIGHTNESS) is None:
                self._scenes = SCENE_LIST_RGB_1000
            else:
                self._scenes = SCENE_LIST_RGBW_1000

            self._scenes = {**self._modes.as_dict(), **self._scenes}

            self._effect_list = list(self._scenes.keys())
        elif self._write_only and self._config.get(CONF_MUSIC_MODE):
            # BLE bulbs with no scene value DP configured
            self._scenes = self._modes.as_dict()

        if self._config.get(CONF_MUSIC_MODE):
            self._effect_list.append(SCENE_MUSIC)

    @property
    def is_on(self):
        """Check if Tuya light is on."""
        return self._state

    @property
    def brightness(self):
        """Return the brightness of the light."""
        brightness = self._brightness
        if brightness is not None and (self.is_color_mode or self.is_white_mode):
            if self._upper_brightness >= 1000:
                # Round to the nearest 10th, since Tuya does that.
                # If the value is less than 5, it will round down to 0.
                # So instead, we take _lower_brightness, which is < 5 in this case.
                brightness = (
                    (brightness + 5) // 10 * 10
                    if brightness >= 5
                    else self._lower_brightness
                )
            return map_range(
                brightness, self._lower_brightness, self._upper_brightness, 0, 255
            )
        return None

    @property
    def hs_color(self):
        """Return the hs color value."""
        if self.is_color_mode:
            return self._hs
        if (
            ColorMode.HS in self.supported_color_modes
            and not ColorMode.COLOR_TEMP in self.supported_color_modes
        ):
            return [0, 0]
        return None

    @property
    def color_temp(self):
        """Return the color_temp of the light."""
        if self._color_temp is None:
            return None
        if self.has_config(CONF_COLOR_TEMP):
            color_temp = (
                self._upper_color_temp - self._color_temp
                if self._color_temp_reverse
                else self._color_temp
            )
            return int(
                self.max_mireds
                - (
                    ((self.max_mireds - self.min_mireds) / self._upper_color_temp)
                    * color_temp
                )
            )
        return None

    @property
    def min_mireds(self):
        """Return color temperature min mireds."""
        return color_util.color_temperature_kelvin_to_mired(self._max_kelvin)

    @property
    def max_mireds(self):
        """Return color temperature max mireds."""
        return color_util.color_temperature_kelvin_to_mired(self._min_kelvin)

    @property
    def effect(self):
        """Return the current effect for this light."""
        if self.is_scene_mode or self.is_music_mode:
            return self._effect
        elif (color_mode := self.__get_color_mode()) in self._scenes.values():
            return self.__find_scene_by_scene_data(color_mode)
        return None

    @property
    def effect_list(self):
        """Return the list of supported effects for this light."""
        if len(self._effect_list) > 0:
            return self._effect_list
        return None

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Flag supported color modes."""
        color_modes: set[ColorMode] = set()

        if self.has_config(CONF_COLOR_TEMP):
            color_modes.add(ColorMode.COLOR_TEMP)
        if self.has_config(CONF_COLOR):
            color_modes.add(ColorMode.HS)

        if not color_modes and self.has_config(CONF_BRIGHTNESS):
            return {ColorMode.BRIGHTNESS}

        if not color_modes:
            return {ColorMode.ONOFF}

        return color_modes

    @property
    def supported_features(self) -> LightEntityFeature:
        """Flag supported features."""
        supports = LightEntityFeature(0)
        if self.has_config(CONF_SCENE) or self.has_config(CONF_MUSIC_MODE):
            supports |= LightEntityFeature.EFFECT
        return supports

    @property
    def is_white_mode(self):
        """Return true if the light is in white mode."""
        color_mode = self.__get_color_mode()
        return color_mode is None or color_mode == self._modes.white

    @property
    def is_color_mode(self):
        """Return true if the light is in color mode."""
        color_mode = self.__get_color_mode()
        return color_mode is not None and color_mode == self._modes.color

    @property
    def is_scene_mode(self):
        """Return true if the light is in scene mode."""
        color_mode = self.__get_color_mode()
        return color_mode is not None and color_mode.startswith(self._modes.scene)

    @property
    def is_music_mode(self):
        """Return true if the light is in music mode."""
        color_mode = self.__get_color_mode()
        return color_mode is not None and color_mode == self._modes.music

    @property
    def color_mode(self) -> ColorMode:
        """Return the color_mode of the light."""
        if len(self.supported_color_modes) == 1:
            return next(iter(self.supported_color_modes))

        if self.is_color_mode:
            return ColorMode.HS
        if self.is_white_mode:
            return ColorMode.COLOR_TEMP
        if self._brightness:
            return ColorMode.BRIGHTNESS

        return ColorMode.ONOFF

    def __is_color_rgb_encoded(self):
        # for now we will prefer non encoded if color is none "added by manual or cloud pull dp"
        color = self.dp_value(CONF_COLOR)
        return False if color is None else len(color) > 12

    def __find_scene_by_scene_data(self, data):
        return next(
            (item for item in self._effect_list if self._scenes.get(item) == data),
            None,
        )

    def __get_color_mode(self):
        return (
            self.dp_value(CONF_COLOR_MODE)
            if self.has_config(CONF_COLOR_MODE)
            else self._modes.white
        )

    def __to_color(self, hs, brightness):
        """Converts HSB values to a string."""
        # FIXME: the format should be selected by DP name, not a fuzzy logic
        if self._write_only: # BLE bulbs
            color = base64.b64encode(
# BASE64-encoded 4-byte value: HHSL
                bytes([
                        round(hs[0]) // 256,
                        round(hs[0]) % 256,
                        round(hs[1]),
                        round(brightness * 100 / self._upper_brightness)
                ])
            ).decode("ascii")
            self._hs = hs
        elif self.__is_color_rgb_encoded():
# It is not
# https://developer.tuya.com/en/docs/iot/dj?id=K9i5ql3v98hn3#title-8-colour_data
            rgb = color_util.color_hsv_to_RGB(
                hs[0], hs[1], int(brightness * 100 / self._upper_brightness)
            )
            color = "{:02x}{:02x}{:02x}{:04x}{:02x}{:02x}".format(
                round(rgb[0]),
                round(rgb[1]),
                round(rgb[2]),
                round(hs[0]),
                round(hs[1] * 255 / 100),
                brightness,
            )
        else:
# https://developer.tuya.com/en/docs/iot/dj?id=K9i5ql3v98hn3#title-9-colour_data_v2
            color = "{:04x}{:04x}{:04x}".format(
                round(hs[0]), round(hs[1] * 10.0), brightness
            )
        return color

    def __from_color(self, color):
        """Convert a string to HSL values."""
        if self._write_only: # BLE bulbs
            hsl = int.from_bytes(
                base64.b64decode(color), byteorder='big', signed=False
            )
            hue = hsl // 65536
            sat = (hsl // 256) % 256
            value = (hsl % 256) * self._upper_brightness / 100
            self._hs = [hue, sat]
            self._brightness = value
        elif self.__is_color_rgb_encoded():
            hue = int(color[6:10], 16)
            sat = int(color[10:12], 16)
            value = int(color[12:14], 16)
            self._hs = [hue, sat]
            self._brightness = value
        else:
            hue, sat, value = [
                int(value, 16) for value in textwrap.wrap(color, 4)
            ]
            self._hs = [hue, sat / 10.0]
            self._brightness = value

    async def async_turn_on(self, **kwargs):
        """Turn on or control the light."""
        states = {}
        if not self.is_on or self._write_only:
            states[self._dp_id] = True
        features = self.supported_features
        color_modes = self.supported_color_modes
        brightness = None
        color_mode = None
        if ATTR_EFFECT in kwargs and (features & LightEntityFeature.EFFECT):
            effect = kwargs[ATTR_EFFECT]
            scene = self._scenes.get(effect)
            if scene is not None:
                if scene.startswith(self._modes.scene) or scene in (
                    self._modes.white,
                    self._modes.color,
                ):
                    color_mode = scene
                else:
                    color_mode = self._modes.scene
                    states[self._config.get(CONF_SCENE)] = scene
            elif effect in self._modes.as_list():
                color_mode = effect
            elif effect == self._modes.music:
                color_mode = self._modes.music

        if ATTR_BRIGHTNESS in kwargs and (
            ColorMode.BRIGHTNESS in color_modes
            or self.has_config(CONF_BRIGHTNESS)
            or self.has_config(CONF_COLOR)
        ):
            brightness = map_range(
                int(kwargs[ATTR_BRIGHTNESS]),
                0,
                255,
                self._lower_brightness,
                self._upper_brightness,
            )
            if self.is_color_mode and self._hs is not None:
                states[self._config.get(CONF_COLOR)] = self.__to_color(self._hs, brightness)
                color_mode = self._modes.color
            else:
                states[self._config.get(CONF_BRIGHTNESS)] = brightness
                color_mode = self._modes.white

        if ATTR_HS_COLOR in kwargs and ColorMode.HS in color_modes:
            if brightness is None:
                brightness = self._brightness
            hs = kwargs[ATTR_HS_COLOR]
            if hs[1] == 0 and self.has_config(CONF_BRIGHTNESS):
                states[self._config.get(CONF_BRIGHTNESS)] = brightness
                color_mode = self._modes.white
            else:
                states[self._config.get(CONF_COLOR)] = self.__to_color(hs, brightness)
                color_mode = self._modes.color

        if ATTR_COLOR_TEMP in kwargs and ColorMode.COLOR_TEMP in color_modes:
            if brightness is None:
                brightness = self._brightness
            mired = int(kwargs[ATTR_COLOR_TEMP])
            if self._color_temp_reverse:
                mired = self.max_mireds - (mired - self.min_mireds)
            if mired < self.min_mireds:
                mired = self.min_mireds
            elif mired > self.max_mireds:
                mired = self.max_mireds
            color_temp = int(
                self._upper_color_temp
                - (self._upper_color_temp / (self.max_mireds - self.min_mireds))
                * (mired - self.min_mireds)
            )
            color_mode = self._modes.white
            states[self._config.get(CONF_BRIGHTNESS)] = brightness
            states[self._config.get(CONF_COLOR_TEMP)] = color_temp

        if color_mode is not None:
            states[self._config.get(CONF_COLOR_MODE)] = color_mode

        await self._device.set_dps(states)

    async def async_turn_off(self, **kwargs):
        """Turn Tuya light off."""
        await self._device.set_dp(False, self._dp_id)

    def status_updated(self):
        """Device status was updated."""
        self._state = self.dp_value(self._dp_id)
        supported = self.supported_features
        self._effect = None

        if brightness_dp_value := self.dp_value(CONF_BRIGHTNESS, None):
            self._brightness = brightness_dp_value

        if ColorMode.HS in self.supported_color_modes:
            color = self.dp_value(CONF_COLOR)
            if color is not None and not self.is_white_mode:
                self.__from_color(color)
            elif self._brightness is None:
                self._brightness = self._upper_brightness

        if ColorMode.COLOR_TEMP in self.supported_color_modes:
            self._color_temp = self.dp_value(CONF_COLOR_TEMP)

        if self.is_scene_mode and supported & LightEntityFeature.EFFECT:
            if self.dp_value(CONF_COLOR_MODE) != self._modes.scene:
                self._effect = self.__find_scene_by_scene_data(
                    self.dp_value(CONF_COLOR_MODE)
                )
            else:
                self._effect = self.__find_scene_by_scene_data(
                    self.dp_value(CONF_SCENE)
                )
                if self._effect is None:
                    self._effect = self.__find_scene_by_scene_data(
                        self._modes.scene
                    )

        if self.is_music_mode and supported & LightEntityFeature.EFFECT:
            self._effect = SCENE_MUSIC


async_setup_entry = partial(async_setup_entry, DOMAIN, LocalTuyaLight, flow_schema)
