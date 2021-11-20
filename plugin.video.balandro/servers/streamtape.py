# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)

    page_url = page_url.replace('/v/', '/e/')
    video_urls = get_aux(page_url)

    if len(video_urls) == 0:
        page_url = page_url.replace('/e/', '/v/')
        video_urls = get_aux(page_url)

    return video_urls

def get_aux(page_url):
    video_urls = []

    referer = {}

    data = httptools.downloadpage(page_url, headers=referer).data

    if "Video not found" in data:
        return  "El archivo no existe o ha sido borrado"

    url_data = scrapertools.find_single_match(data, """getElementById\('\w+link'\).innerHTML = "[^"]+" .* \('.+?/([^']+)'\)""")

    if not url_data:
        import time
        from platformcode import platformtools
        espera = 3

        platformtools.dialog_notification('Cargando Streamtape', 'Espera requerida de %s segundos' % espera)
        time.sleep(int(espera))

        referer = {"Referer": page_url}
        data = httptools.downloadpage(page_url, headers=referer).data
        url_data = scrapertools.find_single_match(data, """getElementById\('\w+link'\).innerHTML = "[^"]+" .* \('.+?/([^']+)'\)""")

    if url_data:
        url = "https://adblockstrtech.link/" + url_data + "&stream=1" + "|User-Agent=" + httptools.get_user_agent()

        video_urls.append(['mp4', url])

    return video_urls

