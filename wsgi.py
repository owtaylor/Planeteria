import cgi
import os
import re
import StringIO
import sys

sys.path.append(os.path.dirname(__file__))

def application(environ, start_response):
    script_name = environ['SCRIPT_NAME']

    handler = None
    extra_args = []
    if script_name == '/new_planet.py':
        import new_planet
        handler = new_planet.handle
    elif re.match(r'/\w+/admin.py', script_name):
        import admin
        handler = admin.handle

    if handler is None:
        response_headers = [('Content-Type', 'text/plain')]
        start_response("404 Not Found", response_headers)
        return ["Not found"]

    input = StringIO.StringIO()
    for val in environ['wsgi.input']:
        input.write(val)
    input.seek(0)

    form = cgi.FieldStorage(input, environ=environ)

    return handler(script_name, form, start_response)
