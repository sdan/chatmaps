from http.server import BaseHTTPRequestHandler, HTTPServer

class HelloWorldRequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, content):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content.encode())

    def do_GET(self):
        if self.path == "/":
            self._send_response("Hello, World!")

def run_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, HelloWorldRequestHandler)
    print(f"Starting server on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
