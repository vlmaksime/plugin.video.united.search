# -*- coding: utf-8 -*-
# Module: context_search
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcgui
import re

from unitedsearch import UnitedSearch, plugin

_ = plugin.initialize_gettext()

us = UnitedSearch()

def main():
    Label       = xbmc.getInfoLabel('ListItem.Label')
    Title       = xbmc.getInfoLabel('ListItem.Title')
    TVShowTitle = xbmc.getInfoLabel('ListItem.TVShowTitle')
    ChannelName = xbmc.getInfoLabel('ListItem.ChannelName')

    if TVShowTitle:
        keyword = TVShowTitle
    elif Title:
        keyword = Title
    else:
        keyword = Label

    keyword = re.sub(r'\([^>]*\)', '', keyword)
    keyword = re.sub(r'\[[^>]*\]', '', keyword)
    keyword = keyword.strip()

    keywords = keyword.split('/')
    plugin.log_error(keywords)
    if len(keywords) > 1:
        for i, cur_keyword in enumerate(keywords):
            keywords[i] = cur_keyword.strip()

        keywords.insert(0, keyword)
        ret = xbmcgui.Dialog().select(_('Select Title'), keywords)
        if ret > 0:
            keyword = keywords[ret]
        else:
            keyword = ''

    cont_edit_keyword = plugin.get_setting('cont_edit_keyword')

    if keyword and cont_edit_keyword:
        kbd = xbmc.Keyboard()
        kbd.setDefault(keyword)
        kbd.setHeading(_('Search'))
        kbd.doModal()
        if kbd.isConfirmed():
            keyword = kbd.getText()
        else:
            keyword = ''

    if keyword:
        params = {'keyword': keyword,
                  'only_search': 'True',
                  }
        us.search(params)

        url = plugin.get_url(action='search_results', item=0)
        if ChannelName:
            xbmc.executebuiltin("ActivateWindow(videos, %s)" % (url))
        else:
            xbmc.executebuiltin('Container.Update("%s")' % url)


if __name__ == '__main__':
    main()