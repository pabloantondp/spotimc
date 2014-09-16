'''
Created on 06/05/2011

@author: mikel

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
# For cherrypy HTTP server
import cherrypy
from cherrypy import wsgiserver


from spotify  import ImageFormat, TrackAvailability, SampleType
import threading, time, StringIO, re, struct

import weakref
from datetime import datetime
import string, random
# from utils import DynamicCallback

#TODO: urllib 3.x compatibility
import urllib2


# xbmcSpotify imports
from utils import NullLogHandler
from proxy import find_free_port
from proxy.sink import QueueItem, BufferStoppedError
import traceback



class HTTPProxyError(Exception):
    pass



def format_http_date(dt):
    """
    As seen on SO, compatible with py2.4+:
    http://stackoverflow.com/questions/225086/rfc-1123-date-representation-in-python
    """
    """Return a string representation of a date according to RFC 1123
    (HTTP/1.1).

    The supplied date must be in UTC.

    """
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
    month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
             "Oct", "Nov", "Dec"][dt.month - 1]
    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month,
        dt.year, dt.hour, dt.minute, dt.second)


#
#
# class ImageCallbacks():
#     __checker = None
#
#
#     def __init__(self, checker):
#         self.__checker = checker
#
#
#     def image_loaded(self, image):
#         self.__checker.check_conditions()



class ImageDirectory:
    __last_modified = None
    images_dir = None

    def __init__(self):
        self.__last_modified = format_http_date(datetime.utcnow())
        self.images_dir = {}

    def _get_clean_image_id(self, image_str):
        #Strip the optional extension...
        r = re.compile('\.jpg$', re.IGNORECASE)
        return re.sub(r, '', image_str)

    def publish_image(self, image):
        '''Publish image in the server. ImageDirectory should be a spotify.image.ImageDirectory object'''
        file = str(image.link) + ".jpg"
        self.images_dir[file] = image

    @cherrypy.expose
    def default(self, image_id, **kwargs):

        method = cherrypy.request.method.upper()
        #Fail for other methods than get or head
        if method not in ("GET", "HEAD"):
              raise cherrypy.HTTPError(405)

        # Find the image in the dictionary
        image = self.images_dir[str(image_id)]

        if (not image.is_loaded):
            image.load(5)


        #Fail if image was not loaded or wrong format
        if not image.is_loaded or image.format != ImageFormat.JPEG:
            raise cherrypy.HTTPError(500)

        else:
            cherrypy.response.headers["Content-Type"] = "image/jpeg"
            cherrypy.response.headers["Content-Length"] = len(image.data)
            cherrypy.response.headers["Last-Modified"] = self.__last_modified

            if method == 'GET':
                return image.data



# class TrackLoadCallback():
#     __checker = None
#
#
#     def __init__(self, checker):
#         self.__checker = checker
#
#
#     def metadata_updated(self, session):
        self.__checker.check_conditions()



class TrackDirectory:
    '''A TrackDirectory represent /track directory into the httpProxy. It constains
    a list of tracks and manage its buffers'''

    #(data, num_samples, sample_type, sample_rate, num_channels, frame_time
    DUMMY_FRAME = QueueItem('',
                            1,
                            SampleType.INT16_NATIVE_ENDIAN,
                            44100,
                            2,
                            1.0 / 44100,
                            )
    __buffer_manager = None
    __is_playing = None
    __allowed_ips = None
    __allow_ranges = None

    __track_dir = None      # Directory with references to proxy tracks url. The keys
                            # are the spotify tracks links

    _finish = False        # To finish serving bucle
    event_close = None

    def __init__(self, buffer_manager, allowed_ips, on_stream_ended, allow_ranges=True):

        self.__buffer_manager = buffer_manager
        self.__allowed_ips = allowed_ips
        self.__is_playing = False
        self.__cb_stream_ended = on_stream_ended
        self.__allow_ranges = allow_ranges
        self.__track_dir = {}
        self.event_close = threading.Event()
        self.event_close.set()  # By default is set what means that there is no request processing

    def publish_track(self, track):
         '''Publish track into the server. track should be a spotify.track.Track object'''
         self.__track_dir[str(track.link)] = track

    def _write_wave_header(self, numsamples, channels, samplerate, bitspersample):
        '''Method to create a string with the WAV RIFF header. It returns the string
        with the header and the chunk size ('''

        # Create the string object
        file = StringIO.StringIO()

        #Generate format chunk
        format_chunk_spec = "<4sLHHLLHH" #Master RIFF Chuck
        format_chunk = struct.pack(
            format_chunk_spec,
            "fmt ", #Chunk id
            16, #Size of this chunk (excluding chunk id and this field)
            1, #Audio format, 1 for PCM
            channels, #Number of channels
            samplerate, #Samplerate, 44100, 48000, etc.
            samplerate * channels * (bitspersample / 8), #Byterate
            channels * (bitspersample / 8), #Blockalign
            bitspersample, #16 bits for two byte samples, etc.
        )

        #Generate data chunk
        data_chunk_spec = "<4sL"
        datasize = numsamples * channels * (bitspersample / 8)
        data_chunk = struct.pack(
            data_chunk_spec,
            "data", #Chunk id
            int(datasize), #Chunk size (excluding chunk id and this field)
        )

        sum_items = [
            #"WAVE" string following size field
            4,

            #"fmt " + chunk size field + chunk size
            struct.calcsize(format_chunk_spec),

            #Size of data chunk spec + data size
            struct.calcsize(data_chunk_spec) + datasize
        ]

        #Generate main header
        all_cunks_size = int(sum(sum_items))
        main_header_spec = "<4sL4s"
        main_header = struct.pack(
            main_header_spec,
            "RIFF",
            all_cunks_size,
            "WAVE"
        )

        #Write all the contents in
        file.write(main_header)
        file.write(format_chunk)
        file.write(data_chunk)

        return file.getvalue(), all_cunks_size + 8


    def _get_sample_width(self, sample_type):

        if sample_type == SampleType.INT16_NATIVE_ENDIAN:
            return 16

        else:
            return -1


    def _get_total_samples(self, track, frame=None):
        '''Calculate the total samples in a track. If frame is None, we use
        the dummy frame with default valuel'''

        if frame is None:
            frame = self.DUMMY_FRAME

        return frame.sample_rate * track.duration / 1000


    def _generate_file_header(self, num_samples, frame=None):
        '''Generate the header of the wav riff file. If frame is None we use
        the default information into dummy frame'''

        if frame is None:
            frame = self.DUMMY_FRAME

        # Build the whole header
        return self._write_wave_header(
                        num_samples, frame.num_channels, frame.sample_rate,
                        self._get_sample_width(frame.sample_type)
                        )

    def _write_content_generator(self, buf, filesize, wave_header=None, max_buffer_size=65535):

        #Initialize some loop vars
        self.event_close.clear()

        output_buffer = StringIO.StringIO()
        bytes_written = 0
        has_frames = True
        frame_num = 0

        #Write wave header
        if wave_header is not None:
            output_buffer.write(wave_header)
            bytes_written = output_buffer.tell()
            yield wave_header
            output_buffer.truncate(0)

        #Loop there's something to output
        while not self._finish and has_frames:

            try:
                frame, has_frames = buf.get_frame_wait(frame_num)

                #Check if this frame fits in the estimated calculation
                if bytes_written + len(frame.data) < filesize:
                    output_buffer.write(frame.data)
                    bytes_written += len(frame.data)
                #Does not fit, we need to truncate the frame data
                else:
                    truncate_size = filesize - bytes_written
                    output_buffer.write(frame.data[:truncate_size])
                    bytes_written = filesize
                    has_frames = False

                #Update counters
                frame_num += 1

            except BufferStoppedError:

                #Handle gracefully a buffer cancellation
                has_frames = False

            finally:

                #Check if the current buffer needs to be flushed
                if not has_frames or output_buffer.tell() > max_buffer_size:
                    try:
                        yield output_buffer.getvalue()
                    except:
                       print '_write_content_generator exception yield'
                    finally:
                        yield ''
                        output_buffer.truncate(0)

        #Add some silence padding until the end is reached (if needed)
        while not self._finish and bytes_written < filesize:

            #The buffer size fits into the file size
            if bytes_written + max_buffer_size < filesize:
                yield '\0' * max_buffer_size
                bytes_written += max_buffer_size

            #Does not fit, just generate the remaining bytes
            else:
                yield '\0' * (filesize - bytes_written)
                bytes_written = filesize

        # Wake up any thread waiting for this reques to finish
        self.event_close.set()

        #Notify that the stream ended
#         self.__cb_stream_ended()


    def _check_request(self):

        method = cherrypy.request.method.upper()
        headers = cherrypy.request.headers

        #Fail for other methods than get or head
        if method not in ("GET", "HEAD"):
            raise cherrypy.HTTPError(405)
#
#         #Error if no token or user agent are provided
#         if 'User-Agent' not in headers or 'X-Spotify-Token' not in headers:
#             raise cherrypy.HTTPError(403)
#
        #Error if the requester is not allowed
        if headers['Remote-Addr'] not in self.__allowed_ips:
            raise cherrypy.HTTPError(403)
#
#         #Check that the supplied token is correct
#         user_token = headers['X-Spotify-Token']
#         user_agent = headers['User-Agent']
#         correct_token = create_user_token(self.__base_token, user_agent)
#         if user_token != correct_token:
#             raise cherrypy.HTTPError(403)
#
        return method

    def _parse_ranges(self):
        '''Method to get the range values of the http header Range'''
        r = re.compile('^bytes=(\d*)-(\d*)$')
        m = r.match(cherrypy.request.headers['Range'])
        if m is not None:
            return m.group(1), m.group(2)


    def _check_track(self, track):
        ''' Check if the track is playable or not. '''
        if track.availability != TrackAvailability.AVAILABLE :
            raise cherrypy.HTTPError(403)

    def get_published_track(self, track_item):

        result = None

        try:
            path_link = track_item.getProperty('spotify_link')
            result = self.__track_dir[path_link]

        finally:

            return result

    def get_track_link(self, track_url):
        '''Get the track link from track url'''
        segments = track_url.rpartition('.')
        return segments[0]

    def _write_http_headers(self, filesize):
        cherrypy.response.headers['Content-Type'] = 'audio/x-wav'
        cherrypy.response.headers['Content-Length'] = filesize
        cherrypy.response.headers['Accept-Ranges'] = 'bytes'

    @cherrypy.expose
    def default(self, track_url, **kwargs):

        #Check sanity of the request
        self._check_request()

        track_link = self.get_track_link(track_url)

        if (track_link is None):
            raise cherrypy.HTTPError(404)

        #Get the object represented by the spotify link
        track_obj = self.__track_dir[track_link]

        #Check if it's playable, to avoid opening a useless buffer
        self._check_track(track_obj)

        #Get the first frame of the track
        if cherrypy.request.method.upper() == 'GET':

            try:
                buf = self.__buffer_manager.open(track_obj)
#                 frame = buf.get_frame_wait(0)[0]
            except:
                print 'default request exception'

        #Or just create a fake one if the method is "HEAD"
        else:
            frame = self.DUMMY_FRAME

        try:
            #Calculate the total number of samples in the track
            num_samples = self._get_total_samples(track_obj)

            #Calculate file size, and obtain the header
            file_header, filesize = self._generate_file_header(num_samples)

            #It's a partial request
            if self.__allow_ranges and 'Range' in cherrypy.request.headers:

                #Get the ranges we where asked to deliver
                r1, r2 = self._parse_ranges()

                #If we where asked to skip the header
                if r1 == str(len(file_header)) and r2 == '':
                    write_header = False

                #Partial request, but asking for the entire file
                elif r1 == '0' and r2 == '':
                    write_header = True

                # We are not allowing other ranges
                else:
                    self._write_http_headers(0)
                    #raise cherrypy.HTTPError(416)

                #Set the appropriate headers
                r1 = int(r1)
                args = (r1, filesize-1, filesize)
                cherrypy.response.status = 206
                cherrypy.response.headers['Content-Range'] = 'bytes %d-%d/%d' % args
                self._write_http_headers(filesize-r1)

            #Just a normal (200) whole file request
            else:

                self._write_http_headers(filesize)
                write_header = True

        except:
            print 'HTTP Request exception yeahh'

        #If method was GET, write the file content
        if cherrypy.request.method.upper() == 'GET':

            if write_header:
                return self._write_content_generator(buf, filesize, file_header)
            else:
                return self._write_content_generator(buf, filesize)

    default._cp_config = {'response.stream': True}



class Root:

    image = None
    track = None


    def __init__(self, buffer_manager,  allowed_ips, on_stream_ended, allow_ranges=True):
        self.image = ImageDirectory()
        self.track = TrackDirectory(buffer_manager,
                           allowed_ips,
                           on_stream_ended,
                           allow_ranges
        )

    def publish_image(self, image):
        self.image.publish_image(image)

    def publish_track(self, track):
        self.track.publish_track(track)

    def get_published_track(self, track_id):
        return self.track.get_published_track(track_id)

    def cleanup(self):

        self.track._finish = True

    def join(self):
        self.track.event_close.wait()

class ProxyRunner(threading.Thread):
    ''' This class represent a Http proxy which will be a link between
    libspotify URI and xbmc URL. The target is to provided URL to xbmc so that it will
    be able to open Spotify files'''

    __server = None             # wsgiserver.CherryPyWSGIServer
    __buffer_manager = None     # XbmcSink
    __allowed_ips = None        # Localhost by default
    __cb_stream_ended = None    # Callback for stream ended
    __root = None

    def __init__(self,
                 buffer_manager,            # Buffer manager
                 host='localhost',          # The host
                 try_ports=range(8080,8090),# The range for ports
                 allowed_ips=['127.0.0.1'], # The allowed ip to access the server
                 allow_ranges=True):        # If we

        # Get the free port
        port = find_free_port(host, try_ports)

        # Init fields with parameters
        self.__buffer_manager = buffer_manager
        self.__allowed_ips = allowed_ips

        # Create base token
#         self.__base_token = create_base_token()

        # Create callbacks, shoudl I change it??
#         self.__cb_stream_ended = DynamicCallback()

        # Create the Root directory for the server
        self.__root = Root(buffer_manager, self.__allowed_ips,
            self.__cb_stream_ended, allow_ranges
        )
        app = cherrypy.tree.mount(self.__root, '/')

        #Don't log to the screen by default
        log = cherrypy.log
        log.access_file = ''
        log.error_file = ''
        log.screen = False
        log.access_log.addHandler(NullLogHandler())
        log.error_log.addHandler(NullLogHandler())

        # Create the server instance
        self.__server = wsgiserver.CherryPyWSGIServer((host, port), app)
        threading.Thread.__init__(self)

    def publish_image(self, image):
        self.__root.publish_image(image)

    def publish_track(self, track):
        self.__root.publish_track(track)

    def set_stream_end_callback(self, callback):
        self.__cb_stream_ended.set_callback(callback)


    def clear_stream_end_callback(self):
        self.__cb_stream_ended.clear_callback();

    def get_published_track(self, track_id):
        return self.__root.get_published_track(track_id)

    def stop_listener(self):
        print 'HTTP proxy: stop listener '

    def run(self):

        self.__server.start()

        # If the http server stop
        print 'HTTP proxy: run method finishing with state ' + str(cherrypy.engine.state)


    def get_port(self):
        return self.__server.bind_addr[1]


    def get_host(self):
        return self.__server.bind_addr[0]

    def get_buffer_manager(self):
        return self.__buffer_manager

    def stop(self):

        try:
            print 'http proxy: Cleaning up root server'
            self.__root.cleanup()
            self.__root.join()
            print 'http_proxy: root cleaned'

            print 'http proxy: stoping server'
            self.__server.stop()
            print 'http proxy: server stopped'
        except:
            print 'stop httpproxy exception'