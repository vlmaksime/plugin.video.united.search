# -*- coding: utf-8 -*-
# Module: unitedsearch
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import urllib
import simplejson as json
import pyxbmct

import resources.lib.gui as gui

from simpleplugin import Plugin

plugin = Plugin()
_ = plugin.initialize_gettext()

class UnitedSearch:
    def __init__( self ):
        self.__load_supported_addons()

    def search( self, params ):
        succeeded = False
        only_search = (params.get('only_search', 'False') == 'True')

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

            listing = []
            enabled_addons = self.__get_enabled_addons()
            total_addons = len(enabled_addons)

            progress = xbmcgui.DialogProgress()
            progress.create(_('Search'), _('Please wait. Searching...'))
            for i, addon in enumerate(enabled_addons):
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
                for file in self.__get_directory(directory):
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
                #succeeded = False
                self.__show_notification(_('Nothing found!'))

        if succeeded and not only_search:
            update_listing = (params.get('update_listing', 'False') == 'True')
            url = plugin.get_url(action='search_results', item=0, update_listing=update_listing)
            xbmc.executebuiltin('Container.Update("%s")' % url)

    def __get_directory( self, directory ):
        request = {'jsonrpc': '2.0',
                   'method': 'Files.GetDirectory',
                   'params': {'properties': ['title', 'genre', 'year', 'rating', 'runtime', 'plot', 'file', 'art', 'sorttitle', 'originaltitle'],
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

    def search_results( self, params ):

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

        return plugin.create_listing(self.__list_serach_result(keyword, listing), content='movies', update_listing=update_listing, sort_methods=[27], category=keyword)

    def __list_serach_result( self, keyword, video_list ):
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
                yield self.__make_item(file, video_item['addon_name'], keyword)
            else:
                yield video_item

    def __make_item( self, video_item, addon_name, keyword ):
        sorttitle = video_item.get('sorttitle')
        originaltitle = video_item.get('originaltitle')
        if not sorttitle:
            sorttitle = video_item.get('title')
        if not sorttitle:
            sorttitle = video_item['label']

        sorttitle = sorttitle.strip()
        if keyword and (keyword.lower() in sorttitle.lower() or originaltitle and keyword.lower() in originaltitle.lower()):
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
                                          'sorttitle':  sorttitle,
                                          'originaltitle': video_item.get('originaltitle', ''),
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

    def search_history( self, params ):
        return plugin.create_listing(self.__list_search_history(), content='files', category=_('Search History'))

    def __list_search_history( self ):
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

    def __show_notification( self, text ):
        xbmcgui.Dialog().notification(plugin.addon.getAddonInfo('name'), text)

    def __load_supported_addons( self ):
        del_unified_name = plugin.del_unified_name

        self.__supported_addons = []

        for addon in self.__get_video_addons():
            addon_object = xbmcaddon.Addon(addon['addonid'])
            united_search = addon_object.getSetting('united_search')
            if united_search:
                us_command = addon_object.getSetting('us_command')
                if not us_command:
                    us_command = 'mode=search&keyword='

                addon_name = addon['name']
                if del_unified_name and addon_name.find('(UnifiedSearch)') > 0:
                    addon_name = addon_name.replace('(UnifiedSearch)','').strip()

                addon_info = {'id':             addon['addonid'],
                              'name':           addon_name,
                              'us_command':     us_command,
                              'united_search': (united_search == 'true')
                              }

                self.__supported_addons.append(addon_info)

    def __get_video_addons( self ):
        request = {'jsonrpc': '2.0',
                   'method':  'Addons.GetAddons',
                   'params':  {'type': 'xbmc.addon.video',
                               'content': 'video',
                               'enabled': True,
                               # 'properties': ['name', 'fanart', 'thumbnail', 'description']
                               'properties': ['name']
                               },
                   'id': 1
                   }
        response = xbmc.executeJSONRPC(json.dumps(request))

        j = json.loads(response)
        result = j.get('result')
        if result:
            for addon in result.get('addons', []):
                yield addon

    def __get_enabled_addons( self ):
        list = []
        for addon in self.__supported_addons:
            if addon['united_search']:
                list.append(addon)
        return list

    def get_supported_addons( self ):
        return self.__supported_addons