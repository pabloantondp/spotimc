'''
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

from gui.views import BaseListContainerView

class PlayqueueDetailView(BaseListContainerView):
    ID_CONTAINER = 2100
    ID_LIST = 2101

    __playqueue = None
    __xbmcSpotify = None

    def __init__(self, xbmcSpotify):

        self.__xbmcSpotify = xbmcSpotify
        self.__playqueue = xbmcSpotify.get_playqueue()


    def click(self, view_manager, control_id):
        pass


    def action(self, view_manager, action_id):
        pass

    def get_container(self, view_manager):
        return view_manager.get_window().getControl(
            PlayqueueDetailView.ID_CONTAINER)

    def get_list(self, view_manager):
        return view_manager.get_window().getControl(PlayqueueDetailView.ID_LIST)

#     def get_context_menu_id(self):
#         return PlayqueueDetailView.ID_CONTEXT_MENU

    def _get_playlist_length_str(self):
        pass

    def _set_playlist_properties(self, view_manager):

        window = view_manager.get_window()

        # Playlist name
        window.setProperty("PlaylistDetailName", 'Playlist Queue')

        #Owner info
        window.setProperty("PlaylistDetailShowOwner", "true")
        window.setProperty("PlaylistDetailOwner", str( self.__xbmcSpotify.get_user_name()))
        window.setProperty("PlaylistDetailCollaborative", "false")

        #Length data
        window.setProperty("PlaylistDetailNumTracks",
                           str(self.__playqueue.lenght()))
#         window.setProperty("PlaylistDetailDuration",
#                             self._get_playlist_length_str())


    def _set_playlist_image(self, view_manager, thumbnails):
        pass



    def render(self, view_manager):

        if self.__playqueue is not None:

            # Get the list and clear it
            list_obj = self.get_list(view_manager)
            list_obj.reset()

            #Set the thumbnails
            self._set_playlist_image(view_manager,None)

            #And the properties
            self._set_playlist_properties(view_manager)

            #Draw the items on the list
            for item in self.__playqueue.items():

                list_obj.addItem(item)

            return True
