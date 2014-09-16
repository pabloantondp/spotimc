'''
Copyright 2011 Mikel Azkolain

This file is part of Spotimc.

Spotimc is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Spotimc is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Spotimc.  If not, see <http://www.gnu.org/licenses/>.
'''


import xbmc
import xbmcgui
import time


class LoginCallbacks():
    __dialog = None

    def __init__(self, dialog):
        self.__dialog = dialog

    def logged_in(self, session, err):
        if err == 0:
            self.__dialog.do_close()

        else:
            self.__dialog.set_error(err)


class LoginWindow(xbmcgui.WindowXMLDialog):

    #Controld id's
    CODE_INPUT_USERNAME = 1101
    CODE_INPUT_PASS = 1102
    CODE_LOGIN_BUTTON = 1104
    CODE_CANCEL_BUTTON = 1105

    ID_LOGIN_CONTAINER = 1000
    ID_FIELDS_CONTAINER = 1100
    ID_LOADING_CONTAINER = 1200

    __xbmcSpotify = None
    __file = None
    __skin_dir = None
    __callbacks = None
    __vars = None

    __username = None
    __password = None

    __cancelled = None

    def __init__(self, file, scriptPath, skin_dir ):
        self.__file = file
        self.__skin_dir = skin_dir
        self.__cancelled = False


    def initialize(self, xbmcSpotify, vars):
        self.__xbmcSpotify = xbmcSpotify
        self.__vars = vars
 #         self.__callbacks = LoginCallbacks(self)
#         self.__session.add_callbacks(self.__callbacks)

    def onInit(self):

        #If there is a remembered user, show it's login name
        username = self.__xbmcSpotify.get_user_name()

        if username is not None:
            self._set_input_value(self.CODE_INPUT_USERNAME, username)

        #Show useful info if previous errors are present
        if self.__vars.has_var('login_last_error'):

            #If the error number was relevant...
            login_last_error = self.__vars.get_var('login_last_error')
            if login_last_error != 0:
                #Wait for the appear animation to complete
                time.sleep(0.2)

                self.set_error(self.__vars.get_var('login_last_error'), True)

    def onAction(self, action):
        pass
#
#         print action.getId()
#         if action.getId() in [9, 10, 92]:
#             self.__cancelled = True
#             self.do_close()

    def set_error(self, code, short_animation=False):
        messages = {
            ErrorType.ClientTooOld: 'Client is too old',
            ErrorType.UnableToContactServer: 'Unable to contact server',
            ErrorType.BadUsernameOrPassword: 'Bad username or password',
            ErrorType.UserBanned: 'User is banned',
            ErrorType.UserNeedsPremium: 'A premium account is required',
            ErrorType.OtherTransient: 'A transient error occurred.'
            'Try again after a few minutes.',
            ErrorType.OtherPermanent: 'A permanent error occurred.',
        }

        if code in messages:
            escaped = messages[code].replace('"', '\"')
            tmpStr = 'SetProperty(LoginErrorMessage, "{0}")'.format(escaped)
            xbmc.executebuiltin(tmpStr)
        else:
            tmpStr = 'SetProperty(LoginErrorMessage, "Unknown error.")'
            xbmc.executebuiltin(tmpStr)
            #self.setProperty('LoginErrorMessage', 'Unknown error.')

        #Set error flag
        xbmc.executebuiltin('SetProperty(IsLoginError,true)')

        #Animation type
        if short_animation:
            xbmc.executebuiltin('SetProperty(ShortErrorAnimation,true)')
        else:
            xbmc.executebuiltin('SetProperty(ShortErrorAnimation,false)')

        #Hide animation
        self.getControl(
            LoginWindow.ID_LOADING_CONTAINER).setVisibleCondition('false')

    def __get_input_value(self, controlID):
        c = self.getControl(controlID)
        return c.getLabel()

    def __set_input_value(self, controlID, value):
        c = self.getControl(controlID)
        c.setLabel(value)

    def do_login(self):
        '''Make the login into spotify'''
        # Get the value of the remember field
        remember_set = xbmc.getCondVisibility(
            'Skin.HasSetting(spotimc_session_remember)'
        )

        #SHow loading animation
        self.getControl(
            LoginWindow.ID_LOADING_CONTAINER).setVisibleCondition('true')

        status = self.__xbmcSpotify.login(self.__username,
                                          self.__password,
                                          remember_set == 1)

        #Unshow loading animation
        self.getControl(
            LoginWindow.ID_LOADING_CONTAINER).setVisibleCondition('false')

        # Return the error status
        return status

    def do_close(self):
        c = self.getControl(LoginWindow.ID_LOGIN_CONTAINER)
        c.setVisibleCondition("False")
        self.close()


    def onClick(self, controlID):
        '''Handler function for Login windows'''
        if controlID == self.CODE_INPUT_USERNAME:
            default = self.__get_input_value(controlID)
            kb = xbmc.Keyboard(default, "Enter username")
            kb.setHiddenInput(False)
            kb.doModal()
            if kb.isConfirmed():
                value = kb.getText()
                self.__username = value
                self.__set_input_value(controlID, value)

        elif controlID == self.CODE_INPUT_PASS:
            kb = xbmc.Keyboard("", "Enter password")
            kb.setHiddenInput(True)
            kb.doModal()
            if kb.isConfirmed():
                value = kb.getText()
                self.__password = value
                self.__set_input_value(controlID, "*" * len(value))

        elif controlID == self.CODE_LOGIN_BUTTON:
            status = self.do_login()

            # Check the status to proceed
            if (status != 0):
                #Clear error status
                xbmc.executebuiltin('SetProperty(IsLoginError,false)')
                self.do_close()

        elif controlID == self.CODE_CANCEL_BUTTON:
            self.__cancelled = True
            self.do_close()

    def is_cancelled(self):
        return self.__cancelled

    def onFocus(self, controlID):
        pass


class TextViewer(xbmcgui.WindowXMLDialog):
    label_id = 1
    textbox_id = 5
    close_button_id = 10

    __heading = None
    __text = None

    def onInit(self):
        #Not all skins implement the heading label...
        try:
            self.getControl(TextViewer.label_id).setLabel(self.__heading)
        except:
            pass

        self.getControl(TextViewer.textbox_id).setText(self.__text)

    def onClick(self, control_id):
        if control_id == 10:
            self.close()

    def initialize(self, heading, text):
        self.__heading = heading
        self.__text = text


def text_viewer_dialog(heading, text, modal=True):
    tv = TextViewer('DialogTextViewer.xml', __addon_path__)
    tv.initialize(heading, text)

    if modal:
        tv.doModal()
    else:
        tv.show()
