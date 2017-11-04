# -*- coding: utf-8 -*-
# Module: context_learn
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmc

from unitedsearch import UnitedSearch
from unitedsearch import plugin

_ = plugin.initialize_gettext()

us = UnitedSearch()

def main():
    path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    us.add_learned_addon(path)

if __name__ == '__main__':
    main()