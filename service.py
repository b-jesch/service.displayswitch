# coding=utf-8

import RPi.GPIO as GPIO
import time
import sys
import os
import subprocess

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib.tools import OsRelease, KodiLib

addon = xbmcaddon.Addon(id='service.displayswitch')
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
addon_profile = xbmc.translatePath(addon.getAddonInfo('profile'))
LOC = addon.getLocalizedString

system_config_path = '/flash/config.txt'
system_config_backup = '/flash/config.txt.origin'

addon_config_path = os.path.join(addon_path, 'resources', 'configs')
user_config_path = os.path.join(addon_profile, 'configs')
user_config_1 = 'config.DSI'
user_config_2 = 'config.HDMI'

osr = OsRelease()
kl = KodiLib()
monitor = xbmc.Monitor()

kl.log('Device is {} on {} ({})'.format(osr.device, osr.osid, osr.project), xbmc.LOGINFO)
if osr.project != "RPi":
    kl.notify(LOC(32010), LOC(32020), xbmcgui.NOTIFICATION_WARNING)
    sys.exit(0)

if not os.path.exists(user_config_path):
    xbmcvfs.mkdirs(user_config_path)
    xbmcvfs.copy(os.path.join(addon_config_path, user_config_1), os.path.join(user_config_path, user_config_1))
    xbmcvfs.copy(os.path.join(addon_config_path, user_config_2), os.path.join(user_config_path, user_config_2))

if not os.path.exists(system_config_backup):
    subprocess.call(['mount', '-o', 'remount,rw', '/flash'], shell=False)
    xbmcvfs.copy(system_config_path, system_config_backup)
    subprocess.call(['mount', '-o', 'remount,ro', '/flash'], shell=False)

# GPIO-Port, an dem die Taste gegen GND angeschlossen ist
# GPIO 5, Pin 29 (GND ist daneben auf Pin 30)

PORT = 5

# Schwelle für Shutdown (in Sekunden), wird die Taste kürzer gedrückt, erfolgt ein Reboot

SHUTDOWN = 3
DEBOUNCE = 0.05

duration = 0


# Interrupt-Routine für den Button

def buttonISR(pin):

    global duration
    if not (GPIO.input(pin)):

        # Button gedrückt
        if duration == 0: duration = time.time()
    else:

        # Button losgelassen
        if duration > 0:
            elapsed = (time.time() - duration)
            duration = 0

            if elapsed > SHUTDOWN:

                kl.log('initiate shutdown')
                kl.notify(LOC(32010), LOC(32023))
                xbmc.sleep(5000)
                xbmc.executebuiltin('Powerdown')

            elif elapsed > DEBOUNCE:

                kl.log('initiate configuration change and reboot')

                curr = addon.getSetting('current')

                if curr == user_config_1:
                    src = user_config_2
                else:
                    src = user_config_1

                subprocess.call(['mount', '-o', 'remount,rw', '/flash'], shell=False)
                changed = xbmcvfs.copy(os.path.join(user_config_path, src), system_config_path)
                addon.setSetting('current', src)
                subprocess.call(['mount', '-o', 'remount,ro', '/flash'], shell=False)

                if changed:
                    kl.notify(LOC(32010), LOC(32022))
                    xbmc.sleep(5000)
                    xbmc.executebuiltin('Reboot')
                else:
                    kl.notify(LOC(32010), LOC(32021), xbmcgui.NOTIFICATION_ERROR)
            else:
                pass


if __name__ == '__main__':

    kl.log('Service started', level=xbmc.LOGINFO)

    # GPIO initialisieren, BMC-Pinnummer, Pullup-Widerstand

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PORT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Interrupt für den Button einschalten

    GPIO.add_event_detect(PORT, GPIO.BOTH, callback=buttonISR)

    while not monitor.abortRequested():
        if monitor.waitForAbort(600):
            break
        kl.log('Service still alive')

    kl.log('Abort requested, service finished', level=xbmc.LOGINFO)

    GPIO.setmode(GPIO.BCM)
    GPIO.remove_event_detect(PORT)
    GPIO.cleanup(PORT)
