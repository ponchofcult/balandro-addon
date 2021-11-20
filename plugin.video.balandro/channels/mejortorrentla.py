# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] < 3:
    import urlparse
else:
    import urllib.parse as urlparse


import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://mejortorrent.la/'

patron_domain = '(?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?(?:[^\.]+\.)?([\w|\-]+\.\w+)(?:\/|\?|$)'
patron_host = '((?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?(?:[^\.]+\.)?[\w|\-]+\.\w+)(?:\/|\?|$)'


def do_downloadpage(url, post=None, raise_weberror=True):
    if '/years/' in url:
        raise_weberror = False

    data = httptools.downloadpage(url, post=post, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'descargar-peliculas-completas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='Castellano', action='list_all', url=host + 'language/castellano/' ))
    itemlist.append(item.clone( title='Latino', action='list_all', url=host + 'language/latino/' ))
    itemlist.append(item.clone( title='Subtitulado', action='list_all', url=host + 'language/subtitulado/' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data,'>Genero<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque,'<a href="(.*?)".*?>(.*?)</a>')

    for url, tit in matches:
        if not url or not tit: continue

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all' ))

    itemlist.append(item.clone( action = 'list_all', title = 'Bélica', url = host + 'category/belica/' ))
    itemlist.append(item.clone( action = 'list_all', title = 'Documental', url = host + 'category/documental/' ))
    itemlist.append(item.clone( action = 'list_all', title = 'Histoia', url = host + 'category/historia/' ))
    itemlist.append(item.clone( action = 'list_all', title = 'Western', url = host + 'category/western/' ))

    return sorted(itemlist, key=lambda it: it.title)


def calidades(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='En Micro HD', url = host + 'quality/MicroHD-1080p/', action='list_all' ))
    itemlist.append(item.clone( title='En HD', url = host + 'quality/hd/', action='list_all' ))
    itemlist.append(item.clone( title='En BD Rip', url = host + 'quality/bdrip/', action='list_all' ))
    itemlist.append(item.clone( title='En Dual 1080', url = host + 'quality/dual-1080p/', action='list_all' ))
    itemlist.append(item.clone( title='En BluRay 720', url = host + 'quality/bluRay-720p/', action='list_all' ))
    itemlist.append(item.clone( title='En BluRay 1080', url = host + 'quality/bluRay-1080p/', action='list_all' ))
    itemlist.append(item.clone( title='En 4K UHD', url = host + 'quality/4k-uhd/', action='list_all' ))
    itemlist.append(item.clone( title='En 3D', url = host + 'quality/3d/', action='list_all' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1965, -1):
        url = host + 'years/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<div class="col-6 col-sm-4 col-lg-3 col-xl-2">(.*?)<span class="card__rate">', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="([^"]+)')
        title = scrapertools.find_single_match(match, ' alt="([^"]+)')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'data-src="([^"]+)')
        qlty = scrapertools.find_single_match(match, '<li>(.*?)</li>').strip()

        lang = scrapertools.find_single_match(match, '</ul>.*?<li>(.*?)</li>').strip()
        if lang == 'Cas': lang = 'Esp'
        elif lang == 'Lat': lang = 'Lat'
        elif lang == 'Sub': lang = 'Vose'
        elif lang == 'VO': lang = 'VO'

        tipo = 'tvshow' if '/series/' in url else 'movie'

        sufijo = '' if item.search_type != 'all' else tipo

        if '/series/' in url:
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            if tipo == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, languages=lang, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': '-'} ))
        else:
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            if tipo == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, languages=lang, qualities=qlty, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', action='list_all', url=next_page_link, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('data-target="#collapse-.*?<span>(.*?)</span>', re.DOTALL).findall(data)

    for title in matches:
        numtempo = title.replace('Temporada ', '').strip()

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.title = title
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = numtempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = numtempo, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    perpage = 50

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<span>' + str(item.title) + '</span>(.*?)</tbody>')

    matches = re.compile('data-season="(.*?)".*?data-serie="(.*?)".*?href="(.*?)"', re.DOTALL).findall(bloque)

    for season, episode, url in matches[item.page * perpage:]:
        if item.contentSeason:
           if not str(item.contentSeason) == season: continue

        titulo = '%sx%s %s' % (season, episode, item.contentSerieName)

        itemlist.append(item.clone( action='findvideos', title = titulo, url = url,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = episode ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > (item.page + 1) * perpage:
        itemlist.append(item.clone( title=">> Página siguiente", action="episodios", page=item.page + 1, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<tbody>(.*?)</tbody>', re.DOTALL).findall(data)

    ses = 0

    for match in matches:
        ses += 1

        url = scrapertools.find_single_match(match, ' href="([^"]+)')

        if url:
            qlty = scrapertools.find_single_match(match, '<td>(.*?)</td>')
            if '<b>Notice</b>' in qlty: qlty = ''

            lang = scrapertools.find_single_match(match, '</td>.*?<td>(.*?)</td>')
            if lang == 'Castellano': lang = 'Esp'
            elif lang == 'Latino': lang = 'Lat'
            elif lang == 'Subtitulado': lang = 'Vose'
            elif lang == 'Version Original': lang = 'VO'

            peso = scrapertools.find_single_match(match, '<td class="hide-on-mobile">.*?<td class="hide-on-mobile">(.*?)</td>')

            servidor = 'torrent'
            srv = ''

            if url.endswith(".torrent"): pass
            elif url.startswith('magnet:'): srv = 'magnet'
            else:
                servidor = 'directo'
                if '/acortalink.me/' in url: srv = 'acortalink'
                elif '/mega.' in url: srv = 'mega'
                else:
                    srv = servertools.get_server_from_url(url)
                    srv = servertools.corregir_servidor(srv)

            other = peso + ' ' + srv

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = lang, quality = qlty,
                                  other = other ))

    if not itemlist:
       url = ''

       servidor = 'torrent'
       other = ''

       if item.url.endswith(".torrent"): url = item.url
       elif item.url.startswith('magnet:'):
          url = item.url
          other = 'magnet'
       else:
           servidor = 'directo'
           if '/acortalink.me/' in item.url:
              url = item.url
              other = 'acortalink'
           elif '/mega.' in item.url:
              url = item.url
              other = 'mega'
           else:
              other = servertools.get_server_from_url(item.url)
              other = servertools.corregir_servidor(other)

       if url:
           itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.server == 'torrent':
        itemlist.append(item.clone( url = item.url, server = 'torrent' ))
    else:
        if 'magnet' in item.other:
            itemlist.append(item.clone( url = item.url, server = 'torrent' ))
            return itemlist

        if 'mega' in item.other:
            try:
                url_id = item_url.split('#')[1]
                file_id = url_id.split('!')[1]
            except:
                file_id = ''

            if file_id:
                get = ''
                post = {'a': 'g', 'g': 1, 'p': file_id}

                if '/#F!' in page_url:
                    get = '&n=' + file_id
                    post = {'a': 'f', 'c': 1, 'r': 0}
 
                import random
                nro = random.randint(0, 0xFFFFFFFF)

                from core import jsontools
                api = 'https://g.api.mega.co.nz/cs?id=%d%s' % (nro, get)
                resp = httptools.downloadpage(api, post=jsontools.dump([post]), headers={'Referer': 'https://mega.nz/'})

                logger.info("check-00-quehay: %s" % resp.data)

        servidor = servertools.get_server_from_url(item.url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, item.url)

        if servidor and servidor != 'directo':
            itemlist.append(item.clone( url = url, server = servidor ))
            return itemlist

        if servidor == 'directo':
            host_torrent = host[:-1]
            url_base64 = decode_url_base64(url, host_torrent)

            if url_base64.startswith('magnet:'):
               itemlist.append(item.clone( url = url_base64, server = 'torrent' ))

            elif url_base64.endswith(".torrent"):
               itemlist.append(item.clone( url = url_base64, server = 'torrent' ))

    return itemlist


def decode_url_base64(url, host_torrent):
    host_list = [
       'acortaenlace.com',
       'short-link.one',
       'mediafire.com'
       ]

    domain = scrapertools.find_single_match(url, patron_domain)

    url_base64 = url

    if len(url_base64) > 1 and not 'magnet:' in url_base64 and not '.torrent' in url_base64:
        patron_php = 'php(?:#|\?\w=)(.*?$)'

        if scrapertools.find_single_match(url_base64, patron_php): url_base64 = scrapertools.find_single_match(url_base64, patron_php)

        try:
            for x in range(20):
                url_base64 = base64.b64decode(url_base64).decode('utf-8')
        except:
            if url_base64 and url_base64 != url: url_base64 = url_base64.replace(' ', '%20')

            if not url_base64: url_base64 = url

            if url_base64.startswith('magnet'): return url_base64
            
            if domain and domain in str(host_list):
                url_base64_bis = sorted_urls(url_base64, url_base64, host_torrent)
            else:
                url_base64_bis = sorted_urls(url, url_base64, host_torrent)

            domain_bis = scrapertools.find_single_match(url_base64_bis, patron_domain)

            if domain_bis: domain = domain_bis

            if url_base64_bis != url_base64: url_base64 = url_base64_bis
                
    if not domain: domain = 'default'

    if host_torrent and host_torrent not in url_base64 and not url_base64.startswith('magnet') and domain not in str(host_list):
        url_base64 = urlparse.urljoin(host_torrent, url_base64)

        if url_base64 != url:
            host_name = scrapertools.find_single_match(url_base64, patron_host)
            url_base64 = re.sub(host_name, host_torrent, url_base64)

    return url_base64


def sorted_urls(url, url_base64, host_torrent):
    sortened_domains = {
            'acortalink.me': ['linkser=uggcf%3A%2F%2Flrfgbeerag.arg', "TTTOzBmk\s*=\s*'(.*?)'", 14, 8, False], 
            'short-link.one': ['linkser=uggcf%3A%2F%2Fzntargcryvf.pbz', "TTTOzBmk\s*=\s*'(.*?)'", 14, 8, False], 
            'mediafire.com': [None, '(?i)=\s*"Download file"\s*href="([^"]+)"\s*id\s*=\s*"downloadButton"', 0, 0, False]
            }
   
    domain = scrapertools.find_single_match(url, patron_domain)

    if sortened_domains.get(domain, False) == False or not url_base64 or url_base64.startswith('magnet'): return url_base64

    host_name = scrapertools.find_single_match(url, patron_host)

    if host_name and not host_name.endswith('/'): host_name += '/'

    data_new = httptools.downloadpage(url, headers={'Referer': host_torrent}, raise_weberror=False).data
    data_new = re.sub(r'\n|\r|\t', '', data_new)

    if sortened_domains[domain][1] and scrapertools.find_single_match(data_new, sortened_domains[domain][1]):
        url_base64 = scrapertools.find_single_match(data_new, sortened_domains[domain][1])
        if url_base64.startswith('magnet') or url_base64.startswith('http'): return url_base64

    post = sortened_domains[domain][0]

    headers = {'Content-type': 'application/x-www-form-urlencoded', 'Referer': url}

    data_new = httptools.downloadpage(host_name, post=post, headers=headers, raise_weberror=False).data
    data_new = re.sub(r'\n|\r|\t', '', data_new)

    if data_new :
        key = scrapertools.find_single_match(data_new, sortened_domains[domain][1])
        if not key or not sortened_domains[domain][1]: return url_base64
    
    try:
        from lib import pyberishaes

        url_base64_bis = None
        url_base64_bis = pyberishaes.GibberishAES(string=url_base64, pass_=key, Nr=sortened_domains[domain][2], Nk=sortened_domains[domain][3], Decrypt=sortened_domains[domain][4])

        if url_base64_bis.result and (url_base64_bis.result.startswith('magnet') or url_base64_bis.result.startswith('http')):
            url_base64 = url_base64_bis.result
        else:
            logger.error('Error Result pyberishaes: ' + url_base64_bis.result)
    except:
        import traceback
        logger.error('Error Key pyberishaes: ' + key)
        logger.error(traceback.format_exc())

    if not (url_base64.startswith('magnet') or url_base64.startswith('http')): key = ''

    if not key: return sorted_urls(url, url_base64, host_torrent)

    return url_base64


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'buscar/?buscar=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
