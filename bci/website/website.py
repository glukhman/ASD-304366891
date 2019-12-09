import http.server, re

class Website:
    routes = {}

    def route(self, path):
        def decorator(f):
            self.routes[path] = f
        return decorator

    def run(self, address):
        http_server = http.server.HTTPServer(address, Handler)
        http_server.serve_forever()

class Handler(http.server.BaseHTTPRequestHandler):

    def _set_headers(self, response_code=200):
        self.send_response(response_code)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        response = (404, '')
        for route in [*Website.routes]:
            match = re.search(route, self.path)
            if match and match.span() == (0,len(self.path)):
                response = Website.routes[route](*match.groups())
                break

        self._set_headers(response[0])
        self.wfile.write(response[1].encode('utf8'))
