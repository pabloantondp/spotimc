'''
Copyright 2011 Mikel Azkolain
Copyright 2014 Pablo Anton

This file is part of XbmcSpotify (Forked from spotimc).

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

import xbmcgui

from gui.views import BaseListContainerView
from gui.views import album
from utils.loaders import load_albumbrowse

from spotify import ImageSize

class NewStuffView(BaseListContainerView):
    ID_CONTAINER = 1200
    ID_LIST = 1201
    ID_CONTEXT_MENU = 5200
    ID_CONTEXT_PLAY_ALBUM = 5202
    ID_CONTEXT_SET_CURRENT = 5203

    __top_list = None
    __initialized = None
    __xbmcSpotify = None
    __list = None
    def __init__(self, xbmcSpotify):

        self.__top_list = xbmcSpotify.get_top_list()
        self.__xbmcSpotify = xbmcSpotify
        self.__list = {}

        if self.__top_list != None:
            self.__initialized = True

    def _get_selected_album(self, view_manager):

        item = self.get_list(view_manager).getSelectedItem()

        link = item.getProperty('spotify_link')
        return self.__list[link]

    def _show_album(self, view_manager):

        album_obj = self._get_selected_album(view_manager)
        view_manager.add_view(album.AlbumTracksView(self.__xbmcSpotify, album_obj))

    def _start_album_playback(self, view_manager):
        session = view_manager.get_var('session')
        album_obj = self._get_selected_album(view_manager)
        albumbrowse = load_albumbrowse(session, album_obj)

        if albumbrowse is not None:
            playlist_manager = view_manager.get_var('playlist_manager')
            playlist_manager.play(albumbrowse.tracks(), session)

    def _set_current_album(self, view_manager):
        session = view_manager.get_var('session')
        album_obj = self._get_selected_album(view_manager)
        albumbrowse = load_albumbrowse(session, album_obj)

        if albumbrowse is not None:
            playlist_manager = view_manager.get_var('playlist_manager')
            playlist_manager.set_tracks(albumbrowse.tracks(), session)

    def click(self, view_manager, control_id):
        # Silently ignore events when not intialized
        if not self.__initialized:
            return

        # If the list was clicked...
        if control_id == NewStuffView.ID_LIST:
            self._show_album(view_manager)

        elif control_id == NewStuffView.ID_CONTEXT_PLAY_ALBUM:
            self._start_album_playback(view_manager)
            view_manager.get_window().setFocus(self.get_container(view_manager))

        elif control_id == NewStuffView.ID_CONTEXT_SET_CURRENT:
            self._set_current_album(view_manager)
            view_manager.get_window().setFocus(self.get_container(view_manager))

    def action(self, view_manager, action_id):
        # Silently ignore events when not intialized
        if not self.__initialized:
            return

        print 'newstuff action: ' + str(action_id)

        # Run parent implementation's actions
        BaseListContainerView.action(self, view_manager, action_id)

        # Do nothing if playing, as it may result counterproductive
        if action_id == 79 and not self.__xbmcSpotify.is_playing():
            print 'ACCIION QUE PODRIA INTERESAR'
            #self._start_album_playback(view_manager)

    def get_container(self, view_manager):
        return view_manager.get_window().getControl(NewStuffView.ID_CONTAINER)

    def get_list(self, view_manager):
        return view_manager.get_window().getControl(NewStuffView.ID_LIST)

    def get_context_menu_id(self):
        return NewStuffView.ID_CONTEXT_MENU


    def render(self, view_manager):
        '''Set the content from __top_list into the
        view_manager list_obj. Return true if everithing goes well'''
        result = False

        # If top list and initialize are well
        if self.__top_list != None and self.__initialized:

            # Take the list of object of the view and reset it
            list_obj = self.get_list(view_manager)
            list_obj.reset()

            # Reset the list of spotify albums
            self.__list = {}

#             playlist_manager = view_manager.get_var('playlist_manager')

            for album in self.__top_list.albums:

                # get the image
                image = album.cover(image_size=ImageSize.SMALL)
                if not image.is_loaded:
                    image.load(10)

                # Get url from xbmcSpotify proxy
                image_url = self.__xbmcSpotify.get_image_url(image)
                item = xbmcgui.ListItem(
                                        album.name,
                                        album.artist.name,
                                        str(image_url)
                                        )

                item.setProperty('spotify_link', str(album.link))
                self.__list[str(album.link)] = album
                list_obj.addItem(item)
            result = True

        return result
