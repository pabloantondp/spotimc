'''
Created on 27/10/2011

@author: mikel
'''
import xbmcgui
from spotymcgui.views import BaseListContainerView

import loaders

from spotify import link, track

from spotymcgui.views.album import AlbumTracksView
from spotymcgui.views.artists import open_artistbrowse_albums



class PlaylistDetailView(BaseListContainerView):
    container_id = 1800
    list_id = 1801
    
    BrowseArtistButton = 5811
    BrowseAlbumButton = 5812
    
    context_toggle_star = 5813
    
    __loader = None
    __playlist = None
    
    
    def __init__(self, session, playlist):
        self.__playlist = playlist
        self.__loader = loaders.FullPlaylistLoader(session, playlist)
    
    
    def _set_loader(self, loader):
        self.__loader = loader
    
    
    def _set_playlist(self, playlist):
        self.__playlist = playlist
    
    
    def _browse_artist(self, view_manager):
        item = self.get_list(view_manager).getSelectedItem()
        pos = int(item.getProperty('TrackIndex'))
        track = self.__playlist.track(pos)
        artist_list = [artist for artist in track.artists()]
        open_artistbrowse_albums(view_manager, artist_list)
    
    
    def click(self, view_manager, control_id):
        if control_id == PlaylistDetailView.list_id:
            item = self.get_list(view_manager).getSelectedItem()
            pos = int(item.getProperty('TrackIndex'))
            playlist_manager = view_manager.get_var('playlist_manager')
            playlist_manager.play(self.__playlist.tracks(), pos)
        
        elif control_id == PlaylistDetailView.BrowseArtistButton:
            self._browse_artist(view_manager)
            
        elif control_id == PlaylistDetailView.BrowseAlbumButton:
            item = self.get_list(view_manager).getSelectedItem()
            pos = int(item.getProperty('TrackIndex'))
            album = self.__playlist.track(pos).album()
            v = AlbumTracksView(view_manager.get_var('session'), album)
            view_manager.add_view(v)
        
        elif control_id == PlaylistDetailView.context_toggle_star:
            item = self.get_list(view_manager).getSelectedItem()
            pos = int(item.getProperty("TrackIndex"))
            
            if pos is not None:
                session = view_manager.get_var('session')
                current_track = self.__playlist.track(pos)
                
                if item.getProperty('IsStarred') == 'true':
                    item.setProperty('IsStarred', 'false')
                    track.set_starred(session, [current_track], False)
                else:
                    item.setProperty('IsStarred', 'true')
                    track.set_starred(session, [current_track], True)
    
    
    def get_container(self, view_manager):
        return view_manager.get_window().getControl(PlaylistDetailView.container_id)
    
    
    def get_list(self, view_manager):
        return view_manager.get_window().getControl(PlaylistDetailView.list_id)
    
    
    def _add_track(self, list, idx, title, artist, album, path, duration, is_starred):
        item = xbmcgui.ListItem(path=path)
        item.setProperty('TrackIndex', str(idx))
        
        if is_starred:
            item.setProperty('IsStarred', 'true')
        else:
            item.setProperty('IsStarred', 'false')
        
        item.setInfo(
            "music",
            {
             "title": title, "artist": artist, "album": album,
             "duration": duration
            }
        )
        list.addItem(item)
    
    
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
        window.setProperty("PlaylistDetailName", self.__loader.get_name())
        
        #Owner info
        session = view_manager.get_var('session')
        current_username = session.user().canonical_name()
        playlist_username = self.__playlist.owner().canonical_name()
        
        if current_username != playlist_username:
            window.setProperty("PlaylistDetailShowOwner", "true")
            window.setProperty("PlaylistDetailOwner", str(playlist_username))
        else:
            window.setProperty("PlaylistDetailShowOwner", "false")
    
        #Collaboratie status
        if self.__playlist.is_collaborative():
            window.setProperty("PlaylistDetailCollaborative", "true")
        else:
            window.setProperty("PlaylistDetailCollaborative", "false")
        
        #Length data
        window.setProperty("PlaylistDetailNumTracks", str(self.__playlist.num_tracks()))
        window.setProperty("PlaylistDetailDuration", self._get_playlist_length_str())
        
        #Subscribers
        window.setProperty("PlaylistDetailNumSubscribers", str(self.__playlist.num_subscribers()))
    
    
    def _set_playlist_image(self, view_manager, thumbnails):
        if len(thumbnails) > 0:
            window = view_manager.get_window()
            
            #Set cover info
            if len(thumbnails) < 4:
                window.setProperty("PlaylistDetailCoverLayout", "one")
            else:
                window.setProperty("PlaylistDetailCoverLayout", "four")
            
            #Now loop to set all the images
            for idx, thumb_item in enumerate(thumbnails):
                window.setProperty("PlaylistDetailCoverItem%d" % (idx + 1), thumb_item)
    
    
    def _populate_list(self, view_manager, track_list):
        session = view_manager.get_var('session')
        list = self.get_list(view_manager)
        list.reset()
        
        for idx, item in enumerate(track_list):
            track_link = link.create_from_track(item)
            track_id = track_link.as_string()[14:]
            track_url = "http://localhost:8080/track/%s.wav" % track_id
            
            self._add_track(
                list,
                idx,
                item.name(),
                ', '.join([artist.name() for artist in item.artists()]),
                item.album().name(),
                track_url,
                item.duration() / 1000,
                item.is_starred(session)
            )
    
    
    def render(self, view_manager):
        if self.__loader.is_loaded():
            #Draw the items on the list
            self._populate_list(view_manager, self.__loader.get_tracks())
            
            #Set the thumbnails
            self._set_playlist_image(view_manager, self.__loader.get_thumbnails())
            
            #And the properties
            self._set_playlist_properties(view_manager)
            
            return True



class SpecialPlaylistDetailView(PlaylistDetailView):
    def __init__(self, session, playlist, name, thumbnails):
        self._set_playlist(playlist)
        self._set_loader(
            loaders.SpecialPlaylistLoader(session, playlist, name, thumbnails)
        )
