# -*- coding: utf-8 -*-
# Module: default
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import urllib
import simplejson as json

from simpleplugin import Plugin

plugin = Plugin()
_ = plugin.initialize_gettext()

_supported_addons = []

@plugin.action()
def root( params ):

    return plugin.create_listing(_list_root(), content='files')

def _list_root():
    items = [ {'action': 'search',           'label': _('New Search')},
              {'action': 'search_results',   'label': _('Last Search')},
              {'action': 'search_history',   'label': _('Search History')},
              {'action': 'supported_addons', 'label': _('Supported Add-ons')} ]

    for item in items:
        url = plugin.get_url(action=item['action'])

        list_item = {'label':  item['label'],
                     'url':    url,
                     'icon':   plugin.icon,
                     'fanart': plugin.fanart}
        yield list_item

@plugin.action()
def search( params ):
    succeeded = False

    keyword = params.get('keyword')
    if not keyword:
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(_('Search'))
        kbd.doModal()
        if kbd.isConfirmed():
            keyword = kbd.getText()

    if keyword:
        succeeded = True

        load_supported_addons()

        listing = []
        total_addons = len(_supported_addons)

        progress = xbmcgui.DialogProgress()
        progress.create(_('Search'), _('Please wait. Searching...'))
        for i, addon in enumerate(_supported_addons):
            result_string = '%s: %d' % (_('Search results'), len(listing))
            progress.update(100 * i / total_addons, line2=addon['name'], line3=result_string)
            if (progress.iscanceled()):
                #succeeded = False
                break

            path = []
            path.append('plugin://')
            path.append(addon['id'])
            path.append('/?usearch=True&')
            path.append(addon['us_command'])
            path.append(urllib.quote(keyword))

            directory = ''.join(path)

            addon_name = addon['name']
            for file in _get_directory(directory):
                item_data = {'file': file,
                             'addon_name': addon_name}
                listing.append(item_data)

        progress.close()

        if succeeded:
            with plugin.get_storage('__history__.pcl') as storage:
                history = storage.get('history', [])

                item_content = {'keyword': keyword.decode('utf-8'), 'listing': listing}
                history.insert(0, item_content)

                if len(history) > plugin.history_length:
                    history.pop(-1)
                storage['history'] = history

        if succeeded and len(listing) == 0:
            succeeded = False
            show_info_notification(_('Nothing found!'))

    if succeeded:
        update_listing = params.get('update_listing', 'False')
        url = plugin.get_url(action='search_results', item=0, update_listing=update_listing)
        xbmc.executebuiltin('Container.Update("%s")' % url)

def _get_directory( directory ):
    request = {'jsonrpc': '2.0',
               'method': 'Files.GetDirectory',
               'params': {'properties': ['title', 'genre', 'year', 'rating', 'runtime', 'plot', 'file', 'art', 'sorttitle'],
                          'directory': directory,
                          'media': 'files'},
                'id': 1
               }
    response = xbmc.executeJSONRPC(json.dumps(request))

    j = json.loads(response)
    result = j.get('result')
    if result:
        for file in result.get('files', []):
            yield file

@plugin.action()
def search_results( params ):

    item = int(params.get('item', '0'))
    update_listing = (params.get('update_listing') == 'True')

    with plugin.get_storage('__history__.pcl') as storage:
        history = storage.get('history', [])

    if len(history) >= (item + 1):
        item_content = history[item]
        listing = item_content.get('listing', [])
        keyword = item_content.get('keyword')
    else:
        listing = []
        keyword = ''

    return plugin.create_listing(_list_serach_result(keyword, listing), content='movies', update_listing=update_listing, sort_methods=[27])

def _list_serach_result( keyword, video_list ):
    if keyword:
        url = plugin.get_url(action='search', update_listing=True, keyword=keyword.encode('utf-8'))
        list_item = {'label':       _('Repeat Search'),
                     'info':        { 'video': {'sorttitle': '!*_repeat_search'} },
                     'is_folder':   False,
                     'is_playable': False,
                     'url':         url,
                     'icon':        plugin.icon,
                     'fanart':      plugin.fanart}
        yield list_item
        
    for video_item in video_list:
        file = video_item.get('file')
        if file:
            yield _make_item(file, video_item['addon_name'], keyword)
        else:
            yield video_item
    
def _make_item( video_item, addon_name, keyword ):
    sorttitle = video_item.get('sorttitle')
    if not sorttitle:
        sorttitle = video_item.get('title')
    if not sorttitle:
        sorttitle = video_item['label']
    
    sorttitle = sorttitle.strip()
    if keyword and keyword.lower() in sorttitle.lower():
		sorttitle = '*' + sorttitle

    label = video_item['label'].strip()
    if plugin.add_name_lable:
        if plugin.add_name_lable_position == 0:
            label = '[%s] %s' % (addon_name, label)
        else:
            label = '%s [%s]' % (label, addon_name)
    
    plot = video_item.get('plot')
    if plugin.add_name_plot:
        if plot:
            plot = '[B]%s[/B]\n\n%s' % (addon_name, plot)
        else: 
            plot = '[B]%s[/B]' % (addon_name)
        
    item_info = {'label': label,
                 'info':  { 'video': {'year':      video_item.get('year', 0),
                                      #'title':     video_item.get('title',''),
                                      'sorttitle': sorttitle,
                                      'genre':     video_item.get('genre', ''),
                                      'rating':    video_item.get('rating', 0),
                                      'duration':  video_item.get('runtime', ''),
                                      'plot':      plot} },
                 'url':         video_item.get('file'),
                 'is_playable': (video_item['filetype'] == 'file'),
                 'is_folder':   (video_item['filetype'] == 'directory'),
                 'art':         { 'poster': video_item['art'].get('poster') },
                 'fanart':      video_item['art'].get('fanart'),
                 'thumb':       video_item['art'].get('thumb')}

    return item_info
    
@plugin.action()
def search_history( params ):
    return plugin.create_listing(_list_search_history(), content='files')

def _list_search_history():
    history_length = plugin.history_length

    with plugin.get_storage('__history__.pcl') as storage:
        history = storage.get('history', [])

        if len(history) > history_length:
            history[history_length - len(history):] = []
            storage['history'] = history

    for i, item in enumerate(history):
        list_item = {'label':  '%s [%d]' % (item['keyword'], len(item['listing'])),
                     'url':    plugin.get_url(action='search_results', item=i),
                     'icon':   plugin.icon,
                     'fanart': plugin.fanart}
        yield list_item
    
@plugin.action()
def supported_addons( params ):
    load_supported_addons(True)

    listing = []
    for addon in _supported_addons:
        status = '[V]' if addon['united_search'] else '[X]'
        label = '[B]%s[/B] %s' % (status, addon['name'])
        #change_status_title = _('Disable') if addon['united_search'] else _('Enable')

        #context_menu = [(_('Settings'), 'RunPlugin(%s)' % plugin.get_url(action='addon_open_settings', id=addon['id'])),
        #                (change_status_title, 'RunPlugin(%s)' % plugin.get_url(action='addon_change_status', id=addon['id'])),]
        item_info = {'label':       label,
                     'info':        { 'video': {'plot':      addon['description'],
                                                'sorttitle': addon['name']} },
                     'url':         plugin.get_url(action='addon_change_status', id=addon['id']),
                     'is_folder':   False,
                     'is_playable': False,
                     #'context_menu': context_menu,
                     'replace_items': True,
                     'fanart':       addon['fanart'],
                     'thumb':        addon['thumbnail']}
        listing.append(item_info)

    return plugin.create_listing(listing, content='files', sort_methods=[27])

@plugin.action()
def addon_open_settings( params ):
    addon_object = xbmcaddon.Addon(params['id'])
    addon_object.openSettings()

@plugin.action()
def addon_change_status( params ):
    addon_object = xbmcaddon.Addon(params['id'])
    united_search = addon_object.getSetting('united_search')

    addon_object.setSetting('united_search', 'false' if united_search == 'true' else 'true')

    xbmc.executebuiltin('Container.Refresh')

def show_info_notification(text):
    xbmcgui.Dialog().notification(plugin.addon.getAddonInfo('name'), text)

def load_supported_addons( all_supported=False ):
    del_unified_name = plugin.del_unified_name

    for addon in _get_video_addons():
        addon_object = xbmcaddon.Addon(addon['addonid'])
        united_search = addon_object.getSetting('united_search')
        if united_search == 'true' or all_supported and united_search == 'false':
            us_command = addon_object.getSetting('us_command')
            if not us_command:
                us_command = 'mode=search&keyword='

            addon_name = addon['name']
            if del_unified_name and addon_name.find('(UnifiedSearch)') > 0:
                addon_name = addon_name.replace('(UnifiedSearch)','').strip()

            addon_info = {'id':             addon['addonid'],
                          'name':           addon_name,
                          'us_command':     us_command,
                          'united_search': (united_search == 'true'),
                          'description':    addon['description'],
                          'thumbnail':      addon['thumbnail'],
                          'fanart':         addon['fanart']}

            _supported_addons.append(addon_info)

def _get_video_addons():
    request = {'jsonrpc': '2.0',
               'method': 'Addons.GetAddons',
               'params': {'type': 'xbmc.addon.video',
                          'content': 'video',
                          'enabled': True,
                          'properties': ['name', 'fanart', 'thumbnail', 'description']},
                'id': 1
               }
    response = xbmc.executeJSONRPC(json.dumps(request))

    j = json.loads(response)
    result = j.get('result')
    if result:
        for addon in result.get('addons', []):
            yield addon

if __name__ == '__main__':

    plugin.run()