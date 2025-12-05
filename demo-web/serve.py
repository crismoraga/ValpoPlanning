#!/usr/bin/env python3
"""
🌊 UWSN Demo Server - Script de despliegue simple
Ejecuta: python serve.py
La demo se abrirá automáticamente en el navegador.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from functools import partial

# Configuración
PORT = 8080
HOST = "localhost"

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Handler silencioso que solo muestra errores importantes."""
    
    def log_message(self, format, *args):
        # Solo mostrar errores (códigos 4xx y 5xx)
        if len(args) >= 2 and str(args[1]).startswith(('4', '5')):
            print(f"⚠️  {args[0]} - {args[1]}")
    
    def end_headers(self):
        # Headers para evitar cache durante desarrollo
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def find_free_port(start_port=8080, max_attempts=20):
    """Encuentra un puerto libre comenzando desde start_port."""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, port))
                return port
        except OSError:
            continue
    return start_port

def main():
    # Cambiar al directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Verificar que index.html existe
    if not os.path.exists("index.html"):
        print("❌ Error: No se encontró index.html en el directorio actual")
        print(f"   Directorio: {script_dir}")
        sys.exit(1)
    
    # Encontrar puerto libre
    port = find_free_port(PORT)
    
    # Crear servidor
    handler = partial(QuietHandler, directory=script_dir)
    
    try:
        with socketserver.TCPServer((HOST, port), handler) as httpd:
            url = f"http://{HOST}:{port}"
            
            print("\n" + "=" * 60)
            print("🌊 UWSN Demo - Puerto de Valparaíso")
            print("=" * 60)
            print(f"\n✅ Servidor iniciado en: {url}")
            print(f"📁 Directorio: {script_dir}")
            print("\n💡 Presiona Ctrl+C para detener el servidor")
            print("=" * 60 + "\n")
            
            # Abrir navegador automáticamente
            webbrowser.open(url)
            
            # Mantener servidor corriendo
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido. ¡Hasta pronto!")
        sys.exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ El puerto {port} está ocupado. Intenta cerrar otras aplicaciones.")
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
