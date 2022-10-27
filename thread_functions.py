import socket
import os  # listdir(), getcwd(), chdir(), mkdir()
from threading import Thread
import subprocess
import dialects


# Directory where server files are stored
ServerFolder = os.getcwd() + "/ServerFolder"

# Initial packets in cached packets
init_pkt_1 = 'Hello'
# init_pkt_2 = 'World'
# cached_pkts = init_pkt_1 + "|" + init_pkt_2
cached_pkts = init_pkt_1

class ThreadFunctions(Thread):
    def __init__(self, client_socket, client_ip, client_port):
        Thread.__init__(self)
        self.client_socket = client_socket
        self.client_ip = client_ip
        self.client_port = client_port
        # self.buffer_size = 1024
        print("Server started thread for client {} on port {}".format(
            self.client_ip, self.client_port))

    def run(self):
        """
        Inherited method from Thread module.
        This is the main function which look at received data/commands from client and
        decides what to do.
        """
        os.chdir(ServerFolder)
        while True:
            # Receive dialect
            global cached_pkts
            handler = None
            # request = self.client_socket.recv(1024).decode().strip()

            # Respond to splitting or shuffling
            '''
            # Splitting
            handler = dialects.Splitting(self.client_socket)
            request, cached_pkts = handler.split_server(cached_pkts)
            print("cached packet: {}".format(cached_pkts))
            '''

            # Shuffling
            handler = dialects.ByteShuffling(self.client_socket)
            request, cached_pkts = handler.shuffle_server(cached_pkts)
            print("cached packet: {}".format(cached_pkts))


            if not request:
                print("Disconnecting fom client {}:{}".format(
                    self.client_ip, self.client_port))
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
                break
            '''
            # Eval 1
            if request == ''.join(request.split(",")):
                print("Invalid request from {}:{}".format(
                    self.client_ip, self.client_port))
                continue
            '''

            request = request.split(",")

            if request[0] == "LS":
                self.ls()
            elif request[0] == "PWD":
                self.pwd()
            elif request[0] == "CD":
                self.cd(request[1])
            elif request[0] == "MKDIR":
                self.mkdir(request[1])
            elif request[0] == "RMDIR":
                self.rmdir(request[1])
            elif request[0] == "RM":
                self.rm(request[1])

            elif request[0] == "rget" and len(request[1:]) == 1:
                self.send_file(*request[1:])

            elif request[0] == "rput" and len(request[1:]) == 2:
                self.receive_file(*request[1:])
            # Eval 2
            else:
                print("Invalid request from {}:{}".format(
                    self.client_ip, self.client_port))                
                continue

    def ls(self):
        packet = subprocess.check_output(
            ["ls", "-l"], universal_newlines=True)
        # print(type(output))
        # packet = ""
        # filelist = os.listdir(os.getcwd())
        # # print(str(filelist))
        # for f in filelist:
        #     packet += f + "   "
        # # print(packet)
        if packet.strip() == "":
            self.client_socket.sendall("EMPTY".encode())
        else:
            # self.client_socket.sendall(packet.encode())
            self.client_socket.sendall(packet.encode())

        # self.client_socket.sendall(response.encode())

    def pwd(self):
        try:
            currDir = os.getcwd()
            self.client_socket.sendall(currDir.encode())
        except:
            self.client_socket.sendall(
                "Server facing issue while getting working directory.")

    def cd(self, dir_path):
        try:
            if (dir_path == '..' and os.getcwd() == ServerFolder):
                self.client_socket.sendall(
                    f"changed directory to '{dir_path}'".encode())
            else:
                os.chdir(dir_path)
                self.client_socket.sendall(
                    f"changed directory to '{dir_path}'".encode())
        except FileNotFoundError:
            self.client_socket.sendall(
                f"directory '{dir_path}' not found".encode())

    def mkdir(self, dir_name):
        try:
            # path = ServerFolder+"/"+dir_name
            os.mkdir(dir_name)
            self.client_socket.sendall(
                f"Directory '{dir_name}' successfully created.".encode())
        except OSError:
            self.client_socket.sendall(
                f"directory named '{dir_name}' already exists.".encode())

    def rmdir(self, dir_name):
        try:
            os.removedirs(dir_name)
            self.client_socket.sendall(
                f"Directory '{dir_name}' successfully removed.".encode())
        except FileNotFoundError:
            self.client_socket.sendall(
                f"directory named '{dir_name}' doesn't exists.".encode())
        except OSError:
            self.client_socket.sendall(f"directory is not empty".encode())

    def rm(self, file_name):
        try:
            os.remove(file_name)
            self.client_socket.sendall(
                f"File '{file_name}' successfully removed.".encode())
        except FileNotFoundError:
            self.client_socket.sendall(
                f"File named '{file_name}' doesn't exists.".encode())
        except IsADirectoryError:
            self.client_socket.sendall(
                f"'{file_name}' is a directory.".encode())
        # except OSError:
        #     self.client_socket.sendall(f"directory is not empty".encode())

    def send_file(self, file_name):
        """
        Sends requested file to client if it exits on the server.

        Params:
            file_name (str): name of file to find and transfer
        """
        # file_name = file_name[0]
        handler = None
        handler = dialects.Splitting(self.client_socket, client_ip = self.client_ip, client_port = self.client_port)
        handler.send_file(file_name)

    def receive_file(self, file_name, length):
        """
        Reads a file that is sent from the client.

        Params:
            file_name (str): name of file to be transfered
            length (str): byte length of the file to be transfered from client
        """
        self.client_socket.sendall("Ready".encode("utf-8"))
        print("Server ready to accept file: {} from client: {}:{}".format(
            file_name, self.client_ip, self.client_port))

        save_file = open("{}".format(file_name), "wb")

        amount_recieved_data = 0
        while amount_recieved_data < int(length):
            recv_data = self.client_socket.recv(1024)
            amount_recieved_data += len(recv_data)
            save_file.write(recv_data)

        save_file.close()

        self.client_socket.sendall("Received,{}".format(
            amount_recieved_data).encode('utf-8'))
        print("Server done receiving from client {}:{}. File Saved.".format(
            self.client_ip, self.client_port))
