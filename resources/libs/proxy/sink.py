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

import time # For sleeping the thread until

from spotify import Sink
import threading
from collections import deque
from spotify import SampleType

import traceback
import xbmc
# General buffer error
class BufferError(IOError):
    pass


# Risen when stutter is detected
class BufferUnderrunError(BufferError):
    pass



class BufferInitializationError(BufferError):
    pass



class BufferStoppedError(BufferError):
    pass


class QueueItem:
    data = None
    num_samples = None
    sample_type = None
    sample_rate = None
    num_channels = None
    frame_time = None

    def __init__(self, data, num_samples, sample_type, sample_rate, num_channels, frame_time):
        self.data = data
        self.num_samples = num_samples
        self.sample_type = sample_type
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.frame_time = frame_time


class XbmcSink(Sink):
    '''Audio sink link spotify and XBMC.'''

    # Queue that holds the in-memory frames indexes
    __frame_indexes = None
    __frame_data = None
    __playback_stopped = False
    __stutter = None            # No se para que es todavia
    __buffer_length = None      # Current buffer length in seconds
    __track = None              # Currently playing track object
    __access_lock = None        # For controlling the read/write access
    __access_condition = None

    __file = None

    def __init__(self, session):

        self.__frame_indexes = deque()
        self.__frame_data = {}
        self.__playback_stopped = False
        self._session = session
        self.__buffer_length = 0
        self.__stutter = 0

        self.__access_event = threading.Event()

        self.on()

    def _on_music_delivery(self, session, audio_format, frames, num_frames):
        '''Listener of the pyspotify sink'''
        try:
            frame_time = 1.0 * num_frames / audio_format.sample_rate

            # Add the data
            self._append_frame(audio_format, frames, num_frames, frame_time)

            # Wake up any thread waiting for this event
            self.__access_event.set()
        except:
            print '_on_music_delivery exception'
        finally:
            return num_frames

    def _append_frame(self, audio_format, frames, num_frames, frame_time):

        # Get the lock
#         self.__access_lock.acquire(True)
        #data, num_samples, audio_format, sample_rate, num_channels, frame_time):
        # Calculate the new frame id
        frame_id = self.get_last_frame_in_buffer() + 1

        # Save the data
        self.__frame_data[frame_id] = QueueItem(
            frames,
            num_frames,
            audio_format.sample_type,
            audio_format.sample_rate,
            audio_format.channels,
            frame_time,
        )

        # Update the buffer
        #self.__buffer_length += frame_time


        # Update the sample counts
        #self.__samples_in_buffer += num_samples
        #self.__total_samples += num_samples

        # And finally index it on the queue
        self.__frame_indexes.append(frame_id)

        # release the lock
#         self.__access_lock.notify_all()
#         self.__access_lock.release()

    def _close(self):

        # Clean the current buffer and unregister as spotify sink listener
        self.__playback_stopped = True
        self.__access_event.set()

    def _will_fill_buffer(self, frame_time):
        return frame_time + self.__buffer_length > self.__max_buffer_length

    def get_first_frame_in_buffer(self):
        '''Get the first frame in the buffer'''
        if len(self.__frame_indexes) > 0:
            return self.__frame_indexes[0]
        else:
            return -1

    def get_last_frame_in_buffer(self):
        if len(self.__frame_indexes) > 0:
            return self.__frame_indexes[-1]

        else:
            return -1

    def get_frame(self, frame_num):
        ''' Try to get the frame in position the __frame_indexes[frame_num]'''
        # What happens if this frame is not on the index?
        if frame_num not in self.__frame_indexes:

            # Buffer was stopped, and we depleted remaining frames
            if self.__playback_stopped:
                raise BufferStoppedError()

            # Frame is no longer available
            elif frame_num < self.get_first_frame_in_buffer():
                raise BufferError("Frame number #%d gone, too late my friend." % frame_num)

            # If it's ahead of the buffer, it's an underrun
            else:
                self.__stutter += 1
                raise BufferUnderrunError("Frame #%d not yet available." % frame_num)

         # Let's serve the frame
        else:

            # Get requested frame
            frame = self.__frame_data[frame_num]

            # If requested frame is higher than the last requested
#             if self.__last_frame < frame_num:
                # Set if as the last requested one
#                 self.__last_frame = frame_num

            # Flag to indicate if there are frames left
            has_frames = frame_num < len(self.__frame_indexes)

            # Store the time buffer was first requested.
            # Also, do not account frame #0, since it's immediately
            # requested after __init__()
#             if self.__start_time is None and frame_num != 0:
#                 self.__start_time = time.time()

            return frame, has_frames

    def get_frame_wait(self, frame_num):

        '''Block method to get a specific frame in the buffer'''
        frame, has_frames = None, None

        while (frame is None):
            try:
                frame, has_frames = self.get_frame(frame_num)
            except BufferStoppedError:
                return None, None
            except:
                self.__access_event.wait()
                self.__access_event.clear()

        return frame, has_frames

    def set_track(self, track):
        self.__track = track

    def clean(self):

        self.__frame_indexes.clear()
        self.__frame_data = {}
        self.__playback_stopped = False
        self.__access_event.clear()
        self.__buffer_length = 0
        self.__stutter = 0
        print 'sink.py Buffer limpio!!'


class BufferManager():

    __xbmcSpotify = None    ## To be able to get the session to libspotify
    __current_buffer = None
    __buffer_size = None
    __buffer_open_lock = None

    # The current track
    __track = None

    def __init__(self, xbmcSpotify, buffer_size=10):
        self.__buffer_size = buffer_size
        self.__buffer_open_lock = threading.Lock()
        self.__xbmcSpotify = xbmcSpotify
        self.__current_buffer = XbmcSink(xbmcSpotify.getSession())

    def _can_share_buffer(self, track):
        """
        Check if the requested track and the current one are the same.
        If true, check if the buffer is still on the start position, so
        this thread can catch up it.
        The result is a shared buffer between threads.
        """
        return(self.__track is not None and
                str(track.link) == str(self.__track.link) and
                self.__current_buffer.get_first_frame_in_buffer() <= 0
        )


    def open(self, track):
        '''Open a track and write the content into the buffer. Track should be an
        instance of spotify.Track class'''
        self.__buffer_open_lock.acquire()

        print "sink.py opening buffer for track " + str(track.name)
        try:
            # If we can't share this buffer start a new one
            if self.__track is None:
                print "sink.py open Creating a new buffer "
                self.__current_buffer.set_track(track)
                self.__xbmcSpotify.getSession().player.load(track)
                self.__xbmcSpotify.getSession().player.play()
                self.__track = track

            elif not self._can_share_buffer(track):
                print "sink.py open New track, new buffer "

                self.__xbmcSpotify.getSession().player.unload()
                self.__current_buffer.clean()
                self.__current_buffer.set_track(track)
                self.__xbmcSpotify.getSession().player.load(track)
                self.__xbmcSpotify.getSession().player.play()
                self.__track = track
            else:
                print "sink.py open compartir el buffer"

        finally:

            self.__buffer_open_lock.release()

            return self.__current_buffer


    def get_stats(self):
        if self.__current_buffer is not None:
            return self.__current_buffer.get_stats()


    def set_track_ended(self):
        if self.__current_buffer is not None:
            self.__current_buffer.set_track_ended()


    def close(self):
        if self.__current_buffer is not None:
            self.__current_buffer.off()


    def cleanup(self):
        self.__current_buffer = None