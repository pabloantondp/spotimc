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
from gui.views import BaseListContainerView, iif


from spotify import TrackAvailability, ImageSize


#from taskutils.decorators import run_in_thread
import threading

#
# class AlbumCallbacks():
#     def albumbrowse_complete(self, albumbrowse):
#         xbmc.executebuiltin("Action(Noop)")


# class MetadataUpdateCallbacks(session._SessionCallbacks):
#
#     __event = None
#
#     def __init__(self, event):
#         self.__event = event
#
#     def metadata_updated(self, session):
#         self.__event.set()


class AlbumTracksView(BaseListContainerView):
    ID_CONTAINER = 1300
    ID_LIST = 1303

    ID_CONTEXT_MENU = 5300
    ID_CONTEXT_TOGGLE_STAR = 5307

    __albumbrowse = None
    __list_rendered = None
    __update_lock = None
    __update_unavailable = None

    __album = None # A spotify.Album object
    __xbmcSpotify = None

    def __init__(self, xbmcSpotify, album):

        self.__list_rendered = False
        self.__update_lock = threading.Lock()
        self.__album = album
        self.__xbmcSpotify = xbmcSpotify

#         cb = AlbumCallbacks()
#         self.__albumbrowse = albumbrowse.Albumbrowse(session, album, cb)

    def _play_selected_track(self, view_manager):

        # Get the ItemList object
        item = self.get_list(view_manager).getSelectedItem()

        # Play the item
        self.__xbmcSpotify.play(item)

    def click(self, view_manager, control_id):

        if control_id == AlbumTracksView.ID_LIST:
            self._play_selected_track(view_manager)

        elif control_id == AlbumTracksView.ID_CONTEXT_TOGGLE_STAR:
            item = self.get_list(view_manager).getSelectedItem()
            pos = int(item.getProperty("ListIndex"))

            if pos is not None:
                session = view_manager.get_var('session')
                current_track = self.__albumbrowse.track(pos)

                if item.getProperty('IsStarred') == 'true':
                    item.setProperty('IsStarred', 'false')
                    _track.set_starred(session, [current_track], False)
                else:
                    item.setProperty('IsStarred', 'true')
                    _track.set_starred(session, [current_track], True)

    def action(self, view_manager, action_id):
        #Run parent implementation's actions
        BaseListContainerView.action(self, view_manager, action_id)

        #Do nothing if playing, as it may result counterproductive
        if action_id == 79 and not self.__xbmcSpotify.is_playing():
            print 'ACCIION QUE PODRIA INTERESAR'

            #self._play_selected_track(view_manager)

    def get_container(self, view_manager):
        return view_manager.get_window().getControl(AlbumTracksView.ID_CONTAINER)

    def get_list(self, view_manager):
        return view_manager.get_window().getControl(AlbumTracksView.ID_LIST)

    def get_context_menu_id(self):
        return AlbumTracksView.ID_CONTEXT_MENU

    def _have_multiple_discs(self):
        for item in self.__albumbrowse.tracks():
            if item.disc() > 1:
                return True

        return False

    def _set_album_info(self, view_manager):
        '''Set the information of the album into the view manager'''

        window = view_manager.get_window()
        url = ''

        try:
            cover = self.__album.cover(image_size=ImageSize.LARGE)
            url = self.__xbmcSpotify.get_image_url(cover)
        except:
            print 'album.py Can not get album cover url'

        window.setProperty("AlbumCover", url)
        window.setProperty("AlbumName", self.__album.name)
        window.setProperty("ArtistName", self.__album.artist.name)

    def _add_disc_separator(self, list_obj, disc_number):
        item = xbmcgui.ListItem()
        item.setProperty("IsDiscSeparator", "true")
        item.setProperty("DiscNumber", str(disc_number))
        list_obj.addItem(item)

    def _get_list_item(self, list_obj, index):
        for current_index in range(index, list_obj.size()):
            item = list_obj.getListItem(current_index)
            if item.getProperty('ListIndex') == str(index):
                return item

    def _item_available(self, item):
        return item.getProperty('IsAvailable') == 'true'

    def _track_available(self, session, track_obj):
        return (track_obj.get_availability(session) ==
                _track.TrackAvailability.Available)

    def hide(self, view_manager):

        BaseListContainerView.hide(self, view_manager)

        #Cancel any potential update loop
        self.__update_unavailable = False

    def _update_metadata(self, view_manager):
        list_obj = self.get_list(view_manager)
        session = view_manager.get_var('session')
        num_unavailable = 0

        for index, track_obj in enumerate(self.__albumbrowse.tracks()):
            item_obj = self._get_list_item(list_obj, index)
            item_available = self._item_available(item_obj)
            track_available = self._track_available(session, track_obj)

            #Increment the counter if it's unavailable
            if not track_available:
                num_unavailable += 1

            #If status changed, update it
            if item_available != track_available:
                status_str = iif(track_available, 'true', 'false')
                item_obj.setProperty('IsAvailable', status_str)

        return num_unavailable

    #@run_in_thread(max_concurrency=1)
    def update_unavailable_tracks(self, view_manager):

        #Try acquiring the update lock
        if self.__update_lock.acquire(False):

            try:

                wait_time = 10
                event = threading.Event()
                session = view_manager.get_var('session')
                m_cb = MetadataUpdateCallbacks(event)
                session.add_callbacks(m_cb)
                self.__update_unavailable = True

                while self.__update_unavailable and wait_time > 0:
                    wait_time -= 1
                    event.wait(1)
                    event.clear()
                    if self._update_metadata(view_manager) == 0:
                        self.__update_unavailable = False

            finally:
                session.remove_callbacks(m_cb)
                self.__update_lock.release()

    def render(self, view_manager):

        if self.__album.is_loaded:

            # Get the browser
            album_browser = self.__album.browse()

            try:
                 album_browser.load(5)
            except (Timeout) as ex:
                raise Exception('Rendering album is not possible')

            has_unavailable = False

            #Reset list
            list_obj = self.get_list(view_manager)
            list_obj.reset()

            #Set album info
            self._set_album_info(view_manager)

            #For disc grouping
#             last_disc = None
#             multiple_discs = self._have_multiple_discs()


            #Iterate over the track list
            for track in album_browser.tracks:

                #If disc was changed add a separator
#                 if multiple_discs and last_disc != track_obj.disc():
#                     last_disc = track_obj.disc()
#                     self._add_disc_separator(list_obj, last_disc)

                #Add the track item
                info = self.__xbmcSpotify.create_track_info(track)
                list_obj.addItem(info)

                #If the track is unavailable, add it to the list
                track_available = track.availability

                if track_available != TrackAvailability.AVAILABLE  and not has_unavailable:
                    has_unavailable = True

#             self.update_unavailable_tracks(view_manager)

            self.__list_rendered = True

            return True
