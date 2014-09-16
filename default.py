'''
Copyright 2011 Mikel Azkolain
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
import xbmcaddon
import xbmcgui
from xbmc import log

import sys
import os
import traceback # For exception control
import gc


class addon_info:
    __addon_id__        = 'script.audio.xbmcSpotify'
    __addon__           = xbmcaddon.Addon(__addon_id__)
    __addon_path__      = __addon__.getAddonInfo('path')
    __addon_version__   = __addon__.getAddonInfo('version')



xbmc.log(msg='Create script.audio.xbmcSpotify v.' + addon_info.__addon_version__ +  ' addon.' + '' , level=xbmc.LOGNOTICE)

# Adding spotimcgui libraries
sys.path.insert(0, os.path.join(addon_info.__addon_path__, "resources/libs"))


# When main is imported twice there is a error on cffi/vengine_cpy.py
from core.main import main
from core.xbmcSpotify import XbmcSpotify

xbmcSpotify = None

# Try to read spotify_appkey.key
try:

    xbmcSpotify = XbmcSpotify()

    xbmc.log(msg='Created XBMCSpotify object', level=xbmc.LOGNOTICE)

    main(xbmcSpotify)

except (Exception) as ex:

    # TODO Inform about the exception
    dlg = xbmcgui.Dialog()
    dlg.ok(ex.__class__.__name__, str(ex))
    print 'default exception'
finally:

#     # Logout if neccesary
#     if (session.connection.state == ConnectionState.LOGGED_IN):
#         session.logout()
#         xbmc.log(msg='script.audio.xbmcSpotify logout ' , level=xbmc.LOGNOTICE)

    gc.enable()
    gc.collect()

    if xbmcSpotify is not None:
        xbmcSpotify.release()

    addon_info.__addon__ = None
    xbmc.log(msg='script.audio.xbmcSpotify Exit ' , level=xbmc.LOGNOTICE)


