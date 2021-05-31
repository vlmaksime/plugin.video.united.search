# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import resources.lib.gui as gui
from resources.lib.unitedsearch import UnitedSearch
from resources.lib.unitedsearch import plugin

_ = plugin.initialize_gettext()

us = UnitedSearch()

@plugin.action()
def root( params ):
    plugin.create_directory(__list_root(), content='files')

def __list_root():
    items = [ {'action': 'search',           'label': _('New Search'), 'is_folder': False},
              {'action': 'search_results',   'label': _('Last Search')},
              {'action': 'search_history',   'label': _('Search History')},
              {'action': 'supported_addons', 'label': _('Supported Add-ons'), 'is_folder': False}]

    for item in items:
        url = plugin.get_url(action=item['action'])

        list_item = {'label':  item['label'],
                     'url':    url,
                     'is_folder': item.get('is_folder', True),
                     'icon':   plugin.icon,
                     'fanart': plugin.fanart}
        yield list_item

@plugin.action()
def search( params ):
    return us.search(params)

@plugin.action()
def search_results( params ):
    return us.search_results(params)

@plugin.action()
def search_history( params ):
    return us.search_history(params)

@plugin.action()
def supported_addons( params):
    window = gui.SupportedAddonsSettings(us.get_supported_addons())
    window.doModal()
    del window

if __name__ == '__main__':
    plugin.run()