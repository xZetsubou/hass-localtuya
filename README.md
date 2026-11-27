<a  href="https://www.buymeacoffee.com/mrbanderx3"  target="_blank"><img  src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png"  alt="Buy Me A Coffee"  style="height: 30px !important;width: 150px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

---


![logo](https://github.com/rospogrigio/localtuya-homeassistant/blob/master/img/logo-small.png)


__A Home Assistant custom Integration for local handling of Tuya-based devices.__

### **Usage and setup [Documentation](https://xzetsubou.github.io/hass-localtuya/)**

<br>

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=hass-localtuya&owner=xZetsubou)



## __𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬__
- Supported Sub-devices - `Devices that function through gateways`
- Remote entities - `Supports IR remotes through native remote entity`
- Auto-configure devices - `Requires a cloud API setup`
- Automatic insertion - `Some fields requires a cloud API setup`
- Devices discovery - `Discovers Tuya devices on your network`
- Cloud API - `Only to help you to setup devices, can work without it.`



<br>

[𝐑𝐞𝐩𝐨𝐫𝐭𝐢𝐧𝐠 𝐚𝐧 𝐢𝐬𝐬𝐮𝐞](https://xzetsubou.github.io/hass-localtuya/report_issue/)

<!-- ### Notes

* Do not declare anything as "tuya", such as by initiating a "switch.tuya". Using "tuya" launches Home Assistant's built-in, cloud-based Tuya integration in lieu of localtuya.

* This custom integration updates device status via pushing updates instead of polling, so status updates are fast (even when manually operated).

* The integration also supports the Tuya IoT Cloud APIs, for the retrieval of info and of the local_keys of the devices. 
The Cloud API account configuration is not mandatory (LocalTuya can work also without it) but is strongly suggested for easy retrieval (and auto-update after re-pairing a device) of local_keys. Cloud API calls are performed only at startup, and when a local_key update is needed. -->

<details><summary> 𝐂𝐫𝐞𝐝𝐢𝐭𝐬 </summary>
<p>
    
[rospogrigio](https://github.com/rospogrigio), the original maintainer of LocalTuya. This fork was created when the [upstream](https://github.com/rospogrigio/localtuya) version was at `v5.2.1`.

[NameLessJedi](https://github.com/NameLessJedi/localtuya-homeassistant) and [mileperhour](https://github.com/mileperhour/localtuya-homeassistant) being the major sources of inspiration, and whose code for switches is substantially unchanged.

[TradeFace](https://github.com/TradeFace), for being the only one to provide the correct code for communication with the cover (in particular, the 0x0d command for the status instead of the 0x0a, and related needs such as double reply to be received): 

sean6541, for the working (standard) Python Handler for Tuya devices.

[jasonacox](https://github.com/jasonacox), for the [TinyTuya](https://github.com/jasonacox/tinytuya) project from where I got big help and references to upgrade integration.

[uzlonewolf](https://github.com/uzlonewolf), for maintaining TinyTuya who improved the tool so much and introduced new features like new protocols, etc.

[postlund](https://github.com/postlund), for the ideas, for coding 95% of the refactoring and boosting the quality of the upstream repository.

</p>
</details> 
