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


import xbmcgui
from gui.views import BaseListContainerView, album
from spotify import AlbumType
from utils.settings import SkinSettings
from utils.loaders import load_albumbrowse


class ArtistAlbumsView(BaseListContainerView):
    ID_CONTAINER = 2000
    ID_LIST = 2001

    #Filtering controls
    ID_CONTEXT_MENU = 6000
    ID_CONTEXT_PLAY_ALBUM = 6002
    ID_CONTEXT_SET_CURRENT = 6003
    ID_FILTER_ALBUMS_BUTTON = 6011
    ID_FILTER_SINGLES_BUTTON = 6012
    ID_FILTER_COMPILATIONS_BUTTON = 6013
    ID_FILTER_APPEARS_IN_BUTTON = 6014
    ID_FILTER_HIDE_SIMILAR = 6016

    __artist = None
    __loader = None         # A spotify.ArtistBrowser instance
    __xbmcSpotify = None
    __settings = SkinSettings()
    __list = None

    def __init__(self, xbmcSpotify, artist):
        self._init_config()
        self.__artist = artist
        self.__xbmcSpotify = xbmcSpotify
        self.__loader = artist.browse()
        self.__loader.load()
        self.__list = {}

    def _init_config(self):
        if not self.__settings.has_bool_true('spotimc_albumbrowse_album_init'):
            self.__settings.set_bool_true('spotimc_albumbrowse_album_init')
            self.__settings.set_bool_true('spotimc_artistbrowse_albums_albums')
            self.__settings.set_bool_true('spotimc_artistbrowse_albums_singles')
            self.__settings.set_bool_true('spotimc_artistbrowse_albums_compilations')
            self.__settings.set_bool_true('spotimc_artistbrowse_albums_appears_in')
            self.__settings.set_bool_true('spotimc_artistbrowse_albums_hide_similar')

    def _get_album_filter(self):
        filter_types = []

        if self.__settings.has_bool_true('spotimc_artistbrowse_albums_albums'):
            filter_types.append(AlbumType.ALBUM)

        if self.__settings.has_bool_true('spotimc_artistbrowse_albums_singles'):
            filter_types.append(AlbumType.SINGLE)

        if self.__settings.has_bool_true('spotimc_artistbrowse_albums_compilations'):
            filter_types.append(AlbumType.COMPILATION)

        if self.__settings.has_bool_true('spotimc_artistbrowse_albums_appears_in'):
            filter_types.append(AlbumType.UNKNOWN)

        return filter_types

    def _get_similar_filter(self):
        return self.__settings.has_bool_true('spotimc_artistbrowse_albums_hide_similar')

    def _get_selected_album(self, view_manager):
        '''Get the selected spotify.Album from the view_manager'''
        item = self.get_list(view_manager).getSelectedItem()

        link = item.getProperty('spotify_link')

        return self.__list[link]

    def _show_album(self, view_manager):
        '''Show album details, tracks, etc...'''

        #Get the selected album
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
        filter_controls = [
            ArtistAlbumsView.ID_FILTER_ALBUMS_BUTTON,
            ArtistAlbumsView.ID_FILTER_SINGLES_BUTTON,
            ArtistAlbumsView.ID_FILTER_COMPILATIONS_BUTTON,
            ArtistAlbumsView.ID_FILTER_APPEARS_IN_BUTTON,
            ArtistAlbumsView.ID_FILTER_HIDE_SIMILAR
        ]

        #If the list was clicked...
        if control_id == ArtistAlbumsView.ID_LIST:
            self._show_album(view_manager)

        elif control_id == ArtistAlbumsView.ID_CONTEXT_PLAY_ALBUM:
            self._start_album_playback(view_manager)
            view_manager.get_window().setFocus(self.get_container(view_manager))

        elif control_id == ArtistAlbumsView.ID_CONTEXT_SET_CURRENT:
            self._set_current_album(view_manager)
            view_manager.get_window().setFocus(self.get_container(view_manager))

        elif control_id in filter_controls:
            print 'Albums.py Filter selected '
            view_manager.show(False)

    def action(self, view_manager, action_id):
        #Run parent implementation's actions
        BaseListContainerView.action(self, view_manager, action_id)

        #Do nothing if playing, as it may result counterproductive
        if action_id == 79 and not self.__xbmcSpotify.is_playing():
            print 'ACCIION QUE PODRIA INTERESAR'
            #self._start_album_playback(view_manager)

    def get_container(self, view_manager):
        return view_manager.get_window().getControl(ArtistAlbumsView.ID_CONTAINER)

    def get_list(self, view_manager):
        return view_manager.get_window().getControl(ArtistAlbumsView.ID_LIST)

    def get_context_menu_id(self):
        return ArtistAlbumsView.ID_CONTEXT_MENU

    def render(self, view_manager):

        if self.__loader.is_loaded:

            l = self.get_list(view_manager)
            l.reset()

            #Set the artist name
            window = view_manager.get_window()
            window.setProperty('artistbrowse_artist_name', self.__artist.name)

            #Get the album types to be shown
            filter_types = self._get_album_filter()

            # Loop over all the loaded albums
            for album in self.__loader.albums:

                album_type = album.type
                is_in_filter = album_type in filter_types

#                 is_available = self.__loader.get_album_available_tracks(index) > 0
#
#                 is_similar = self._get_similar_filter() and \
#                     index not in non_similar_list

                #Discard vailable/non-filtered/similar albums
                if album.is_available and is_in_filter: # and not is_similar:

                    image_url = self.__xbmcSpotify.get_image_url(album.cover())

                    item = xbmcgui.ListItem(
                        album.name, str(album.year), image_url
                    )

                    item.setProperty('spotify_link', str(album.link))

                    self.__list[str(album.link)] = album
                    l.addItem(item)

            return True
