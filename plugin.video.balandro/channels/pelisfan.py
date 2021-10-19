# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://pelisfan.com/'

perpage = 20


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/release-year/' in url:
        raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone ( title = 'Catálogo', action = 'list_all', url = host + 'movies/', search_type = 'movie' ))

    itemlist.append(item.clone ( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone ( title = 'Por año', action = 'anios', search_type = 'movie' ))
    itemlist.append(item.clone ( title = 'Por país', action = 'paises', search_type = 'movie' ))

    itemlist.append(item.clone ( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = [
       ('accion', 'Acción'),
       ('action-adventure', 'Action & Adventure'),
       ('animacion', 'Animación'),
       ('aventura', 'Aventura'),
       ('belica', 'Bélica'),
       ('ciencia-ficcion', 'Ciencia ficción'),
       ('comedia', 'Comedia'),
       ('crimen', 'Crimen'),
       ('documental', 'Documental'),
       ('drama', 'Drama'),
       ('familia', 'Familia'),
       ('fantasia', 'Fantasía'),
       ('misterio', 'Misterio'),
       ('musica', 'Música'),
       ('romance', 'Romance'),
       ('sci-fi-fantasy', 'Sci-Fi & Fantasy'),
       ('suspense', 'Suspense'),
       ('terror', 'Terror'),
       ('western', 'Western')
    ]

    for opc, tit in opciones:
        itemlist.append(item.clone( title=tit, url= host + 'genero/' + opc + '/', action = 'list_all' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1979, -1):
        itemlist.append(item.clone( title = str(x), url = host + 'release-year/' + str(x) + '/', action = 'list_all' ))

    return itemlist


def paises(item):
    logger.info()
    itemlist=[]

    web_paises = [
       ['ar', 'Argentina'],
       ['au', 'Australia'],
       ['at', 'Austria'],
       ['be', 'Belgium'],
       ['bo', 'Bolivia'],
       ['br', 'Brazil'],
       ['bg', 'Bulgaria'],
       ['ca', 'Canada'],
       ['cl', 'Chile'],
       ['cn', 'China'],
       ['co', 'Colombia'],
       ['cr', 'Costa Rica'],
       ['hr', 'Croatia'],
       ['cu', 'Cuba'],
       ['cz', 'Czech Republic'],
       ['dk', 'Denmark'],
       ['do', 'Dominican Republic'],
       ['ec', 'Ecuador'],
       ['sv', 'El Salvador'],
       ['ee', 'Estonia'],
       ['fi', 'Finland'],
       ['fr', 'France'],
       ['de', 'Germany'],
       ['gt', 'Guatemala'],
       ['hn', 'Honduras'],
       ['hk', 'Hong Kong SAR China'],
       ['hu', 'Hungary'],
       ['ie', 'Ireland'],
       ['it', 'Italy'],
       ['jp', 'Japan'],
       ['mx', 'Mexico'],
       ['nl', 'Netherlands'],
       ['ni', 'Nicaragua'],
       ['no', 'Norway'],
       ['pa', 'Panama'],
       ['py', 'Paraguay'],
       ['pe', 'Peru'],
       ['pl', 'Poland'],
       ['pt', 'Portugal'],
       ['pr', 'Puerto Rico'],
       ['ro', 'Romania'],
       ['ru', 'Russia'],
       ['es', 'Spain'],
       ['se', 'Sweden'],
       ['ch', 'Switzerland'],
       ['sy', 'Syria'],
       ['gb', 'United Kingdom'],
       ['us', 'United States'],
       ['uy', 'Uruguay'],
       ['ve', 'Venezuela']
       ]

    url = host + 'country/'

    for x in web_paises:
        itemlist.append(item.clone( title = x[1], url = url + str(x[0]) + '/', action = 'list_all' ))

    return itemlist


def list_all(item): 
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<div data-movie-id=(.*?)</div></div>', re.DOTALL).findall(data)

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(match, ' href="([^"]+)"')
        title = scrapertools.find_single_match(match, '<h2>(.*?)</h2>')
        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, '<img data-original=="([^"]+)"')

        year = scrapertools.find_single_match(match, 'rel="tag">(.*?)</a>')
        if year:
            title = title.replace('(' + year + ')', '')
        else:
            year = '-'

        qlty = scrapertools.find_single_match(match, '<div class="jtip-quality">(.*?)</div>')
        if qlty == 'Adixxy+':
            qlty = 'HD 720'
        elif qlty == 'Adixxy+HD':
            qlty = 'HD 1080'

        plot = scrapertools.find_single_match(match, '<<p>(.*?)</a>')

        itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail = thumb, qualities = qlty,
                                    contentType = 'movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    buscar_next = True
    if num_matches > perpage:
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, action='list_all', text_color='coral' ))
            buscar_next = False

    if buscar_next:
        if itemlist:
            next_page = scrapertools.find_single_match(data, "<li class='active'>.*?href='(.*?)'")
            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone (url = next_page, page = 0, title = '>> Página siguiente', action = 'list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<div id="tab(.*?)".*?src="(.*?)"')

    ses = 0

    for opt, url in matches:
        ses += 1

        qlty = scrapertools.find_single_match(data, '<a href="#tab' + str(opt)+ '">(.*?)</a>')

        if 'hqq' in url or 'waaw' in url or 'netu' in url: continue
        elif 'openload' in url: continue
        elif 'powvideo' in url: continue
        elif 'streamplay' in url: continue
        elif 'rapidvideo' in url: continue
        elif 'streamango' in url: continue
        elif 'verystream' in url: continue
        elif 'vidtodo' in url: continue

        if url.endswith('.htm'): url = url + 'l'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        itemlist.append(Item( channel = item.channel, action = 'play', title = '', server = servidor, url = url, quality = qlty ))

    # ~ downloads

    if '<div id="lnk list-downloads">' in data:
        bloque = scrapertools.find_single_match(data, '<div id="lnk list-downloads">(.*?)<script>')

        matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?<span class="lang_tit">(.*?)</span>.*?<span class="lnk lnk-dl" >(.*?)</span>')

        for url, lang, qlty in matches:
            ses += 1

            if '1fichier' in url: continue
            elif 'ul.to' in url: continue
            elif 'katfile' in url: continue
            elif 'rapidgator' in url: continue

            if lang == 'Spanish':
                lang = 'Esp'

            url = url.replace('//mrdhan.com/', '//dutrag.com/')

            if url.endswith('.htm'): url = url + 'l'

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', server = servidor, url = url,
                                  language = lang, quality = qlty, other = 'D' ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

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
