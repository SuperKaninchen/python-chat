'''
Python chat using sockets and TKinter
Copyright (C) 2019  Max Nijenhuis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''


import socket
import threading
import requests
import time
import requests
import netifaces
import sys

# IP, PORT = input('Server address: ').split(':', 2)#'127.0.0.1'
IP = '127.0.0.1'
PORT = 5000

default_gateway_if = netifaces.gateways()['default'][netifaces.AF_INET][1]
ip_of_default_gateway_if = netifaces.ifaddresses(default_gateway_if)[netifaces.AF_INET][0]['addr']

def usage():
    print("usage: server.py [dyndns-register-url]")
    print("example: server.py http://tdyn.de/MY-PRIVATE-KEY")
    sys.exit(1)

if len(sys.argv) > 1:
    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
        usage()
    dyndns_base_url = sys.argv[1]
    try:
        dyndns_url = "%s?%s" % (dyndns_base_url, ip_of_default_gateway_if)
        r = requests.get(dyndns_url)
        if r.status_code == 200:
            print("IP# %s successfully registered as DynDNS host" % (ip_of_default_gateway_if))
            print("IP# returned from DynDNS server: %s" % (r.text))
            IP = r.text
        else:
            print("Failed to register IP %s, status code: %s" % (ip_of_default_gateway_if, r.status_code))
    except Exception as e:
        print("Error on DynDNS registration")
        sys.exit(1)


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, int(PORT)))
server_socket.listen()

sockets_list = [server_socket]
clients = {}
users = []
known_users = []
known_passwds = []
with open('users') as f:
    for line in f.readlines():
        known_user, known_passwd = line.split(':;', 2)
        known_users.append(known_user)
        known_passwds.append(known_passwd)
threads = []
error_text = '\033[31;1m' + '[ERROR] ' + '\033[m'
failed_login_text = '[SERVER]: Failed login attempt from %s:%s, username: %s'


def decode_msg(msg):
    msg = msg.decode()
    if ':' in msg:
        usr, msg = msg.split(':', 2)
    else:
        print(
            error_text
            + 'decode_msg: No : in msg'
            )
    if not usr or not msg:
        print(
            error_text
            + 'decode_msg: either usr or msg is empty! usr:%s | msg:%s' %
            (usr, msg)
        )
        usr = 'broken_usr'
        msg = 'broken_msg'
    return usr, msg


def encode_msg(usr, msg):
    msg = usr + ':' + msg
    msg = msg.encode()
    return msg


def update_users_file():
    with open('users', 'w') as f:
        for usr in known_users:
            line = usr + ':;' + known_passwds[known_users.index(usr)]
            f.write(line + '\n')


def client_thread(client_socket, client_address):
    while True:
        message = client_socket.recv(4096)
        if not message:
            client_socket.close()
            print('Lost connection to %s:%s' % client_address)
            break
        user, message = decode_msg(message)
        if message == 'LOG OFF':
            for sock in sockets_list:
                if sock != server_socket:
                    sock.send(encode_msg(user, message))
            client_socket.close()
            print(user + ' logged off')
            sockets_list.remove(client_socket)
            del clients[client_socket]
            users.remove(user)
            break
        if not user:
            continue
        print(user + ' > ' + message)
        if client_socket in sockets_list:
            for sock in sockets_list:
                if sock != server_socket:
                    sock.send(encode_msg(user, message))
        else:
            if 'LOG ON' in message:
                if user in users or user == '[SERVER]':
                    client_socket.send(
                        encode_msg('[SERVER]', 'Username already taken')
                    )
                    client_socket.close()
                    break
                else:
                    if user in known_users:
                        logon, given_passwd = message.split('||', 2)
                        required_passwd = known_passwds[
                            known_users.index(user)
                        ].rstrip()
                        print(required_passwd)
                        if given_passwd != required_passwd:
                            client_socket.send(
                                encode_msg(
                                    '[SERVER]',
                                    'WRONG PASSWORD'
                                )
                            )
                            client_socket.close()
                            print(
                                failed_login_text % (*client_address, user)
                            )
                            break
                    else:
                        logon, given_passwd = message.split('||', 2)
                        known_users.append(user)
                        known_passwds.append(given_passwd)
                        update_users_file()
                    message, given_passwd = message.split('||', 2)
                    for sock in sockets_list:
                        if sock != server_socket:
                            sock.send(encode_msg(user, message))
                    sockets_list.append(client_socket)
                    clients[client_socket] = user
                    users.append(user)
                    print(
                        'Accepted new connection from %s:%s, username: %s' %
                        (*client_address, user)
                    )
                    client_socket.send(
                        encode_msg('[SERVER]', 'Connection accepted')
                    )
                    for usr in users:
                        print('userlist sending: ' + usr)
                        time.sleep(.1)
                        client_socket.send(encode_msg('[userlist]', usr))
                    continue
            else:
                continue


def runserver():
    while True:
        client_socket, client_address = server_socket.accept()
        newthread = threading.Thread(
            target=client_thread,
            args=(client_socket, client_address,)
        )
        newthread.start()
        threads.append(newthread)


if __name__ == '__main__':
    print('Starting server on %s:%s' % (IP, PORT))
    runserver()

# use modeline modelines=1 in vimrc
# vim: set fileencoding=utf-8 sta sts=4 sw=4 ts=4 ai et:
