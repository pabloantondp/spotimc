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

from cherrypy.process import servers
from core.settings import GuiSettingsReader

def find_free_port(host, port_list):
    ''' Method to find a free port in port_list'''
    for port in port_list:
        try:
            servers.check_port(host, port, .1)
            return port
        except:
            pass

    list_str = ','.join([str(item) for item in port_list])
    raise HTTPProxyError("Cannot find a free port. Tried: %s" % list_str)


def get_audio_buffer_size():
    '''Get the audio buffer size from settings.musicplayer.crossfade'''
    #Base buffer setting will be 10s
    buffer_size = 10

    try:
        reader = GuiSettingsReader()
        value = reader.get_setting('settings.musicplayer.crossfade')
        buffer_size += int(value)

    except:
        xbmc.log(
            'Failed reading crossfade setting. Using default value.',
            xbmc.LOGERROR
        )

    return buffer_size


__all__ = ["httpproxy", "audio","sink"]