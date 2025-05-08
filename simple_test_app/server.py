"""
Simple HTTP server to host the Face Lock Test App.
This allows the web application to be served locally while communicating with the Face Lock Server.
"""

import http.server
import socketserver
import os
import webbrowser
from urllib.parse import urlparse

# Configuration
PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler with directory set to the current directory"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers to allow communication with the Face Lock Server
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def run_server():
    """Run the HTTP server and open the application in a browser"""
    
    # Create the server
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        server_url = f"http://localhost:{PORT}"
        print(f"Server running at {server_url}")
        print("Press Ctrl+C to stop the server")
        
        # Open the app in the default web browser
        webbrowser.open(server_url)
        
        # Keep the server running
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")

if __name__ == "__main__":
    run_server()
