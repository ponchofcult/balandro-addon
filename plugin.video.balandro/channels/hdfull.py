# -*- coding: utf-8 -*-

import sys

PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str

import re, base64, xbmcgui

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, servertools, tmdb
from lib import balandroresolver


dominios = ['https://new.hdfull.one/', 'https://hdfull.one/', 'https://hdfull.vip/']

host = config.get_setting('dominio', 'hdfull', default=dominios[0])

ant_hosts = ['https://www2.hdfull.cx/', 'https://hdfull.sh/', 'https://hdfull.ch/', 
             'https://hdfull.im/', 'https://hdfull.in/', 'https://hdfull.pro/',
             'https://hdfull.la/', 'https://hdfull.tv/', 'https://hd-full.cc/',
             'https://hdfull.me/', 'https://hdfullcdn.cc/']

perpage = 20


class login_dialog(xbmcgui.WindowDialog):
    def __init__(self):
        avis = True
        if config.get_setting('hdfull_username', 'hdfull', default=False): 
            if config.get_setting('hdfull_password', 'hdfull', default=False):
                if config.get_setting('hdfull_login', 'hdfull', default=False):
                    avis = False

        if avis:
            self.login_result = False
            platformtools.dialog_ok("Recomendación Balandro - HdFull", '[COLOR yellow]Sugerimos crear una nueva cuenta para registrarse en la web, no deberiais indicar ninguna de vuestras cuentas personales.[/COLOR]', 'Para más detalles al respecto, acceda a la Ayuda, apartado Uso, Información dominios que requieren registrase.')

        self.background = xbmcgui.ControlImage(250, 150, 800, 355, filename=config.get_thumb('ContentPanel'))
        self.addControl(self.background)
        self.icon = xbmcgui.ControlImage(265, 220, 225, 225, filename=config.get_thumb('hdfull', 'thumb', 'channels'))
        self.addControl(self.icon)
        self.username = xbmcgui.ControlEdit(530, 320, 400, 120, 'Indicar su usuario: ', font='font13', textColor='0xDD171717', focusTexture=config.get_thumb('button-focus'), noFocusTexture=config.get_thumb('black-back2'))

        self.addControl(self.username)
        if platformtools.get_kodi_version()[1] >= 18:
            self.password = xbmcgui.ControlEdit(530, 320, 400, 120, 'Indicar la contraseña: ', font='font13', textColor='0xDD171717', focusTexture=config.get_thumb('button-focus'), noFocusTexture=config.get_thumb('black-back2'))
        else:
            self.password = xbmcgui.ControlEdit(530, 320, 400, 120, 'Indicar la contraseña: ', font='font13', textColor='0xDD171717', focusTexture=config.get_thumb('button-focus'), noFocusTexture=config.get_thumb('black-back2'), isPassword=True)

        self.buttonOk = xbmcgui.ControlButton(588, 460, 125, 25, 'Confirmar', alignment=6, focusTexture=config.get_thumb('button-focus'), noFocusTexture=config.get_thumb('black-back2'))
        self.buttonCancel = xbmcgui.ControlButton(720, 460, 125, 25, 'Cancelar', alignment=6, focusTexture=config.get_thumb('button-focus'), noFocusTexture=config.get_thumb('black-back2'))
        self.addControl(self.password)
        self.password.setVisible(True)
        self.password.controlUp(self.username)
        self.addControl(self.buttonOk)
        self.password.controlDown(self.buttonOk)
        self.username.setLabel('Indicar su usuario: ')
        if int(platformtools.get_kodi_version()[1]) >= 18:
            self.password.setType(xbmcgui.INPUT_TYPE_PASSWORD, 'Indicar la contraseña: ')

        self.password.setLabel('Indicar la contraseña: ')
        self.setFocus(self.username)
        self.username.controlUp(self.buttonOk)
        self.username.controlDown(self.password)
        self.buttonOk.controlUp(self.password)
        self.buttonOk.controlDown(self.username)
        self.buttonOk.controlRight(self.buttonCancel)
        self.buttonOk.controlLeft(self.buttonCancel)
        self.addControl(self.buttonCancel)
        self.buttonCancel.controlRight(self.buttonOk)
        self.buttonCancel.controlLeft(self.buttonOk)
        self.username.setPosition(500, 210)
        self.username.setWidth(500)
        self.username.setHeight(50)
        self.password.setPosition(500, 300)
        self.password.setWidth(500)
        self.password.setHeight(50)

        self.doModal()

        if self.username.getText() and self.password.getText():
            config.set_setting('hdfull_username', self.username.getText(), 'hdfull')
            config.set_setting('hdfull_password', self.password.getText(), 'hdfull')
            config.set_setting('hdfull_login', True, 'hdfull')
            self.login_result = True

    def onControl(self, control):
        control = control.getId()
        if control in range(3000, 30010):
            self.close()


def do_make_login_logout(url, post=None):
    # ~ data = httptools.downloadpage(url, post=post, raise_weberror=False).data
    data = httptools.downloadpage_proxy('hdfull', url, post=post, raise_weberror=False).data

    if 'id="captcha-bypass"' in data:
        platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]Dominio hidden CAPTCHA[/B][/COLOR]')
        return ''

    return data


def login(item):
    logger.info()

    status = config.get_setting('hdfull_login', 'hdfull', default=False)

    domain = config.get_setting('dominio', 'hdfull', default=dominios[0])

    username = config.get_setting('hdfull_username', 'hdfull', default='')
    password = config.get_setting('hdfull_password', 'hdfull', default='')

    data = ''

    if domain:
        if domain in dominios:
            if not config.get_setting('dominio', 'hdfull'):
                config.set_setting('dominio', domain, 'hdfull')

            if username:
                if password:
                    data = do_make_login_logout(domain)
                    if not data: return False
        else:
            platformtools.dialog_notification(config.__addon_name, '[COLOR yellowgreen]HdFull Falta configurar Dominio[/COLOR]')
            return False

    user = scrapertools.find_single_match(data, '<a href="[^"]+" class="tour-join2 join">([^<]+)<\/a>')

    if user:
        if username:
            if username in user:
                if not status:
                    config.set_setting('hdfull_login', True, 'hdfull')
                if not item:
                    platformtools.dialog_notification(config.__addon_name, '[COLOR chartreuse]HdFull Login correcto[/COLOR]')

                platformtools.itemlist_refresh()
                return True

    if not username or not password:
        login = login_dialog()
        if not login.login_result: return False

        if not item:
            if not domain:
                config.set_setting('dominio', dominios[0], 'hdfull')
            else:
                if not domain in dominios:
                   config.set_setting('dominio', dominios[0], 'hdfull')

            platformtools.dialog_notification(config.__addon_name, '[COLOR yellow]HdFull Credenciales guardadas[/COLOR]')
            return False

    username = config.get_setting('hdfull_username', 'hdfull', default='')
    password = config.get_setting('hdfull_password', 'hdfull', default='')

    url = '%slogin' %(domain)

    data = do_make_login_logout(url)

    sid = scrapertools.find_single_match(data, '__csrf_magic.*?value="(.*?)"')
    if sid:
        post = {'__csrf_magic': sid, 'username': username, 'password': password, 'action': 'login'}
        data = do_make_login_logout(url, post=post)

        if 'Bienvenido %s' % username in data or "<script>window.location='/'" in data or "<script>window.location=''" in data:
            platformtools.dialog_notification(config.__addon_name, '[COLOR chartreuse]HdFull Login correcto[/COLOR]')
            if not status:
                config.set_setting('hdfull_login', True, 'hdfull')

            platformtools.itemlist_refresh()
            return True

    post = {'username': username, 'password': password}

    data = do_make_login_logout(url, post=post)
    jdata = jsontools.load(data)

    if jdata:
        try:
            if jdata.get('status') == "OK":
                if not status:
                    config.set_setting('hdfull_login', True, 'hdfull')

                platformtools.itemlist_refresh()
                return True
        except:
            pass

    platformtools.dialog_notification(config.__addon_name, '[COLOR red]HdFull Login incorrecto[/COLOR]')
    return False


def logout(item):
    logger.info()

    domain = config.get_setting('dominio', 'hdfull', default=dominios[0])

    url = "%slogout" %(domain)

    data = do_make_login_logout(url)

    config.set_setting('hdfull_login', False, 'hdfull')

    platformtools.dialog_notification(config.__addon_name, '[COLOR chartreuse]HdFull Sesión cerrada[/COLOR]')

    platformtools.itemlist_refresh()

    return 


def item_configurar_dominio(item):
    plot = 'Este canal tiene varios posibles dominios. Si uno no te funciona puedes probar con los otros antes de intentarlo con proxies.'
    return item.clone( title = 'Configurar dominio a usar ...', action = 'configurar_dominio', folder=False, plot=plot, text_color='yellowgreen' )

def configurar_dominio(item):
    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])
    num_dominio = dominios.index(dominio) if dominio in dominios else 0
    ret = platformtools.dialog_select('Dominio a usar HdFull', dominios, preselect=num_dominio)
    if ret == -1: return False

    if not dominio == dominios[ret]:
        if config.get_setting('hdfull_login', 'hdfull', default=False):
            logout(item)
            platformtools.itemlist_refresh()

    config.set_setting('dominio', dominios[ret], 'hdfull')
    return True


def item_configurar_proxies(item):
    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + dominio + ' necesitarás un proxy.'
    return item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' )

def configurar_proxies(item):
    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, dominio)


def do_downloadpage(url, post=None, referer=None):
    domain = config.get_setting('dominio', 'hdfull', default=dominios[0])

    # ~ por si viene de enlaces guardados posteriores
    if url.startswith('/'):  # ~ solo v. 2.0.0
        url = domain + url[1:]

    for ant in ant_hosts:
        url = url.replace(ant, domain)

    headers = {}

    if referer:
        headers = {'Referer': referer}
    else:
        headers = {'Referer': domain}
 
    # ~ data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=False).data
    data = httptools.downloadpage_proxy('hdfull', url, post=post, headers=headers, raise_weberror=False).data

    if '<div id="popup_login_result"></div>' in data:
        if not config.get_setting('hdfull_login', 'hdfull', default=False):
            platformtools.dialog_notification(config.__addon_name, '[COLOR yellow][B]HdFull Debe iniciar Sesión[/B][/COLOR]')

        result = login('')
        if result == True:
            return do_downloadpage(url, post=post, referer=referer)

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    if not config.get_setting('hdfull_login', 'hdfull', default=False):
        itemlist.append(item.clone( title = '[COLOR chartreuse]Iniciar sesión[/COLOR]', action = 'login' ))

        itemlist.append(item_configurar_dominio(item))
        itemlist.append(item_configurar_proxies(item))

        itemlist.append(Item( channel='helper', action='show_help_register', title='Información para registrase', thumbnail=config.get_thumb('help'), text_color='green' ))

        platformtools.itemlist_refresh()

    if config.get_setting('hdfull_login', 'hdfull', default=False):
        itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
        itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

        itemlist.append(item.clone( title = 'Listas populares', action = 'list_listas', target_action = 'top', search_type = 'all' ))

        itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

        itemlist.append(item.clone( title = 'Búsqueda de personas:', action = '', folder=False, text_color='plum' ))

        itemlist.append(item.clone( title = ' - Buscar intérprete ...', action = 'search', group = 'actor', search_type = 'person',
                                    plot = 'Debe indicarse el nombre y apellido/s del intérprete (lo más exacto posible).'))
        itemlist.append(item.clone( title = ' - Buscar dirección ...', action = 'search', group = 'director', search_type = 'person',
                                    plot = 'Debe indicarse el nombre y apellido/s del director (lo más exacto posible).'))

        itemlist.append(item.clone( title = 'Búsqueda en listas:', action = '', folder=False, text_color='plum' ))
        itemlist.append(item.clone( title = ' - Buscar lista ...', action = 'search', target_action = 'top', search_type = 'all',
                                        plot = 'Debe indicarse el título de la lista (ó parte del mismo).'))

        itemlist.append(item.clone( title = '[COLOR teal]Menú usuario[/COLOR]', action = 'mainlist_user', search_type = 'all' ))

        itemlist.append(item_configurar_dominio(item))
        itemlist.append(item_configurar_proxies(item))

        itemlist.append(item.clone( title = '[COLOR chartreuse]Cerrar sesión[/COLOR]', action = 'logout' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    if not config.get_setting('hdfull_login', 'hdfull', default=False):
        itemlist.append(item.clone( title = '[COLOR chartreuse]Iniciar sesión[/COLOR]', action = 'login' ))

        itemlist.append(item_configurar_dominio(item))
        itemlist.append(item_configurar_proxies(item))

        itemlist.append(Item( channel='helper', action='show_help_register', title='Información para registrase', thumbnail=config.get_thumb('help'), text_color='green' ))

        platformtools.itemlist_refresh()
 
    if config.get_setting('hdfull_login', 'hdfull', default=False):
        itemlist.append(item.clone( action='list_all', title='Últimos estrenos', url = dominio + 'peliculas-estreno', search_type = 'movie' ))
        itemlist.append(item.clone( action='list_all', title='Últimas actualizadas', url = dominio + 'peliculas-actualizadas', search_type = 'movie' ))

        itemlist.append(item.clone( action='list_all', title='Más valoradas', url = dominio + 'peliculas/imdb_rating', search_type = 'movie' ))

        itemlist.append(item.clone( action='list_all', title='Por fecha', url = dominio + 'peliculas/date', search_type = 'movie' ))
        itemlist.append(item.clone( action='list_all', title='Por alfabético', url = dominio + 'peliculas/abc', search_type = 'movie' ))

        itemlist.append(item.clone( action='generos', title='Por género', search_type = 'movie' ))

        itemlist.append(item.clone( title = 'Listas populares', action = 'list_listas', target_action = 'top', search_type = 'all' ))

        itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

        itemlist.append(item.clone( title = '[COLOR teal]Menú usuario[/COLOR]', action = 'mainlist_user', search_type = 'movie' ))

        itemlist.append(item_configurar_dominio(item))
        itemlist.append(item_configurar_proxies(item))

        itemlist.append(item.clone( title = '[COLOR chartreuse]Cerrar sesión[/COLOR]', action = 'logout' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    if not config.get_setting('hdfull_login', 'hdfull', default=False):
        itemlist.append(item.clone( title = '[COLOR chartreuse]Iniciar sesión[/COLOR]', action = 'login' ))

        itemlist.append(item_configurar_dominio(item))
        itemlist.append(item_configurar_proxies(item))

        itemlist.append(Item( channel='helper', action='show_help_register', title='Información para registrase', thumbnail=config.get_thumb('help'), text_color='green' ))

        platformtools.itemlist_refresh()

    if config.get_setting('hdfull_login', 'hdfull', default=False):
        itemlist.append(item.clone( action='list_episodes', title='Episodios estreno', opcion = 'premiere' ))
        itemlist.append(item.clone( action='list_episodes', title='Episodios anime ', opcion = 'anime' ))

        itemlist.append(item.clone( action='list_episodes', title='Últimos episodios', opcion = 'latest' ))
        itemlist.append(item.clone( action='list_episodes', title='Episodios actualizados', opcion = 'updated' ))

        itemlist.append(item.clone( action='list_all', title='Últimas actualizadas', url = dominio + 'series/date',
                                    referer = dominio + 'series/date', search_type='tvshow' ))

        itemlist.append(item.clone( action='list_all', title='Más valoradas', url= dominio + 'series/imdb_rating', search_type = 'tvshow' ))

        itemlist.append(item.clone( action='series_abc', title='Por letra (A - Z)', search_type = 'tvshow' ))
        itemlist.append(item.clone( action='generos', title='Por género', search_type='tvshow' ))

        itemlist.append(item.clone( title = 'Listas populares', action = 'list_listas', target_action = 'top', search_type = 'all' ))

        itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

        itemlist.append(item.clone( title = '[COLOR teal]Menú usuario[/COLOR]', action = 'mainlist_user', search_type = 'tvshow' ))

        itemlist.append(item_configurar_dominio(item))
        itemlist.append(item_configurar_proxies(item))

        itemlist.append(item.clone( title = '[COLOR chartreuse]Cerrar sesión[/COLOR]', action = 'logout' ))

    return itemlist


def mainlist_user(item):
    logger.info()
    itemlist = []

    domain = config.get_setting('dominio', 'hdfull', default=dominios[0])

    data = do_downloadpage(domain)

    patron = '<a href="[^"]+" class="dropdown-toggle"><b class="caret"><\/b>.*?Mi Cuenta</a>\s*<ul class="dropdown-menu">(.*?)</ul>'

    bloque = scrapertools.find_single_match(data, patron)

    matches = re.compile('<li><a href="([^"]+)">([^<]+)').findall(bloque)

    for url, title in matches:
        if title in ['Pedidos', 'Ajustes', 'Salir']: continue

        if title == 'Mis Peliculas':
            tipo_list = 'movies'
        elif title == 'Mis Series':
            tipo_list = 'shows'
        elif title == 'Mis Listas':
            tipo_list = 'listas'

        if not item.search_type == 'all':
            if item.search_type == 'movie':
                if tipo_list == 'shows': continue
            elif item.search_type == 'tvshow':
                if tipo_list == 'movies': continue

        itemlist.append(item.clone( title = title, url = domain + url if not url.startswith('/') else domain + url[1:],
                                    action = 'user_subsections', search_type = item.search_type, tipo_list = tipo_list ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    data = do_downloadpage(dominio)

    tipo_gen = 'TV' if item.search_type == 'tvshow' else 'Pel&iacute;culas'

    bloque = scrapertools.find_single_match(data, '<b class="caret"></b>&nbsp;&nbsp;%s</a>\s*<ul class="dropdown-menu">(.*?)</ul>' % tipo_gen)

    matches = re.compile('<li><a href="([^"]+)">([^<]+)', re.DOTALL).findall(bloque)
    for url, title in matches:
        if url.startswith('/'):
            url = dominio + url[1:]

        itemlist.append(item.clone( title = title, url = url, action = 'list_all' ))

    return sorted(itemlist, key=lambda it: it.title)


def series_abc(item):
    logger.info()
    itemlist = []

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ9':
        itemlist.append(item.clone( title = letra if letra != '9' else '#', url = dominio + 'series/abc/' + letra, action = 'list_all' ))

    return itemlist


def detectar_idiomas(txt):
    languages = []
    if '/spa.png' in txt: languages.append('Esp')
    if '/lat.png' in txt: languages.append('Lat')
    if '/sub.png' in txt: languages.append('Vose')
    if '/eng.png' in txt: languages.append('Eng')
    return languages


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    if item.search_post:
        data = do_downloadpage(item.url, post=item.search_post, referer = item.referer if item.referer else dominio + ('series' if item.search_type == 'tvshow' else 'peliculas'))
    else:
        data = do_downloadpage(item.url)

    patron = '<div class="item"[^>]*">'
    patron += '\s*<a href="([^"]+)"[^>]*>\s*<img class="[^"]*"\s+src="([^"]+)"[^>]*>'
    patron += '\s*</a>\s*</div>\s*<div class="rating-pod">\s*<div class="left">(.*?)</div>'
    patron += '.*? title="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    if item.search_post != '' and item.search_type != 'all':
        matches = list(filter(lambda x: ('/pelicula/' in x[0] and item.search_type == 'movie') or ('/serie/' in x[0] and item.search_type == 'tvshow'), matches))

    num_matches = len(matches)

    for url, thumb, langs, title in matches[item.page * perpage:]:
        title = title.strip()
        languages = detectar_idiomas(langs)

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if url.startswith('/'):
            url = dominio + url[1:]

        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, languages=', '.join(languages), fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, languages=', '.join(languages), fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, referer=item.url, infoLabels={'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    buscar_next = True
    if num_matches > perpage:
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title = '>> Página siguiente', page = item.page + 1, action = 'list_all', text_color = 'coral' ))
            buscar_next = False

    if buscar_next:
        next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)">&raquo;</a>')
        if next_page_link:
            itemlist.append(item.clone( title = '>> Página siguiente', url = next_page_link, page = 0, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    data = do_downloadpage(item.url, referer = item.referer if item.referer else '%s/buscar/' % dominio)

    sid = scrapertools.find_single_match(data, "var sid = '([^']+)';")

    patron = 'itemprop="season"[^>]*>'
    patron += '\s*<a href=\'([^\']+)\'[^>]*>\s*<img class="[^"]*"\s+original-title="([^"]+)"\s+alt="[^"]*"\s+src="([^"]+)"[^>]*>'
    patron += '\s*<h5[^>]*>([^<]+)</h5>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, title, thumb, retitle in matches:
        if title not in ['Especiales', 'Specials']:
            numtempo = scrapertools.find_single_match(title, 'Temporada (\d+)')
            if numtempo == '': numtempo = scrapertools.find_single_match(url, '-(\d+)$')
            if numtempo == '': continue
        else:
            numtempo = 0

        titulo = title
        if retitle != title: titulo += ' - ' + retitle

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.referer = item.url
            item.url = url
            item.thumbnail = thumb
            item.sid = sid
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = numtempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', url = url, title = titulo, thumbnail = thumb, sid = sid, referer = item.url,
                                    contentType = 'season', contentSeason = numtempo, page = 0 ))

    if len(itemlist) == 0: # Alguna serie de una sola temporada que no la tiene identificada
        itemlist.append(item.clone( action='episodios', url = item.url + '/temporada-1', title = 'Temporada 1', sid = sid, referer = item.url,
                                    contentType = 'season', contentSeason = 1, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    color_lang = config.get_setting('list_languages_color', default='red')

    if not item.page: item.page = 0
    perpage = 50

    if not item.sid:
        data = do_downloadpage(item.url)
        item.sid = scrapertools.find_single_match(data, "var sid = '([^']+)';")
        if not item.sid: return itemlist

    post = 'action=season&show=%s&season=%s' % (item.sid, item.contentSeason)
    data = jsontools.load(do_downloadpage(dominio + 'a/episodes', post=post, referer=item.referer))

    for epi in data[item.page * perpage:]:
        tit = epi['title']['es'] if 'es' in epi['title'] and epi['title']['es'] else epi['title']['en'] if 'en' in epi['title'] and epi['title']['en'] else ''
        titulo = '%sx%s %s' % (epi['season'], epi['episode'], tit)

        langs = ['Vose' if idio == 'ESPSUB' else idio.capitalize() for idio in epi['languages']]
        if langs: titulo += ' [COLOR %s][%s][/COLOR]' % (color_lang, ', '.join(langs))

        thumb = dominio + 'tthumb/220x124/' + epi['thumbnail']
        url = item.url + '/episodio-' + epi['episode']

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = epi['season'], contentEpisodeNumber = epi['episode'] ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(data) > ((item.page + 1) * perpage):
        itemlist.append(item.clone( title = ">> Página siguiente", action = "episodios", page = item.page + 1, text_color = 'coral' ))

    return itemlist


def puntuar_calidad(txt):
    orden = ['CAM', 'TS', 'DVDSCR', 'DVDRIP', 'HDTV', 'RHDTV', 'HD720', 'HD1080']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def findvideos(item):
    logger.info()
    itemlist = []

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    data_js = do_downloadpage(dominio + 'templates/hdfull/js/jquery.hdfull.view.min.js')

    key = scrapertools.find_single_match(data_js, 'JSON.parse\(atob.*?substrings\((.*?)\)')
    if not key: 
        key = scrapertools.find_single_match(data_js, 'JSON.*?\]\((0x[0-9a-f]+)\)\);')
        if key: key = int(key, 16)
        else: key = scrapertools.find_single_match(data_js, 'JSON.*?\]\(([0-9]+)\)\);')

    data_js = do_downloadpage(dominio + 'js/providers.js')

    provs = balandroresolver.hdfull_providers(data_js)

    data = do_downloadpage(item.url, referer = dominio)

    data_obf = scrapertools.find_single_match(data, "var ad\s*=\s*'([^']+)")

    try:
       data_decrypt = jsontools.load(balandroresolver.obfs(base64.b64decode(data_obf), 126 - int(key)))
    except:
       data_decrypt = ''

    matches = []
    for match in data_decrypt:
        if match['provider'] in provs:
            try:
               embed = provs[match['provider']][0]
               url = eval(provs[match['provider']][1].replace('_code_', "match['code']"))
               matches.append([match['lang'], match['quality'], url, embed])
            except:
               pass

    ses = 0

    for idioma, calidad, url, embed in matches:
        ses += 1

        if embed == 'd' and 'uptobox' not in url: continue

        if not PY3:
            calidad = unicode(calidad, 'utf8').upper().encode('utf8')

        idioma = idioma.capitalize() if idioma != 'ESPSUB' else 'Vose'

        itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, 
                              language = idioma, quality = calidad, quality_num = puntuar_calidad(calidad) ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def list_episodes(item):
    logger.info()
    itemlist = []

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    color_lang = config.get_setting('list_languages_color', default='red')

    if not item.opcion: item.opcion = 'latest'
    if not item.desde: item.desde = 0

    post = 'action=%s&start=%d&limit=%d&elang=ALL' % (item.opcion, item.desde, perpage)

    data = jsontools.load(do_downloadpage(dominio + 'a/episodes', post=post, referer = dominio + 'episodios'))

    for epi in data:
        show = epi['show']['title']['es'] if 'es' in epi['show']['title'] and epi['show']['title']['es'] != '' else epi['show']['title']['en'] if 'en' in epi['show']['title'] else ''

        tit = epi['title']['es'] if 'es' in epi['title'] and epi['title']['es'] != '' else epi['title']['en'] if 'en' in epi['title'] else ''
        titulo = '%s %sx%s %s' % (show, epi['season'], epi['episode'], tit)

        langs = ['Vose' if idio == 'ESPSUB' else idio.capitalize() for idio in epi['languages']]
        if langs: titulo += ' [COLOR %s][%s][/COLOR]' % (color_lang, ', '.join(langs))

        thumb = dominio + 'tthumb/220x124/' + epi['thumbnail']

        url_serie = dominio + 'serie/' + epi['show']['permalink']
        url_tempo = url_serie + '/temporada-' + epi['season']
        url = url_tempo + '/episodio-' + epi['episode']

        context = []
        context.append({ 'title': '[COLOR pink]Listar temporada %s[/COLOR]' % epi['season'], 
                         'action': 'episodios', 'url': url_tempo, 'context': '', 'folder': True, 'link_mode': 'update' })

        context.append({ 'title': '[COLOR pink]Listar temporadas[/COLOR]',
                         'action': 'temporadas', 'url': url_serie, 'context': '', 'folder': True, 'link_mode': 'update' })

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, context = context,
                                    contentType = 'episode', contentSerieName = show, contentSeason = epi['season'], contentEpisodeNumber = epi['episode'] ))

    tmdb.set_infoLabels(itemlist)

    if len(itemlist) >= perpage:
        itemlist.append(item.clone( title = '>> Página siguiente', desde = item.desde + perpage, action = 'list_episodes', text_color = 'coral' ))

    return itemlist


def user_subsections(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<a data-action="([^"]+)">([^<]+)').findall(data)

    for action, title in matches:
        itemlist.append(item.clone( title = title, target_action = action, action = 'list_user_subsections' if item.tipo_list != 'listas' else 'list_listas' ))

    return itemlist


def list_user_subsections(item):
    logger.info()
    itemlist = []

    domain = config.get_setting('dominio', 'hdfull', default=dominios[0])

    post = "target=%s&action=%s&start=0&limit=28" % (item.tipo_list, item.target_action)
    url = "%sa/my" % domain

    data = do_downloadpage(url, post=post)

    data = jsontools.load(data)

    for match in data:
        title = match.get('title').get('es') if match.get('title').get('es') else match.get('title').get('en')
        thumb = '%sthumb/172x256/%s' % (domain, match.get('thumb'))

        perma = match.get('perma')
        if not perma:
            perma = match.get('permalink')

        if item.tipo_list == 'movies':
            url = '%spelicula/%s' % (domain, perma)

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': '-'} ))
        else:
            url = '%sserie/%s' % (domain, perma)

            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def list_listas(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1

    perpage = 28

    domain = config.get_setting('dominio', 'hdfull', default=dominios[0])

    url = '%sa/my' % domain

    if item.post:
        post = item.post
    else:
        post = 'target=lists&action=%s&start=0&limit=28' % (item.target_action)

    data = jsontools.load(do_downloadpage(url, post=post))

    for match in data:
        title = match.get('title')
        url = '%slista/%s' % (domain, match.get('permalink'))

        itemlist.append(item.clone( action = 'list_all', title = title, url = url ))

    if itemlist:
        if not '&search=' in item.post:
            next_start = (item.page * perpage)
            next_page = item.page + 1

            next_post = 'target=lists&action=%s&start=%s&limit=28' % (item.target_action, next_start)

            itemlist.append(item.clone( title = '>> Página siguiente', post = next_post, page = next_page, pageaction = 'list_listas', text_color = 'coral' ))

    return itemlist


def search(item, texto):
    logger.info()

    dominio = config.get_setting('dominio', 'hdfull', default=dominios[0])

    try:
        if item.group:
            item.url = dominio + 'buscar' + '/' + item.group + '/' + texto
        elif item.target_action:
            item.post = 'target=lists&action=search&search=%s&start=0&limit=99' % texto.replace(' ','+')
            return list_listas(item)
        else:
            data = do_downloadpage(dominio)

            magic = scrapertools.find_single_match(data, "name='__csrf_magic'\s*value=\"([^\"]+)")
            item.search_post = '__csrf_magic=%s&menu=search&query=%s' % (magic, texto.replace(' ','+'))
            item.url = dominio + 'buscar'

        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
