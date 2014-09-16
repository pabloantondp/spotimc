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


# For the threading event
import threading

from spotify import ConnectionState

class CallBacks:
    '''Class for control the main callbacks from libspotify'''

    logged_in_event = None
    end_of_track = None

    def __init__(self):
        pass

    def start_login_event(self):

        if (self.logged_in_event == None):
            self.logged_in_event = threading.Event()

    def logged_in_wait(self, timeout = 10):

        self.logged_in_event.wait(timeout)

    # Methods for handler connections Events
    def connection_state_listener(self, session):
        '''This method is in charge of analysing different session events'''
        if session.connection.state is ConnectionState.LOGGED_IN:
            self.logged_in_event.set()

    def on_end_of_track(self, session):
        pass

    def release(self):

        # Unlock threads waiting for loggin
        if self.logged_in_event is not None:
            self.logged_in_event.set()

        # Unlock threads waiting for end of track
        if self.end_of_track is not None:
            self.end_of_track.set()
