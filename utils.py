from constants import *


def add_padding(msg: str) -> str:
    length = len(msg)
    while length < MAX_BUFFER_SIZE:
        msg += '~'
        length += 1
    return msg


def remove_padding(response: str) -> str:
    i = 0
    for i in range(len(response)):
        if response[i] == '~':
            break
    return response[:i]


def send_receive(msg, client_socket):
    msg = add_padding(msg)
    client_socket.send(msg.encode())
    response = client_socket.recv(MAX_BUFFER_SIZE).decode()
    response = remove_padding(response)
    print('\nResponse:\n' + str(response))
    return response


def encapsulate_request_data(method: str, host: str, port: int = 0, rfc_number: str = '', rfc_title: str = '',
                             os_info: str = '') -> str:
    """Encapsulates request data addressed to the peer into protocol.

    Args:
        method: any of the 4 -> GET, ADD, LIST, LOOKUP.
        host: hostname of the host sending the request.
        port: port to which the upload server of the host is attached.
        rfc_number: (optional) value to this parameter should have 'RFC' prefix. eg: RFC 123
        rfc_title: (optional) title of the RFC.
        os_info: (optional) for GET RFC request to download.

    Returns:
        encapsulated data to be sent to server as request.
    """
    data = f'{method} {rfc_number} {PROTOCOL}\nHost: {host}\n'
    if port:
        data += f'Port: {str(port)}\n'
    if rfc_title and os_info:
        raise Exception('RFC Title and OS can\'t be part of on datagram')
    if rfc_title:
        data += f'Title: {rfc_title}\n'
    if os_info:
        data += f'OS: {os_info}\n'
    return data


def extract_request_data(request_data: str) -> (str, dict):
    """Extracts request from the protocol that is received from the peer.

    Extracts request message from P2P-CI/1.0 protocol and calls helper
    function to prepare response message back to the peer.

    Args:
        request_data: the entire P2P-CI/1.0 protocol as a string.

    Returns:
        a tuple os (str, dict). Protocol Action as str and request_header as dictionary.
    """
    data_list = request_data.split()
    method = data_list[0].upper()
    version = data_list[3] if method not in ['LIST', 'DEL'] else data_list[2]
    assert version == PROTOCOL, 'Exception: Undefined App Layer Protocol...'

    peer_info = dict()
    peer_info['host'] = data_list[data_list.index('Host:') + 1]

    if 'Port:' in data_list:
        peer_info['port'] = data_list[data_list.index('Port:') + 1]

    if method.upper() not in ['LIST', 'DEL']:
        peer_info['rfc_number'] = data_list[2]

    if 'Title:' in data_list:
        peer_info['rfc_title'] = ' '.join(data_list[data_list.index('Title:') + 1:])

    if 'OS:' in data_list:
        peer_info['os_info'] = ' '.join(data_list[data_list.index('OS:') + 1:])

    return method, peer_info


def encapsulate_response_data(status_code: int, phrase: str = None, list_active_peers: list = [], file_size: int = 0,
                              curr_datetime: str = None, os_info: str = None, last_modified: str = None) -> str:
    """Encapsulates response data addressed to the peer into protocol.

    Prepares the response message back for the peer by encapsulating
    response data addressed to the peer into P2P-CI/1.0 protocol.

    Args:
        status_code: status code indicates of the success or failure
                     of the request. Based on HTTP status code.
        phrase: phrase indicates the additional information of the
                failure of the request or its success. Based on HTTP status
                code.
        list_active_peers: list of active peers at the current moment.
        file_size: applicable for file download response
        curr_datetime: applicable for file download response
        os_info: applicable for file download response
        last_modified: applicable for file download response

    Returns:
        encapsulated data to be sent back to client as response.
    """
    data = f'{PROTOCOL} {status_code}'
    data += f' {phrase}\n' if phrase else f' {STATUS_CODE_MESSAGE[status_code]}\n'
    for active_peer in list_active_peers:
        data += f'{active_peer}\n'
    if curr_datetime:
        data += f'Date: {str(curr_datetime)}\n'
    if os_info:
        data += f'OS: {str(os_info)}\n'
    if last_modified:
        data += f'Last-Modified: {str(last_modified)}\n'
    if file_size:
        data += f'Content-Length: {str(file_size)}\nContent-Type: text/plain\n'

    return data


def extract_response_data(request_data: str) -> dict:
    """Extracts response from the protocol that is received from the server.
        This function should not be used for response from peer/upload server to download file.
    Args:
        request_data: the entire P2P-CI/1.0 protocol as a string.

    Returns:
        response_header as dictionary.
    """
    data_list = request_data.split('\n')
    header = data_list[0].split()
    version = header[0]
    assert version == PROTOCOL, 'Exception: Undefined App Layer Protocol...'

    response = dict()
    response['status_code'] = header[1]
    response['status_message'] = header[2]

    if len(data_list) > 1:
        response['peers'] = list()
        for rfc in data_list[1:]:
            rfc = rfc.split()
            peer_info = dict()
            peer_info['rfc_number'] = rfc[1]
            peer_info['rfc_title'] = rfc[2]
            peer_info['host_name'] = rfc[-2]
            peer_info['upload_port'] = rfc[-1]
            response['peers'].append(peer_info)

    return response
