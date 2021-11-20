﻿# -*- coding: utf-8 -*-

import re

from platformcode import logger, config, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools

host = 'https://www.pelitorrent.com/'

IDIOMAS = {'Español': 'Esp', 'Latino': 'Lat', 'Subtitulado': 'Vose'}


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    url = url.replace('/www.tupelihd.com/', '/www.pelitorrent.com/')
    url = url.replace('/senininternetin.com/', '/www.pelitorrent.com/')

    data = httptools.downloadpage(url, post=post, headers=headers).data
    return data


def mainlist(item):
    return mainlist_pelis(item)

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    return itemlist

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'torrents-peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'estrenos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades',  search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action='alfabetico', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def estrenos(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Estrenos 2021', action = 'list_all', url = host + 'peliculas/estrenos-2021/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Estrenos 2020', action = 'list_all', url = host + 'peliculas/estrenos-2020/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Estrenos 2019', action = 'list_all', url = host + 'peliculas/estrenos-2019/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Estrenos 2018', action = 'list_all', url = host + 'peliculas/estrenos-2018/', search_type = 'movie' ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'En 4K UHD Micro', action = 'list_all', url = host + 'peliculas/4k-uhdmicro/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'En 4K UHD Rip', action = 'list_all', url = host + 'peliculas/4k-uhdrip/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'En Bluray MicroHD', action = 'list_all', url = host + 'peliculas/bluray-microhd/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'En BDremux', action = 'list_all', url = host + 'peliculas/bdremux/', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, 'Generos</span></a>\s*<ul class="sub-menu">(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)"><i[^>]*></i><span>([^<]+)')
    for url, title in matches:
        if '/estrenos/' in url: continue

        itemlist.append(item.clone( action='list_all', title=title, url=url ))

    if item.search_type == 'movie':
        itemlist.append(item.clone( action = 'list_all', title = 'Cine Clásico', url = host + 'peliculas/cine-clasico/' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1938, -1):
        itemlist.append(item.clone( title=str(x), url= host + 'release/' + str(x) + '/', action='list_all' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    for letra in '#ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        letras = letra.lower()
        if letras == '#': letras = '0-9'

        url = host + 'letters/' + letras + '/'

        itemlist.append(item.clone( action = 'list_all', title = letra, url = url ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1(.*?)<h3')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')

        title = scrapertools.find_single_match(article, '<div class="Title">(.*?)</div>')
        if not title: title = scrapertools.find_single_match(article, '<h2 class=.*?>(.*?)</h2>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        year = scrapertools.find_single_match(article, '<span class="year">(\d+)</span>')
        if not year: year = '-'

        qlty_lang = scrapertools.find_single_match(article, '<span class="calidad">(.*?)</span')
        if '|' in qlty_lang:
            qlty = qlty_lang.split('|')[0].strip()
            lang = qlty_lang.split('|')[1].strip()
        else:
            qlty = qlty_lang
            lang = ''

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, qualities=qlty, languages=IDIOMAS.get(lang, lang),
                                    contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '>SIGUIENTE<' in data:
            next_page = scrapertools.find_single_match(data, '<a class="page-link current".*?<a class="page-link".*?href="(.*?)"')

            if next_page:
               itemlist.append(item.clone (url = next_page, title = '>> Página siguiente', action = 'list_all', text_color='coral' ))

    return itemlist


def puntuar_calidad(txt):
    txt = txt.replace(' ', '').replace('-', '').lower()

    orden = [
	'cam',
	'hdcam',
	'webscreener',
	'tsscreener',
	'hdtcscreener',
	'brscreener',
	'hdtv',
	'hdtv720p',
	'microhd',
	'dvdrip',
	'bluraymicrohd',
	'blurayrip',
	'hdrip',
	'hd720',
	'hd1080',
	'4kuhdmicro',
	'4kuhdrip'
	]

    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def normalize_server(server):
    server = servertools.corregir_servidor(server)
    if server:
        server = server.replace('.com', '').replace('.net', '').replace('.to', '')

    if server == 'uploaded': return 'uploadedto'
    return server


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<section class="section player(.*?)</section>')

    matches = scrapertools.find_multiple_matches(bloque, ' href="#options-(.*?)".*?class="server">(.*?)</span>')

    ses = 0

    # enlaces
    for opt, server_idioma in matches:
        ses += 1

        s_i = scrapertools.find_single_match(server_idioma, '(.*?)-(.*?)$')
        if not s_i: continue

        servidor = s_i[0].strip().lower()
        if not servidor: continue
        elif servidor == 'youtube': continue

        lang = s_i[1].strip()

        url = scrapertools.find_single_match(bloque, '<div id="options-' + opt + '.*?<iframe src="(.*?)"')
        if not url: url = scrapertools.find_single_match(bloque, '<div id="options-' + opt + '.*?<iframe data-src="(.*?)"')
        if not url: continue

        servidor = normalize_server(servidor)
		
        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, other = 'e',
                              language = IDIOMAS.get(lang, lang) ))

    # descargas
    if '>Descargar Torrent<' in data:
        bloque = scrapertools.find_single_match(data, '<table>(.*?)</table>')

        matches = re.compile('<td><span class="num">(.*?)</tr>', re.DOTALL).findall(bloque)

        for match in matches:
            ses += 1

            url = scrapertools.find_single_match(match, ' href="([^"]+)"')
            if url.startswith('//'): url = 'https:' + url
            if not url: continue

            servidor = scrapertools.find_single_match(match, 'class=".*?">(.*?)</a>').strip()
            if not servidor: continue

            lang = scrapertools.find_single_match(match, '</td>.*?<td>(.*?)</td>').strip()
            qlty = scrapertools.find_single_match(match, '<td><span>(.*?)</span>').strip()

            other = ''
            if servidor.lower() != 'torrent':
                other = 't'
                servidor = ''

            servidor = normalize_server(servidor)

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, other = other,
                                  language = IDIOMAS.get(lang, lang), quality = qlty, quality_num = puntuar_calidad(qlty) ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    item.url = item.url.replace('&#038;', '&').replace(' class=', '')

    url = ''

    if item.other:
        if not item.url.startswith == host:
            return itemlist

    if item.server == 'torrent':
        itemlist.append(item.clone( url = item.url, server = 'torrent' ))
        return itemlist

    elif item.other == 't':
        url = httptools.downloadpage(item.url, only_headers = True, follow_redirects = False).headers.get('location')

        if url:
            if url.endswith('.torrent'):
               itemlist.append(item.clone( url = url, server = 'torrent' ))
               return itemlist

    else:
        data = do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"')

    if url:
       if item.server == 'torrent':
            itemlist.append(item.clone(url = url, server = item.server))
       else:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            if servidor and servidor != 'directo':
                url = servertools.normalize_url(servidor, url)
                itemlist.append(item.clone( url = url, server = servidor ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
