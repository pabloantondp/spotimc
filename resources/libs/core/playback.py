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

# from spotify.sink import TestSink, AlsaSink

import xbmc
import xbmcgui
import traceback
from __main__ import addon_info

# from spotify import link, track, image
# import time
# from __main__ import __addon_version__
# import math
# import random
# import settings
# from taskutils.decorators import run_in_thread
# from taskutils.threads import current_task
# import re
#
# #Cross python version import of urlparse
# try:
#     from urlparse import urlparse
# except ImportError:
#     from urllib.parse import urlparse

#
#Cross python version import of urlencode
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

class Playqueue:
    ''' This class represent the currrent playlist queue that is going to play'''

    __playlist = None   # The xbmc.PlayList with remains items
    __playqueue = None  # The list with all items

    __index = 0

    def __init__(self):
        self.__playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        self.__playqueue = []

#     def add_item(self, item, index=0):
#         '''Add one item to the queue at first position.'''
#
#         self.__playqueue.add(item.getProperty('path'),
#                                 listitem= item,
#                                 index=index).add(item.getProperty('path'),
#                                 listitem= item,
#                                 index=index)

    def add_current_item(self, item):
        '''Method to add an item just ahead of the current one'''

        index = len(self.__playqueue)
        print "Playqueue posicion " + str (index)
        print "playlist posicion " + str (self.__playlist.getposition()) + " size: " + str(self.__playlist.size())

        self.__playqueue.append(item)

        self.__playlist.clear()
        self.__playlist.add(item.getProperty('path'),
                                listitem= item,
                                index=self.__index)
        self.__index += 1

    def get_playlist(self):
        return self.__playlist



class PlaylistManager:

    # For proxy server connection
    __server = None
    __server_port = None
    __user_agent = None

#     __play_token = None
    __server_ip = None
    __url_headers = None

    # To work with libspotify
    __session = None

    # To manage playList
    __playqueue = None

    __player = None
    __buffer_manager = None

    def __init__(self, session, server=None):

        self.__session = session

        if server is not None:
            self.__server = server
            self.__server_port = server.get_port()
#             self.__play_token = server.get_user_token(self._get_user_agent())
            self.__server_ip = server.get_host()

        self.__playqueue = Playqueue()
        self.__player = xbmc.Player()


    def set_proxy(self, server):
        ''' Set the proxy server to the PlayList'''
        self.__server = server
        self.__server_port = server.get_port()
#         self.__play_token = server.get_user_token(self._get_user_agent())
        self.__server_ip = server.get_host()
        self.__buffer_manager = server.get_buffer_manager()

    def publish_image(self, image):
        ''' Publish an image into the server '''
        if image is not None:
            self.__server.publish_image(image)

    def publish_track(self, track):
        ''' Publish a track into the server '''
        if track is not None:
            self.__server.publish_track(track)

    def _get_user_agent(self):
        pass
#         if self.__user_agent is None:
#             xbmc_build = xbmc.getInfoLabel("System.BuildVersion")
#             self.__user_agent = 'XbmcSpotify/{0} (XBMC/{1})'.format(
#                 addon_info.__addon_version__, xbmc_build)
#
#         return self.__user_agent

    def _play_item(self, offset):
        pass
#         self.__player.playselected(offset)

    def clear(self):
        pass
#         self.__playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
#         self.__playlist.clear()

    def _get_track_id(self, track):
        pass
#         track_link = link.create_from_track(track)
#         return track_link.as_string()[14:]

    def _get_url_headers(self):
        pass
#         if self.__url_headers is None:
#             str_agent = self._get_user_agent()
#             str_token = self._get_play_token()
#             header_dict = {
#                 'User-Agent': str_agent,
#                 'X-Spotify-Token': str_token
#                 }
#             self.__url_headers = urlencode(header_dict)
#
#         return self.__url_headers

    def get_track_url(self, track):
        '''Get the proxy track URL for a given spotify.track.Track object'''
        if (self.__server_ip is not None) and track is not None:
            args = (self.__server_ip, self.__server_port, track.link)
            return 'http://{0}:{1:d}/track/{2}.wav'.format(*args)
        else:
            return ''

    def get_image_url(self, image_id):
        ''' Get the proxy image URL for a given spotify.image.Image object'''
        if (self.__server_ip is not None) and image_id is not None:
            args = (self.__server_ip, self.__server_port, image_id)
            return 'http://{0}:{1:d}/image/{2}.jpg'.format(*args)
        else:
            return ''

    def _calculate_track_rating(self, track):
        popularity = track.popularity()
        if popularity == 0:
            return 0
        else:
            return int(math.ceil(popularity * 6 / 100.0)) - 1

    def _item_is_playable(self, item):
        return bool(item.getProperty('IsAvailable'))

    def stop(self, block=True):
        #Stop the stream and wait until it really got stopped
        #self.__player.stop()
        pass
#
#         xbmc.executebuiltin('PlayerControl(stop)')
#
#         while block and self.__player.isPlaying():
#             time.sleep(.1)

    def is_playing(self, consider_pause=True):
        if consider_pause:
            return xbmc.getCondVisibility('Player.Playing | Player.Paused')
        else:
            return xbmc.getCondVisibility('Player.Playing')

    def get_shuffle_status(self):
        #Get it directly from a boolean tag (if possible)
        pass
#         if self.is_playing() and len(self.__playlist) > 0:
#             return xbmc.getCondVisibility('Playlist.IsRandom')
#
#         #Otherwise read it from guisettings.xml
#         else:
#             try:
#                 reader = settings.GuiSettingsReader()
#                 value = reader.get_setting('settings.mymusic.playlist.shuffle')
#                 return value == 'true'
#
#             except:
#                 xbmc.log(
#                     'Failed reading shuffle setting.',
#                     xbmc.LOGERROR
#                 )
#                 return False


    def set_tracks(self, track_list, session, omit_offset=None):
        pass
#         self._cancel_loop()
#         self._set_tracks(track_list, session, omit_offset)


    def get_published_track(self, item):
        '''Return the track object corresponding to a ItemList. If the Track has
        not been published it returns None'''
        return self.__server.get_published_track(item)

    def add_play(self, item):
        ''' Add the item to current position of the queue and play it'''

        #Get shuffle status
#         is_shuffle = self.get_shuffle_status()

        #Check if the selected item is playable
        if not self._item_is_playable(item):
            d = xbmcgui.Dialog()
            d.ok('Spotimc', 'The selected track is not playable')

        #Continue normally
        else:

            #Start playing music with libspotify
            track = self.__server.get_published_track(item)

            if track is not None and track.is_loaded:

                # Start loading the buffer
                self.__buffer_manager.open(track)

                # Add the desired item to current playlist and play with
                # xbmc player
                try:

                    self.__playqueue.add_current_item(item)
                    self.__player.play(self.__playqueue.get_playlist())
                except:
                    print 'Playback add_play exception'
                print "Playback.py play Agnadido el item al playlist"

            else:
                d = xbmcgui.Dialog()
                d.ok('Spotimc', 'The selected track can not be loaded')

    def get_item(self, sess_obj, index):
        pass
#         item = self.__playlist[index]
#         return self._get_track_from_url(sess_obj, item.getfilename())

    def get_current_item(self, sess_obj):
        pass
#         return self._get_track_from_url(
#             sess_obj, xbmc.getInfoLabel('Player.Filenameandpath')
#         )

    def get_next_item(self, sess_obj):
        pass
#         next_index = self.__playlist.getposition() + 1
#         if next_index < len(self.__playlist):
#             return self.get_item(sess_obj, next_index)

    def close(self):
        ''' Clean lists and stop any song that could be playing '''
        if self.__server is not None:
            self.__server.stop()
            self.__server = None

        if self.__player is not None and self.__player.isPlaying():
            self.__player.stop()
            self.__player = None

#         if self.__playlist is not None:
#             self.__playlist.clear()
#             self.__playlist = None

        if self.__buffer_manager is not None:
            self.__buffer_manager.close()
            self.__buffer_manager = None

        self.__session.player.unload()
