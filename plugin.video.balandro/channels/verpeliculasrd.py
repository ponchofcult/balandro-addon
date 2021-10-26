# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'http://ver-peliculasrd.com/'

perpage = 25


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data,'>GÉNEROS DE PELÍCULAS<(.*?)<h2>AÑO DE LANZAMIENTO</h2>')

    matches = scrapertools.find_multiple_matches(bloque,'href="(.*?)".*?</ion-icon>(.*?)<span')

    for url, tit in matches:
        if url == '#': continue

        url = host + url
        tit = tit.strip()

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1919, -1):
        url = host + 'años/peliculas-' + str(x) + '/' + str(x) + '.html'

        itemlist.append(item.clone( title=str(x), url= url, action='list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<div class="item-temporada pull-left">(.*?)</a></div>').findall(data)

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')
        title = scrapertools.find_single_match(match, ' alt="(.*?)"').strip()
        if not title:
            title = scrapertools.find_single_match(match, '<div class="item-detail"><p>(.*?)</p>').strip()

        if not url or not title: continue

        year = scrapertools.find_single_match(match, '<span class="year text-center">(.*?)</span>')
        if year:
            title = title.replace(year, '').strip()
        else:
            year = '-'

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        thumb = host + thumb

        url = host + url

        itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail = thumb,
                                            contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if num_matches > perpage:
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, action='list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<li id="" class="tab-video(.*?)</a></li>')

    ses = 0

    for match in matches:
        ses += 1

        url = scrapertools.find_single_match(match, 'data-source="([^"]+)"')

        if url:
            if '/hqq.' in url or '/waaw.' in url or '/netu.' in url:
                continue

            qlty = scrapertools.find_single_match(match, 'data-quality=="([^"]+)"')

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            lng = 'Lat'
            if servidor == 'mega': lng = 'Vose'

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', server = servidor, url = url, quality = qlty, language = lng ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if not item.texbus in data:
        return itemlist

    matches = re.compile('<div class="item-temporada pull-left">(.*?)</a></div>').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')
        title = scrapertools.find_single_match(match, ' alt="(.*?)"').strip()
        if not title:
            title = scrapertools.find_single_match(match, '<div class="item-detail"><p>(.*?)</p>').strip()

        if not url or not title: continue

        if not item.texbus in title:
           if not item.texbus.capitalize() in title:
              if not item.texbus.upper() in title:
                  continue

        year = scrapertools.find_single_match(match, '<span class="year text-center">(.*?)</span>')
        if year:
            title = title.replace(year, '').strip()
        else:
            year = '-'

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        thumb = host + thumb

        url = host + url

        itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail = thumb,
                                            contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host
        item.texbus = texto.strip()
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

