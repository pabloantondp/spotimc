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
import detail
from gui.views import BaseListContainerView, iif
#from taskutils.decorators import run_in_thread

from spotify import Timeout

class PlaylistView(BaseListContainerView):

    # Constant identifiers for UI
    ID_CONTAINER = 1700
    ID_LIST = 1701

    ID_CONTEXT_MENU = 5700
    ID_CONTEXT_PLAY_PLAYLIST = 5702
    ID_CONTEXT_SET_CURRENT = 5703

    __starred_playlist = None
    __inbox_playlist = None
    __container_playlist = None
    __playqueue = None
    __xbmcSpotify = None

    __initialized = None

    def __init__(self, xbmcSpotify):

        self._initialize(xbmcSpotify)

    def _initialize(self, xbmcSpotify):

        #Add the starred playlist
        self.__xbmcSpotify = xbmcSpotify
        self.__starred_playlist = xbmcSpotify.get_starred()
        self.__inbox_playlist = xbmcSpotify.get_inbox()
        self.__container_playlist = xbmcSpotify.get_playlist_container()
#         self.__playqueue = self.__xbmcSpotify.get_playlist_queue()
        self.__initialized = True


    def _get_playlist(self, playlist_id):
        if playlist_id == 'starred':
            return self.__starred_playlist

        elif playlist_id == 'inbox':
            return self.__inbox_playlist

        else:
            return self.__container_playlist[int(playlist_id)]

    def _get_selected_playlist(self, view_manager):
        item = self.get_list(view_manager).getSelectedItem()
        return item.getProperty('PlaylistId')

    def _show_selected_playlist(self, view_manager):
        ''' Update the view_manager with the playlist items selected'''
#
#         pm = view_manager.get_var('playlist_manager')
#         session = view_manager.get_var('session')
        playlist_id = self._get_selected_playlist(view_manager)

        print 'list.py _show_selected_playlist get playlist  ' + str(playlist_id)

        playlist = self._get_playlist(playlist_id)

        print 'list.py _show_selected_playlist get playlist ' + str(playlist)
        #Special treatment for starred & inbox
        if playlist_id in ['starred', 'inbox']:
            pass
#             view_obj = detail.SpecialPlaylistDetailView(
#                 session, playlist.get_playlist(), pm,
#                 playlist.get_name(), playlist.get_thumbnails()
#             )

        else:
            # Treat as a normal Playlist
            view_obj = detail.PlaylistDetailView(self.__xbmcSpotify, playlist)

        view_manager.add_view(view_obj)

    def _start_playlist_playback(self, view_manager):
        playlist_id = self._get_selected_playlist(view_manager)
        track_list = self._get_playlist(playlist_id).get_tracks()
        session = view_manager.get_var('session')
        playlist_manager = view_manager.get_var('playlist_manager')
        playlist_manager.play(track_list, session)

    def _set_current_playlist(self, view_manager):
        playlist_id = self._get_selected_playlist(view_manager)
        track_list = self._get_playlist(playlist_id).get_tracks()
        playlist_manager = view_manager.get_var('playlist_manager')
        session = view_manager.get_var('session')
        playlist_manager.set_tracks(track_list, session)

    def click(self, view_manager, control_id):

        print "list.py click() :" + str(control_id)

        #Silently ignore events when not intialized
        if not self.__initialized:
            return

        if control_id == PlaylistView.ID_LIST:
            self._show_selected_playlist(view_manager)

        elif control_id == PlaylistView.ID_CONTEXT_PLAY_PLAYLIST:
            self._start_playlist_playback(view_manager)
            view_manager.get_window().setFocus(
                self.get_container(view_manager))

        elif control_id == PlaylistView.ID_CONTEXT_SET_CURRENT:
            self._set_current_playlist(view_manager)
            view_manager.get_window().setFocus(
                self.get_container(view_manager))

    def action(self, view_manager, action_id):
        #Silently ignore events when not intialized
        if not self.__initialized:
            return

        #Run parent implementation's actions
        BaseListContainerView.action(self, view_manager, action_id)

        #Do nothing if playing, as it may result counterproductive
        if action_id == 79 and not self.__xbmcSpotify.is_playing():
            print 'ACCIION QUE PODRIA INTERESAR'
            #self._start_playlist_playback(view_manager)

    def get_container(self, view_manager):
        return view_manager.get_window().getControl(PlaylistView.ID_CONTAINER)

    def get_list(self, view_manager):
        return view_manager.get_window().getControl(PlaylistView.ID_LIST)

    def get_context_menu_id(self):
        return PlaylistView.ID_CONTEXT_MENU

    def _add_playlist(self, list, key, playlist, show_owner):

        global image_load_event


        item = xbmcgui.ListItem()
        item.setProperty("PlaylistId", str(key))

        # Spetial treatment for starred and inbox names
        if key in ['starred', 'inbox']:
            item.setProperty("PlaylistName", str(key))

        else:
            item.setProperty("PlaylistName", playlist.name.encode('ascii','ignore'))

        item.setProperty("PlaylistNumTracks", str(len(playlist.tracks)))

        item.setProperty("PlaylistShowOwner", iif(show_owner, "true", "false"))

        if show_owner:
            owner_name = playlist.owner.canonical_name
            item.setProperty("PlaylistOwner", str(owner_name))

        #Collaborative status
        is_collaborative = playlist.collaborative
        item.setProperty("PlaylistCollaborative", iif(is_collaborative,
                                                      "true", "false"))

        #Thumbnails
        #image = playlist.image(self.__xbmcSpotify.getCallbacks().load_image_callback)
        image = playlist.image()

        if (image is not None) and not image.is_loaded:
            image.load(10)

        # Get url from xbmcSpotify proxy
        image_url = self.__xbmcSpotify.get_image_url(image)
        item.setThumbnailImage(image_url)

#         if thumbnails. > 0:
#             #Set cover info
#             item.setProperty("CoverLayout",
#                              iif(len(thumbnails) < 4, "one", "four"))
#
#             #Now loop to set all the images
#             for idx, thumb_item in enumerate(thumbnails):
#                 item_num = idx + 1
#                 is_remote = thumb_item.startswith("http://")
#                 item.setProperty("CoverItem{0:d}".format(item_num), thumb_item)
#                 item.setProperty("CoverItem{0:d}IsRemote".format(item_num),
#                                  iif(is_remote, "true", "false"))

        list.addItem(item)


    def render(self, view_manager):

        if not self.__initialized:
            return False

        #Clear the list
        list = self.get_list(view_manager)
        list.reset()

        #Get the logged in user
        container_user = self.__container_playlist.owner
        container_username = None

        if container_user is not None:
            container_username = container_user.canonical_name

        #Add the starred and inbox playlists
        self._add_playlist(list, 'starred', self.__starred_playlist, False)
        self._add_playlist(list, 'inbox', self.__inbox_playlist, False)

        index = 0
        #And iterate over the rest of the playlists
        for playlist in self.__container_playlist:

            try:
                if not playlist.is_loaded:
                    playlist.load(10)

                playlist_username = playlist.owner.canonical_name
                show_owner = playlist_username != container_username
                self._add_playlist(list, str(index), playlist, show_owner)

                index += 1
            except (Timeout) as ex:
                print "Exception for the playlist: " + playlist.name

        return True
