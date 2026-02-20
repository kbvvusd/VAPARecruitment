import http.server
import socketserver
import webbrowser
import threading
import time

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

class MyHandler(Handler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def open_browser():
    """Open the browser after a short delay to ensure server is running."""
    time.sleep(1)
    print(f"Opening browser at http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")

def main():
    print(f"Starting server at port {PORT}")
    # Allow address reuse to prevent "Address already in use" errors on restart
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server.")
        
        # Start browser in a separate thread so it doesn't block server startup
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
            httpd.server_close()

if __name__ == "__main__":
    main()
