import os
import sys
from urllib.parse import parse_qs, urlencode

# Tambahkan direktori root dan Backend ke sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "Backend")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from werkzeug.middleware.proxy_fix import ProxyFix
from Backend.app import app

# Beritahu Flask bahwa ia berjalan di balik reverse proxy HTTPS Vercel
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Middleware untuk mengekstrak path asli yang dikirim oleh Vercel via __vercel_url
class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get('QUERY_STRING', '')
        if '__vercel_url' in qs:
            params = parse_qs(qs)
            if '__vercel_url' in params and params['__vercel_url']:
                raw_path = params['__vercel_url'][0]
                clean_path = '/' + raw_path.lstrip('/')
                del params['__vercel_url']
                environ['QUERY_STRING'] = urlencode(params, doseq=True)
                environ['PATH_INFO'] = clean_path

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)





