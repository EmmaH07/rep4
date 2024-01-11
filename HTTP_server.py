"""
Author: Barak Gonen and Nir Dweck
EDITOR: Emma Harel
DATE 9.1.24
Description: HTTP server
"""
import os
import re
import socket
import logging

QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
MAX_PACKET = 1024
WEB_ROOT = 'webroot'
DEFAULT_URL = '\index.html'
REDIRECTION_DICTIONARY = {"/forbidden": "403 FORBIDDEN", "/error": "500 INTERNAL SERVER ERROR"}
CONTENT_TYPES = {
    '.html': 'text/html;charset=utf-8', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.js': "text/javascript; charset=UTF-8", '.css': 'text/css', '.txt': 'text/plain', '.ico': 'image/x-icon',
    '.gif': 'image/jpeg'
}

logging.basicConfig(filename='HTTP_server.log', level=logging.DEBUG)


def get_file_data(file_name):
    """
    Get data from file
    :param file_name: the name of the file.
    :return: the file data in bytes.
    """
    file_path = WEB_ROOT + "\\" + file_name
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        return data
    except FileNotFoundError:
        logging.error(f"Error: File '{file_name}' not found.")
        return None  # Return None to indicate file not found
    except PermissionError:
        logging.error(f"Error: Permission denied to access file '{file_name}'.")
        return None  # Return None to indicate permission error
    except Exception as e:  # Catch any other unexpected errors
        logging.error(f"Error reading file '{file_name}': {str(e)}")
        return None  # Return None to signal an error


def handle_client_request(resource, client_socket):
    """
    Check the required resource, generate proper HTTP response and send
    to client
    :param resource: the required resource
    :param client_socket: a socket for the communication with the client
    :return: None
    """

    if resource == '/':
        uri = DEFAULT_URL
    else:
        uri = resource

    if uri in REDIRECTION_DICTIONARY.keys():
        response = (f"HTTP/1.1 {REDIRECTION_DICTIONARY[uri]}\r\nContent-Length: {len(REDIRECTION_DICTIONARY[uri])}"
                    f"\r\n\r\n")
        client_socket.sendall(response.encode())
        client_socket.close()
        return

    elif uri == '/moved':
        msg = '302 MOVED TEMPORARILY'
        response = f"HTTP/1.1 {msg}\r\nLocation: {DEFAULT_URL}\r\nContent-Length: {len(msg)}\r\n\r\n"
        client_socket.sendall(response.encode())
        client_socket.close()
        return

    data = get_file_data(uri)

    if data is None:
        data = get_file_data('404pic.png')
        if data is not None:
            response = (f"HTTP/1.1 404 NOT FOUND\r\nContent-Type: image/png\r\nContent-Length: {len(data)}\r\n"
                        f"Not Found\r\n\r\n")
            client_socket.sendall(response.encode() + data)
            client_socket.close()
        else:
            msg = 'NOT FOUND'
            response = (f"HTTP/1.1 {msg}\r\nContent-Type: text/plain\r\nContent-Length: {len(msg)}\r\n\r\n"
                        f"Not Found\r\n\r\n")
            client_socket.sendall(response.encode())
            client_socket.close()
        return

    filename, file_extension = os.path.splitext(uri)

    if file_extension == '.html':
        content_type = 'text/html;charset=utf-8'
    elif file_extension in ('.jpg', '.jpeg'):
        content_type = 'image/jpeg'
    elif file_extension == '.png':
        content_type = 'image/png'
    elif file_extension == '.js':
        content_type = "text/javascript; charset=UTF-8"
    elif file_extension == '.css':
        content_type = 'text/css'
    elif file_extension == '.txt':
        content_type = 'text/plain'
    elif file_extension == '.ico':
        content_type = 'image/x-icon'
    elif file_extension == '.gif':
        content_type = 'image/jpeg'
    else:
        content_type = 'application/octet-stream'  # Default content type

    response = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(data)}\r\n\r\n"
    client_socket.sendall(response.encode() + data)
    client_socket.close()


def validate_http_request(request):
    """
    Check if request is a valid HTTP request and returns TRUE / FALSE and
    the requested URL
    :param request: the request which was received from the client
    :return: a tuple of (True/False - depending on if the request is valid,
    the requested resource )
    """
    http_pattern = r"^GET (.*) HTTP/1.1"  # Pattern to match the GET request and URL
    match = re.search(http_pattern, request)

    if match:
        requested_url = match.group(1)
        return True, requested_url
    return False, "400 BAD REQUEST"


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP, calls
    function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    logging.debug('Client connected')
    try:
        while True:
            client_request = client_socket.recv(MAX_PACKET).decode()
            while not client_request.endswith("\r\n\r\n"):
                client_request += client_socket.recv(MAX_PACKET).decode()

                if client_request == '':
                    break
            valid_http, resource = validate_http_request(client_request)

            if valid_http:
                logging.debug('Got a valid HTTP request')
                handle_client_request(resource, client_socket)

            else:
                logging.error('Error: Not a valid HTTP request')
                response = f"HTTP/1.1 400 BAD REQUEST\r\n\r\n"
                client_socket.sendall(response.encode())
                logging.debug('Closing connection')
                break

        if client_request == '':
            client_socket.close()

    except KeyboardInterrupt:
        logging.error('received KeyboardInterrupt')

    except socket.error as err:
        logging.error('received socket exception - ' + str(err))


# Main function
def main():
    """Starts the server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        logging.debug("Listening for connections on port %d" % PORT)

        while True:
            client_socket, client_address = server_socket.accept()
            try:
                logging.debug('New connection received')
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
            except socket.error as err:
                logging.error('received socket exception - ' + str(err))
    except socket.error as err:
        logging.error('received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    assert validate_http_request("Get Falafel") == (False, "400 BAD REQUEST")
    assert get_file_data('cyber') is None
    main()
