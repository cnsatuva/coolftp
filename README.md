# Cool File Transfer Protocol

Cool File Transfer Protocol is a simple file transfer protcol that uses plain english commands and ASCII-only transfers. Cool FTP doesn't use encryption natively. For secure file transfers, tunnel the connection over stunnel or a similar application.

Since Cool FTP is ASCII-only, all files will be uploaded and downloaded as base64-encoded data.

How it works
---

All connections should be made to the server with TCP. On connection open, the server will expect the 5 byte message ```HELLO```, and it will respond with ```HELLO```. If the server has a password, it will instead respond with ```PASSWORD``` and require the client to return the predetermined password. If an incorrect password is passed, the connection will be dropped.

After a connection has been established, the server will accept one of the following commands. Note that the connection will be dropped 600 seconds after the last command.

#### LIST [dir]

```LIST``` will return a formatted JSON response containing files in the ```dir``` directory, as well as metadata about each file. If ```dir``` is not given, ```LIST``` will return information for the default user directory.

**Example Request/Response**

```
LIST /home/johndoe

{
    "path": "/home/johndoe",
    "files": {
        "/home/johndoe/hello.txt": {
            "filesize": 1024
        },
        "/home/johndoe/foobar.sh": {
            "filesize": 324
        }
    }
}
```

#### DOWNLOAD \<path\>

```DOWNLOAD``` will return the file denoted by ```path```. Paths given should be absolute - relative paths will result in an error. Note that ```encoded``` indicates the hex encoded filesize and ```filesize``` is the uncompressed filesize.

**Example Request/Response**

```
DOWNLOAD /home/johndoe/hello.txt

{
	"path": "/home/johndoe",
	"filesize": 1024,
	"encoded": 1053,
	"data": "4C6F7265..."
}
```

#### UPLOAD \<path\> \<filesize\> \<compressed\> \<filedata\>

```UPLOAD``` will upload and store the ```filedata``` with length ```filesize``` at the path ```path```. The path given should be an absolute path - relative paths will result in an error. ```filedata``` should be the hex-encoded filedata, with length ```compressed```.

Any value besides 0 indicates an error, with message denoted by the ```message``` field.

**Example Request/Response**

```
UPLOAD /home/johndoe/binary.file 1024 1053 4C6F7265...

{
	"result": 0,
	"message": "File uploaded successfully"
}
```

#### INFO \<path\>

```INFO``` will return file information for the path given. Path must be absolute - relative paths will result in an error. The file information given by ```INFO``` is the same format used for each file individually in the ```LIST``` command

**Example Request/Response**

```
INFO /home/johndoe/binary.file

{
	"path": "/home/johndoe/binary.file",
	"info": {
		"filesize": 1024
	}
}
```

#### BYE

Ends the connection. Server will respond with ```BYE``` and immediately end the connection.

Security
---

By default, Cool FTP does not encrypt the connection. For secure file transfers, use stunnel or something similar.

Connecting to the server does not require passwords by default. However, the server can optionally respond to the initial ```HELLO``` with ```PASSWORD```, and require the client to respond with a predetermined password. If an incorrect password is passed, the connection will be dropped.

If users do not have permission to access a given file, it will not be visible to the client. Attempts to download it will result in a non-existent file error. **However, users can find protected files by attempting to upload to an protected file's path and receiving an error!**
