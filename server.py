"""
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
"""


import socket
import threading
import requests
import time

# IP, PORT = input("Server address: ").split(":", 2)#"127.0.0.1"
IP = "127.0.0.1"
PORT = 5000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, int(PORT)))
server_socket.listen()

sockets_list = [server_socket]
clients = {}
users = []
threads = []


def decode_msg(msg):
    msg = msg.decode()
    if "§" in msg:
        usr, msg = msg.split("§", 2)
    else:
        print("decode_msg: No § in msg")
    if not usr or not msg:
        print(
            "decode_msg: either usr or msg is empty! usr:%s | msg:%s" %
            (usr, msg)
        )
        usr = "broken_usr"
        msg = "broken_msg"
    return usr, msg


def encode_msg(usr, msg):
    msg = usr + "§" + msg
    msg = msg.encode()
    return msg


def client_thread(client_socket, client_address):
    while True:
        message = client_socket.recv(4096)
        if not message:
            client_socket.close()
            print("Lost connection to %s:%s" % client_address)
            break
        user, message = decode_msg(message)
        if message == "LOG OFF":
            for sock in sockets_list:
                if sock != server_socket:
                    sock.send(encode_msg(user, message))
            client_socket.close()
            print(user + " logged off")
            break
        if not user:
            continue
        print(user + " > " + message)
        if client_socket in sockets_list:
            for sock in sockets_list:
                if sock != server_socket:
                    sock.send(encode_msg(user, message))
        else:
            if message == "LOG ON":
                if user in users or user == "[SERVER]":
                    client_socket.send(
                        encode_msg("[SERVER]", "Username already taken")
                    )
                    client_socket.close()
                    break
                else:
                    for sock in sockets_list:
                        if sock != server_socket:
                            sock.send(encode_msg(user, message))
                    sockets_list.append(client_socket)
                    clients[client_socket] = user
                    users.append(user)
                    print(
                        "Accepted new connection from %s:%s, username: %s" %
                        (*client_address, user)
                    )
                    client_socket.send(
                        encode_msg("[SERVER]", "Connection accepted")
                    )
                    for usr in users:
                        print("userlist sending: " + usr)
                        time.sleep(.1)
                        client_socket.send(encode_msg("[userlist]", usr))
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
