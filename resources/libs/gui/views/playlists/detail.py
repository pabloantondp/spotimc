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
from gui.views import BaseListContainerView, iif
from gui.views.album import AlbumTracksView
from gui.views.artists import open_artistbrowse_albums

from spotify import ErrorType
from spotify import TrackAvailability
from spotify import Timeout

import threading
from utils.tasks.decorators import run_async


class PlaylistDetailView(BaseListContainerView):
    ID_CONTAINER = 1800
    ID_LIST = 1801

    ID_BROWSER_ARTIST = 5811
    ID_BROWSE_ALBUM = 5812

    ID_CONTEXT_MENU = 5800
    ID_CONTEXT_TOGGLE_STAR = 5813

    __playlist = None
    __xbmcSpotify = None

    def __init__(self, xbmcSpotify, playlist):

        try:
            if not playlist.is_loaded:
                playlist.load(10)

            self.__playlist = playlist
            self.__xbmcSpotify = xbmcSpotify

        except (Timeout) as ex:
            print 'No se ha podido leer playlist '

    def _browse_artist(self, view_manager):
        item = self.get_list(view_manager).getSelectedItem()
        track_obj = self.__xbmcSpotify.get_track(item)
        open_artistbrowse_albums(view_manager, self.__xbmcSpotify, track_obj.artists)

    def _browse_album(self, view_manager):
        item = self.get_list(view_manager).getSelectedItem()
        album = self.__xbmcSpotify.get_album(item)
        v = AlbumTracksView(self.__xbmcSpotify, album)
        view_manager.add_view(v)

    def _play_selected_track(self, view_manager):

        # Get the ItemList object
        item = self.get_list(view_manager).getSelectedItem()

        # Get the list index property to get the track object
#         pos = int(item.getProperty('ListIndex'))

        self.__xbmcSpotify.add_play(item)

    def _queue_selected_track(self, view_manager):
        print 'details.py _queue_selected_track'

    def doubleClick(self, view_manager, control_id):

        print 'Bien estamos en el doubleclick de datail.py'

        if control_id == PlaylistDetailView.ID_LIST:
            # Playing a track of the showed playlist
            self._play_selected_track(view_manager)

        else:
            # Others commands are treated as one click
            self.click(view_manager, control_id)

    @run_async
    def click(self, view_manager, control_id):

#          try :
#             if self.__clicked:
#                 self.__timer.cancel()
#                 print 'Double click stop timer and call double click'
#                 self.__timer.cancel()
#                 self.__view_list[self.__position].doubleClick(self, control_id)
#                 self.__clicked = False
#             else:
#                 self.__clicked = True
#                 view = self.__view_list[self.__position]
#                 self.__timer = Timer(ViewManager.DOUBLE_CLICK_SPEED,
#                                      view.click,
#                                      [self, control_id])
#                 self.__timer.start()
#                 print 'Before the join ....'
#                 self.__timer.join()
#                 self.__clicked = False
#                 print 'After the join ....'
#
#         except:
#             traceback.print_exc()
#             self.__clicked = False


        if control_id == PlaylistDetailView.ID_LIST:
            # Playing a track of the showed playlist
            self._queue_selected_track(view_manager)

        elif control_id == PlaylistDetailView.ID_BROWSER_ARTIST:
            # Browser the specific artist
            self._browse_artist(view_manager)

        elif control_id == PlaylistDetailView.ID_BROWSE_ALBUM:

            # Browse the specific album of the artist
            self._browse_album(view_manager)

        elif control_id == PlaylistDetailView.ID_CONTEXT_TOGGLE_STAR:
            item = self.get_list(view_manager).getSelectedItem()
            pos = int(item.getProperty("ListIndex"))

            if pos is not None:
                session = view_manager.get_var('session')
                current_track = self.__loader.get_track(pos)

                if item.getProperty('IsStarred') == 'true':
                    item.setProperty('IsStarred', 'false')
                    track.set_starred(session, [current_track], False)
                else:
                    item.setProperty('IsStarred', 'true')
                    track.set_starred(session, [current_track], True)

    def action(self, view_manager, action_id):
        #Run parent implementation's actions
        BaseListContainerView.action(self, view_manager, action_id)

        #Do nothing if playing, as it may result counterproductive
        if action_id == 79 and not self.__xbmcSpotify.is_playing():
            print 'ACCIION QUE PODRIA INTERESAR'
            #self._play_selected_track(view_manager)

    def get_container(self, view_manager):
        return view_manager.get_window().getControl(
            PlaylistDetailView.ID_CONTAINER)

    def get_list(self, view_manager):
        return view_manager.get_window().getControl(PlaylistDetailView.ID_LIST)

    def get_context_menu_id(self):
        return PlaylistDetailView.ID_CONTEXT_MENU

    def _get_playlist_length_str(self):
        total_duration = 0

        for track in self.__playlist.tracks():
            total_duration += track.duration() / 1000

        #Now the string ranges
        one_minute = 60
        one_hour = 3600
        one_day = 3600 * 24

        if total_duration > one_day:
            num_days = int(round(total_duration / one_day))
            if num_days == 1:
                return 'one day'
            else:
                return '%d days' % num_days

        elif total_duration > one_hour:
            num_hours = int(round(total_duration / one_hour))
            if num_hours == 1:
                return 'one hour'
            else:
                return '%d hours' % num_hours

        else:
            num_minutes = int(round(total_duration / one_minute))
            if num_minutes == 1:
                return 'one minute'
            else:
                return '%d minutes' % num_minutes

    def _set_playlist_properties(self, view_manager):

        window = view_manager.get_window()

        #Playlist name
        window.setProperty("PlaylistDetailName", self.__playlist.name)

        #Owner info
        current_username = self.__xbmcSpotify.get_user_name()
        playlist_username = self.__playlist.owner.canonical_name
        show_owner = current_username != playlist_username
        window.setProperty("PlaylistDetailShowOwner",
                           iif(show_owner, "true", "false"))
        if show_owner:
            window.setProperty("PlaylistDetailOwner", str(playlist_username))

        #Collaboratie status
        is_collaborative_str = iif(self.__playlist.collaborative,
                                   "true", "false")
        window.setProperty("PlaylistDetailCollaborative", is_collaborative_str)

        #Length data
        window.setProperty("PlaylistDetailNumTracks",
                           str(len(self.__playlist.tracks)))
#         window.setProperty("PlaylistDetailDuration",
#                            self._get_playlist_length_str())

        #Subscribers
        window.setProperty("PlaylistDetailNumSubscribers",
                           str(self.__playlist.subscribers))

    def _set_playlist_image(self, view_manager, thumbnails):

        if len(thumbnails) > 0:
            window = view_manager.get_window()

            #Set cover layout info
            cover_layout_str = iif(len(thumbnails) < 4, "one", "four")
            window.setProperty("PlaylistDetailCoverLayout", cover_layout_str)

            #Now loop to set all the images
            for idx, thumb_item in enumerate(thumbnails):
                item_num = idx + 1
                is_remote = thumb_item.startswith("http://")
                is_remote_str = iif(is_remote, "true", "false")
                prop = "PlaylistDetailCoverItem{0:d}".format(item_num)
                window.setProperty(prop, thumb_item)
                prop = "PlaylistDetailCoverItem{0:d}IsRemote".format(item_num)
                window.setProperty(prop, is_remote_str)




    def render(self, view_manager):

        if self.__playlist is not None:

            list_obj = self.get_list(view_manager)

            #Set the thumbnails
            #self._set_playlist_image(view_manager,
            #                          self.__loader.get_thumbnails())

            #And the properties
            self._set_playlist_properties(view_manager)

            #Clear the list
            list_obj.reset()

            #Draw the items on the list
            for track in self.__playlist.tracks:

                try:

                    if not track.is_loaded:
                        track.load(5)

                    if (track.error == ErrorType.OK and
                        track.availability == TrackAvailability.AVAILABLE):

                        info = self.__xbmcSpotify.create_track_info(track)

                        if info is not None:
                            list_obj.addItem(info)


                except (Timeout ) as ex:
                    print 'Detail.py render, fail to load track ' + str(track.error)

            return True


class SpecialPlaylistDetailView(PlaylistDetailView):
    def __init__(self, session, playlist, playlist_manager, name, thumbnails):
        self._set_playlist(playlist)
        loader = loaders.SpecialPlaylistLoader(
            session, playlist, playlist_manager, name, thumbnails
        )
        self._set_loader(loader)
