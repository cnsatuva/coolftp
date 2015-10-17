import socket
import threading
import SocketServer
import sys
import select
import os
import json
import fnmatch

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def process(self, s, data, root):

        print data
        parts = data.split()
        parts[0] = parts[0].upper()
        if parts[0] == 'LIST':
            try:
                path = os.path.normcase(os.path.normpath(os.path.abspath("".join(parts[1:]))))
                if not fnmatch.fnmatch(path, root):
                    raise ValueError

                output = {"path": path, "files": []}

                for (dirpath, dirnames, filenames) in os.walk(path):
                    for d in dirnames:
                        full_path = os.path.join(path, d)
                        if not os.access(full_path, os.R_OK):
                            continue
                        output["files"].append({full_path: {"type": "dir"}})

                    for f in filenames:
                        full_path = os.path.join(path, f)
                        if not os.access(full_path, os.R_OK):
                            continue
                        output["files"].append({full_path: {"type": "file", "filesize": os.path.getsize(full_path)}})
                    break
            except:
                self.request.sendall(json.dumps({"result": 1}))

            self.request.sendall(json.dumps(output))

        elif parts[0] == 'DOWNLOAD':
            try:
                path = os.path.normcase(os.path.normpath(os.path.abspath("".join(parts[1:]))))
                if not fnmatch.fnmatch(path, root):
                    raise ValueError

                if not os.access(path, os.R_OK):
                    raise ValueError

                with open(path) as f:
                    data = f.read()
                    encoded = data.encode("hex")
                    self.request.sendall(json.dumps({"path": path, "filesize": len(data), "encoded": len(encoded), "data": encoded}))

            except IOError as e:
                self.request.sendall(json.dumps({"result": 1}))
                return False

        elif parts[0] == 'UPLOAD':

            try:
                pathlength = int(data[len(parts[0]) + 1:len(parts[0]) + 11])
                path_start = len(parts[0]) + 11
                path_end = len(parts[0]) + 11 + pathlength
                dirty = data[path_start:path_end]
                path = os.path.normcase(os.path.normpath(os.path.abspath(dirty)))
                next_parts = data[path_end:].strip().split()
                filesize = next_parts[0]
                compressed = next_parts[1]
                filedata = next_parts[2]

                if not fnmatch.fnmatch(path, root):
                    raise ValueError

                if not os.access(path, os.W_OK):
                    raise ValueError

                if os.path.exists(path):
                    self.request.sendall(json.dumps({"result": 2}))
                    return False

                with open(path, "wb") as f:
                    f.write(filedata.decode("hex"))

                self.request.sendall(json.dumps({"result": 0, "message": "File uploaded successfully"}))

            except:
                self.request.sendall(json.dumps({"result": 2}))
                return False

        elif parts[0] == 'INFO':
            try:
                path = os.path.normcase(os.path.normpath(os.path.abspath("".join(parts[1:]))))

                if not fnmatch.fnmatch(path, root):
                    raise ValueError

                if not os.access(path, os.R_OK):
                    raise ValueError

                output = {"path": path}

                if os.path.isdir(path):
                    output["info"] = {"type": "dir"}
                else:
                    output["info"] = {"type": "file", "filesize": os.path.getsize(path)}

                self.request.sendall(json.dumps(output))
            except:
                self.request.sendall(json.dumps({"result": 3}))

        elif parts[0] == 'BYE':
            self.request.sendall("BYE")
            return False
        else:
            return False

        return True

    def handle(self):

        # FIXME: No password by default
        password = ""

        # Look for opening message
        if not self.request.recv(5) == 'HELLO':
            return

        if len(password) > 0:
            self.request.sendall("PASSWORD\n")
            if self.request.recv(100) != password:
                return
        else:
            self.request.sendall("HELLO\n")

        while (True):
            result = select.select([self.request], [], [], 60)
            if result[0]:
                length = self.request.recv(4).strip()
                if len(length) > 0:
                    try:
                        data = self.request.recv(int(length))
                    except:
                        # Client must have closed the connection
                        break

                    # Length must be valid
                    if len(data) != length:
                        break

                    # Check for errors
                    if self.process(self.request, data, os.path.join(os.getcwd(), "data")) is False:
                        break
                else:
                    break

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "0.0.0.0", 0
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address
    print "Server running on port:", port

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print "Server loop running in thread:", server_thread.name

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    server.shutdown()
    server.server_close()
