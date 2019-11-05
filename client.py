import socket
import threading
from functools import partial
from tkinter import *
from tkinter import scrolledtext
import tkinter


def decode_msg(msg):
    msg = msg.decode()
    if msg == "Username already taken":
        print("Username already taken on that server")
        return "", "stop"
        disconnect()
    usr, msg = msg.split("§", 2)
    return usr, msg
def encode_msg(usr, msg):
    msg = usr + "§" + msg
    msg = msg.encode()
    return msg


IP = "1.2.3.4"
PORT = 1234
my_username = "guest"
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = "none"

config_file = open("config.txt")
servers_file = open("servers.txt")
known_servers = servers_file.readlines()

window = Tk()
window.minsize(600, window.winfo_reqheight())
windowHeight = window.winfo_height()
windowWidth = window.winfo_width()

main_frame = Frame(window, width=600, height=600, bg="green")
chat_frame = Frame(main_frame, width=500, height=500, bg="blue")
chat_text = Text(chat_frame, width=500, height=500, font="Courier 26")
entry_text = Text(main_frame)
menubar = Menu(window)
bookmark_menu = Menu(menubar, tearoff = 0)

def send_msg(*args):
    global connected
    if connected is "none":
        print("[ERROR] send_msg: currently not connected")
    else:
        msg = entry_text.get("1.0", "end-1c")
        client_socket.send(encode_msg(my_username, msg))
        #msg = msg + " < " + my_username
        print(my_username + " > " + msg)
        chat_text["state"] = NORMAL
        chat_text.insert("end", msg, ("right"))
        chat_text.insert("end", " < ", ("right", "green"))
        chat_text.insert("end", my_username + "\n", ("right", "blue"))
        chat_text["state"] = DISABLED
        entry_text.delete("1.0", "end")

def receive_msg():
    while True:
        try:
            user, message = decode_msg(client_socket.recv(4096))
            if message == "stop":
                break
            if user != my_username:
                msg = user + " > " + message
                chat_text["state"] = NORMAL
                chat_text.insert("end", user, ("left", "blue"))
                chat_text.insert("end", " > ", ("left", "green"))
                chat_text.insert("end", message + "\n", ("left"))
                chat_text["state"] = DISABLED
                print(user + " > " + message)

        except Exception as e:
            print('[ERROR] receive_msg: Reading error: '+str(e))
            break

def custom_connect(addr):
    ip, port = addr.split(":")
    print("Trying to connect " + my_username + " to " + ip + ":" + port)
    client_socket.connect((ip, int(port)))
    global connected
    connected = addr
    client_socket.send(encode_msg(my_username, "LOG ON"))
    newthread = threading.Thread(target=receive_msg)
    newthread.start()

def disconnect(*args):
    #try:
    global client_socket
    client_socket.send(encode_msg(my_username, "LOG OFF"))
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    global connected
    connected = "none"
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connection_prompt_func():
    connection_prompt = Toplevel()
    ip_var = StringVar()
    port_var = IntVar()
    username_var = StringVar()

    def connect(*args):
        IP = ip_var.get()
        PORT = port_var.get()
        #my_username = username_var.get()
        print("Trying to connect " + my_username + " to " + str(IP) + ":" + str(PORT))
        client_socket.connect((IP, PORT))
        global connected
        connected = str(IP)+":"+str(PORT)
        client_socket.send(encode_msg(my_username, "LOG ON"))
        newthread = threading.Thread(target=receive_msg)
        connection_prompt.destroy()
        newthread.start()

    connection_prompt.geometry("600x150")
    connection_prompt.bind("<Return>", connect)
    connection_prompt.wm_title("New connection")
    connection_prompt.title("New connection")

    ip_label = Label(connection_prompt, text="Server IP:", bg="red", font="Courier 20")
    ip_label.place(x=0, y=0, width=200, height=50)
    ip_entry = Entry(connection_prompt, font="Courier 20", textvariable=ip_var)
    ip_entry.place(x=200, y=0, width=400, height=50)

    port_label = Label(connection_prompt, text="Server Port:", bg="red", font="Courier 20")
    port_label.place(x=0, y=50, width=200, height=50)
    port_entry = Entry(connection_prompt, font="Courier 20", textvariable=port_var)
    port_entry.place(x=200, y=50, width=400, height=50)

    connection_button = Button(connection_prompt, text="Connect", command=connect)
    connection_button.place(x=0, y=100, width=600, height=50)

def add_bookmark_prompt_func():
    bookmark_prompt = Toplevel()
    name_var = StringVar()

    def add_bookmark(addr):
        if addr != "none":
            f = open("servers.txt", "a")
            name = name_var.get()
            addr = addr.rstrip()
            f.write(name + "§;" + addr + "\n")
            global known_servers
            i = len(known_servers)
            known_servers.append(name + "§;" + addr)
            bookmark_menu.insert_command(index=i, label=name, command=partial(custom_connect, addr))
            bookmark_prompt.destroy()
        else:
            print("[ERROR] add_bookmark: not connected to any server")

    bookmark_prompt.geometry("600x150")
    bookmark_prompt.wm_title("New bookmark")
    bookmark_prompt.title("New bookmark")

    name_label = Label(bookmark_prompt, text="Bookmark name:", bg="red", font="Courier 20", anchor="w")
    name_label.place(x=0, y=0, width=300, height=50)
    name_entry = Entry(bookmark_prompt, font="Courier 20", textvar=name_var)
    name_entry.place(x=300, y=0, width=300, height=50)

    addr_label = Label(bookmark_prompt, text="Bookmark address: " + connected.rstrip(), bg="red", font="Courier 20", anchor="w")
    addr_label.place(x=0, y=50, width=600, height=50)

    bookmark_prompt.bind("<Return>", partial(add_bookmark, connected))

    add_button = Button(bookmark_prompt, text="Add bookmark", command=partial(add_bookmark, connected))
    add_button.place(x=0, y=100, width=600, height=50)

def edit_bookmark_prompt_func():
    bookmark_prompt = Toplevel()
    name_var = StringVar()

    bookmark_prompt.geometry("600x300")
    bookmark_prompt.wm_title("Edit bookmark")
    bookmark_prompt.title("Edit bookmark")

    bookmark_list = Listbox(bookmark_prompt, selectmode=SINGLE)
    bookmark_list.place(x=300, y=0, width=300, height=200)

    bookmark_name_var = StringVar()
    bookmark_address_var = StringVar()
    bookmark_index = (0,)

    bookmark_name_label = Label(bookmark_prompt, text="Name:")
    bookmark_name_label.place(x=0, y=50, width=75, height=50)
    bookmark_name_entry = Entry(bookmark_prompt, textvariable=bookmark_name_var)
    bookmark_name_entry.place(x=75, y=50, width=200, height=50)

    bookmark_address_label = Label(bookmark_prompt, text="Address:")
    bookmark_address_label.place(x=0, y=150, width=75, height=50)
    bookmark_address_entry = Entry(bookmark_prompt, textvariable=bookmark_address_var)
    bookmark_address_entry.place(x=75, y=150, width=200, height=50)

    def update_bookmarks():
        global known_servers
        servers_file = open("servers.txt")
        known_servers = servers_file.readlines()
        bookmark_list.delete(0, "end")

        for server in known_servers:
            server_name, server_address = server.split("§;")
            bookmark_list.insert("end", server_name)

    def add_bookmark(*args):
        name = bookmark_name_var.get()
        addr = bookmark_address_var.get()

        if addr != "":
            f = open("servers.txt", "a")
            f.write(name + "§;" + addr + "\n")
            global known_servers
            i = len(known_servers)
            known_servers.append(name + "§;" + addr)
            bookmark_menu.insert_command(index=i, label=name, command=partial(custom_connect, addr))
            update_bookmarks()
        else:
            print("[ERROR] add_bookmark: name entry is empty")

    def edit_bookmark(*args):
        global known_servers
        i = bookmark_index[0]
        new_name = bookmark_name_var.get()
        new_address = bookmark_address_var.get()
        new_bookmark = new_name + "§;" + new_address + "\n"
        #known_servers[i] = new_bookmark
        f = open("servers.txt", "r")
        old_servers = f.readlines()
        old_servers[i] = new_bookmark
        f.close()
        f = open("servers.txt", "w")
        f.writelines(old_servers)
        update_bookmarks()

    def onselect(*args):

        if bookmark_list.curselection() != ():
            global bookmark_name_entry
            bookmark_name_entry = Entry(bookmark_prompt, textvariable=bookmark_name_var)
            global bookmark_address_entry
            bookmark_address_entry = Entry(bookmark_prompt, textvariable=bookmark_address_var)
            global bookmark_index
            bookmark_index = bookmark_list.curselection()
            name, address = known_servers[bookmark_index[0]].split("§;")
            address = address.rstrip()
            bookmark_name_entry.delete(0, END)
            bookmark_name_entry.insert(0, name)
            bookmark_address_entry.delete(0, END)
            bookmark_address_entry.insert(0, address)

    bookmark_list.bind('<<ListboxSelect>>', onselect)

    update_bookmarks()

    edit_button = Button(bookmark_prompt, text="Update bookmark", command=edit_bookmark)
    edit_button.place(x=300, y=250, width=150, height=50)
    add_button = Button(bookmark_prompt, text="New bookmark", command=add_bookmark)
    add_button.place(x=150, y=250, width=150, height=50)

window.title("Chat Client")
window.geometry("600x600")

def username_prompt_func():
    username_prompt = Toplevel()
    username_prompt.title("Enter a Username")
    username_prompt.geometry("600x100")

    def confirm_name(*args):
        global my_username

        if connected == "none":
            my_username = username_entry.get()
            username_prompt.destroy()
        else:
            old_addr = connected
            disconnect()
            my_username = username_entry.get()
            custom_connect(old_addr)
            username_prompt.destroy()

    username_label = Label(username_prompt, text="Enter your username:")
    username_entry = Entry(username_prompt)
    username_button = Button(username_prompt, text="Confirm username", command=confirm_name)
    username_label.configure(wraplength=150, font="Courier 20")
    username_label.place(x=0, y=0, width=150, height=75)
    username_entry.configure(font="Courier 26")
    username_entry.place(x=150, y=0, width=450, height=75)
    username_entry.focus()
    username_button.configure(font="Courier 20")
    username_button.place(x=150, y=75, width=450, height=25)
    username_prompt.lift()
    username_prompt.bind("<Return>", confirm_name)
    username_prompt.grab_set()
    username_entry.focus()
    username_prompt.attributes('-topmost', 'true')

menubar = Menu(window)

server_menu = Menu(menubar, tearoff = 0)
server_menu.add_command(label="Connect", command=connection_prompt_func)#command = donothing)
server_menu.add_command(label="Disconnect", command=disconnect)
server_menu.add_separator()
server_menu.add_command(label="Exit", command=window.quit)
menubar.add_cascade(label="Server", menu=server_menu)

edit_menu = Menu(menubar, tearoff = 0)
edit_menu.add_command(label="Change username", command=username_prompt_func)
menubar.add_cascade(label="Edit", menu=edit_menu)

bookmark_menu = Menu(menubar, tearoff = 0)
for bookmark in known_servers:
    bookmark_name, bookmark_address = bookmark.split("§;")
    bookmark_menu.add_command(label=bookmark_name, command=partial(custom_connect, bookmark_address))
bookmark_menu.add_separator()
bookmark_menu.add_command(label="Add", command=add_bookmark_prompt_func)
bookmark_menu.add_command(label="Edit", command=edit_bookmark_prompt_func)
menubar.add_cascade(label="Bookmarks", menu=bookmark_menu)
window.configure(menu=menubar)

main_frame = Frame(window, width=600, height=600, bg="green")
main_frame.place(x=0, y=0)

chat_frame = Frame(main_frame, width=500, height=500, bg="blue")
chat_frame.place(x=100, y=0)

chat_text = Text(chat_frame, width=500, height=500, font="Times 20")
chat_text.place(x=0, y=0, width=500, height=500)
chat_text["state"] = DISABLED

chat_text.tag_configure("right", justify="right")
chat_text.tag_configure("left", justify="left")
chat_text.tag_config("green", foreground="green")
chat_text.tag_config("blue", foreground="blue")

entry_text = Text(main_frame)
entry_text.place(x=100, y=500, width=400, height=50)
entry_button = Button(main_frame, text="Send", font="Courier 20", command=send_msg)
entry_button.place(x=500, y=500, width=100, height=50)

username_prompt_func()

window.update()
window.minsize(600, 600)

window.mainloop()
