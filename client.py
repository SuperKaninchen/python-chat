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
from functools import partial
from tkinter import *
from tkinter import scrolledtext
import tkinter
import time
import datetime
import json

users = []
with open('config') as f:
    config = f.readlines()
error_text = '\033[31;1m' + '[ERROR] ' + '\033[m'
passwd = ''

welcome = '''
Python chat  Copyright (C) 2019  Max Nijenhuis😀
This program comes with ABSOLUTELY NO WARRANTY
This is free software, and you are welcome to redistribute it
under certain conditions🤮
click on Help -> License for details.
'''

print(welcome)


def decode_msg(msg):
    global users
    msg = msg.decode()
    try:
        msg_dict = json.loads(msg)
    except json.decoder.JSONDecodeError:  # invalid json, cant't build msg_dict
        msg_dict = {}
    usr = msg_dict.get('usr')
    msg = msg_dict.get('msg')
    if not usr or not msg:
        return '', ''
    if msg == 'Username already taken':
        print('Username already taken on that server')
        return '', 'stop'
        disconnect()

    if msg == 'LOG ON':
        users.append(usr)
        users_text['state'] = NORMAL
        users_text.delete('1.0', 'end')
        for user in users:
            users_text.insert('end', user + '\n')
        users_text['state'] = DISABLED
        return '[SERVER]', usr + ' has logged on'

    if msg == 'LOG OFF':
        users.remove(usr)
        users_text['state'] = NORMAL
        users_text.delete('1.0', 'end')
        for user in users:
            users_text.insert('end', user + '\n')
        users_text['state'] = DISABLED
        return '[SERVER]', usr + ' has logged off'

    if usr == '[userlist]':
        users.append(msg)
        users_text['state'] = NORMAL
        users_text.delete('1.0', 'end')
        for user in users:
            users_text.insert('end', user + '\n')
        users_text['state'] = DISABLED

    return usr, msg


def encode_msg(usr, msg):
    msg_dict = {'usr': usr, 'msg': msg}
    print(msg_dict)
    msg = json.dumps(msg_dict).encode()
    return msg


start_time = time.time()
timestamp_posted = False
now = datetime.datetime.now()


def print_timestamp():
    global start_time
    global timestamp_posted
    time_since_last = time.time() - start_time
    if time_since_last >= 300:
        current_time = time.asctime(time.localtime(time.time()))
        chat_text['state'] = NORMAL
        if timestamp_posted:
            chat_text.delete('end - 2 lines linestart', 'end')
        chat_text.insert(
            'end',
            '\n' + current_time + '\n',
            ('timestamp', 'center')
        )
        chat_text['state'] = DISABLED
        timestamp_posted = True
    start_time = time.time()
    chat_text.see('end')


def send_msg(*args):
    global connected
    if connected is None:
        print(error_text + 'send_msg: currently not connected')
    else:
        print_timestamp()
        msg = entry_text.get('1.0', 'end-1c')
        if not msg:
            return
        client_socket.send(encode_msg(my_username, msg))
        entry_text.delete('1.0', 'end')


def receive_msg():
    global start_time
    global timestamp_posted
    while True:
        if connected is None:
            break
        try:
            user, message = decode_msg(client_socket.recv(4096))
            if message == 'stop':
                break
            if user == '[userlist]':
                continue
            print_timestamp()
            msg_timestamp = time.strftime('%H:%M')
            if user == my_username:
                chat_text['state'] = NORMAL
                chat_text.insert('end', message, ('right'))
                chat_text.insert('end', ' < ', ('right', 'green'))
                chat_text.insert('end', my_username, ('right', 'blue'))
                chat_text.insert('end', msg_timestamp + '\n', ('timestamp', 'right'))
                chat_text['state'] = DISABLED
                timestamp_posted = False
                print(user + ' > ' + message)
                chat_text.see('end')
            else:
                chat_text['state'] = NORMAL
                chat_text.insert('end', msg_timestamp, ('timestamp', 'left'))
                chat_text.insert('end', user, ('left', 'blue'))
                chat_text.insert('end', ' > ', ('left', 'green'))
                chat_text.insert('end', message + '\n', ('left'))
                chat_text['state'] = DISABLED
                timestamp_posted = False
                print(user + ' > ' + message)
                chat_text.see('end')

        except Exception as e:
            raise
            print(error_text + 'receive_msg: '+str(e))
            break


def passwd_prompt_func():
    passwd_prompt = Toplevel()
    passwd_prompt.title('Enter your password')
    passwd_prompt.geometry('600x100')

    passwd_label = Label(
        passwd_prompt,
        text='Enter your password:'
    )

    def confirm_passwd(*args):
        global passwd
        passwd = passwd_entry.get()
        passwd_prompt.destroy()

    passwd_entry = Entry(passwd_prompt)
    passwd_button = Button(
        passwd_prompt,
        text='Confirm password',
        command=confirm_passwd
    )
    passwd_label.configure(
        wraplength=150,
        font='Courier 12'
    )
    passwd_label.place(
        x=0,
        y=0,
        width=150,
        height=50
    )
    passwd_entry.configure(font='Courier 20', show='^')
    passwd_entry.place(
        x=150,
        y=0,
        width=450,
        height=50
    )
    passwd_entry.focus()
    passwd_button.configure(
        font='Courier 20',
        command=partial(confirm_passwd)
    )
    passwd_button.place(
        x=150,
        y=50,
        width=450,
        height=50
    )
    passwd_prompt.protocol('WM_DELETE_WINDOW', on_close)
    passwd_prompt.lift()
    passwd_prompt.bind('<Return>', confirm_passwd)
    passwd_prompt.grab_set()
    passwd_prompt.focus()
    passwd_prompt.attributes('-topmost', 'true')


def custom_connect(addr):
    ip, port = addr.split(':')
    print('Trying to connect ' + my_username + ' to ' + ip + ':' + port)
    client_socket.connect((ip, int(port)))
    global connected
    connected = addr
    # passwd_prompt_func()
    msg = 'LOG ON||' + passwd
    client_socket.send(encode_msg(my_username, msg))
    global newthread
    newthread = threading.Thread(target=receive_msg)
    global userlist
    userlist = []
    newthread.start()


def disconnect(*args):
    users_text['state'] = NORMAL
    users_text.delete('1.0', 'end')
    users_text['state'] = DISABLED
    global client_socket
    client_socket.send(encode_msg(my_username, 'LOG OFF'))
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    global connected
    connected = None
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def get_prompt(geometry, title):
    elem = Toplevel()
    elem.geometry(geometry)
    elem.wm_title(title)
    elem.title(title)
    return elem


def connection_prompt_func():
    connection_prompt = Toplevel()
    ip_var = StringVar()
    port_var = IntVar()
    username_var = StringVar()

    def connect(*args):
        IP = ip_var.get()
        PORT = port_var.get()
        custom_connect(IP, PORT)
        connection_prompt.destroy()

    connection_prompt.geometry('600x150')
    connection_prompt.bind('<Return>', connect)
    connection_prompt.wm_title('New connection')
    connection_prompt.title('New connection')

    ip_label = Label(
        connection_prompt,
        text='Server IP:',
        bg='red',
        font='Courier 20'
    )
    ip_label.place(
        x=0,
        y=0,
        width=200,
        height=50
    )
    ip_entry = Entry(
        connection_prompt,
        font='Courier 20',
        textvariable=ip_var
    )
    ip_entry.place(
        x=200,
        y=0,
        width=400,
        height=50
    )

    port_label = Label(
        connection_prompt,
        text='Server Port:',
        bg='red',
        font='Courier 20'
    )
    port_label.place(
        x=0,
        y=50,
        width=200,
        height=50
    )
    port_entry = Entry(
        connection_prompt,
        font='Courier 20',
        textvariable=port_var
    )
    port_entry.place(
        x=200,
        y=50,
        width=400,
        height=50
    )

    connection_button = Button(
        connection_prompt,
        text='Connect',
        command=connect
    )
    connection_button.place(
        x=0,
        y=100,
        width=600,
        height=50
    )


def add_bookmark_prompt_func():
    bookmark_prompt = Toplevel()
    name_var = StringVar()

    def add_bookmark(addr):
        if addr != 'none':
            name = name_var.get()
            addr = addr.rstrip()
            with open('servers', 'a') as servers_file:
                servers_file.write(name + ':;' + addr + '\n')
            global known_servers
            known_servers.append(name + ':;' + addr)
            bookmark_menu.insert_command(
                index=i,
                label=name,
                command=partial(custom_connect, addr)
            )
        else:
            print(error_text + 'add_bookmark: not connected to any server')
        bookmark_prompt.destroy()

    bookmark_prompt.geometry('600x150')
    bookmark_prompt.wm_title('New bookmark')
    bookmark_prompt.title('New bookmark')

    name_label = Label(
        bookmark_prompt,
        text='Bookmark name:',
        bg='red',
        font='Courier 20',
        anchor='w'
    )
    name_label.place(
        x=0,
        y=0,
        width=300,
        height=50
    )
    name_entry = Entry(
        bookmark_prompt,
        font='Courier 20',
        textvar=name_var
    )
    name_entry.place(
        x=300,
        y=0,
        width=300,
        height=50
    )

    addr_label = Label(
        bookmark_prompt,
        text='Bookmark address: ' + connected.rstrip(),
        bg='red',
        font='Courier 20',
        anchor='w'
    )
    addr_label.place(
        x=0,
        y=50,
        width=600,
        height=50
    )

    bookmark_prompt.bind('<Return>', partial(add_bookmark, connected))

    add_button = Button(
        bookmark_prompt,
        text='Add bookmark',
        command=partial(add_bookmark, connected)
    )
    add_button.place(
        x=0,
        y=100,
        width=600,
        height=50
    )


def edit_bookmark_prompt_func():
    bookmark_prompt = Toplevel()
    name_var = StringVar()

    bookmark_prompt.geometry('600x300')
    bookmark_prompt.wm_title('Edit bookmark')
    bookmark_prompt.title('Edit bookmark')

    bookmark_list = Listbox(bookmark_prompt, selectmode=SINGLE)
    bookmark_list.place(
        x=300,
        y=0,
        width=300,
        height=200
    )

    bookmark_name_var = StringVar()
    bookmark_address_var = StringVar()
    bookmark_index = (0,)

    bookmark_name_label = Label(bookmark_prompt, text='Name:')
    bookmark_name_label.place(
        x=0,
        y=50,
        width=75,
        height=50
    )
    bookmark_name_entry = Entry(
        bookmark_prompt,
        textvariable=bookmark_name_var
    )
    bookmark_name_entry.place(
        x=75,
        y=50,
        width=200,
        height=50
    )

    bookmark_address_label = Label(bookmark_prompt, text='Address:')
    bookmark_address_label.place(
        x=0,
        y=150,
        width=75,
        height=50
    )
    bookmark_address_entry = Entry(
        bookmark_prompt,
        textvariable=bookmark_address_var
    )
    bookmark_address_entry.place(
        x=75,
        y=150,
        width=200,
        height=50
    )

    def update_bookmarks():
        global known_servers
        servers_file = open('servers')
        known_servers = servers_file.readlines()
        bookmark_list.delete(0, 'end')

        for server in known_servers:
            server_name, server_address = server.split(':;')
            bookmark_list.insert('end', server_name)

    def add_bookmark(*args):
        name = bookmark_name_var.get()
        addr = bookmark_address_var.get()

        if addr != '':
            f = open('servers', 'a')
            f.write(name + ':;' + addr + '\n')
            global known_servers
            i = len(known_servers)
            known_servers.append(name + ':;' + addr)
            bookmark_menu.insert_command(
                index=i,
                label=name,
                command=partial(custom_connect, addr)
            )
            update_bookmarks()
        else:
            print(error_text + 'add_bookmark: name entry is empty')

    def edit_bookmark(*args):
        global known_servers
        i = bookmark_index[0]
        new_name = bookmark_name_var.get()
        new_address = bookmark_address_var.get()
        new_bookmark = new_name + ':;' + new_address + '\n'
        f = open('servers', 'r')
        old_servers = f.readlines()
        old_servers[i] = new_bookmark
        f.close()
        f = open('servers', 'w')
        f.writelines(old_servers)
        update_bookmarks()
        f.close()

    def onselect(*args):

        if bookmark_list.curselection() != ():
            global bookmark_name_entry
            bookmark_name_entry = Entry(
                bookmark_prompt,
                textvariable=bookmark_name_var
            )
            global bookmark_address_entry
            bookmark_address_entry = Entry(
                bookmark_prompt,
                textvariable=bookmark_address_var
            )
            global bookmark_index
            bookmark_index = bookmark_list.curselection()
            name, address = known_servers[bookmark_index[0]].split(':;')
            address = address.rstrip()
            bookmark_name_entry.delete(0, END)
            bookmark_name_entry.insert(0, name)
            bookmark_address_entry.delete(0, END)
            bookmark_address_entry.insert(0, address)

    bookmark_list.bind('<<ListboxSelect>>', onselect)

    update_bookmarks()

    edit_button = Button(
        bookmark_prompt,
        text='Update bookmark',
        command=edit_bookmark
    )
    edit_button.place(
        x=300,
        y=250,
        width=150,
        height=50
    )
    add_button = Button(
        bookmark_prompt,
        text='New bookmark',
        command=add_bookmark
    )
    add_button.place(
        x=150,
        y=250,
        width=150,
        height=50
    )


def username_prompt_func():
    username_prompt = Toplevel()
    username_prompt.title('Enter a Username')
    username_prompt.geometry('600x100')

    def confirm_name(*args):
        global my_username

        if connected is None:
            my_username = username_entry.get().rstrip()
            username_prompt.destroy()
        else:
            old_addr = connected
            disconnect()
            my_username = username_entry.get().rstrip()
            custom_connect(old_addr)
            username_prompt.destroy()

    username_label = Label(
        username_prompt,
        text='Enter your username:'
    )
    username_entry = Entry(username_prompt)
    username_button = Button(
        username_prompt,
        text='Confirm username',
        command=confirm_name
    )
    username_label.configure(
        wraplength=150,
        font='Courier 20'
    )
    username_label.place(
        x=0,
        y=0,
        width=150,
        height=75
    )
    username_entry.configure(font='Courier 26')
    username_entry.place(
        x=150,
        y=0,
        width=450,
        height=75
    )
    username_entry.focus()
    username_button.configure(font='Courier 20')
    username_button.place(
        x=150,
        y=75,
        width=450,
        height=25
    )
    username_prompt.lift()
    username_prompt.bind('<Return>', confirm_name)
    username_prompt.grab_set()
    username_entry.focus()
    username_prompt.attributes('-topmost', 'true')


def license_prompt_func():
    license_prompt = Toplevel()
    license_prompt.title('About')
    license_prompt.geometry('600x600')

    license_text = Text(license_prompt)
    license_text.place(
        x=0,
        y=0,
        width=600,
        height=600
    )
    f = open('LICENSE')
    license_lines = f.readlines()
    for line in license_lines:
        license_text.insert('end', line)
    license_text['state'] = DISABLED
    f.close()


def config_prompt_func():
    config_prompt = Toplevel()
    config_prompt.title('Options')
    config_prompt.geometry('600x600')

    def confirm_name(*args):
        global my_username
        global config

        if connected is None:
            my_username = username_entry.get()
        else:
            old_addr = connected
            disconnect()
            my_username = username_entry.get()
            time.sleep(.1)
            custom_connect(old_addr)
        with open('config', 'w') as config_file:
            if remember_username.get():
                config[0] = 'username:;' + my_username
                for line in config:
                    config_file.write(line)
            else:
                config[0] = 'username:;USERNAME NOT SET'
                for line in config:
                    config_file.write(line)

    username_check = Checkbutton(config_prompt)
    username_check.configure(
        text='Remember Username',
        variable=remember_username
    )
    if config[0].rstrip() != 'username:;USERNAME NOT SET':
        username_check.select()
    username_check.place(
        x=0,
        y=0,
        width=200,
        height=50
    )
    username_entry = Entry(config_prompt)
    username_entry.configure(font='Courier 12')
    username_entry.place(
        x=200,
        y=0,
        width=250,
        height=50
    )
    username_entry.delete(0, END)
    username_entry.insert(0, my_username)
    username_set_button = Button(config_prompt)
    username_set_button.configure(
        font='Courier 12',
        text='Save config',
        command=confirm_name
    )
    username_set_button.place(
        x=450,
        y=0,
        width=150,
        height=50
    )


# XXX: encapsulate global vars - in fact the client state - into object?
IP = '1.2.3.4'
PORT = 1234
my_username = 'guest'
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = None
newthread = None

with open('servers') as servers_file:
    known_servers = servers_file.readlines()

window = Tk()
window.minsize(600, window.winfo_reqheight())
windowHeight = window.winfo_height()
windowWidth = window.winfo_width()


def on_close():
    if connected is not None:
        try:
            disconnect()
        except BrokenPipeError:
            print(error_text + 'on_close: Broken pipe error')
    newthread.join()
    window.destroy()


window.protocol('WM_DELETE_WINDOW', on_close)

main_frame = Frame(
    window,
    width=600,
    height=600,
    bg='green'
)
chat_frame = Frame(
    main_frame,
    width=500,
    height=500,
    bg='blue'
)
chat_text = Text(
    chat_frame,
    width=500,
    height=500,
    font='Courier 22'
)
entry_text = Text(main_frame)
menubar = Menu(window)
bookmark_menu = Menu(menubar, tearoff=0)

window.title('Chat Client')
window.geometry('600x600')

remember_username = BooleanVar()

menubar = Menu(window)

server_menu = Menu(menubar, tearoff=0)
# command = donothing)
server_menu.add_command(label='Connect', command=connection_prompt_func)
server_menu.add_command(label='Disconnect', command=disconnect)
server_menu.add_separator()
server_menu.add_command(label='Exit', command=window.quit)
menubar.add_cascade(label='Server', menu=server_menu)

edit_menu = Menu(menubar, tearoff=0)
edit_menu.add_command(label='Change username', command=username_prompt_func)
edit_menu.add_separator()
edit_menu.add_command(label='Options', command=config_prompt_func)
menubar.add_cascade(label='Edit', menu=edit_menu)

bookmark_menu = Menu(menubar, tearoff=0)
for bookmark in known_servers:
    bookmark_name, bookmark_address = bookmark.split(':;')
    bookmark_menu.add_command(
        label=bookmark_name,
        command=partial(custom_connect, bookmark_address)
    )


bookmark_menu.add_separator()
bookmark_menu.add_command(label='Add', command=add_bookmark_prompt_func)
bookmark_menu.add_command(label='Edit', command=edit_bookmark_prompt_func)
menubar.add_cascade(label='Bookmarks', menu=bookmark_menu)

help_menu = Menu(menubar, tearoff=0)
help_menu.add_command(label='License', command=license_prompt_func)
menubar.add_cascade(label='Help', menu=help_menu)

window.configure(menu=menubar)

main_frame = Frame(window, width=600, height=600, bg='green')
main_frame.place(x=0, y=0)

chat_frame = Frame(main_frame, width=500, height=500, bg='blue')
chat_frame.place(x=100, y=0)

chat_text = Text(chat_frame, width=500, height=500, font='Times 20')
chat_text.place(x=0, y=0, width=500, height=500)
chat_text['state'] = DISABLED

chat_text.tag_configure(
    'right',
    justify='right'
)
chat_text.tag_configure(
    'left',
    justify='left'
)
chat_text.tag_configure(
    'center',
    justify='center',
)
chat_text.tag_configure(
    'green',
    foreground='green'
)
chat_text.tag_configure(
    'blue',
    foreground='blue'
)
chat_text.tag_config(
    'timestamp',
    foreground='grey',
    font='Umpush 10'
)

entry_text = Text(main_frame)
entry_text.place(x=100, y=500, width=400, height=50)
entry_button = Button(
    main_frame,
    text='Send',
    font='Courier 20',
    command=send_msg
)
entry_button.place(x=500, y=500, width=100, height=50)

users_text = Text(main_frame)
users_text.place(x=0, y=0, width=100, height=500)

if config[0].rstrip() == 'username:;USERNAME NOT SET':
    username_prompt_func()
else:
    var, value = config[0].split(':;', 2)
    my_username = value

passwd_prompt_func()

window.update()
window.minsize(600, 600)
window.resizable(0, 0)

window.mainloop()
