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

# This class is like cgi.FieldStorage, but decodes values as UTF-8 when
# accessed. This is a partial implementation of just the FieldStorage
# method we actually use; there are other methods like getfirst()
# that would also need to be handled in a full implementation. It might
# be better to actually modify the objects held in the internal storage
# rather than converting on access, to make indexing with []
# work as expected.

def decode_utf8(v):
    if type(v) is type([]):
        return map(decode_utf8, v)
    else:
        return unicode(v, "UTF-8")

class UnicodeFieldStorage(cgi.FieldStorage):
    def getvalue(self, key, default=None):
        return decode_utf8(cgi.FieldStorage.getvalue(self, key, default))

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

        full_path = os.path.join(cfg.OUTPUT_DIR, path)
        if os.path.isdir(full_path):
            response_headers = [('Location', path + '/')]
            start_response("301 Moved Permanently", response_headers)
            return []

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

    form = UnicodeFieldStorage(input, environ=environ)

    return handler(path, form, start_response)
