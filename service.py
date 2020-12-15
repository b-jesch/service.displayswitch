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

flash_path = '/flash/config.txt'
flash_backup = '/flash/config.txt.origin'

config_templates = os.path.join(addon_path, 'resources', 'configs')
user_config_path = os.path.join(addon_profile, 'configs')

default_config_1 = 'config.DSI'
default_config_2 = 'config.HDMI'

if addon.getSetting('default') == default_config_1:
    user_config_1 = os.path.join(user_config_path, default_config_1)
else:
    user_config_1 = addon.getSetting('default')

if addon.getSetting('alternate') == default_config_2:
    user_config_2 = os.path.join(user_config_path, default_config_2)
else:
    user_config_2 = addon.getSetting('alternate')

osr = OsRelease()
kl = KodiLib()
monitor = xbmc.Monitor()

kl.log('Device is {} on {} ({})'.format(osr.device, osr.osid, osr.project), xbmc.LOGINFO)
if osr.project != "RPi":
    kl.notify(LOC(32010), LOC(32020), xbmcgui.NOTIFICATION_WARNING)
    sys.exit(0)

# Prerequisites and backups

if not os.path.exists(flash_backup):
    subprocess.call(['mount', '-o', 'remount,rw', '/flash'], shell=False)
    xbmcvfs.copy(flash_path, flash_backup)
    subprocess.call(['mount', '-o', 'remount,ro', '/flash'], shell=False)

if not os.path.exists(user_config_path):
    xbmcvfs.mkdirs(user_config_path)
    xbmcvfs.copy(os.path.join(config_templates, default_config_1), os.path.join(user_config_path, default_config_1))
    xbmcvfs.copy(os.path.join(config_templates, default_config_2), os.path.join(user_config_path, default_config_2))

# GPIO-Port, an dem die Taste gegen GND angeschlossen ist
# GPIO 5, Pin 29 (GND ist daneben auf Pin 30)

PORT = 5

# Schwelle für Shutdown (in Sekunden), wird die Taste kürzer gedrückt, erfolgt ein Reboot

SHUTDOWN = 3
DEBOUNCE = 0.05

duration = 0


def copy_config(src):
    try:
        subprocess.check_call(['mount', '-o', 'remount,rw', '/flash'], shell=False)
    except subprocess.CalledProcessError as e:
        kl.log('Failed to remount (rw) flash: {}'.format(e.returncode))
        return False
    kl.log('Copy {} to flash'.format(src))
    copied = xbmcvfs.copy(src, flash_path)
    try:
        subprocess.check_call(['mount', '-o', 'remount,ro', '/flash'], shell=False)
    except subprocess.CalledProcessError as e:
        kl.log('Failed to remount (ro) flash: {}'.format(e.returncode))
    return copied

def execute_command(command):

    if command == 'poweroff':
        kl.log('initiate shutdown')
        if addon.getSetting('use_default_boot').lower() == "true":
            boot_config = [user_config_1, user_config_2]
            idx = int(addon.getSetting('start_config'))
            src = boot_config[idx]

            if copy_config(src):
                kl.log('Default boot configuration copied to flash')
                if idx == 0:
                    ps = default_config_1 if addon.getSetting('default') == default_config_1 else user_config_1
                else:
                    ps = default_config_2 if addon.getSetting('default') == default_config_2 else user_config_2
                addon.setSetting('current', ps)
            else:
                kl.log('Couldn\'t copy default boot configuration to flash', xbmc.LOGERROR)

        kl.notify(LOC(32010), LOC(32023))
        xbmc.sleep(5000)
        xbmc.executebuiltin('Powerdown')

    elif command == 'switch':
        kl.log('initiate configuration change and reboot')
        curr = addon.getSetting('current')

        if curr == default_config_1:
            src = user_config_2
            ps = default_config_2 if addon.getSetting('alternate') == default_config_2 else user_config_2
        elif curr == default_config_2:
            src = user_config_1
            ps = default_config_1 if addon.getSetting('default') == default_config_1 else user_config_1
        elif curr == user_config_1:
            src = user_config_2
            ps = default_config_2 if addon.getSetting('alternate') == default_config_2 else user_config_2
        else:
            src = user_config_1
            ps = default_config_1 if addon.getSetting('default') == default_config_1 else user_config_1

        if copy_config(src):
            addon.setSetting('current', ps)
            kl.notify(LOC(32010), LOC(32022))
            xbmc.sleep(5000)
            xbmc.executebuiltin('Reboot')
        else:
            kl.notify(LOC(32010), LOC(32021), xbmcgui.NOTIFICATION_ERROR)
    else:
        kl.log('unknown Command: {}'.format(command), xbmc.LOGERROR)


# Interrupt function for PORT (GPIO)

def buttonISR(pin):

    global duration
    if not (GPIO.input(pin)):

        # Button pressed
        if duration == 0: duration = time.time()
    else:

        # Button released
        if duration > 0:
            elapsed = (time.time() - duration)
            duration = 0

            if elapsed > SHUTDOWN:
                execute_command('poweroff')

            elif elapsed > DEBOUNCE:
                execute_command('switch')
            else:
                pass


if __name__ == '__main__':

    kl.log('Service started', level=xbmc.LOGINFO)

    try:

        if sys.argv[1]:
            execute_command(sys.argv[1])
            sys.exit(0)

    except IndexError:

        # GPIO Init, BMC-Pin, Pullup-Resistor

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PORT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(PORT, GPIO.BOTH, callback=buttonISR)

        # Main service loop

        while not monitor.abortRequested():
            if monitor.waitForAbort(600):
                break
            kl.log('Service still alive')

        kl.log('Abort requested, service finished', level=xbmc.LOGINFO)

        GPIO.setmode(GPIO.BCM)
        GPIO.remove_event_detect(PORT)
        GPIO.cleanup(PORT)
