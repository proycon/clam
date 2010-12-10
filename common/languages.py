#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Webservice --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

LANGUAGENAMES = { #ISO-639-3
    'nld': u'Nederlands',
    'spa': u'Español',
    'cat': u'Català',
    'eng': u'English',
    'fra': u'Français',
    'ita': u'Italiano',
    'por': u'Português',
    'epo': u'Esperanto',
    'rus': u'Русский',
    'swe': u'Svenska',
    'nor': u'Norsk',
    'dan': u'Danish',
    'ara': u'عربية',
    'zho': u'中文',
}

def languagename(code):
    global LANGUAGENAMES
    if code in LANGUAGENAMES:
        return LANGUAGENAMES['code']
    else:
        return code
