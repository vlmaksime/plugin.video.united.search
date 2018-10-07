# -*- coding: utf-8 -*-
# Module: gui
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcaddon
import pyxbmct

from simpleplugin import Plugin

plugin = Plugin()
_ = plugin.initialize_gettext()

class SupportedAddonsSettings(pyxbmct.AddonDialogWindow):

    def __init__(self, supported_addons):
        super(SupportedAddonsSettings, self).__init__(_('Supported Add-ons'))
        self._supported_addons = supported_addons

        self.setGeometry(700, 450, 9, 4)
        
        self.page = 0
        self.list = []
        self.set_active_controls()
        self.set_navigation()

        self.draw_page()

        # Connect a key action (Backspace) to close the window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

    def set_active_controls(self):
        
        # Button
        self.button_prev = pyxbmct.Button(_('Previous'))
        self.placeControl(self.button_prev, 8, 0)
        self.connect(self.button_prev, self.prev_page)

        # Button
        self.button_next = pyxbmct.Button(_('Next'))
        self.placeControl(self.button_next, 8, 1)
        self.connect(self.button_next, self.next_page)
        
        # Button
        self.button_close = pyxbmct.Button(_('Close'))
        self.placeControl(self.button_close, 8, 3)
        # Connect control to close the window.
        self.connect(self.button_close, self.close)


    def draw_page(self):
        for item in self.list:
            self.removeControl(item['btn'])

        self.list = []

        start_index = self.page*8
        for i, addon in enumerate(self._supported_addons[start_index:] ):
            radiobutton = pyxbmct.RadioButton(addon['name'])
            self.placeControl(radiobutton, i, 0, 1, 4)
            addon_object = xbmcaddon.Addon(addon['id'])
            if addon['learned']:
                united_search = (addon_object.getSetting('united_search_learned') == 'true')
            else:
                united_search = (addon_object.getSetting('united_search') == 'true')
            radiobutton.setSelected(united_search)
            self.connect(radiobutton, self.radio_update)

            self.list.append({'btn': radiobutton, 'id': addon['id'], 'status': united_search, 'learned': addon['learned']})
            if i >= 7: break

        self.vis_prev_btn = (self.page > 0)
        self.button_prev.setVisible(self.vis_prev_btn)
        self.vis_next_btn = (len(self._supported_addons[((self.page+1)*8):]) > 0)
        self.button_next.setVisible(self.vis_next_btn)

        self.set_page_navigation()

    def set_navigation(self):
        # Set navigation between controls
        self.button_prev.controlRight(self.button_next)
        self.button_next.controlRight(self.button_close)
        self.button_close.controlLeft(self.button_next)
        self.button_next.controlLeft(self.button_prev)

    def set_page_navigation(self):
        list_len = len(self.list)
        if list_len > 0:
            for i in range(list_len):
                cur_btn = self.list[i]['btn']
                if i == 0:
                    self.setFocus(cur_btn)
                if i > 0:
                    cur_btn.controlUp(self.list[i-1]['btn'])
                if i < (list_len-1):
                    cur_btn.controlDown(self.list[i+1]['btn'])
            last_btn = self.list[list_len-1]['btn']
        
            self.button_prev.controlUp(last_btn)
            self.button_next.controlUp(last_btn)
            self.button_close.controlUp(last_btn)

            if self.vis_next_btn:
                last_btn.controlDown(self.button_next)
            elif self.vis_prev_btn:
                last_btn.controlDown(self.button_prev)
            else:    
                last_btn.controlDown(self.button_close)
        else:
            self.setFocus(self.button_close)

    def radio_update(self):
        for item in self.list:
            is_selected = (item['btn'].isSelected() == 1)
            if is_selected != item['status']:
                item['status'] = is_selected
                addon_object = xbmcaddon.Addon(item['id'])
                if item['learned']:
                    addon_object.setSetting('united_search_learned', 'true' if item['status'] else 'false')
                else:
                    addon_object.setSetting('united_search', 'true' if item['status'] else 'false')

    def next_page(self):
        self.page += 1
        self.draw_page()

    def prev_page(self):
        self.page -= 1
        self.draw_page()
                
    def setAnimation(self, control):
        # Set fade animation for all add-on window controls
        control.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=500',),
                                ('WindowClose', 'effect=fade start=100 end=0 time=500',)])