# Peer to peer with Centralized Index.
In this project, our aim is to implement a simple peer-to-peer (P2P) system with a centralized index (CI) for downloading RFCs. 
Sample RFCs are initially downloaded from the IETF web site (http://www.ietf.org/). 
Rather than using this centralized server for downloading RFCs, we built a P2P-CI system in which peers who wish to
download an RFC that they do not have in their hard drive, may download it from another active peer who does.
All communication among peers or between a peer and the server take place over TCP.

## Team-members:
- Vishaka Yadav (vyadav)
- Nisarg Shah (nsshah5)

## Prerequisites:
Python version >= 3.10
OS: any except Windows.

## Restrictions:
- All RFC files that are initially taken from the IETF web-site should follow the naming convention `RFC<rfc_number>.txt` (case-sensitive)
- Since the processes are multithreaded, it is important to follow the steps for smooth exit.
  - Use the `5. Quit` menu option for all the running peers, and then press Ctrl+C if required.
  - Once all the peer are stopped, do `Ctrl+C` on the centralized_server.py process

## I. Steps to run the server side 
- Run the Server: $python CentralizedServer.py (We have used python version 3.10) 

## II. Steps to run the Peer side 
- Run peer on one of the peer $python Peer.py
- Enter the Upload Port (any available port) for Peer-to-Peer communication
- Enter Server IP (IP of the centralized server) for RFC registration

> Multiple ports can support different peers.

### Menu Options available on Client/Peer Side

Here are a list of options that come up for a Peer.
1. Register RFC:  _request on server to register the peer along with the rfc details_
2. List all RFCs: _request on server to list all registered rfcs_
3. Lookup RFC: _request on server to find a rfc with given number and title_
4. Download RFC: _using lookup functionality, host gets the peer information that already has the rfc and then request is sent to this peer for file download followed by request on server to register the new rfc corresponding to the host._
5. Quit (Press Ctrl+C after status: OK): _unregisters the peer on server before quitting_


## III. Project Folder Structure
```
P2P-CI
├── rfc_files                   # Folder with RFC files, new RFCs are downloaded here
│   ├── RFC123.txt              # sample RFC file
│   └── ...                     # etc.
├── centralized_server.py       # server code
├── constants.py                # file with constants used across the project
├── peer.py                     # peer code with upload server and menu driven program
├── proj1.pdf                   # CSC 573 project 1 description
├── README.md                   # Documentation file
└── utils.py                    # include utility functions used across client and server
```

- Copy the rfcs from http://www.ietf.org/ under `rfc_files` folder.
- Naming Convention for the copied file is: RFC<rfc_number>.txt
- We have a sample RFC file - `RFC123.txt` for testing purpose.
- The new RFCs are downloaded at `P2P-CI/rfc_files/`


## P2P-CI/1.0 protocol
For this project, specific application layer protocol is defined for the Register Server and peers to communicate among themselves.
### Peer-to-Register Server P2P-CI/1.0 communication protocol
Peer-to-Register Server __REQUEST__ message format is defined as follows:
```
-----------------------------------------------------
| Method  | RFC Number | Protocol name and version  |
-----------------------------------------------------
| Host:   |                  IPv4                   |
-----------------------------------------------------
| Port:   |                 Integer                 |
-----------------------------------------------------
| Title:  |              Title of RFC               |
-----------------------------------------------------
```
There are three methods:
- ADD, to add a locally available RFC to the server’s index,
- LOOKUP, to find peers that have the specified RFC, and
- LIST, to request the whole index of RFCs from the server.


Register Server-to-Peer __RESPONSE__ message format in response for request messages is defined as follows:
```
----------------------------------------------------------
| Protocol name and version |  Status Code |   Phrase    |
----------------------------------------------------------
|              OPTIONAL FIELD (Only for success)         |
|                REPEATED for list Operations            |
|                                                        |
| RFC Number |  RFC Title   |   Hostname   | Upload Port |
----------------------------------------------------------
```

### Peer-to-Peer (Peer-to-Peer Server) P2P-CI/1.0 communication protocol
Peer-to-Peer Server (another peer) `GET RFC` __REQUEST__ message format is defined as follows:
```
-----------------------------------------------------
| Method  | RFC Number | Protocol name and version  |
-----------------------------------------------------
| Host:   |                  IPv4                   |
-----------------------------------------------------
| OS:     |                 System                  |
-----------------------------------------------------

```
Example:
GET RFC 123 P2P-CI/1.0
Host: 192.168.1.137
OS: Darwin 20.5.0

RFC Server-to-Peer __RESPONSE__ message format in response for `GET RFC` request message is defined as follows. Note that protocol itself comes as plane text, but the requested RFC document in the binary mode:
```
--------------------------------------------------------
| Protocol name and version |  Status Code  |  Phrase  |
--------------------------------------------------------
| Date:           |  weekday, dd mmm yyyy %H:%M:%S GMT |
--------------------------------------------------------
| OS:             |               System               |
--------------------------------------------------------
| Last Modified:  |  weekday, dd mmm yyyy %H:%M:%S GMT |
--------------------------------------------------------
| Content-Length: |               Integer              |
--------------------------------------------------------
| Content-Type:   |              text/plain            |
--------------------------------------------------------
                Wait for Accepting message 
--------------------------------------------------------
|                                                      |
|                         RFC                          |
|                    (Binary Mode)                     |
|                                                      |
--------------------------------------------------------
```

## Example for each Request and Response

>**Request to Register RFC:**\
`ADD RFC 123 P2P-CI/1.0`\
`Host: 192.168.1.137`\
`Port: 8080`\
`Title: qwe`\
**Response:**\
`P2P-CI/1.0 200 OK`\
`RFC 123 qwe 192.168.1.137 8080`


>**Request to List All RFCs**\
`LIST ALL P2P-CI/1.0`\
`Host: 192.168.1.137`\
`Port: 8080`\
**Success Response:**\
`P2P-CI/1.0 200 OK`\
`RFC 123 qwe 192.168.1.137 8080`\
`RFC 123 abc 192.168.1.137 8081`


>**Request to Lookup RFC** - RFC Number 123 and RFC Title qwe\
`LOOKUP RFC 123 P2P-CI/1.0`\
`Host: 192.168.1.137`\
`Port: 8080`\
`Title: qwe`\
**Success Response:**\
`P2P-CI/1.0 200 OK`\
`RFC 123 qwe 192.168.1.137 8080`


>**Request to Peer for file download**\
`GET RFC 123 P2P-CI/1.0`\
`Host: 192.168.1.137`\
`OS: Darwin 20.5.0`\
**Success Response:**\
`P2P-CI/1.0 200 OK`\
`Date: Tue, 08 Nov 2022 07:17:34GMT`\
`OS: Darwin 20.5.0`\
`Last-Modified: Mon, 07 Nov 2022 11:37:40 GMT`\
`Content-Length: 4805`\
`Content-Type: text/plain`\
`data ....`

- **Error Responses:**
    - `P2P-CI/1.0 404 Not Found`
    - `P2P-CI/1.0 400 Bad Request`
    - `P2P-CI/1.0 505 P2P-CI Version Not Supported`
