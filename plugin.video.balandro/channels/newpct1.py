# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] < 3:
    PY3 = False
else:
    PY3 = True
    unicode = str


import os, re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://atomixhq.one/'

clon_name = 'Atomix'

perpage = 20

color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')


CLONES = [
   ['atomix', 'https://atomixhq.one/', 'movie, tvshow', 'atomixhq.png'],
   ['descargas2020', 'https://descargas2020.net/', 'movie', 'descargas2020.jpg']
   ]

# ~ 'descargas2020'  prescindimos de series y buscar      sin proxies

# ~ Para una misma peli/serie no siempre hay uno sólo enlace, pueden ser múltiples. La videoteca de momento no está preparada para acumular
# ~ múltiples enlaces de un mismo canal, así que solamente se guardará el enlace del último agregado.

# ~ Las entradas en la web parecen manuales y pueden ser un poco dispares, lo cual dificulta interpretar título, idioma, calidades, etc.


def item_configurar_proxies(item, clon_host):
    plot = 'Es posible que para poder "utilizar/reproducir" este canal en alguno de sus clones necesites configurar algún proxy,'
    plot += ' ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + clon_host + ' necesitarás un proxy.'
    title = 'Configurar proxies a usar ... [COLOR plum](comunes en todos los clones)[/COLOR]'
    return item.clone( title = title, action = 'configurar_proxies', host = clon_host, folder=False, plot=plot, text_color='red' )

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, item.host)


def do_downloadpage(item, url, post=None):
    # ~ por si viene de enlaces guardados
    url = url.replace('https://pctmix.com/', host)
    url = url.replace('https://pctmix1.com/', host)
    url = url.replace('https://pctreload.com/', host)
    url = url.replace('https://pctreload1.com/', host)
    url = url.replace('https://maxitorrent.com/', host)
    url = url.replace('https://atomixhq.com/', host)

    # ~ intento sin proxies
    data = ''

    try:
       data = httptools.downloadpage(url, post=post).data
    except:
       pass

    if config.get_setting('proxies', item.channel, default=''):
        if not data:
            data = httptools.downloadpage_proxy('newpct1', url, post=post).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ... (búsquedas solo en ' + clon_name + ')', action = 'search', search_type = 'all' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    for clone in CLONES:
        if 'movie' in clone[2]:
            thumb = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', clone[3])
            url = clone[1]

            color = 'white'

            if config.get_setting('proxies', item.channel, default=''):
                color = color_list_proxies

            itemlist.append(item.clone( title = clone[0].capitalize(), action = 'mainlist_pelis_clon', url = url, thumbnail = thumb, text_color=color ))

    itemlist.append(item.clone( title = 'Buscar película ... (búsquedas solo en ' + clon_name + ')', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_pelis_clon(item):
    logger.info()
    itemlist = []

    item.category += '~' + item.title

    clon_host = item.url

    itemlist.append(item_configurar_proxies(item, clon_host))

    if not 'descargas2020' in clon_host:
        itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', url = item.url, search_type = 'movie', text_color='yellowgreen' ))

    enlaces = [
        ['Estrenos', 'estrenos-de-cine/'],
        ['En castellano', 'peliculas/'],
        ['En latino', 'peliculas-latino/'],
        # - ['Películas en Subtitulado', 'peliculas-vo/'],
        ['En HD', 'peliculas-hd/'],
        ['En HD FullBluRay', 'peliculas-hd/fullbluray-1080p/'],
        ['En HD BluRay', 'peliculas-hd/bluray-1080p/'],
        ['En HD MicroHD', 'peliculas-hd/microhd-1080p/'],
        ['En X264', 'peliculas-x264-mkv/'],
        ['En 4K UltraHD', 'peliculas-hd/4kultrahd/'],
        ['En 4K UHDremux', 'peliculas-hd/4k-uhdremux/'],
        ['En 4K UHDmicro', 'peliculas-hd/4k-uhdmicro/'],
        ['En 4K UHDrip', 'peliculas-hd/4k-uhdrip/'],
        ['En 4K Full UHD4K', 'peliculas-hd/full-uhd4k/'],
        ['En 4K Webrip', 'peliculas-hd/4k-webrip/'],
        ['En 3D', 'peliculas-3d/']
        ]

    if 'descargas2020' in item.url: 
        item.url += 'categoria/'
        enlaces = [
            ['Estrenos', 'estrenos-de-cine/'],
            ['En castellano', 'peliculas-castellano/'],
            ['En latino', 'peliculas-latino/'],
            ['En HD', 'peliculas-hd/'],
            ['En X264', 'peliculas-x264-mkv/'],
            ['En Rip', 'peliculas-rip/'],
            ['En 3D', 'peliculas-3d/']
            ]

    for enlace in enlaces:
        itemlist.append(item.clone( title = enlace[0], action = 'list_all', url = item.url + enlace[1], search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    for clone in CLONES:
        if 'tvshow' in clone[2]:
            thumb = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', clone[3])
            url = clone[1]

            color = 'white'

            if config.get_setting('proxies', item.channel, default=''):
                color = color_list_proxies

            itemlist.append(item.clone( title = clone[0].capitalize(), action = 'mainlist_series_clon', url = url, thumbnail = thumb, text_color=color ))

    itemlist.append(item.clone( title = 'Buscar serie ... (búsquedas solo en ' + clon_name + ')', action = 'search', search_type = 'tvshow' ))

    return itemlist


def mainlist_series_clon(item):
    logger.info()
    itemlist = []

    item.category += '~' + item.title

    clon_host = item.url

    itemlist.append(item_configurar_proxies(item, clon_host))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', url = item.url, search_type = 'tvshow', text_color='yellowgreen' ))

    enlaces = [
        ['Catálogo', 'series/'],
        ['En HD', 'series-hd/'],
        ['Subtituladas', 'series-vo/']
    ]

    if 'descargas2020' in item.url: 
        del enlaces[1:]

    for enlace in enlaces:
        itemlist.append(item.clone( title = enlace[0], action = 'list_all', url = item.url + enlace[1], search_type = 'tvshow' ))

    return itemlist


def limpiar_titulo(title, quitar_sufijo=''):
    prefijos = ['Ver en linea ', 'Ver online ', 'Descarga Gratis ', 'Descarga Serie HD ',
                'Descargar Estreno ', 'Descargar Pelicula ', 'Descargar torrent ']

    for prefijo in prefijos:
        if title.startswith(prefijo): title = title[len(prefijo):]

    if title.endswith(' en HD'): title = title.replace(' en HD', '')

    m = re.match(r"^Descargar (.*?) torrent gratis$", title)
    if m: title = m.group(1)

    m = re.match(r"^Descargar (.*?)gratis$", title)
    if m: title = m.group(1)

    m = re.match(r"^Descargar (.*?) torrent$", title)
    if m: title = m.group(1)

    m = re.match(r"^Pelicula en latino (.*?) gratis$", title)
    if m: title = m.group(1)

    if quitar_sufijo != '':
        title = re.sub(quitar_sufijo+'[A-Za-z .]*$', '', title)

    return title.strip()


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    quitar_sufijo = ''
    if '-3d/' in item.url: quitar_sufijo = ' 3D'

    data = do_downloadpage(item, item.url)

    patron = '<li>\s*<a href="([^"]+)" title="([^"]+)">\s*<img src="([^"]+)"[^>]+>'
    patron += '\s*<h2[^>]*>[^<]+</h2>\s*<span>([^<]+)</span>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    num_matches = len(matches)

    for url, title, thumb, quality in matches[item.page * perpage:]:
        if '/varios/' in item.url and quality in ['ISO','DVD-Screener']: continue # descartar descargas de pc, revistas pdf

        year = scrapertools.find_single_match(title, '\((\d{4})\)')
        if year: title = title.replace('(%s)' % year, '').strip()
        else: year = '-'

        title = limpiar_titulo(title, quitar_sufijo)
        titulo = title

        if item.search_type == 'tvshow':
            m = re.match(r"^(.*?) - (Temporada \d+) Capitulo \d*", title)
            if not m:
                m = re.match(r"^(.*?) - (Temporada \d+)", title)
            if m:
                title = m.group(1)
                titulo = '%s [%s]' % (title, m.group(2))

        if item.search_type == 'tvshow':
            itemlist.append(item.clone( action='episodios', url=url, title=titulo, thumbnail=thumb, qualities=quality, 
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))
        else:
            itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, qualities=quality, 
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if len(itemlist) >= perpage: break


    tmdb.set_infoLabels(itemlist)

    buscar_next = True
    if num_matches > perpage:
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, text_color='coral' ))
            buscar_next = False

    if buscar_next:
        next_page_link = scrapertools.find_single_match(data, '<li><a href="([^"]+)">Next</a>')
        if next_page_link:
            itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, page=0, text_color='coral' ))

    return itemlist


def tracking_all_episodes(item):
    itemlist = episodios(item)
    while itemlist[-1].title == '>> Página siguiente':
        itemlist = itemlist[:-1] + episodios(itemlist[-1])
    return itemlist


def extrae_show_s_e(title):
    show = ''
    season = ''
    episode = ''

    datos = scrapertools.find_single_match(title, '(.*?) (?:Temporada|Temp\.) (\d+) (?:Capitulo|Cap\.) (\d+)')
    if not datos: datos = scrapertools.find_single_match(title, '(.*?) (?:Temporada|Temp\.) (\d+) (?:Capitulos|Cap\.) (\d+)')

    if datos:
        show, season, episode = datos
    else:
        datos = scrapertools.find_single_match(title, '(.*?) - (?:Temporada|Temp\.) (\d+).*?\[Cap\.(\d+)\]')
        if datos:
            show, season, episode = datos
            if episode.startswith(season): episode = episode[len(season):]
        else:
            datos = scrapertools.find_single_match(title, '(.*?) Temporada[^0-9]*(\d+)[^C]*Capitulo[^0-9]*(\d+)')
            if datos:
                show, season, episode = datos

    if show.startswith('Serie '): show = show.replace('Serie ', '')

    return show.strip(), season, episode


def episodios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item, item.url)

    ul = scrapertools.find_single_match(data, '<ul class="buscar-list">(.*?)</ul>')
    matches = re.compile('<li[^>]*>(.*?)</li>', re.DOTALL).findall(ul)
    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')

        title = scrapertools.find_single_match(article, '<strong[^>]*>(.*?)</strong>')
        if title == '':
            title = scrapertools.find_single_match(article, '<h2[^>]*>(.*?)</h2>')

        title = scrapertools.htmlclean(title)

        show, season, episode = extrae_show_s_e(title)
        if show == '' or season == '' or episode == '': 
            if title != '':
                logger.debug('Serie/Temporada/Episodio no detectados! %s' % title)
            continue

        titulo = '%sx%s %s' % (season, episode, show)

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, 
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<li><a href="([^"]+)">Next</a>')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, text_color='coral' ))

    return itemlist


def extrae_idioma(txt):
    txt = txt.lower()
    if 'latino' in txt: return 'Lat'
    elif 'castellano' in txt: return 'Esp'
    elif 'español' in txt: return 'Esp'
    elif 'subtitulado espa' in txt: return 'Vose'
    elif 'subtitulado' in txt: return 'Vose'
    else: return 'VO'


def findvideos(item):
    logger.info()
    itemlist = []

    if not 'descargas2020' in item.url:
        item.url = item.url.replace('/descargar/', '/descargar/torrent/')

    data = do_downloadpage(item, item.url)

    # torrent
    calidad = ''
    idioma = ''

    h1 = scrapertools.find_single_match(data, '<h1[^>]*>(.*?)</h1>')
    h1 = scrapertools.htmlclean(h1.replace('\n', ''))

    datos = scrapertools.find_multiple_matches(h1, '\[([^\]]+)\]')
    if datos:
        calidad = datos[0]

        if len(datos) > 1: idioma = datos[1]
        if idioma:
            idioma = extrae_idioma(idioma)

        if idioma == 'VO' and len(datos) > 2: idioma = extrae_idioma(datos[2]) # a veces no es el segundo []
        if idioma == 'VO' and len(datos) > 3: idioma = extrae_idioma(datos[3]) # a veces no es el tercero []

    if not idioma:
        if '/peliculas-castellano/' in item.url: idioma = extrae_idioma('Castellano')
        elif '/peliculas-latino/' in item.url: idioma = extrae_idioma('Latino')
        elif '/peliculas-subtitulado/' in item.url: idioma = extrae_idioma('Subtitulado')

    tamano = scrapertools.find_single_match(data, '<strong>Size:</strong>([^<]+)</span>').strip()
    url = scrapertools.find_single_match(data, 'window.location.href\s*=\s*"([^"]+)')

    if url:
        if url.startswith('//'): url = 'https:' + url

        if url.startswith('/'): url = ''

        if url:
            if not url.endswith('.torrent'): url = url + '.torrent'

            itemlist.append(Item(channel = item.channel, action = 'play', title = '', url = url, server = 'torrent',
                                                         language = idioma, quality = calidad, other = tamano ))

    # streaming
    patron = '<div class="box2">([^<]+)</div>\s*<div class="box3">([^<]+)</div>\s*<div class="box4">([^<]+)</div>'
    patron += '\s*<div class="box5"><a href=\'([^\']+)[^>]+>([^<]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for servidor, idioma, calidad, url, tipo in matches:
        if url.startswith('javascript:'): continue

        servidor = servidor.replace('.com', '').replace('.net', '').replace('.org', '').replace('.co', '').replace('.cc', '').strip()
        servidor = servidor.replace('.to', '').replace('.tv', '').replace('.ru', '').replace('.io', '').replace('.eu', '').replace('.ws', '').strip()
        servidor = servertools.corregir_servidor(servidor)

        if not idioma:
            if '/peliculas-castellano/' in item.url: idioma = 'Castellano'
            elif '/peliculas-latino/' in item.url: idioma = 'Latino'
            elif '/peliculas-subtitulado/' in item.url: idioma = 'Subtitulado'

        itemlist.append(Item(channel = item.channel, action = 'play', title = '', url = url, server = servidor,
                                                     language = extrae_idioma(idioma), quality = calidad ))

    # Otros
    if not matches:
        patron = '<div class="box2">(.*?)</div>.*?<div class="box3">(.*?)</div>.*?<div class="box4">(.*?)</div>.*?<div class="box5">.*?'
        patron += "<a href='(.*?)'"

        matches = re.compile(patron, re.DOTALL).findall(data)
        for servidor, idioma, calidad, url in matches:
            if url.startswith('javascript:'): continue

            servidor = servidor.replace('.com', '').replace('.net', '').replace('.org', '').replace('.co', '').replace('.cc', '').strip()
            servidor = servidor.replace('.to', '').replace('.tv', '').replace('.ru', '').replace('.io', '').replace('.eu', '').replace('.ws', '').strip()
            servidor = servertools.corregir_servidor(servidor)

            if not idioma:
                if '/peliculas-castellano/' in item.url: idioma = 'Castellano'
                elif '/peliculas-latino/' in item.url: idioma = 'Latino'
                elif '/peliculas-subtitulado/' in item.url: idioma = 'Subtitulado'

            itemlist.append(Item(channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = extrae_idioma(idioma) ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.url.endswith('.torrent'):
        if '/atomtt.com/' in item.url:
            item.url = item.url.replace('/download/', '/download-link/').replace('.torrent', '')

            itemlist.append(item.clone( url = item.url, server = 'torrent' ))
        else:
            data = do_downloadpage(item, item.url)

            new_url = scrapertools.find_single_match(data, 'window.location.href.*?"(.*?)"')
            if new_url:
                itemlist.append(item.clone( url = new_url, server = 'torrent' ))
            else:
                itemlist.append(item.clone( url = item.url, server = 'torrent' ))
           
    else:
        itemlist.append(item.clone( url= item.url, server = item.server ))

    return itemlist


def busqueda(item):
    logger.info()
    itemlist = []

    post = 'categoryIDR=&categoryID=&idioma=&calidad=&ordenar=Fecha&inon=Descendente&s=%s&pg=%d' % (item.busca_texto, item.busca_pagina)
    data = do_downloadpage(item, item.url, post=post)

    data = data.replace('\\/', '/')

    dominio = item.url.replace('get/result/', '')

    patron = '"torrentID":"([^"]+)","torrentName":"([^"]+)","calidad":"([^"]+)","torrentDateAdded":"([^"]+)","torrentSize":"([^"]+)"'
    patron += ',"imagen":"([^"]+)","guid":"([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for tid, tname, tcali, tdate, tsize, timg, tguid in matches:
        url = dominio + tguid
        thumb = dominio + timg[1:]

        is_tvshow = '/serie' in url or '/descargar-serie' in url
        if (item.search_type == 'tvshow' and not is_tvshow) or (item.search_type == 'movie' and is_tvshow): continue
        if url in [it.url for it in itemlist]: continue

        title = unicode(tname, 'unicode-escape', 'ignore').encode('utf8')

        idioma = ''
        if 'Castellano]' in title: idioma = 'Esp'

        year = scrapertools.find_single_match(title, '\((\d{4})\)')
        if year: title = title.replace('(%s)' % year, '').strip()
        else: year = '-'

        title = re.sub('(\[[^\]]*\])', '', title).strip()

        if re.match('.*?temporada \d+ completa', title, flags=re.IGNORECASE): continue # descartar enlaces a temporadas completas

        titulo = title
        if item.search_type == 'tvshow':
            m = re.match(r"^(.*?) - (Temporada \d+) Capitulo \d*", title)
            if not m:
                m = re.match(r"^(.*?) - (Temporada \d+)", title)
            if m:
                title = m.group(1)
                titulo = '%s [%s]' % (title, m.group(2))

        if is_tvshow:
            sufijo = '' if item.search_type != 'all' else 'tvshow'

            itemlist.append(item.clone( action='episodios', url=url, title=titulo, thumbnail=thumb, languages=idioma, qualities=tcali, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))
        else:
            sufijo = '' if item.search_type != 'all' else 'movie'

            itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, languages=idioma, qualities=tcali, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if '"items":30,' in data:
        itemlist.append(item.clone( title='>> Página siguiente', action='busqueda', busca_pagina = item.busca_pagina + 1, text_color='coral' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        if item.url == '': item.url = host
        item.url += 'get/result/'

        item.busca_texto = texto.replace(" ", "+")
        item.busca_pagina = 1
        return busqueda(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
