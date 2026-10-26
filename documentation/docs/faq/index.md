# FAQ

#### Low Power Devices
!!! abstract ""
    A device that has [Low Power Mode](https://developer.tuya.com/en/docs/iot-device-dev/Low_consumption_Wi_Fi?id=Kay3gha1um42e){target="_blank"}, applied on such as __`Wi-Fi door locks and sensors`__. <br>
    The device will report its status every x minutes. Most of the time, the device will go into sleep mode, and most likely it will disconnect from the network.
    Some Device has an option to control the reports period.
    In order to add this device, you need to specify the device sleep time in the [device configartion](../usage/configure_add_device.md). <br>
    !!! tip ""
        If you add the device while it's sleeping and it's `disconnected` from the network, it won't connect <br>
        If you changed any value on the device while it is asleep, the new states will be applied when it wakes up. <br>
        Try to avoid WiFi Sensors devices and go for BLE or ZigBee.

<br>

#### IR Remotes
!!! abstract ""
    Usually, the IR remote devices doesn't have DPS status, so if you encounter an error `no datapoints could be found` If the device information is incorrect, this won't work. <br>
    you can ignore the handshake (which fails if no DPS is found) by adding __`0`__ in the manual DPS field.

<br>

#### Access Control Keypads
!!! abstract ""
    Card / PIN keypads and door controllers (Tuya category __`mk`__) only *push* their datapoints when something happens, so adding one fails with `no datapoints could be found`.
    Add __`0`__ in the manual DPS field to skip the handshake; with the cloud configured, `auto configure` then creates the entities. <br>
    Remote unlock is a code handshake: set the lock's __`Remote unlock key DP`__ to `remote_no_pd_setkey` (usually `8`) and use `remote_no_dp_key` (usually `9`) as the lock DP.
    Each unlock registers a one-time code that is valid for a few minutes, then unlocks with it. `closed_opened_kit` (usually `35`) as the lock state DP shows the strike opening and relocking.
    !!! warning ""
        Remote *lock* is refused for these devices: the keypads tested open the strike for a lock command too, and they relock on their own.

<br>

#### ZigBee Gateway
!!! abstract ""
    The ZigBee gateway isn't supposed to be added unless it has more features other than just being a hub. <br>
    Otherwise, if you added them, you will encounter an error stating `no datapoints could be found`.

<br>

### Devices Discovery
!!! abstract ""
    By default, `LocalTuya` includes a discovery feature that scans for Tuya devices within the local network and lists them in the config flow. 
    However, this function requires Home Assistant to have the same subnets as Tuya devices

<br>

### Cloud Pull
!!! abstract ""
    The cloud pull feature is just something I added to inform users that there might be some DPS that can be used, but weren't reported by the device. 
    Most of the cloud-pulled DPS aren't really useful; they might be encrypted or have empty values. 
    However, it won't change the fact that the device contains these DPS, so using them is up to the user.

<!-- ### Scenes Controllers
!!! abstract ""
    If you want to control Home Assistant automations from scene control devices, such as `remotes or switches`, you should consider adding them and relying on [events](/ha_events/) -->

