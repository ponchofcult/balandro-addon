# -*- coding: utf-8 -*-

from core import httptools, scrapertools, servertools
from platformcode import logger
from lib import jsunpack


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    page_url = page_url.replace('//cloudemb.com/e/', '//cloudemb.com/')

    if '//tubesb.com/' in page_url:
        page_url = page_url.replace('//tubesb.com/e/', '//streamsb.net/play/')

    data = httptools.downloadpage(page_url).data

    if 'File Not Found' in data or 'File is no longer available' in data:
        return 'El fichero no existe o ha sido borrado'

    if not "text/javascript'>(eval" in data:
        media_url = scrapertools.find_single_match(str(data), 'sources:.*?file.*?"(.*?)"')
        if 'master.m3u8' in str(media_url):
            video_urls.append(['.m3u8 ', media_url])
            video_urls = servertools.get_parse_hls(video_urls)
            return video_urls

    packed = scrapertools.find_single_match(data, r"'text/javascript'>(eval.*?)\n")
    if packed:
        unpacked = jsunpack.unpack(packed)

        video_srcs = scrapertools.find_single_match(unpacked, "sources:\s*\[[^\]]+\]")
        video_info = scrapertools.find_multiple_matches(video_srcs, r'{(file:.*?)}}')

        try:
           sub = scrapertools.find_single_match(unpacked, r'{file:"([^"]+)",label:"[^"]+",kind:"captions"')
        except:
           sub = ''

        for info in video_info:
            url = scrapertools.find_single_match(info, r'file:"([^"]+)"')

            if url:
                if url == sub: continue

                extension = scrapertools.get_filename_from_url(video_url)[-4:]
                if extension in ('.png`', '.jpg'): continue

                if extension == '.mpd':
                    video_urls.append(['mpd', url])
                else:
                    video_urls.append([sub, url])

    return video_urls
