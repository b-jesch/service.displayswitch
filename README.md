<h1>RPi Display Switch</h1>

This service is used to switch the output between the different video ports of a Raspberry Pi. For example, it is possible 
to switch between a connected SDI device (RPi TFT Display) and a device connected to the HDMI output.
 
To do this, the original config.txt is exchanged against a user-defined configuration and the RPi restarts inorder to load 
the new configuration.

To switch the display configuration a push button is connected to GPIO 5 and GND. If this button is pressed, the configuration 
files in the read-only ```/flash``` partition are exchanged and the RPi restarts.

If the button was pressed for more than 3 seconds, a shutdown is performed without changing the display configuration.

The configuration files for the displays are located in the directory ```/storage/.kodi/userdata/addon_data/service.displayswitch/configs/``` and 
should only be changed or adapted here. This prevents unintentional changes to the configuration files after an update of the addon.

Additionally, the first time the addon is started, the original configuration is copied to ```/flash/config.txt.origin```. If the RPi 
does not start after a configuration change, this file on the SD card can be simply copied back to ```config.txt``` e.g. on a Windows PC 
with a card reader.

If you want to use a remote control or a keyboard to switch between the display you can simply define a button in the ```keymap.xml``` - which 
must reside within the ```.kodi/userdata/keymaps``` folder of your installation. In this example the buttons CTRL-F1 and CTRL-F2
are used to switch between the displays and poweroff the device:

    <keymap>
        <global>
            <keyboard>
                <f1 mod="ctrl">XBMC.RunScript(service.displayswitch,switch)</f1>
                <f2 mod="ctrl">XBMC.RunScript(service.displayswitch,poweroff)</f1>
            </keyboard>
        </global>
    </keymap>
