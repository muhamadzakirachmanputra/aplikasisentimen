import os
import sys

# Tambahkan direktori root dan Backend ke sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "Backend")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from Backend.app import app

# Middleware untuk mereset prefix /api/index yang dikirim oleh rewrite Vercel
class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path in ('/api/index', '/api/index/', '/api', '/api/'):
            environ['PATH_INFO'] = '/'
        elif path.startswith('/api/index/'):
            environ['PATH_INFO'] = path[len('/api/index'):]
        elif path.startswith('/api/'):
            # Jaga agar route API Flask asli (misal /api/comparison) tetap utuh
            if not path.startswith('/api/comparison') and not path.startswith('/api/prediksi') and not path.startswith('/api/tfidf') and not path.startswith('/api/uji-sentimen'):
                environ['PATH_INFO'] = path[len('/api'):]
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)


