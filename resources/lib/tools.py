import platform
import xbmc
import xbmcaddon
import xbmcgui

class OsRelease(object):

    def __init__(self):
        self.platform = platform.system()
        self.hostname = platform.node()
        item = {}
        if self.platform == 'Linux':

            try:
                with open('/etc/os-release', 'r') as _file:
                    for _line in _file:
                        parameter, value = _line.split('=')
                        item[parameter] = value.strip('\"\n')
            except IOError as e:
                KodiLib.log(e.message, xbmc.LOGERROR)

        self.osname = item.get('NAME', 'unknown')
        self.osid = item.get('ID', 'unknown')
        self.osversion = item.get('VERSION_ID', 'unknown')
        self.project = item.get('LIBREELEC_PROJECT', 'unknown')
        self.device = item.get('LIBREELEC_DEVICE', 'unknown')

class KodiLib(object):

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.addon_id = self.addon.getAddonInfo('id')
        self.addon_version = self.addon.getAddonInfo('version')

        self.osd = xbmcgui.Dialog()

    def log(self, message, level=xbmc.LOGDEBUG):
        xbmc.log('[{} - {}]: {}'.format(self.addon_id, self.addon_version, message.encode('utf-8')), level)

    def notify(self, header, message, level=xbmcgui.NOTIFICATION_INFO):
        self.osd.notification(header, message.encode('utf-8'), icon=level)

