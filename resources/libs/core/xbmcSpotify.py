'''
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

# XBMC imports
import xbmc
import xbmcgui

#Related to spotify in other file
from spotify import Config
from spotify import Session
from spotify import EventLoop
from spotify import SessionEvent
from spotify import ConnectionState
from spotify import ToplistType
from spotify import Timeout
from spotify import ImageSize
from spotify import ErrorType

#from spotimcgui.playback import PlaylistManager

from core.playback import PlaylistManager
from core.settings import VarManager
from core.settings import SettingsManager
from core.callbacks import CallBacks
from proxy.sink import XbmcSink


class XbmcSpotify:
    '''Class which represent a XBMC Spotify application addon.'''

    __session = None
    __config = None
    __settings = None
    __playlist_manager = None
    __loop = None
    __audio = None
    __callbacks = None

    def __init__(self, callbacks=None, config= None):

        #Set global addon information first
        self.__settings = SettingsManager('script.audio.xbmcSpotify')

#         vars.set_var('playlist_manager', __playlist_manager)

        # Set the config
        if config == None:
            #Check pySpotify library and configure it
            self.__config = Config()
            self.__config.user_agent = 'XBMC Spotify Application'

            self.__config.load_application_key_file(self.__settings.__addon_path__ + '/spotify_appkey.key')
            self.__config.user_agent = 'xbmcSpotify'
            self.__config.tracefile = b'/tmp/libspotify-trace.log'

            xbmc.log(msg='Configure XBMC spotify library', level=xbmc.LOGNOTICE)
        else:
            self.__config = config

        self.__session = Session(self.__config)

        #Instantiate the playlist manager
        self.__playlist_manager = PlaylistManager(self.__session)

        if callbacks == None:
            self.__callbacks = CallBacks()
        else:
            self.__callbacks = callbacks

        # Configure the sink for audio
        #self.__audio = XbmcSink(self.__session)

        # Create the event loop
        self.__loop = EventLoop(self.__session)
        self.__loop.start()

        # Configure session and player listeners
        self.__session.on(SessionEvent.END_OF_TRACK, self.__callbacks.on_end_of_track)

        self.__session.on(SessionEvent.CONNECTION_STATE_UPDATED,
                          self.__callbacks.connection_state_listener)


    ## Getter and Setters for private fields
    def getSettings(self):
        return self.__settings

    def setSettings(self, settings):
        self.__settings = settings

    ## Getter and Setters for private fields
    def getConfig(self):
        return self.__config

    def setConfig(self, config):
        self.__config = config

    ## Getter and Setters for private fields
    def getSession(self):
        return self.__session

    def getCallbacks(self):
        return self.__callbacks

    settings = property(getSettings, setSettings)
    config = property(getConfig, setConfig)

    def login(self, username, password, remember,timeout=10):

        try:

            # It should not hapend but...
            if self.__session == None:
                self.__session = Session(self.__config)

            # Create a thread for the loggin
            self.__callbacks.start_login_event()

            # Try to login
            self.__session.login(username, password, remember_me=remember)

            # Wait until loggin is done or 10 seconds
            self.__callbacks.logged_in_wait(timeout)

            status = self.__session.connection.state
        except (Exception) as ex:

            status = 0

        finally:
            return status

    def get_user_name(self):
        ''' Return a unicode object with the user name or None if the session is not logged in'''
        if (self.__session is not None and self.__session.connection.state == ConnectionState.LOGGED_IN):
            return str(self.__session.user_name)
        else:
            return None

    def remembered_user(self):
        return self.__session.remembered_user_name

    def forget_user(self):
        self.__session.forget_me()

    def relogin(self, timeout=10):

        # Create a thread for the loggin
        self.__callbacks.start_login_event()

        self.__session.relogin()

        # Wait until loggin is done or 10 seconds
        self.__callbacks.logged_in_wait(timeout)

        return  self.__session.connection.state == ConnectionState.LOGGED_IN


    def get_top_list(self, timeout= 10):

        toplist = self.__session.get_toplist(type = ToplistType.ALBUMS, region='US')

        # Configure a listener for connection updates
        try:
            toplist.load()

        except (Timeout) as ex:
            toplist = None

        finally:
            return toplist

    def get_playlist_container(self):

        container = self.__session.playlist_container

        try:
            if (not container.is_loaded):
                container.load(10)

        except (Timeout) as ex:
            container = None

        finally:

            return container

    def get_starred(self):

        playlist = self.__session.get_starred()
        try:
            if (not playlist.is_loaded):
                playlist.load(10)

        except (Timeout) as ex:
            playlist = None

        finally:

            return playlist

    def get_inbox(self):
        inbox = self.__session.inbox

        try:
            if (not inbox.is_loaded):
                inbox.load(10)

        except (Timeout) as ex:
            inbox = None

        finally:

            return inbox

    def get_image_url(self, image):
        '''Method to get the url of the spotify.Image object from the http proxy. If the
        image parameter is None the method return an empty string'''
        result = ''

        if image is not None:
            self.__playlist_manager.publish_image(image)
            result = self.__playlist_manager.get_image_url(image.link)

        return result

    def get_album_images_url(self, album):

        if album is not None and album.is_loaded:
            image_normal = album.cover()
            image_large = album.cover(image_size=ImageSize.LARGE)

            return (self.get_image_url(image_normal),  self.get_image_url(image_large))

        return ('', '')

    def get_track_url(self, track):

        result = ''
        if track is not None and track.is_loaded:
            self.__playlist_manager.publish_track(track)
            result = self.__playlist_manager.get_track_url(track)

        return result

    def set_proxy(self, server):
        '''Set the proxy to the playlist_manager which also contains the buffer
        for the sink '''
        self.__playlist_manager.set_proxy(server)

    def create_track_info(self, track):
        '''Create the track info and return a xbmcgui.ListItem. Parameter track should be
        a spotify.track.Track object'''

        #Track is ok
        if track.is_loaded and track.error == ErrorType.OK:

            #Get track attributes
            album = track.album.name
            artist = ', '.join([artist.name for artist
                                in track.artists])

            #pyspotify do not give you track image, get the album image
            normal_image, large_image = self.get_album_images_url(track.album)

            track_url = self.get_track_url(track)

#             rating_points = str(self._calculate_track_rating(track))

            item = xbmcgui.ListItem(
                label=track.name,
                iconImage=normal_image,
                thumbnailImage=large_image,
                path=track_url,
            )


            info = {
                "title": track.name,
                "album": album,
                "artist": artist,
                "duration": track.duration / 1000,
                "tracknumber": track.index,
                "rating": track.popularity
            }


            item.setInfo("music", info)
            item.setProperty('name', track.name)
            item.setProperty('path', track_url)
            item.setProperty('spotify_link', str(track.link))

            if track.starred:
                item.setProperty('IsStarred', 'true')
            else:
                item.setProperty('IsStarred', 'false')

            if track.playable:
                item.setProperty('IsAvailable', 'True')
            else:
                 item.setProperty('IsAvailable', 'False')

            #Rating points, again as a property for the custom stars
            item.setProperty('RatingPoints', str(track.popularity))

            #Tell that analyzing the stream data is discouraged
            item.setProperty('do_not_analyze', 'true')

            return item

        #Track has errors
        else:
            return None

    def get_album(self, item):
        '''Get the spotify.Album object from a specific ItemList. Could return None if
        the track has not been correctly published or if the track has not been loaded'''
        album = None

        # Get the
        track = self.__playlist_manager.get_published_track(item)

        if (track is not None):

            if not  track.is_loaded:
                try:
                    track.load(5)
                except (Timeout) as ex:
                    print 'XbmcSpotify: can not load track ' + str (item.getProperty('name'))

            album = track.album

        # Load the album in case of it exists
        if (album is not None):
            try:
                album.load(5)
            except (Timeout) as ex:
                print 'XbmcSpotify: can not load album ' + str (item.getInfo("album"))

        return album

    def get_track(self, item):

        return self.__playlist_manager.get_published_track(item)

    def add_play(self, item):
        '''Play a itemList'''

        print "xbmcSpotify play: " + item.getProperty('name')
        self.__playlist_manager.add_play(item)


    def is_playing(self):
        return self.__playlist_manager.is_playing()


    def release(self):
        '''Method to release all resources taken from XbmcSpotify class'''

        if self.__callbacks is not None:
            self.__callbacks.release()
            self.__callbacks = None

        # Stop and close playlistManager
        if self.__playlist_manager is not None:
            self.__playlist_manager.close()
            self.__playlist_manager = None

        if not (self.__session == None):
            self.__session.logout()
            self.__session = None

        self.__settings = None
