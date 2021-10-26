# -*- coding: utf-8 -*-

import sys
if sys.version_info[0] < 3:
    from urlparse import urlparse
    from urllib import quote, unquote
    import BaseHTTPServer
else:
    import http.server as BaseHTTPServer
    from urllib.parse import urlparse, quote, unquote

import time, types, os, re

from platformcode import logger

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        pass

    def parse_range(self, range):
        if range:
            m = re.compile('bytes=(\\d+)-(\\d+)?').match(range)
            if m:
                return (m.group(1), m.group(2))
        return (None, None)

    def do_GET(self):
        self.server._client.connected = True
        if self.do_HEAD():
            with self.server._client.file.create_cursor(self.offset) as (f):
                sended = 0
                while sended < self.size:
                    buf = f.read(16384)
                    if buf:
                        if sended + len(buf) > self.size:
                            buf = buf[:self.size - sended]
                        self.wfile.write(buf)
                        sended += len(buf)
                    else:
                        break

    def send_pls(self, files):
        playlist = '[playlist]\n\n'
        for x, f in enumerate(files):
            playlist += 'File' + str(x + 1) + '=http://' + self.server._client.ip + ':' + str(self.server._client.port) + '/' + quote(f.name) + '\n'
            playlist += 'Title' + str(x + 1) + '=' + f.name + '\n'

        playlist += 'NumberOfEntries=' + str(len(files))
        playlist += 'Version=2'
        self.send_response(200, 'OK')
        self.send_header('Content-Length', str(len(playlist)))
        self.finish_header()
        self.wfile.write(playlist)

    def do_HEAD(self):
        url = urlparse(self.path).path
        while not self.server._client.files:
            time.sleep(1)

        if url == '/playlist.pls':
            self.send_pls(self.server._client.files)
            return False
        else:
            if sys.version_info[0] < 3:
                filename = unquote(url)[1:].decode('utf-8')
            else:
                filename = unquote(url)[1:]
            if not self.server._client.file or unquote(url)[1:] != self.server._client.file.name:
                for f in self.server._client.files:
                    if f.name == filename:
                        self.server._client.file = f
                        break

            if self.server._client.file and filename == self.server._client.file.name:
                range = False
                self.offset = 0
                size, mime = self._file_info()
                start, end = self.parse_range(self.headers.get('Range', ''))
                self.size = size
                if start != None:
                    if end == None:
                        end = size - 1
                    self.offset = int(start)
                    self.size = int(end) - int(start) + 1
                    range = (int(start), int(end), int(size))
                else:
                    range = None
                self.send_resp_header(mime, size, range)
                return True
            self.send_error(404, 'Not Found')
            return

    def _file_info(self):
        size = self.server._client.file.size
        ext = os.path.splitext(self.server._client.file.name)[1]
        mime = self.server._client.VIDEO_EXTS.get(ext)
        if not mime:
            mime = 'application/octet-stream'
        return (
         size, mime)

    def send_resp_header(self, cont_type, size, range=False):
        if range:
            self.send_response(206, 'Partial Content')
        else:
            self.send_response(200, 'OK')
        self.send_header('Content-Type', cont_type)
        self.send_header('Accept-Ranges', 'bytes')
        if range:
            if isinstance(range, (tuple, list)) and len(range) == 3:
                self.send_header('Content-Range', 'bytes %d-%d/%d' % range)
                self.send_header('Content-Length', range[1] - range[0] + 1)
            else:
                raise ValueError('Invalid range value')
        else:
            self.send_header('Content-Length', size)
        self.send_header('Connection', 'close')
        self.end_headers()