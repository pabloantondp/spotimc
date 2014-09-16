'''
Copyright 2011 Mikel Azkolain
Copyright 2014 Pablo Anton

This file is part of XbmcSpotify (forked from spotimc).

XbmcSpotify is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

XbmcSpotify is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with XbmcSpotify.  If not, see <http://www.gnu.org/licenses/>.
'''
# General use
import os
import traceback # For exception control
from threading import Event
import gc

# XBMC specifics imports
import xbmcgui
import xbmc

# Some pyspotify staff
from spotify import ConnectionState

#And perform the rest of the import statements
from utils.skin.fonts import FontManager
from utils.skin.includes import IncludeManager



from core.xbmcSpotify import XbmcSpotify
from core.settings import VarManager
from core.settings import InfoValueManager
from gui import windows
from gui import dialogs
from utils import check_addon_version
from utils import check_dirs
from utils.environment import get_audio_buffer_size
from gui import show_legal_warning

from proxy.httpproxy import ProxyRunner
from proxy.sink import BufferManager

# class SpotimcCallbacks():
#     __mainloop = None
#     __audio_buffer = None
#     __logout_event = None
#     __app = None
#     __logger = None
#     __log_regex = None
#
#     def __init__(self, mainloop, audio_buffer, app):
#         self.__mainloop = mainloop
#         self.__audio_buffer = audio_buffer
#         self.__app = app
#         self.__logger = ()
#         self.__log_regex = re.compile('[0-9]{2}:[0-9]{2}:[0-9]{2}'
#                                       '\.[0-9]{3}\s(W|I|E)\s')
#
#     def logged_in(self, session, error_num):
#         #Log this event
#         self.__logger.debug('logged in: {0:d}'.format(error_num))
#
#         #Store last error code
#         self.__app.set_var('login_last_error', error_num)
#
#         #Take action if error status is not ok
#         if error_num != ErrorType.Ok:
#
#             #Close the main window if it's running
#             if self.__app.has_var('main_window'):
#                 self.__app.get_var('main_window').close()
#
#             #Otherwise, set the connstate event
#             else:
#                 self.__app.get_var('connstate_event').set()
#
#     def logged_out(self, session):
#         self.__logger.debug('logged out')
#         self.__app.get_var('logout_event').set()
#
#     def connection_error(self, session, error):
#         self.__logger.error('connection error: {0:d}'.format(error))
#
#     def message_to_user(self, session, data):
#         self.__logger.info('message to user: {0}'.format(data))
#
#     def _get_log_message_level(self, message):
#         matches = self.__log_regex.match(message)
#         if matches:
#             return matches.group(1)
#
#     def log_message(self, session, data):
#         message_level = self._get_log_message_level(data)
#         if message_level == 'I':
#             self.__logger.info(data)
#         elif message_level == 'W':
#             self.__logger.warning(data)
#         else:
#             self.__logger.error(data)
#
#     def streaming_error(self, session, error):
#         self.__logger.info('streaming error: {0:d}'.format(error))
#
#     @run_in_thread
#     def play_token_lost(self, session):
#
#         #Cancel the current buffer
#         self.__audio_buffer.stop()
#
#         if self.__app.has_var('playlist_manager'):
#             self.__app.get_var('playlist_manager').stop(False)
#
#         dlg = xbmcgui.Dialog()
#         dlg.ok('Playback stopped', 'This account is in use on another device.')
#
#     def end_of_track(self, session):
#         self.__audio_buffer.set_track_ended()
#
#     def notify_main_thread(self, session):
#         self.__mainloop.notify()
#
#     def music_delivery(self, session, data, num_samples, sample_type,
#                        sample_rate, num_channels):
#         return self.__audio_buffer.music_delivery(
#             data, num_samples, sample_type, sample_rate, num_channels)
#
#     def connectionstate_changed(self, session):
#
#         #Set the apropiate event flag, if available
#         self.__app.get_var('connstate_event').set()
#
#
# class MainLoopRunner(threading.Thread):
#     __mainloop = None
#     __session = None
#     __proxy = None
#
#     def __init__(self, mainloop, session):
#         threading.Thread.__init__(self)
#         self.__mainloop = mainloop
#         self.__session = weakref.proxy(session)
#
#     def run(self):
#         self.__mainloop.loop(self.__session)
#
#     def stop(self):
#         self.__mainloop.quit()
#         self.join(10)
#
#


#


#
# def set_settings(settings_obj, session):
#     pass
    #If cache is enabled set the following one
#     if settings_obj.get_cache_status():
#         if settings_obj.get_cache_management() == CacheManagement.Manual:
#             cache_size_mb = settings_obj.get_cache_size() * 1024
#             session.set_cache_size(cache_size_mb)
#
#     #Bitrate config
#     br_map = {
#         StreamQuality.Low: Bitrate.Rate96k,
#         StreamQuality.Medium: Bitrate.Rate160k,
#         StreamQuality.High: Bitrate.Rate320k,
#     }
#     session.preferred_bitrate(br_map[settings_obj.get_audio_quality()])
#
#     #And volume normalization
#     session.set_volume_normalization(settings_obj.get_audio_normalize())
#
#     #And volume normalization
#     session.set_volume_normalization(settings_obj.get_audio_normalize())

def do_login(xbmcSpotify, skin_dir, vars):
    '''Method to perform the login process. It will show a login
    template if necessary. It will return True if the login is possible or
    false in other case'''

    #Get the last error if we have one
    if vars.has_var('login_last_error'):
        prev_error = vars.get_var('login_last_error')
    else:
        prev_error = 0

    #If no previous errors and we have a remembered user
    if prev_error == 0 and xbmcSpotify.remembered_user() is not None:
        status = xbmcSpotify.relogin()

        # If the login is not possible, clean the cache of the user
        if status == ConnectionState.LOGGED_OUT:
            xbmcSpotify.forget_user()

    #Otherwise let's do a normal login process
    else:
        loginwin = dialogs.LoginWindow("login-window.xml",
                                   xbmcSpotify.settings.__addon_path__,
                                   skin_dir
                                   )
        loginwin.initialize(xbmcSpotify, vars)
        loginwin.doModal()
        status = not loginwin.is_cancelled()

    return status

#
# def login_get_last_error(app):
#     if app.has_var('login_last_error'):
#         return app.get_var('login_last_error')
#     else:
#         return 0

#
# def get_preloader_callback(session, playlist_manager, buffer):
#     session = weakref.proxy(session)
#
#     def preloader():
#         next_track = playlist_manager.get_next_item(session)
#         if next_track is not None:
#             ta = next_track.get_availability(session)
#             if ta == _track.TrackAvailability.Available:
#                 buffer.open(session, next_track)
#
#     return preloader


def gui_main(xbmcSpotify):

    #Initialize app var storage
    vars = VarManager()

    logout_event = Event()
    connstate_event = Event()

    info_value_manager = InfoValueManager()
    #app.set_var('login_last_error', ErrorType.Ok)
    vars.set_var('connstate_event', connstate_event)
    vars.set_var('exit_requested', False)
    vars.set_var('info_value_manager', info_value_manager)

    #Check needed directories first
    data_dir, cache_dir, settings_dir = check_dirs(xbmcSpotify)

    #Show legal warning
    show_legal_warning(xbmcSpotify.settings)

    #Start checking the version
    check_addon_version(xbmcSpotify)

    #Don't set cache folder if it's disabled
    if not xbmcSpotify.settings.get_cache_status():
        cache_dir = ''

#     callbacks = SpotimcCallbacks(ml, buf, app)

    #Set the exit flag if login was cancelled
    if not do_login(xbmcSpotify, "DefaultSkin", vars):
        vars.set_var('exit_requested', True)
        raise Exception('Impossible to perform the login ')

    else:

        # Create the buffer object cont httpproxy read and sink write
        buf = BufferManager(xbmcSpotify)

        # Start the http proxy
        proxy_runner = ProxyRunner(buf, host='127.0.0.1',allow_ranges=True)
        proxy_runner.start()

        xbmcSpotify.set_proxy(proxy_runner)

    #Stay on the application until told to do so
    while not vars.get_var('exit_requested'):
        mainwin = windows.MainWindow("main-window.xml",
                                         xbmcSpotify.settings.__addon_path__,
                                         "DefaultSkin")
        mainwin.initialize(xbmcSpotify,vars)
        vars.set_var('main_window', mainwin)
        mainwin.doModal()


#            show_busy_dialog()
    # Destroy the windows
    del mainwin

    #Some uninitialization
    info_value_manager.deinit()

## Cogido de _sporify/__init__.py
# _library_cache = {}
# def unload_library(name):
#     if os.name != 'nt':
#         """
#         Don't unload the library on windows, as it may result in a crash when
#         this gets really unloaded.
#         """
#         if name in _library_cache:
#             dlclose(_library_cache[name]._handle)
#             del _library_cache[name]
###

def main(xbmcSpotify):

    #Look busy while everything gets initialized
    #show_busy_dialog()

    # Try to read use pyspotify
    try:
        #Set font & include manager vars
        fm = None
        im = None

        #Add the system specific library path
        #set_dll_paths('resources/dlls')
        #Install custom fonts
        fm = FontManager()

        skin_dir = os.path.join(xbmcSpotify.settings.__addon_path__, "resources/skins/DefaultSkin")
        xml_path = os.path.join(skin_dir, "720p/font.xml")
        font_dir = os.path.join(skin_dir, "fonts")

        fm.install_file(xml_path, font_dir)

        #Install custom includes
        im = IncludeManager()
        include_path = os.path.join(skin_dir, "720p/includes.xml")
        im.install_file(include_path)
        xbmc.executebuiltin("XBMC.ReloadSkin()")

        #Show the busy dialog again after reload_skin(), as it may go away
        #---------------------------------------------------- show_busy_dialog()

        #Load & start the actual gui, no init code beyond this point
        gui_main(xbmcSpotify)

        xbmc.log(msg='Main bucle finish', level=xbmc.LOGNOTICE)
        xbmc.executebuiltin("XBMC.UnloadSkin()")
    except (Exception) as ex:

        dlg = xbmcgui.Dialog()
        dlg.ok(ex.__class__.__name__, str(ex))
        print 'main exception'
