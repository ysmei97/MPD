import socket
import os
from threading import Thread
import subprocess
import hmac
import time

from typing import List

key = '1227'

class ByteShuffling:

    def __init__(self, client_socket, client_ip = None, client_port = None, Hash = None):
        self.client_socket = client_socket
        self.client_ip = client_ip
        self.client_port = client_port
        self.Hash = Hash


    def shuffle_server(self, cached_pkts):
        '''Shuffle bytes in packets for server side'''
        # Generate keyed hash value as pseudo-random number
        # Receive request dialect
        packet = self.client_socket.recv(1024).decode().strip()
        print("customized packet: {}".format(packet))
        keyed_hash = hmac.new(key.encode('utf-8'), cached_pkts.encode('utf-8'), digestmod = 'MD5').hexdigest()
        print('keyed hash value: %s' % (keyed_hash))
        list_dialect = [[0,1,2],[1,1,2],[2,1,2],[0,2,2],[1,2,2],[2,2,2],[0,1,3],[1,1,3],[2,1,3],[0,2,3],[1,2,3],[2,2,3]]
        k = int(keyed_hash, 16) // ((2**128 // 12) + 1) + 1
        pos, length, offset = list_dialect[k-1]
        print('pos: %d, length: %d, offset: %d, index: %d' % (pos, length, offset, k))

        # Concatenation
        # cached_pkts = ''.join(cached_pkts.split("|", 1)[1]) + "|" + packet
        cached_pkts = packet

        # Start shuffling back the packet
        packet = list(packet)
        sub_pkt = packet[pos: pos + length]
        packet[pos: pos + length] = packet[pos + offset: pos + offset + length]
        packet[pos + offset: pos + offset + length] = sub_pkt
        packet = ''.join(packet)
        print("original packet: {}".format(packet))

        return packet, cached_pkts


    def shuffle_client(self, packet, cached_pkts):
        '''Shuffle bytes in packets for client side'''
        # Generate keyed hash value as pseudo-random number
        # Predefine 12 dialects
        keyed_hash = hmac.new(key.encode('utf-8'), cached_pkts.encode('utf-8'), digestmod = 'MD5').hexdigest()
        print('keyed hash value: %s' % (keyed_hash))
        list_dialect = [[0,1,2],[1,1,2],[2,1,2],[0,2,2],[1,2,2],[2,2,2],[0,1,3],[1,1,3],[2,1,3],[0,2,3],[1,2,3],[2,2,3]]
        k = int(keyed_hash, 16) // ((2**128 // 12) + 1) + 1
        pos, length, offset = list_dialect[k-1]
        print('pos: %d, length: %d, offset: %d, index: %d' % (pos, length, offset, k))

        # Start shuffling the packet
        packet = list(packet)
        sub_pkt = packet[pos: pos + length]
        packet[pos: pos + length] = packet[pos + offset: pos + offset + length]
        packet[pos + offset: pos + offset + length] = sub_pkt
        packet = ''.join(packet)

        # Concatenation
        # cached_pkts = ''.join(cached_pkts.split("|", 1)[1]) + "|" + packet
        cached_pkts = packet

        return packet, cached_pkts


    def send_file(self, file_name):
        '''server side: send file in dialect'''
        try:
            dataPort = self.client_socket.recv(1024).decode()
            print("[Control] Data port is {}".format(dataPort))

            # Connect to the data connection
            dataConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dataConnection.connect((self.client_ip, int(dataPort)))

            print(file_name, type(file_name))
            file_size = os.path.getsize(file_name)
            self.client_socket.sendall(
                "Exists,{}".format(file_size).encode('utf-8'))

            while True:
                recv_data = self.client_socket.recv(1024)
                request = recv_data.decode('utf-8').strip().split(",")

                if request[0] == "Ready":
                    print("Sending file {} to client {}".format(
                        file_name, self.client_ip))

                    with open(file_name, "rb") as file:
                        dataConnection.sendfile(file)
                elif request[0] == "Received":
                    if int(request[1]) == file_size:
                        self.client_socket.sendall("Success".encode('utf-8'))
                        print("{} successfully downloaded to client {}".format(
                            file_name, self.client_ip))
                        break
                    else:
                        print("Something went wrong trying to download to client {}:{}. Try again".format(
                            self.client_ip, self.client_port))
                        break
                else:
                    print("Something went wrong trying to download to client {}:{}. Try again".format(
                        self.client_ip, self.client_port))
                    break
        except IOError:
            print("File {} does not exist on server".format(file_name))
            self.client_socket.sendall("Failed".encode('utf-8'))


    def do_get(self, args, cached_pkts):
        '''client side: send request in dialect'''
        file = args.split()

        if len(file) != 1:
            print("rget requires exactly 1 argument.")
            return
            
        file_name = file[0]
        try:
            packet = "rget,{}".format(file_name)

            print("original packet: {}".format(packet))
            pkt_dialect, cached_pkts = self.shuffle_client(packet, cached_pkts)
            print("customized packet: {}".format(pkt_dialect))
            print("cached packet: {}".format(cached_pkts))
            self.client_socket.sendall(pkt_dialect.encode())

            # Initilize data connection
            dataConnection = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            dataConnection.bind(('', 0))
            dataConnection.listen(1)
            dataPort = dataConnection.getsockname()[1]

            # Send data connection port to server over control connection
            # so server can connect.
            self.client_socket.send(str(dataPort).encode())

            # Wait for server to connect.
            dataConnection, maddr = dataConnection.accept()
            print('[Control] Got connection from', maddr)

            print('200 PORT command successful')

            while True:
                recv_data = self.client_socket.recv(1024)

                packet_info = recv_data.decode(
                    'utf-8').strip().split(",")

                if packet_info[0] == "Exists":
                    self.client_socket.sendall("Ready".encode('utf-8'))
                    # print(
                    #     "{} exits on the server, ready to download.".format(file_name))

                    save_file = open(file_name, "wb")

                    amount_recieved_data = 0
                    while amount_recieved_data < int(packet_info[1]):
                        recv_data = dataConnection.recv(1024)
                        amount_recieved_data += len(recv_data)
                        save_file.write(recv_data)

                        # printing hashes for each 1024 bytes of data transfered
                        if self.Hash == True:
                            print('#', end="")

                    # printing new line after printing hashes
                    if self.Hash == True:
                        print()

                    save_file.close()

                    self.client_socket.sendall("Received,{}".format(
                        amount_recieved_data).encode('utf-8'))
                elif packet_info[0] == "Success":
                    print('226 Transfer complete')
                    break
                elif packet_info[0] == "Failed":
                    print(
                        "File {} does not exist on server.".format(file_name))
                    break
                else:
                    print("Something went wrong when downloading '{}' from server. Try again.".format(
                        file_name))
                    break
            return cached_pkts
        except socket.error:
            print("SOCKET_ERROR: Check and ensure that server is running.")



class Splitting:

    def __init__(self, client_socket, client_ip = None, client_port = None, Hash = None):
        self.client_socket = client_socket
        self.client_ip = client_ip
        self.client_port = client_port
        self.Hash = Hash


    def split_server(self, cached_pkts):
        '''Shuffle bytes in packets for server side'''
        # Generate keyed hash value as pseudo-random number
        keyed_hash = hmac.new(key.encode('utf-8'), cached_pkts.encode('utf-8'), digestmod = 'MD5').hexdigest()
        print('keyed hash value: %s' % (keyed_hash))
        list_dialect = [[1,1,1],[2,1,1],[1,2,1],[1,1,2],[2,2,1],[2,1,2],[1,2,2],[2,2,2]]
        k = int(keyed_hash, 16) // ((2**128 // 8) + 1) + 1
        pkt1, pkt2, pkt3 = list_dialect[k-1]

        # Receive t subpackets and merge into single request packet
        t = 4
        packet_len = int(self.client_socket.recv(1024).decode().strip())
        print('packet length: %d' % (packet_len))
        packet = [] # Merge unprocessed subpackets
        request = []
        # length = int(packet_len / t)
        print('pkt1 length: %d, pkt2 length: %d, pkt3 length: %d, pkt4 length: %d, index: %d' %
              (pkt1, pkt2, pkt3, (packet_len - pkt1 - pkt2 - pkt3), k))
        self.client_socket.settimeout(3.0)
        for i in range(t):
            try:
                subpacket = self.client_socket.recv(packet_len).decode().strip()
            except socket.timeout as e:
                if e.args[0] == 'timed out':
                    print('receiving subpacket timed out')
                    continue
                else:
                    print(e)
                    break
            else:
                if i == (t - 1) and packet_len != (pkt1 + pkt2 + pkt3):
                    # request.append(self.client_socket.recv(packet_len - num * length).decode().strip())
                    packet.append(subpacket)
                    request.append(subpacket[0:(packet_len - pkt1 - pkt2 - pkt3)])
                    self.client_socket.sendall("Subpacket received".encode('utf-8'))
                else:
                    packet.append(subpacket)
                    request.append(subpacket[0:list_dialect[k][i]])
                    self.client_socket.sendall("Subpacket received".encode('utf-8'))
        self.client_socket.settimeout(100.0)
        print("customized packet: {}".format(packet))

        # Concatenation
        # cached_pkts = ''.join(cached_pkts.split("|", 1)[1]) + "|" + ''.join(packet)
        cached_pkts = ''.join(packet)

        # Merge the subpackets
        request = ''.join(request)
        print("original packet: {}".format(request))

        return request, cached_pkts


    def split_client(self, packet, cached_pkts):
        '''Split packets for client side, establish more handshakes'''
        # Generate keyed hash value as pseudo-random number
        packet_len = len(packet)
        print('packet length: %d' % (packet_len))
        keyed_hash = hmac.new(key.encode('utf-8'), cached_pkts.encode('utf-8'), digestmod = 'MD5').hexdigest()
        print('keyed hash value: %s' % (keyed_hash))
        list_dialect = [[1,1,1],[2,1,1],[1,2,1],[1,1,2],[2,2,1],[2,1,2],[1,2,2],[2,2,2]]
        k = int(keyed_hash, 16) // ((2**128 // 8) + 1) + 1
        pkt1, pkt2, pkt3 = list_dialect[k-1]
        # length = int(packet_len / num)
        print('pkt1 length: %d, pkt2 length: %d, pkt3 length: %d, pkt4 length: %d, index: %d' %
              (pkt1, pkt2, pkt3, (packet_len - pkt1 - pkt2 - pkt3), k))

        # Start splitting into t subpackets
        t = 4
        self.client_socket.sendall(str(packet_len).encode())
        pkt = list(packet)
        sub_pkt = []
        start = 0
        end = 0
        for i in range(t):
            if i == (t - 1) and packet_len != (pkt1 + pkt2 + pkt3):
                sub_pkt.append(pkt[start: ])
            else:
                end += list_dialect[k][i]
                sub_pkt.append(pkt[start: end])
                start += list_dialect[k][i]
            print("customized packet: {}".format(sub_pkt[i]))

        # Concatenation
        # cached_pkts = ''.join(cached_pkts.split("|", 1)[1]) + "|" + packet
        cached_pkts = packet

        return sub_pkt, cached_pkts


    def send_file(self, file_name):
        '''server side: send file in dialect'''
        try:
            dataPort = self.client_socket.recv(1024).decode()
            print("[Control] Data port is {}".format(dataPort))

            # Connect to the data connection
            dataConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dataConnection.connect((self.client_ip, int(dataPort)))

            print(file_name, type(file_name))
            file_size = os.path.getsize(file_name)
            self.client_socket.sendall(
                "Exists,{}".format(file_size).encode('utf-8'))

            while True:
                recv_data = self.client_socket.recv(1024)
                request = recv_data.decode('utf-8').strip().split(",")

                if request[0] == "Ready":
                    print("Sending file {} to client {}".format(
                        file_name, self.client_ip))

                    with open(file_name, "rb") as file:
                        dataConnection.sendfile(file)
                elif request[0] == "Received":
                    if int(request[1]) == file_size:
                        self.client_socket.sendall("Success".encode('utf-8'))
                        print("{} successfully downloaded to client {}".format(
                            file_name, self.client_ip))
                        break
                    else:
                        print("Something went wrong trying to download to client {}:{}. Try again".format(
                            self.client_ip, self.client_port))
                        break
                else:
                    print("Something went wrong trying to download to client {}:{}. Try again".format(
                        self.client_ip, self.client_port))
                    break
        except IOError:
            print("File {} does not exist on server".format(file_name))
            self.client_socket.sendall("Failed".encode('utf-8'))


    def do_get(self, args, cached_pkts):
        '''client side: send request in dialect'''
        file = args.split()

        if len(file) != 1:
            print("rget requires exactly 1 argument.")
            return
            
        file_name = file[0]
        try:
            packet = "rget,{}".format(file_name)

            print("original packet: {}".format(packet))
            sub_pkt, cached_pkts = self.split_client(packet, cached_pkts)
            # print("customized subpacket: {}".format(sub_pkt))
            print("cached packet: {}".format(cached_pkts))
            for i in range(len(sub_pkt)):
                self.client_socket.sendall(''.join(sub_pkt[i]).encode())
                if "Subpacket received" == self.client_socket.recv(1024).decode().strip():
                    continue
                else:
                    print("No subpacket ack")
                    break
                # time.sleep(0.1)

            # Initilize data connection
            dataConnection = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            dataConnection.bind(('', 0))
            dataConnection.listen(1)
            dataPort = dataConnection.getsockname()[1]

            # Send data connection port to server over control connection
            # so server can connect.
            self.client_socket.send(str(dataPort).encode())

            # Wait for server to connect.
            dataConnection, maddr = dataConnection.accept()
            print('[Control] Got connection from', maddr)

            print('200 PORT command successful')

            while True:
                recv_data = self.client_socket.recv(1024)

                packet_info = recv_data.decode(
                    'utf-8').strip().split(",")

                if packet_info[0] == "Exists":
                    self.client_socket.sendall("Ready".encode('utf-8'))
                    # print(
                    #     "{} exits on the server, ready to download.".format(file_name))

                    save_file = open(file_name, "wb")

                    amount_recieved_data = 0
                    while amount_recieved_data < int(packet_info[1]):
                        recv_data = dataConnection.recv(1024)
                        amount_recieved_data += len(recv_data)
                        save_file.write(recv_data)

                        # printing hashes for each 1024 bytes of data transfered
                        if self.Hash == True:
                            print('#', end="")

                    # printing new line after printing hashes
                    if self.Hash == True:
                        print()

                    save_file.close()

                    self.client_socket.sendall("Received,{}".format(
                        amount_recieved_data).encode('utf-8'))
                elif packet_info[0] == "Success":
                    print('226 Transfer complete')
                    break
                elif packet_info[0] == "Failed":
                    print(
                        "File {} does not exist on server.".format(file_name))
                    break
                else:
                    print("Something went wrong when downloading '{}' from server. Try again.".format(
                        file_name))
                    break
            return cached_pkts
        except socket.error:
            print("SOCKET_ERROR: Check and ensure that server is running.")

