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
import xbmcgui


def show_legal_warning(settings_obj):

    shown = settings_obj.get_legal_warning_shown()
    if not shown:
        settings_obj.set_legal_warning_shown(True)
        d = xbmcgui.Dialog()
        l1 = 'XbmcSpotify uses SPOTIFY(R) CORE but is not endorsed,'
        l2 = 'certified or otherwise approved in any way by Spotify.'

        d.ok('XbmcSpotify', l1, l2)