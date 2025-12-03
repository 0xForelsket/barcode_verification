import socket
import os
import json
import gc

class HTTPServer:
    def __init__(self, port=80):
        self.port = port
        self.routes = {}
        self.static_folder = '/www'
        
    def route(self, path, method='GET'):
        def decorator(handler):
            self.routes[(method, path)] = handler
            return handler
        return decorator
        
    def serve_static(self, path):
        # Security check
        if '..' in path:
            return 403, 'text/plain', 'Forbidden'
            
        filepath = self.static_folder + path
        if path == '/':
            filepath = self.static_folder + '/index.html'
            
        try:
            # Determine content type
            ext = filepath.split('.')[-1]
            content_type = {
                'html': 'text/html',
                'css': 'text/css',
                'js': 'application/javascript',
                'json': 'application/json',
                'ico': 'image/x-icon'
            }.get(ext, 'text/plain')
            
            with open(filepath, 'rb') as f:
                return 200, content_type, f.read()
        except OSError:
            return 404, 'text/plain', 'Not Found'

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.port))
        s.listen(5)
        print(f"Server listening on port {self.port}")
        
        while True:
            try:
                conn, addr = s.accept()
                request = conn.recv(1024).decode()
                
                # Parse request line
                lines = request.split('\r\n')
                if not lines:
                    conn.close()
                    continue
                    
                request_line = lines[0].split()
                if len(request_line) < 2:
                    conn.close()
                    continue
                    
                method, path = request_line[0], request_line[1]
                
                # Parse body (simple)
                body = None
                if method == 'POST':
                    try:
                        body_start = request.find('\r\n\r\n') + 4
                        if body_start > 4:
                            body = request[body_start:]
                            # Attempt JSON parse
                            try:
                                body = json.loads(body)
                            except:
                                pass
                    except:
                        pass
                
                # Handle Route
                handler = self.routes.get((method, path))
                
                if handler:
                    try:
                        response = handler(body)
                        if isinstance(response, tuple):
                            status, content_type, content = response
                        else:
                            status, content_type, content = 200, 'application/json', json.dumps(response)
                    except Exception as e:
                        print(f"Error: {e}")
                        status, content_type, content = 500, 'text/plain', str(e)
                else:
                    # Try static file
                    status, content_type, content = self.serve_static(path)
                
                # Send Response
                header = f"HTTP/1.1 {status} OK\r\nContent-Type: {content_type}\r\nAccess-Control-Allow-Origin: *\r\n\r\n"
                conn.send(header.encode())
                if isinstance(content, bytes):
                    conn.send(content)
                else:
                    conn.send(content.encode())
                
                conn.close()
                gc.collect()
                
            except Exception as e:
                print(f"Server Error: {e}")
