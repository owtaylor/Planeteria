import cgi
import os
import re
import StringIO
import sys

base_dir = os.path.dirname(__file__)
sys.path.append(base_dir)

import config as cfg

class FileIterator:
    def __init__(self, f):
        self.f = f

    def __iter__(self):
        return self

    def next(self):
        # The chunk size we read in is arbitrary - none of the files we are reading
        # are actually too big to just read in a single chunk, but we keep the
        # chunk size smaller to save a miniscule amount of memory and so the
        # read-in-chunks code is tested.
        data = self.f.read(8192)
        if data == "":
            self.f.close()
            self.f = None
            raise StopIteration()
        return data

def application(environ, start_response):
    path = os.path.join(environ['SCRIPT_NAME'], environ['PATH_INFO'])

    handler = None
    extra_args = []
    if path == '/new_planet.py':
        import new_planet
        handler = new_planet.handle
    elif re.match(r'/\w+/admin.py', path):
        import admin
        handler = admin.handle

    if handler is None:
        if path.endswith('/'):
            path += 'index.html';
        if path.startswith('/'):
            path = path[1:]

        try:
            f = open(os.path.join(cfg.OUTPUT_DIR, path))
        except IOError:
            f = None

        if f is None:
            components = path.split(os.sep)
            if len(components) > 1 and components[0] != 'pub.d':
                fallback_path = os.path.join(cfg.opt['new_planet_dir'], path)
            else:
                fallback_path = os.path.join(cfg.base_dir, 'www', path)

            try:
                f = open(fallback_path)
            except IOError:
                response_headers = [('Content-Type', 'text/plain')]
                start_response("404 Not Found", response_headers)
                return ["Not found"]

        content_type = None
        if path.endswith(".html"):
            content_type = "text/html";
        elif path.endswith(".css"):
            content_type = "text/css";
        elif path.endswith(".js"):
            content_type = "application/javascript";
        elif path.endswith(".png"):
            content_type = "image/png";
        elif path.endswith(".jpg"):
            content_type = "image/jpeg";
        elif path.endswith(".gif"):
            content_type = "image/gif";

        response_headers = [('Content-Type', content_type)]
        start_response("200 OK", response_headers)
        return FileIterator(f)

    input = StringIO.StringIO()
    for val in environ['wsgi.input']:
        input.write(val)
    input.seek(0)

    form = cgi.FieldStorage(input, environ=environ)

    return handler(path, form, start_response)
