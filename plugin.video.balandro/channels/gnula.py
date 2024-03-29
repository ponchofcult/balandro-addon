# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = "http://gnula.nu/"

url_estrenos = host + 'peliculas-online/lista-de-peliculas-online-parte-1/'
url_recomendadas = host + 'peliculas-online/lista-de-peliculas-recomendadas/'

IDIOMAS = {'VC': 'Esp', 'VL': 'Lat', 'VS': 'Vose', 'castellano': 'Esp', 'latino': 'Lat', 'vose': 'Vose'}

perpage = 15


def item_configurar_proxies(item):
    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' )

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)

def do_downloadpage(url, post=None):
    # ~ timeout
    timeout = 40

    if '/generos/' in url:
        timeout = 50

    # ~ data = httptools.downloadpage(url, post=post, timeout=timeout).data
    data = httptools.downloadpage_proxy('gnula', url, post=post, timeout=timeout).data
    return data


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = url_estrenos ))

    itemlist.append(item.clone( title = 'Recomendadas', action = 'list_all', url = url_recomendadas ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    itemlist.append(item_configurar_proxies(item))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'generos/lista-de-generos/')

    matches = re.compile('<td>\s*<strong>([^<]+)</strong>\s*\[<a href="([^"]+)" title="([^"]+)"', re.DOTALL).findall(data)
    for title, url, plot in matches:
        itemlist.append(item.clone( title=title, url=url, action='list_all', plot=plot ))

    matches = re.compile('<td>\s*<strong>([^<]+)</strong>\s*\[<a href="([^"]+)"', re.DOTALL).findall(data)
    for title, url in matches:
        if url in [it.url for it in itemlist]: continue # descartar repetidos

        itemlist.append(item.clone( title=title, url=url, action='list_all' ))

    return sorted(itemlist, key=lambda it: it.title)


def idiomas(item):
    logger.info()
    itemlist = []

    # Enlaces por idioma según las preferencias del usuario en servidores
    idio = {'Esp': ['Castellano', 'VC'], 'Lat': ['Latino', 'VL'], 'VO': ['Subtitulado', 'VS']}
    prefs = config.get_lang_preferences()
    prefs = sorted(prefs.items(), key=lambda p: p[1])

    for lg, num in prefs:
        if num == 0: continue
        itemlist.append(item.clone( title = '%s estrenos' % idio[lg][0], action = 'list_all', url = url_estrenos, filtro_lang = idio[lg][1] ))
        itemlist.append(item.clone( title = '%s recomendadas' % idio[lg][0], action = 'list_all', url = url_recomendadas, filtro_lang = idio[lg][1] ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)

    patron  = '<a class="Ntooltip" href="([^"]+)">([^<]+)<span><br[^<]+'
    patron += '<img src="([^"]+)"></span></a>(.*?)<br'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if item.filtro_lang: # reducir lista según idioma
        matches = list(filter(lambda m: '(%s)' % item.filtro_lang in m[3], matches))

    if item.filtro_search: # reducir lista según texto buscado
        buscado = item.filtro_search.lower().strip()
        if ' ' not in buscado:
            matches = list(filter(lambda m: buscado in m[1].lower(), matches))
        else:
            palabras = list(filter(lambda p: len(p) > 3, buscado.split(' '))) # descartar palabras demasiado cortas (la, de, los, etc)
            if len(palabras) == 0: return [] # No hay palabras a buscar

            def contiene(texto, palabras):
                found = False
                for palabra in palabras:
                    if palabra in texto: found = True; break
                return found

            matches = list(filter(lambda m: contiene(m[1].lower(), palabras), matches))

    for url, title, thumb, resto in list(matches)[item.page * perpage:]:
        year = scrapertools.find_single_match(url, '-(\d+)-online/$')
        spans = scrapertools.find_multiple_matches(resto, '<span style="[^"]+">([^<]+)</span>')
        langs = []; quality = ''
        for span in spans:
            if span.startswith('(') and span.endswith(')'):
                lg = span[1:-1]
                langs.append(IDIOMAS.get(lg, lg))
            elif len(langs) > 0:
                quality = span
                break

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, languages=', '.join(langs), qualities=quality,
                                    contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if not item.filtro_search and len(list(matches)) > (item.page + 1) * perpage:
        itemlist.append(item.clone( title=">> Página siguiente", page=item.page + 1, action='list_all', text_color='coral' ))

    return itemlist


def puntuar_calidad(txt):
    orden = ['CAM', 'TS', 'TS-HQ', 'WEB-S', 'HD-S', 'DVD-S', 'BR-S', 'HD-TC', 'HD-TV', 'DVD-R', 'HD-R', 'BR-R']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<em>([^<]+)</em></p>(.*?)<table[^>]*>(.*?)</table>', re.DOTALL).findall(data)
    if len(matches) == 0:
        patron = '<strong>Ver película online</strong> \[<span style="[^"]*">([^<]+)</span>\](.*?)<table[^>]*>(.*?)</table>'
        matches = re.compile(patron, re.DOTALL).findall(data)

    for opcion, iframes, tabla in matches:
        opcs = opcion.split(',')
        lang = opcs[1].strip().lower()
        quality = opcs[2].strip().upper()

        links = re.compile('<iframe width="[^"]+" height="[^"]+" src="([^"]+)', re.DOTALL).findall(iframes)
        if not links: links = re.compile('<iframe src="([^"]+)', re.DOTALL).findall(iframes)
        for url in links:
            if url.endswith('/soon') or url.startswith('http://soon.'): continue

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url,
                                  language = IDIOMAS.get(lang, lang), quality = quality ))

        links = re.compile('<a href="([^"]+)', re.DOTALL).findall(tabla)
        for url in links:
            if url.endswith('/soon') or url.startswith('http://soon.'): continue

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url,
                                  language = IDIOMAS.get(lang, lang), quality = quality, quality_num = puntuar_calidad(quality) ))

    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


# No hay buscador propio en la web, usan el buscador genérico de google en su site.
def search(item, texto):
    logger.info()
    try:
        item.filtro_search = texto

        item.url = url_estrenos
        itemlist = list_all(item)

        item.url = url_recomendadas
        itemlist2 = list_all(item)
        for it2 in itemlist2:
            if it2.url not in [it.url for it in itemlist]:
                itemlist.append(it2)

        return itemlist

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
