"""
Servidor sencillo para la demo web UWSN.
Ejecuta: python serve_demo.py
Abre http://localhost:8001 automáticamente.
"""
import http.server
import socketserver
import webbrowser
from pathlib import Path

PORT = 8001
ROOT = Path(__file__).parent / "demo-web"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)


def main():
    if not ROOT.exists():
        raise SystemExit(f"Directorio no encontrado: {ROOT}")

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/"
        print(f"🌊 Sirviendo demo desde {ROOT} en {url}")
        try:
            webbrowser.open(url)
        except Exception:
            print("⚠️ No se pudo abrir el navegador automáticamente. Abrir manualmente el URL.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor detenido por usuario")


if __name__ == "__main__":
    main()
