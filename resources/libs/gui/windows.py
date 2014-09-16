'''
Copyright 2011 Mikel Azkolain

This file is part of Spotimc.

Spotimc is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Spotimc is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Spotimc.  If not, see <http://www.gnu.org/licenses/>.
'''


import xbmc
import xbmcgui
import views
import views.newstuff
import views.album
import views.search
import views.nowplaying
import views.playlists.list
import views.playlists.detail
import views.more
import weakref

from views.playlists.list import PlaylistView

from core.settings import StartupScreen
from utils import environment


class MainWindow(xbmcgui.WindowXML):
    __view_manager = None
    __playlist_manager = None
    __vars = None
    __active_tab = None
    __xbmcSpotify = None

    # Button id constants
    ID_NOW_PLAYING_BUTTON = 201
    ID_NEW_STUFF_BUTTON = 212
    ID_PLAYLISTS_BUTTON = 213
    ID_SEARCH_BUTTON = 214
    ID_MORE_BUTTON = 215
    ID_EXIT_BUTTON = 216

    # Loading gif id
    loading_image = 50

    __double_clicked = False

    def __init__(self, file, script_path, skin_dir):

        self.__view_manager = views.ViewManager(self)

    def initialize(self, xbmcSpotify, vars):
        '''Initialize the object with reference to xbmcSpotify object'''
        self.__vars = vars
        self.__xbmcSpotify = xbmcSpotify

    def show_loading(self):
        c = self.getControl(MainWindow.loading_image)
        c.setVisibleCondition("True")

    def hide_loading(self):
        c = self.getControl(MainWindow.loading_image)
        c.setVisibleCondition("False")

    def __set_active_tab(self, tab=None):

        # Update the variable and the infolabel
        if tab is not None:
            self.__active_tab = tab
            self.setProperty('MainActiveTab', tab)

        # Otherwise update again the current tab
        elif self.__active_tab is not None:
            self.setProperty('MainActiveTab', self.__active_tab)

    def __init_new_stuff(self):

        self.__set_active_tab('newstuff')
        v = views.newstuff.NewStuffView(self.__xbmcSpotify)
        self.__view_manager.add_view(v)

        print '__init_new_stuff terminado'


    def __init_playlists(self):
        '''Function to start the playlist view'''
        self.__set_active_tab('playlists')

        v = views.playlists.list.PlaylistView(self.__xbmcSpotify)
        self.__view_manager.add_view(v)

    def onInit(self):

        xbmc.log(msg='windows.py onInit  ' , level=xbmc.LOGNOTICE)

        # Check if we already added views because after
        # exiting music vis this gets called again.
        if self.__view_manager.num_views() == 0:

            # Get the startup view from the settings
            startup_screen = self.__xbmcSpotify.settings.get_misc_startup_screen()

            if startup_screen == StartupScreen.Playlists:
                self._init_playlists()
            # Always display new stuff as a fallback
            else:
                self.__init_new_stuff()

        # Otherwise show the current view
#         else:
#             self.__set_active_tab()
#             self.__view_manager.show()

        #Store current window id
        manager = self.__vars.get_var('info_value_manager')
        manager.set_infolabel('spotimc_window_id',
                              xbmcgui.getCurrentWindowId())

    __count = 0
    def onAction(self, action):

        print 'ACTION ' + str(self.__count) + "   " + str(action.getId())
        self.__count +=  1

        if (action.getId() == 103):
            self.__double_clicked = True
        # We catch here mouse action to diferenciate between click and double click
        # IDs lower than 1000 belong to the common layout
#         if control_id < 1000:
#             self._process_layout_click(control_id)
#
#         # Hand the rest to the view manager
#         else:
#             self.__view_manager.click(control_id)

#         xbmc.log(msg='windows.py onAction ' + str(type(action)) + "  " + str(action.getId()) , level=xbmc.LOGNOTICE)

        # TODO: Remove magic values #10 is for esc
#         if action.getId() in [9, 10, 92]:
#             if self.__view_manager.position() > 0:
#                 self.__view_manager.previous()
#             #elif environment.has_background_support():
#                 #Flush caches before minimizing
#             #    self.__session.flush_caches()
#             #    xbmc.executebuiltin("XBMC.ActivateWindow(0)")
#
#         # Noop action
#         # TODO: Remove magic values
#         elif action.getId() in [0, 999]:
#             self.__view_manager.show()
#
#         else:
#             self.__view_manager.action(action.getId())

    def _process_layout_click(self, control_id):

        xbmc.log(msg='windows.py _process_layout_click ' + str(control_id) , level=xbmc.LOGNOTICE)

        if control_id == MainWindow.ID_NOW_PLAYING_BUTTON:
            self.__set_active_tab('nowplaying')
#             v = views.nowplaying.NowPlayingView()
#             self.__view_manager.clear_views()
#             self.__view_manager.add_view(v)

        elif control_id == MainWindow.ID_PLAYLISTS_BUTTON:
            self.__view_manager.clear_views()
            self.__init_playlists()

        elif control_id == MainWindow.ID_NEW_STUFF_BUTTON:
            self.__view_manager.clear_views()
            self.__init_new_stuff()

#         elif control_id == MainWindow.ID_SEARCH_BUTTON:
#             term = views.search.ask_search_term()
#             if term:
#                 self.__set_active_tab('search')
#                 v = views.search.SearchTracksView(self.__session, term)
#                 self.__view_manager.clear_views()
#                 self.__view_manager.add_view(v)
#
#         elif control_id == MainWindow.ID_MORE_BUTTON:
#             self.__set_active_tab('more')
#             v = views.more.MoreView()
#             self.__view_manager.clear_views()
#             self.__view_manager.add_view(v)

        elif control_id == MainWindow.ID_EXIT_BUTTON:
            self.__vars.set_var('exit_requested', True)
            self.close()

    def onClick(self, control_id):
        print 'CLICK ' + str(self.__count) + "   " + str(control_id)
        self.__count +=  1

        if self.__double_clicked:
            print 'Asi lo vamos a hacer'
            self.__double_clicked = False
#         xbmc.log(msg='windows.py onClick ' + str(control_id) , level=xbmc.LOGNOTICE)
#

#         # IDs lower than 1000 belong to the common layout
#         if control_id < 1000:
#             self._process_layout_click(control_id)
#
#         # Hand the rest to the view manager
#         else:
#             self.__view_manager.click(control_id)

    def onDoubleClick(self, control_id):
        xbmc.log(msg='windows.py onDoubleClick ' + str(control_id) , level=xbmc.LOGNOTICE)

    def onFocus(self, controlID):
        pass
