import os
import platform
import socket
import sys
import threading
import time

import utils
from constants import SERVER_PORT, MAX_BUFFER_SIZE


class ClientServer(object):
    quit_flag = False

    def __init__(self, upload_port: int):
        self.upload_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host_name = socket.gethostbyname(socket.gethostname())
        self.upload_port = upload_port

    def start_upload_server(self):
        try:
            self.upload_server_socket.bind((self.host_name, self.upload_port))
        except OSError as err:
            print('Binding of socket to given ip, port failed. Error Message: ' + str(err))
            sys.exit()

    @staticmethod
    def close():
        ClientServer.quit_flag = True

    def listen_upload_server(self):
        try:
            while not ClientServer.quit_flag:
                self.upload_server_socket.listen(3)
                (client_socket, socket_addr) = self.upload_server_socket.accept()
                print('\nConnection initialized on port : ', socket_addr[1])
                peer_thread = threading.Thread(target=self.peer_response, args=(client_socket,))
                peer_thread.start()
            print("Closed upload server")
            self.upload_server_socket.close()
        except KeyboardInterrupt:
            print("Closed asd server")
            self.upload_server_socket.close()

    @staticmethod
    def peer_response(peer_socket):
        response = peer_socket.recv(MAX_BUFFER_SIZE).decode()
        print('\nRequest:\n' + response)
        _, data = utils.extract_request_data(response)
        filename = f"RFC{data['rfc_number']}.txt"
        rfc_folder = os.path.join(os.getcwd(), 'rfc_files/')
        rfc_files = os.listdir(rfc_folder)
        if filename not in rfc_files:
            msg = utils.encapsulate_response_data(404)
            peer_socket.send(msg.encode())
        else:
            filename = os.path.join(rfc_folder, filename)
            curr_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + ' GMT'
            last_modified = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(os.path.getmtime(filename))) + ' GMT'
            msg = utils.encapsulate_response_data(200, file_size=os.path.getsize(filename), curr_datetime=curr_time,
                                                  os_info=f'{platform.system()} {platform.release()}',
                                                  last_modified=last_modified)
            peer_socket.send(msg.encode())
            with open(filename, 'r') as f:
                file_data = f.read(MAX_BUFFER_SIZE)
                peer_socket.send(file_data.encode())
                while file_data != "":
                    file_data = f.read(MAX_BUFFER_SIZE)
                    peer_socket.send(file_data.encode())
        peer_socket.close()
        print('Enter your choice:')
        sys.exit(0)


class Client(object):
    def __init__(self, server_ip: str, server_port: int, upload_port: int):
        self.client_server_socket = None
        self.server_ip = server_ip
        self.server_port = server_port
        self.host_name = socket.gethostbyname(socket.gethostname())
        self.upload_port = upload_port

    def register_rfc(self, rfc_number: str = None, rfc_title: str = None) -> str:
        if rfc_title is None:
            rfc_number = input('Enter the RFC Number: ')
            rfc_title = input('Enter the RFC Title : ')
        msg = utils.encapsulate_request_data('ADD', self.host_name, port=self.upload_port,
                                             rfc_number=f'RFC {rfc_number}', rfc_title=rfc_title)
        return utils.send_receive(msg, self.client_server_socket)

    def list_peer_rfcs(self) -> str:
        msg = utils.encapsulate_request_data('LIST', self.host_name, port=self.upload_port, rfc_number='ALL')
        return utils.send_receive(msg, self.client_server_socket)

    def lookup_rfc(self) -> str:
        rfc_number = input('Enter the RFC Number: ')
        rfc_title = input('Enter the RFC Title: ')
        msg = utils.encapsulate_request_data('LOOKUP', self.host_name, port=self.upload_port,
                                             rfc_number=f'RFC {rfc_number}', rfc_title=rfc_title)
        return utils.send_receive(msg, self.client_server_socket)

    def unregister_rfc(self) -> str:
        msg = utils.encapsulate_request_data('DEL', self.host_name, port=self.upload_port, rfc_number='SELF')
        return utils.send_receive(msg, self.client_server_socket)

    @staticmethod
    def peer_download_request(peer_host_name: str, peer_upload_port: int, rfc_number: str):
        if rfc_number is None:
            raise Exception('Invalid RFC Number')
        msg = utils.encapsulate_request_data('GET', peer_host_name, rfc_number=f'RFC {rfc_number}',
                                             os_info=f'{platform.system()} {platform.release()}')
        filename = os.path.join(os.getcwd(), f'rfc_files/RFC{rfc_number}.txt')

        p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        p2p_socket.connect((peer_host_name, peer_upload_port))
        p2p_socket.send(msg.encode())
        header = p2p_socket.recv(MAX_BUFFER_SIZE).decode()
        print('\nResponse Header:\n' + header)
        print(f'File is Downloaded at', filename)
        data = p2p_socket.recv(MAX_BUFFER_SIZE).decode()
        with open(filename, "w") as f:
            while data:
                f.write(data)
                data = p2p_socket.recv(MAX_BUFFER_SIZE).decode()

        p2p_socket.close()
        return 0

    def connect_to_server(self):
        self.client_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_server_socket.connect((self.server_ip, self.server_port))
        while not ClientServer.quit_flag:
            selection = menu()
            match selection:
                case '1':
                    self.register_rfc()
                case '2':
                    self.list_peer_rfcs()
                case '3':
                    self.lookup_rfc()
                case '4':
                    res = utils.extract_response_data(self.lookup_rfc())
                    if res['status_code'] == '200':
                        peer = res['peers'][0]
                        self.peer_download_request(peer['host_name'], int(peer['upload_port']), peer['rfc_number'])
                        self.register_rfc(rfc_number=peer['rfc_number'], rfc_title=peer['rfc_title'])
                case '5':
                    self.unregister_rfc()
                    ClientServer.close()
                case _:
                    print('Invalid Input. Enter again: ')
        self.client_server_socket.close()
        print("Closed client server connect")


def menu():
    print('\n************Select option*******************')
    print('1. Register RFC')
    print('2. List all RFCs')
    print('3. Lookup RFC')
    print('4. Download RFC')
    print('5. Quit (Press Ctrl+C after status: OK)')
    return input('Enter your choice:')


def main():
    server_port = SERVER_PORT
    upload_port = int(input('Enter the upload port: '))
    client_server = ClientServer(upload_port)
    client_server.start_upload_server()
    server_name = input('Enter the server IP: ')
    client = Client(server_name, server_port, upload_port)
    try:
        upload_server_thread = threading.Thread(name='upload_server_thread', target=client_server.listen_upload_server)
        upload_server_thread.setDaemon(True)
        upload_server_thread.start()
        connect_server_thread = threading.Thread(name='connect_to_server_thread', target=client.connect_to_server)
        connect_server_thread.setDaemon(True)
        connect_server_thread.start()
        connect_server_thread.join()
        upload_server_thread.join()
    except KeyboardInterrupt:
        client_server.quit_flag = True


if __name__ == '__main__':
    main()
