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
import os

import xbmc
import xbmcgui

def check_addon_version(xbmcSpotify):
    '''Check if the last version executed is different than the current
    one '''
    last_run_version = xbmcSpotify.settings.get_last_run_version()

    #If current version is higher than the stored one...
    if xbmcSpotify.settings.__addon_version__ > last_run_version:
        xbmcSpotify.settings.set_last_run_version(xbmcSpotify.settings.__addon_version__)

        #Don't display the upgrade message if it's the first run
        if last_run_version != '':

            d = xbmcgui.Dialog()
            l1 = 'XbmcSpotify was updated since the last run.'
            l2 = 'Do you want to see the changelog?'

            if d.yesno('XbmcSpotify', l1, l2):
                file = xbmcSpotify.settings.get_addon_obj().getAddonInfo('changelog')
                changelog = open(file).read()
                dialogs.text_viewer_dialog('ChangeLog', changelog)

def check_dirs(xbmcSpotify):
    addon_data_dir = os.path.join(
        xbmc.translatePath('special://profile/addon_data'),
        xbmcSpotify.settings.__addon_id__
    )

    #Auto-create profile dir if it does not exist
    if not os.path.exists(addon_data_dir):
        os.makedirs(addon_data_dir)

    #Libspotify cache & settings
    sp_cache_dir = os.path.join(addon_data_dir, 'libspotify/cache')
    sp_settings_dir = os.path.join(addon_data_dir, 'libspotify/settings')

    if not os.path.exists(sp_cache_dir):
        os.makedirs(sp_cache_dir)

    if not os.path.exists(sp_settings_dir):
        os.makedirs(sp_settings_dir)

    return (addon_data_dir, sp_cache_dir, sp_settings_dir)

