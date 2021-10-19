# -*- coding: utf-8 -*-

from platformcode import logger
from core import httptools, scrapertools
from lib import balandroresolver

def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)

    video_urls = []

    page_url = page_url.replace('/uptobox/', '/uptobox.com/')

    vid = scrapertools.find_single_match(page_url, "(?:uptobox.com/|uptostream.com/)(?:iframe/|)([A-z0-9]+)")
    if not vid: return video_urls

    try:
       video_urls = balandroresolver.resolve_uptobox().getLink(vid, video_urls)
    except Exception as e:
       if '150 minutos' in e:
         return "Tienes que esperar 150 minutos para poder reproducir de este servidor"

       return "Acceso temporalmente restringido"

    return video_urls

