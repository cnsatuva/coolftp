import socket
import threading
import SocketServer
import sys
import select
import os
import json

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def process(self, s, data):

        print data
        parts = data.split()
        parts[0] = parts[0].upper()
        if parts[0] == 'LIST':
            path = os.path.normcase(os.path.normpath(os.path.abspath("".join(parts[1:]))))
            output = {}
            output["path"] = path
            output["files"] = []
            for (dirpath, dirnames, filenames) in os.walk(path):
                for d in dirnames:
                    full_path = os.path.join(path, d)
                    output["files"].append({full_path: {"type": "dir"}})

                for f in filenames:
                    full_path = os.path.join(path, f)
                    output["files"].append({full_path: {"type": "file", "filesize": os.path.getsize(full_path)}})
                break

            self.request.sendall(json.dumps(output))

        elif parts[0] == 'DOWNLOAD':
            path = os.path.normcase(os.path.normpath(os.path.abspath("".join(parts[1:]))))
            try:
                with open(path) as f:
                    data = f.read()
                    encoded = data.encode("hex")
                    self.request.sendall(json.dumps({"path": path, "filesize": len(data), "encoded": len(encoded), "data": encoded}))

            except IOError as e:
                self.request.sendall("no such file")

        elif parts[0] == 'UPLOAD':

            pathlength = int(data[len(parts[0]) + 1:len(parts[0]) + 11])
            path_start = len(parts[0]) + 11
            path_end = len(parts[0]) + 11 + pathlength
            dirty = data[path_start:path_end]
            path = os.path.normcase(os.path.normpath(os.path.abspath(dirty)))
            next_parts = data[path_end:].strip().split()
            filesize = next_parts[0]
            compressed = next_parts[1]
            filedata = next_parts[2]

            if os.path.isfile(path):
                return "file already exists"

            try:
                with open(path, "wb") as f:
                    f.write(filedata.decode("hex"))
            except:
                self.request.sendall("cannot upload file")
            self.request.sendall(json.dumps({"result": 0, "message": "File uploaded successfully"}))


        elif parts[0] == 'INFO':
            path = os.path.normcase(os.path.normpath(os.path.abspath("".join(parts[1:]))))
            output = {}
            output["path"] = path
            if os.path.isdir(path):
                output["info"] = {"type": "dir"}
            else:
                output["info"] = {"type": "file", "filesize": os.path.getsize(path)}

            self.request.sendall(json.dumps(output))

        elif parts[0] == 'BYE':
            self.request.sendall("BYE")
            return False
        else:
            return False

        return True

    def handle(self):

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
                    data = self.request.recv(int(length))
                    if self.process(self.request, data) is False:
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
