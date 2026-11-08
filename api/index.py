import os
import sys

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

# Middleware untuk membaca rute asli dari header Vercel
class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        
        # Ambil URL asli dari header yang diteruskan oleh Vercel
        forwarded = environ.get('HTTP_X_FORWARDED_URI') or environ.get('HTTP_X_MATCHED_PATH')
        if forwarded and not forwarded.startswith('/api/index'):
            clean_path = forwarded.split('?')[0]
            environ['PATH_INFO'] = clean_path if clean_path.startswith('/') else '/' + clean_path
        elif path.startswith('/api/index'):
            subpath = path[len('/api/index'):]
            if not subpath or subpath == '/':
                environ['PATH_INFO'] = '/'
            else:
                environ['PATH_INFO'] = subpath if subpath.startswith('/') else '/' + subpath
        elif path in ('/api', '/api/'):
            environ['PATH_INFO'] = '/'
            
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)




