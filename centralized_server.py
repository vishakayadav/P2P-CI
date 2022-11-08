import socket
import sys
import threading

import utils
from constants import SERVER_PORT, MAX_BUFFER_SIZE


class ActivePeer:
    def __init__(self, host='None', port='None'):
        self.host_name = host
        self.upload_port = port

    def __str__(self):
        return f'Host Name: {str(self.host_name)} Upload Port: {str(self.upload_port)}'

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.host_name == other.host_name and self.upload_port == other.upload_port
        return False


class RFC:
    def __init__(self, rfc_number='None', rfc_title='None', active_peer=ActivePeer()):
        self.rfc_number = rfc_number
        self.rfc_title = rfc_title
        self.rfc_active_peer = active_peer

    def __str__(self):
        return (f'RFC {str(self.rfc_number)} {str(self.rfc_title)} '
                f'{str(self.rfc_active_peer.host_name)} {str(self.rfc_active_peer.upload_port)}')

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.rfc_number == other.rfc_number and \
                   self.rfc_title == other.rfc_title and \
                   self.rfc_active_peer == other.rfc_active_peer
        return False


class CentralizedServer(object):
    def __init__(self, RFCs=None, peers=None) -> None:
        self.active_RFCs = RFCs if RFCs else []
        self.active_peers = peers if peers else []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host_name = socket.gethostbyname(socket.gethostname())

    def start(self):
        try:
            self.server_socket.bind((self.host_name, SERVER_PORT))  # Bind to the port
        except OSError as err:
            print('Binding to local address unsuccessful. Error Message: ' + str(err))
            sys.exit()
        try:
            while True:
                self.server_socket.listen(50)
                # Accepting connections
                (conn, socket_info) = self.server_socket.accept()
                # Spawn thread for each peer connection
                server_thread = threading.Thread(target=self.handle_client_request, args=(conn,))
                server_thread.start()
        except KeyboardInterrupt:
            self.server_socket.close()
            sys.exit(0)

    def register(self, peer_info, peer_socket):
        peer = ActivePeer(peer_info['host'], peer_info['port'])
        if peer not in self.active_peers:
            self.active_peers.append(peer)
        rfc = RFC(peer_info['rfc_number'], peer_info['rfc_title'], peer)
        if rfc not in self.active_RFCs:
            self.active_RFCs.append(rfc)
        msg = utils.encapsulate_response_data(200, list_active_peers=[rfc])
        peer_socket.send(msg.encode())

    def lookup(self, peer_info, peer_socket):
        relevant_RFCs = [active_RFC for active_RFC in self.active_RFCs if
                         active_RFC.rfc_number == peer_info['rfc_number'] and active_RFC.rfc_title == peer_info[
                             'rfc_title']]
        if len(relevant_RFCs) <= 0:
            msg = utils.encapsulate_response_data(404)
        else:
            msg = utils.encapsulate_response_data(200, list_active_peers=relevant_RFCs)
        peer_socket.send(msg.encode())

    def list(self, peer_socket):
        if len(self.active_RFCs) <= 0:
            msg = utils.encapsulate_response_data(404)
        else:
            msg = utils.encapsulate_response_data(200, list_active_peers=self.active_RFCs)
        peer_socket.send(msg.encode())

    def delete_peer(self, peer_info, peer_socket):
        copy_active_RFCS = []
        for active_RFC in self.active_RFCs:
            if active_RFC.rfc_active_peer.host_name == peer_info['host'] and \
                    active_RFC.rfc_active_peer.upload_port == peer_info['port']:
                continue
            else:
                copy_active_RFCS.append(active_RFC)
        self.active_RFCs[:] = copy_active_RFCS
        copy_active_peers = []
        for active_peer in self.active_peers:
            if active_peer.host_name == peer_info['host'] and active_peer.upload_port == peer_info['port']:
                continue
            else:
                copy_active_peers.append(active_peer)
        self.active_peers[:] = copy_active_peers
        msg = utils.encapsulate_response_data(200)
        peer_socket.send(msg.encode())

    def handle_client_request(self, peer_socket):
        try:
            while True:
                response = peer_socket.recv(MAX_BUFFER_SIZE).decode()
                if len(response) == 0:
                    peer_socket.close()
                    return
                response = utils.remove_padding(response)
                print('\nRequest:\n' + response)
                action, peer_info = utils.extract_request_data(response)
                if action == 'ADD':
                    self.register(peer_info, peer_socket)
                elif action == 'LOOKUP':
                    self.lookup(peer_info, peer_socket)
                elif action == 'LIST':
                    self.list(peer_socket)
                elif action == 'DEL':
                    self.delete_peer(peer_info, peer_socket)
        except KeyboardInterrupt:
            peer_socket.close()
            sys.exit(0)


if __name__ == '__main__':
    CentralizedServer().start()
