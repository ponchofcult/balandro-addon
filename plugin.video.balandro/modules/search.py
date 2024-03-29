# -*- coding: utf-8 -*-

import os, time
from threading import Thread

from platformcode import config, logger, platformtools
from core.item import Item
from core import channeltools

color_list_prefe = config.get_setting('channels_list_prefe_color', default='gold')
color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')
color_list_inactive = config.get_setting('channels_list_inactive_color', default='gray')

color_alert = config.get_setting('notification_alert_color', default='red')
color_infor = config.get_setting('notification_infor_color', default='pink')
color_adver = config.get_setting('notification_adver_color', default='violet')
color_avis = config.get_setting('notification_avis_color', default='yellow')
color_exec = config.get_setting('notification_exec_color', default='cyan')


def mainlist(item):
    logger.info()
    itemlist = []

    thumb_filmaffinity = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'filmaffinity.jpg')
    thumb_tmdb = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'tmdb.jpg')

    item.category = 'Buscar'

    itemlist.append(item.clone( action='', title= 'Búsquedas por titulo:', text_color='yellowgreen', folder=False ))

    if config.get_setting('channels_link_main', default=True):
        itemlist.append(item.clone( action='search', search_type='all', title= ' - Buscar Película y/o Serie ...',
                                    plot = 'Buscar indistintamente películas y/o series en todos los canales' ))

    itemlist.append(item.clone( action='search', search_type='movie', title= ' - Buscar Película ...', thumbnail=config.get_thumb('movie'),
                                plot = 'Escribir el nombre de una película para buscarla en los canales de películas' ))

    itemlist.append(item.clone( action='search', search_type='tvshow', title= ' - Buscar Serie ...', thumbnail=config.get_thumb('tvshow'),
                                plot = 'Escribir el nombre de una serie para buscarla en los canales de series' ))

    itemlist.append(item.clone( action='search', search_type='documentary', title= ' - Buscar Documental ...', thumbnail=config.get_thumb('documentary'),
                                plot = 'Escribir el nombre de un documental para buscarlo en los canales de documentales' ))

    itemlist.append(item.clone( action='', title= 'Búsquedas especiales:', text_color='yellowgreen', folder=False ))

    itemlist.append(item.clone( channel='tmdblists', action='mainlist', title= ' - Búsquedas y listas en TMDB', thumbnail=thumb_tmdb,
                                plot = 'Buscar personas y ver listas de películas y series de la base de datos de The Movie Database' ))

    itemlist.append(item.clone( channel='filmaffinitylists', action='mainlist', title= ' - Listas en Filmaffinity', thumbnail=thumb_filmaffinity,
                                plot = 'Ver listas de películas, series, documentales y otros de Filmaffinity' ))

    itemlist.append(item.clone( action='', title= 'Búsquedas en canales con proxies:', text_color='red', folder=False ))

    itemlist.append(item.clone( channel='filters', title=  ' - Qué canales pueden usar proxies', action='with_proxies',
                                thumbnail=config.get_thumb('stack'), folder=False ))

    itemlist.append(item.clone( channel='proxysearch', title =  ' - Configurar proxies a usar [COLOR plum](en los canales que los necesiten)[/COLOR]',
                                action = 'proxysearch_all', thumbnail=config.get_thumb('flame') ))

    if config.get_setting('proxysearch_excludes', default=''):
        itemlist.append(item.clone( channel='proxysearch', title =  ' - Anular los canales excluidos de Configurar proxies a usar',
                                    action = 'channels_proxysearch_del', thumbnail=config.get_thumb('flame'), text_color='coral', folder = False ))

    itemlist.append(item.clone( action='', title= 'Personalizacion búsquedas:', text_color='moccasin', folder=False ))

    itemlist.append(item.clone( channel='filters', action='no_actives', title= ' - Qué canales no intervienen en las búsquedas (están desactivados)',
                                thumbnail=config.get_thumb('stack'), folder=False ))

    itemlist.append(item.clone(  channel='filters', action='channels_status', title= ' - Personalizar canales (Desactivar o Re-activar)', des_rea = True,
                                thumbnail=config.get_thumb('stack'), folder=False ))

    itemlist.append(item.clone( channel='filters', action='only_prefered', title= ' - Qué canales tiene marcados como preferidos',
                                thumbnail=config.get_thumb('stack'), folder=False ))

    itemlist.append(item.clone( channel='filters', action='channels_status', title= ' - Personalizar canales Preferidos (Marcar o Des-marcar)', des_rea = False,
                                thumbnail=config.get_thumb('stack'), folder=False ))

    itemlist.append(item.clone( channel='filters', title = ' - [COLOR cyan]Excluir canales en las búsquedas[/COLOR]', action = 'mainlist',
                                thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='actions', title= 'Ajustes categorías [COLOR yellowgreen](proxies y buscar)[/COLOR]', action = 'open_settings',
                                thumbnail=config.get_thumb('settings'), folder=False ))

    itemlist.append(item.clone( action='show_help', title='[COLOR green]Información búsquedas[/COLOR]', thumbnail=config.get_thumb('help'), folder=False ))

    return itemlist


def show_help(item):
    txt = 'Desde la configuración del addon se puede definir el número de resultados que se previsualizan para cada canal.'
    txt += ' Si por ejemplo el canal devuelve 15 resultados y se previsualizan 2, entrar en el enlace de la búsqueda para verlos todos.'
    txt += '[CR]'
    txt += '[CR]Según cada web/canal su buscador puede permitir diferenciar por películas/series o no, y también es variable la sensibilidad de la búsqueda (si busca sólo en el título o también en la sinopsis, el tratamiento si hay varias palabras, si devuelve muchos o pocos resultados, etc)'
    txt += '[CR]'
    txt += '[CR]Desde cualquier película/serie mostrada en el addon, acceder al menú contextual para buscar esa misma película/serie en los demás canales.'
    txt += '[CR]'
    txt += '[CR]Desde cualquier película/serie guardada en enlaces, si al acceder se produce un error en la web, se ofrece un diálogo para volver a buscar esa misma película/serie en los demás canales o en el mismo canal (por si han cambiado las urls de la web y el enlace ya no funciona).'

    platformtools.dialog_textviewer('Información sobre búsquedas', txt)
    return True


def search(item, tecleado):
    logger.info()

    item.category = 'Buscar ' + tecleado
    if item.search_type == '': item.search_type = 'all'

    itemlist = do_search(item, tecleado)

    return itemlist


def do_search_channel(item, tecleado, ch):
    canal = __import__('channels.' + item.channel, fromlist=[''])
    if hasattr(canal, 'search'):
        ch['itemlist_search'] = canal.search(item, tecleado)
    else:
        logger.error('Search not found in channel %s. Implementar search o quitar searchable!' % item.channel)


def do_search(item, tecleado):
    itemlist = []

    multithread = config.get_setting('search_multithread', default=True)
    threads = []

    search_limit_by_channel = config.get_setting('search_limit_by_channel', default=2)

    progreso = platformtools.dialog_progress('Buscando ' + tecleado, '...')

    filtros = { 'searchable': True, 'status': 0 } # status para descartar desactivados por el usuario, solamente se busca en activos y preferidos
    if item.search_type != 'all': filtros['search_types'] = item.search_type

    ch_list = channeltools.get_channels_list(filtros=filtros)
    if item.from_channel != '': # descartar from_channel (búsqueda en otros canales)
        ch_list = [ch for ch in ch_list if ch['id'] != item.from_channel]
    if item.search_type == 'all':
        if item.only_channels_group and (item.group == 'docs' or item.group == '3d'): pass
        else: ch_list = [ch for ch in ch_list if 'documentary' not in ch['categories']]

    num_canales = float(len(ch_list))

    only_torrents = ''
    if item.extra == 'only_torrents': only_torrents = item.extra

    only_prefered = config.get_setting('search_only_prefered', default=False)
    no_torrents = config.get_setting('search_no_torrents', default=False)
    no_inestables = config.get_setting('search_no_inestables', default=False)
    no_proxies = config.get_setting('search_no_proxies', default=False)

    no_channels = config.get_setting('search_no_channels', default=False)

    if item.search_type == 'movie':
        channels_search_excluded = config.get_setting('search_excludes_movies', default='')

    elif item.search_type == 'tvshow':
        channels_search_excluded = config.get_setting('search_excludes_tvshows', default='')

    elif item.search_type == 'documentary':
        channels_search_excluded = config.get_setting('search_excludes_documentaries', default='')

    elif item.extra == 'only_torrents':
        channels_search_excluded = config.get_setting('search_excludes_torrents', default='')

    else:
        channels_search_excluded = config.get_setting('search_excludes_mixed', default='')
        channels_search_excluded = channels_search_excluded + config.get_setting('search_excludes_all', default='')

    for i, ch in enumerate(ch_list):
        perc = int(i / num_canales * 100)

        progreso.update(perc, 'Analizar %s  en el canal %s ' % (tecleado, ch['name']))

        c_item = Item( channel=ch['id'], action='search', search_type=item.search_type, title='Buscar en '+ch['name'], thumbnail=ch['thumbnail'] )

        if no_torrents:
            if 'torrents' in ch['clusters']:
                num_canales = num_canales - 1
                continue

        if 'register' in ch['clusters']:
            check_login = config.get_setting('channel_%s_%s_login' % (ch['id'], ch['id']), default=False)
            if check_login == False:
                num_canales = num_canales - 1
                continue
                
        if no_inestables:
            if 'inestable' in ch['clusters']:
                num_canales = num_canales - 1
                continue

        if no_proxies:
            if 'proxies' in ch['notes'].lower():
                cfg_proxies_channel = 'channel_' + ch['name'].lower() + '_proxies'
                if config.get_setting(cfg_proxies_channel, default=''):
                    if no_channels:
                        platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado por proxies[/COLOR][/B]' % color_adver)

                    num_canales = num_canales - 1
                    continue

        if channels_search_excluded:
            channels_preselct = str(channels_search_excluded).replace('[', '').replace(']', ',')
            if ("'" + ch['id'] + "'") in str(channels_preselct):
                if no_channels:
                    platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado por excluido[/COLOR][/B]' % color_exec)

                num_canales = num_canales - 1
                continue

        if item.only_channels_group:
            if not ("'" + ch['id'] + "'") in str(item.only_channels_group):
                num_canales = num_canales - 1
                continue
        else:
            if only_prefered:
                cfg_status_channel = 'channel_' + ch['name'].lower() + '_status'
                if not config.get_setting(cfg_status_channel, default=''):
                    num_canales = num_canales - 1
                    continue

            elif only_torrents:
                if not 'torrents' in ch['clusters']:
                   num_canales = num_canales - 1
                   continue

        if multithread:
            t = Thread(target=do_search_channel, args=[c_item, tecleado, ch], name=ch['name'])
            t.setDaemon(True)
            t.start()
            threads.append(t)
        else:
            do_search_channel(c_item, tecleado, ch)

        if progreso.iscanceled(): break

    if multithread:
        pendent = [a for a in threads if a.isAlive()]
        while len(pendent) > 0:
            hechos = num_canales - len(pendent)
            perc = int(hechos / num_canales * 100)
            mensaje = ', '.join([a.getName() for a in pendent])

            progreso.update(perc, 'Buscando %d de %d canales. Quedan %d : %s' % (hechos, num_canales, len(pendent), mensaje))

            if progreso.iscanceled(): break

            time.sleep(0.5)

            pendent = [a for a in threads if a.isAlive()]

    if item.from_channel != '': 
        # Búsqueda exacta en otros/todos canales de una peli/serie : mostrar sólo las coincidencias exactas
        tecleado_lower = tecleado.lower()
        for ch in ch_list:
            if 'itemlist_search' in ch and len(ch['itemlist_search']) > 0:
                for it in ch['itemlist_search']:
                    if it.contentType not in ['movie','tvshow','season']: continue
                    if it.infoLabels['tmdb_id'] and item.infoLabels['tmdb_id']:
                        if it.infoLabels['tmdb_id'] != item.infoLabels['tmdb_id']: continue
                    else:
                        if it.contentType == 'movie' and it.contentTitle.lower() != tecleado_lower: continue
                        if it.contentType in ['tvshow','season'] and it.contentSerieName.lower() != tecleado_lower: continue
                    it.title += ' [COLOR gold][%s][/COLOR]' % ch['name']
                    itemlist.append(it)

    else:
        # Búsqueda parecida en todos los canales : link para acceder a todas las coincidencias y previsualización de n enlaces por canal
        no_results = config.get_setting('search_no_results', default=False)
        no_results_proxies = config.get_setting('search_no_results_proxies', default=True)

        nro = 0
        color = 'chartreuse'
        titulo = ''

        for ch in sorted(ch_list, key=lambda ch: True if 'itemlist_search' not in ch or len(ch['itemlist_search']) == 0 else False):
            action = ''

            cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

            if 'itemlist_search' in ch:
                if len(ch['itemlist_search']) == 0:
                    if no_results:
                        titulo = ch['name'] + '[COLOR coral] sin resultados'

                        if config.get_setting(cfg_proxies_channel, default=''):
                            titulo = titulo + ' [COLOR red]debe configurar nuevos proxies'
                    else:
                        if config.get_setting(cfg_proxies_channel, default=''):
                            if no_results_proxies:
                                titulo = ch['name'] + '[COLOR coral] sin resultados'
                                titulo = titulo + ' [COLOR red]debe configurar nuevos proxies'
                            else:
                                continue
                        else:
                            if no_channels:
                               platformtools.dialog_notification(ch['name'], '[B][COLOR %s]Ignorado sin resultados[/COLOR][/B]' % color_avis)
                            continue
                else:
                    action = 'search'
                    texto = 'resultados'
                    if len(ch['itemlist_search']) == 1: texto = 'resultado'
                    titulo = '%s [COLOR mediumspringgreen]... %d %s' % (ch['name'], len(ch['itemlist_search']), texto)
            else:
                if progreso.iscanceled():
                    titulo = '%s [COLOR mediumaquamarine]búsqueda cancelada' % ch['name']
                else:
                    if item.only_channels_group:
                        if not ("'" + ch['id'] + "'") in str(item.only_channels_group): continue

                    titulo = '%s [COLOR plum]No se ha buscado' % ch['name']

                    if no_torrents:
                        if 'torrents' in ch['clusters']:
                            continue

                    if no_inestables:
                        if 'inestable' in ch['clusters']:
                            continue

                    if no_proxies:
                        if 'proxies' in ch['notes'].lower():
                            if config.get_setting(cfg_proxies_channel, default=''):
                                if no_channels:
                                    titulo = '%s [COLOR red]Ignorado por proxies' % ch['name']
                            continue
                    else:
                       if only_prefered: continue
                       elif only_torrents: continue

                       if 'proxies' in ch['notes'].lower():
                           titulo = titulo + ' [COLOR red]comprobar si necesita proxies'
                       elif 'register' in ch['clusters']:
                           titulo = titulo + ' [COLOR teal]comprobar credenciales cuenta'
                       else:
                           titulo = titulo + ' [COLOR yellow]comprobar canal'

            nro += 1

            if nro == 1:
                itemlist.append(Item( channel='groups', action='submnu_search', title='Personalizar próximas búsquedas',
                                      extra = item.search_type, thumbnail=config.get_thumb('settings'), text_color='moccasin' ))

            if not titulo:
                itemlist.append(Item( action = '', title = tecleado + '[COLOR coral]sin resultados en ningún canal[/COLOR]' ))
                break

            context = []

            if not 'debe configurar nuevos proxies' in titulo:
                tit = '[COLOR %s]Marcar canal como Preferido[/COLOR]' % color_list_prefe
                context.append({'title': tit, 'channel': 'actions', 'action': '_marcar_canales', 'estado': 1, 'canal': ch['id']})

                tit = '[COLOR %s]Des-Marcar canal como Preferido[/COLOR]' % color_list_prefe
                context.append({'title': tit, 'channel': 'actions', 'action': '_marcar_canales', 'estado': 0, 'canal': ch['id']})

            tit = '[COLOR %s]Marcar canal como Desactivado[/COLOR]' % color_list_inactive
            context.append({'title': tit, 'channel': 'actions', 'action': '_marcar_canales', 'estado': -1, 'canal': ch['id']})

            tit = '[COLOR %s]Des-Marcar canal como Desactivado[/COLOR]' % color_list_inactive
            context.append({'title': tit, 'channel': 'actions', 'action': '_marcar_canales', 'estado': 0, 'canal': ch['id']})

            tit = '[COLOR white]Marcar canal como Activo[/COLOR]'
            context.append({'title': tit, 'channel': 'actions', 'action': '_marcar_canales', 'estado': 0, 'canal': ch['id']})

            titulo = '[B][COLOR %s]%s[/COLOR][/B]' % (color, titulo)
            itemlist.append(Item( channel=ch['id'], action=action, buscando=tecleado, title=titulo, context=context,
                                                    thumbnail=ch['thumbnail'], search_type=item.search_type ))

            if 'itemlist_search' in ch:
                for j, it in enumerate(ch['itemlist_search']):
                    if it.contentType not in ['movie', 'tvshow', 'season']: continue
                    if j < search_limit_by_channel:
                        itemlist.append(it)
                    else:
                        break

            if 'búsqueda cancelada' in titulo: break

    progreso.close()

    if len(itemlist) == 0:
        if only_prefered:
            platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Búsqueda solo en preferidos[/COLOR][/B]' % color_infor)
        elif only_torrents:
            platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Búsqueda solo en torrents[/COLOR][/B]' % color_infor)
        else:
            platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Búsqueda sin resultados[/COLOR][/B]' % color_infor)

    return itemlist

