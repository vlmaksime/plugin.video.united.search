# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import urllib
import json
import pyxbmct
import threading

import gui

from simpleplugin import Plugin

plugin = Plugin('plugin.video.united.search')
_ = plugin.initialize_gettext()

def _get_directory_threaded( us, directory ):
    us.result = []
    for item in us.get_directory(directory):
        us.result.append(item)

class UnitedSearch(object):
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
                    return

                addon_name = addon['name']
                if addon['learned']:
                    directory_list = self.__get_learned_directory(addon['us_command'], keyword)
                else:
                    us_command = addon['us_command']
                    if us_command.find('?')>=0:
                        path_tpl = 'plugin://{0}/{1}{2}&usearch=True'
                    else:
                        path_tpl = 'plugin://{0}/?{1}{2}&usearch=True'
                        
                    directory = path_tpl.format(addon['id'], us_command, urllib.quote(keyword))

                    directory_list = self.get_directory(directory)
                
                for file in directory_list:
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

    def get_directory( self, directory ):
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

    def __get_learned_directory( self, directory, keyword ):
        t = threading.Thread(target=_get_directory_threaded, args = (self, directory))
        t.start()

        params = {'text': keyword,
                  'done': True
                  }
        
        self.__wait_keyboard(params)
        t.join(10)

        return self.result
                
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
            united_search_learned = addon_object.getSetting('united_search_learned')
            use_us = (united_search or united_search_learned)
            united_search_flag = False
            learned_flag = False
            if united_search:
                united_search_flag = (united_search == 'true')
                us_command = addon_object.getSetting('us_command')
                if not us_command:
                    us_command = 'mode=search&keyword='
            elif united_search_learned:
                learned_flag = True
                united_search_flag = (united_search_learned == 'true')
                us_command = addon_object.getSetting('usl_command')
            
            if use_us:
                addon_name = addon['name']
                if del_unified_name and addon_name.find('(UnifiedSearch)') > 0:
                    addon_name = addon_name.replace('(UnifiedSearch)','').strip()

                addon_info = {'id':            addon['addonid'],
                              'name':          addon_name,
                              'us_command':    us_command,
                              'united_search': united_search_flag,
                              'learned':       learned_flag,
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
        
    def add_learned_addon( self, path ):
        if path[0:9] == 'plugin://':
            addonid = path[9:].split('/')[0]
            addon_object = xbmcaddon.Addon(addonid)
            united_search = addon_object.getSetting('united_search')
            plugin.log_error(united_search)
            if united_search in ['true','false']:
                self.__show_notification(_('Addon has native support'))
            elif self.__sheck_learned_directory(path):
                addon_object.setSetting('united_search_learned', 'true')
                addon_object.setSetting('usl_command', path)
                self.__show_notification(_('Added search support'))
            else:
                self.__show_notification(_('Missing keyboard call'))
        else:
            self.__show_notification(_('This is not addon item'))
            
    def __wait_keyboard(self, params):

        count = 0
        max_count = 50
        sleep_time = 100
        wait_keyboard = True

        while wait_keyboard and count <= max_count:
            window_name = xbmc.getInfoLabel('Window.Property(xmlfile)')
            request = None
            if window_name == 'DialogKeyboard.xml':
                wait_keyboard = False
                if params['done']:
                    request = {'jsonrpc': '2.0',
                               'method': 'Input.SendText',
                               'params': params,
                               'id': 1
                               }
                else:
                    request = {'jsonrpc': '2.0',
                               'method': 'Input.Back',
                               'id': 1
                               }
                    

            elif window_name == 'DialogSelect.xml':
                request = {'jsonrpc': '2.0',
                           'method': 'Input.Select',
                           'id': 1
                           }

            response = xbmc.executeJSONRPC(json.dumps(request))
            count += 1
            xbmc.sleep(sleep_time)
            
        return not wait_keyboard

    def __sheck_learned_directory( self, directory ):
        t = threading.Thread(target=_get_directory_threaded, args = (self, directory))
        t.start()

        params = {'text': '',
                  'done': False
                  }
        
        result = self.__wait_keyboard(params)
        t.join(10)

        return result
                
