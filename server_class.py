from _thread import start_new_thread
import random
import sys
from functools import reduce
from socket import *
import struct
import time
import threading
import asyncio
from typing import Tuple


class Server:

    def __init__(self):
        self.__serverName = '127.0.0.1'
        self.__udp_port = 13117 # default udp port
        self.__serverPort = 12000
        # self.__multicast_group = (self.__serverName, self.__serverPort)
        # set udp multicast socket and tcp socket for client
        self.__serverUDPSocket = socket(AF_INET, SOCK_DGRAM)
        self.__serverTCPSocket = socket(AF_INET, SOCK_STREAM)
        self.__groups = [[], []]
        self.__groups_lock = threading.Lock()
        self.__counter_A_lock = threading.Lock()
        self.__counter_B_lock = threading.Lock()
        self.__counter_group_A = 0
        self.__counter_group_B = 0
        self.__connections = []
        self.__err_count = 0
        self.__con_msg = ""

    def reset(self):
        self.__serverUDPSocket = socket(AF_INET, SOCK_DGRAM)
        self.__serverTCPSocket = socket(AF_INET, SOCK_STREAM)
        self.__groups = [[], []]
        # self.__groups_lock = threading.Lock()
        self.__counter_group_A = 0
        self.__counter_group_B = 0
        self.__connections = []

    def run(self):
        # self.set_env()
        self.__con_msg = "Server started, listening on IP address " + Color.PINK + self.__serverName + Color.BLUE + "..."
        self.reset()
        self.wait_for_clients()
        self.game_mode()
        self.run()

    def set_env(self):
        """
            Set environment (development or testing).
        """
        while True:
            print(Color.YELLOW + "Please pick environment (dev/test):" + Color.END_C)
            env = input()
            if env == "dev":
                self.__serverName = '172.1.0.24'
                break
            elif env == "test":
                self.__serverName = '172.99.0.24'
                break
            else:
                print(Color.BR_RED + "Wrong input dummy -_-" + Color.END_C)

    def print_error(self, error_msg):
        """
            Print errors, if we get 5 errors for the connection -
            return boolean value indicating if we reached 5 errors.
        :param error_msg: msg to be printed to the screen.
        :return: True while we have less than 5 errors counted, else return False.
        """
        if self.__err_count < 5:
            if self.__err_count == 0:
                print(Color.BR_RED + error_msg + Color.END_C)
            self.__err_count = self.__err_count + 1
            return True
        else:
            # reset the counter
            self.__err_count = 0
            print(Color.BR_RED + "Trying to re-connect..." + Color.END_C)
            return False

    def add_client_to_group(self, client_name):
        """
            Adds the client's team name to group A or B
        :param client_name: Team name of the client
        :param client_address: the client (IP address, port)
        """
        group_num = random.randint(0, 1)
        self.__groups_lock.acquire()
        self.__groups[group_num].append(client_name)
        self.__groups_lock.release()

    def UDP_broadcast(self, startTime, msg):
        """
            Broadcast function, sends the msg for 10 seconds, using UDP connection
        :param startTime: start time
        :param msg: message to broadcast
        """
        while time.time() - startTime <= 10:
            try:
                self.__serverUDPSocket.sendto(msg, (self.__serverName, self.__udp_port))
                # print("UDP broadcast")
                time.sleep(1)
            except error:
                err_msg = "Couldn't send broadcast msg on UDP connection"
                if not self.print_error(err_msg):
                    self.run()
        try:
            self.__serverUDPSocket.close()
        except error:
            print(Color.BR_RED + "Couldn't close UDP connection socket - reset socket" + Color.END_C)
            self.__serverUDPSocket = socket(AF_INET, SOCK_DGRAM)
        exit(0)

    def record_client_name(self, startTime, connectionSocket, client_address):
        """
            Waits for client's name, and add him to a group
        :param connectionSocket:
        """
        connectionSocket.setTimeout(5)
        while time.time() - startTime <= 10:
            try:
                client_name = connectionSocket.recv(1024)
                client_name = client_name.decode('UTF-8')
                print("Server got client name ", client_name)
                self.add_client_to_group(client_name)
                self.__connections.append((connectionSocket, client_name))
                exit()
            except error:
                err_msg = "Error receiving data from client: " + client_address
                if not self.print_error(err_msg):
                    print(Color.RED + "Client: " + client_address + " disconnected!" + Color.END_C)
                    # close obsolete connection socket
                    try:
                        connectionSocket.close()
                    except error:
                        pass
                    exit()
        # print("Client " + client_address + "didn't send team name")

    def wait_for_clients(self):
        """
            wait for clients - send out offer msg and response to requests and new tcp connections.
            We leave this state after 10 seconds
        :return:
        """
        self.__serverUDPSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        # set offer msg - format = unsigned int (4 byte), unsigned char (1 byte), unsigned short (2 byte)
        msg = struct.pack('IbH', 0xfeedbeef, 0x2, self.__serverPort)

        startTime = time.time()
        print(Color.BLUE + self.__con_msg + Color.END_C)
        # Creates new thread to broadcast the announcements using UDP connection
        start_new_thread(self.UDP_broadcast, (startTime, msg))

        self.__serverTCPSocket.bind((self.__serverName, self.__serverPort))
        # start listening to tcp requests
        self.__serverTCPSocket.listen(5)
        # limit the serverTCPSocket time waiting for clients to ~10sec
        self.__serverTCPSocket.settimeout(9)
        # for 10 seconds wait for clients to connect with a TCP connection
        while time.time() - startTime <= 10:
            try:
                # establish TCP connection with client
                print("listen to clients")
                connectionSocket, address = self.__serverTCPSocket.accept()
                print("got tcp connection request from client : ", address)
                # Creates new thread to for client
                start_new_thread(self.record_client_name, (startTime, connectionSocket, address))
            except error:
                print("Unfortunately, the socket just won't accept this nonsense... - line 163")
                # pass

    def add_score_to_group(self, team_name):
        """
            Increase relevant group score by 1
        :param team_name: team name name who got the score, team_name belongs to Group A/B
        """
        if team_name in self.__groups[0]:
            self.__counter_A_lock.acquire()
            self.__counter_group_A += 1
            self.__counter_A_lock.release()
        else:
            self.__counter_B_lock.acquire()
            self.__counter_group_B += 1
            self.__counter_B_lock.release()

    def get_client_score(self, connSocket, team_name, start_time):
        """
            Listening to connSocket for 10 seconds and count the clients keyboard types
        :param connSocket: connection to listen to
        :param team_name: team name of the client on this connection
        :param start_time: start time of the game
        """
        # startTime = time.time()
        connSocket.setTimeout(5)
        while time.time() - start_time <= 10:
            try:
                # get byte from client
                # TODO: recv is blocking, need to handle when the client doesnt send's team name
                char = connSocket.recv(1)
                char = char.decode('UTF-8')
                print(char)
                self.add_score_to_group(team_name)
            except error:
                err_msg = "Error - in recv function TCP connection - line 198"
                if not self.print_error(err_msg):
                    print(Color.RED + "client: " + connSocket.getsockname() + " disconnected!" + Color.END_C)
                    try:
                        connSocket.close()
                    except error:
                        pass
                break

    def game_mode(self):
        """
            Collect chars from the network and calculate the score - leave this state after 10 seconds
        :return:
        """
        # creates the welcome message
        welcome_msg = "Welcome to Keyboard Spamming Battle Royale.\n" + "Group 1:\n==\n"
        welcome_msg += "Empty Group\n" if len(self.__groups[0]) == 0 \
            else reduce(lambda acc, curr: acc + "\n" + curr[0], self.__groups[0][1:], self.__groups[0][0])
        welcome_msg += "Group 2:\n==\n"
        welcome_msg += "Empty Group\n" if len(self.__groups[1]) == 0 \
            else reduce(lambda acc, curr: acc + "\n" + curr[0], self.__groups[1][1:], self.__groups[1][0])
        welcome_msg += "Start pressing keys on your keyboard as fast as you can!!"

        # sends all the clients the welcome message only once
        for con in self.__connections:
            try:
                con[0].send(welcome_msg.encode('UTF-8'))
            except error:
                pass

        startTime = time.time()

        # for each client creates a thread for listening
        for con in self.__connections:
            start_new_thread(self.get_client_score, (con[0], con[1], startTime))
        # map(lambda con: start_new_thread(self.get_client_score, (con, startTime)), self.__connections)
        while time.time() - startTime <= 10:
            1

        # creates the summary message
        summary_message = Color.CYAN + Color.ITALIC + Color.BOLD + "Game over!\n"
        summary_message += "Group 1 typed in " + str(self.__counter_group_A) + " characters."
        summary_message += " Group 2 typed in " + str(self.__counter_group_B) + " characters.\n"
        summary_message += "Group 1 wins!" if self.__counter_group_A > self.__counter_group_B \
            else "Group 2 wins!" if self.__counter_group_A < self.__counter_group_B else 'It\'s a TIE!!'
        summary_message += Color.GREEN + Color.BOLD + "\n\nCongratulations to the winners:\n==\n" + Color.BR_PINK + Color.BOLD
        winner = 0 if self.__counter_group_A > self.__counter_group_B else 1
        summary_message += "Empty Group\n" if len(self.__groups[winner]) == 0 \
            else reduce(lambda acc, curr: acc + "\n" + curr[0], self.__groups[winner][1:], self.__groups[winner][0])
        print(summary_message + Color.END_C)

        for con in self.__connections:
            try:
                con[0].send(summary_message.encode('UTF-8'))
            except error:
                print(Color.BR_RED + "Error- client: " + con[0].getsockname() + ", closed his TCP connection, couldn't send summary message" + Color.END_C)

        # close all TCP connections
        for con in self.__connections:
            try:
                con[0].close()
            except error:
                print(Color.BR_RED + "Error - error with closing TCP connection" + Color.END_C)

        self.__serverTCPSocket.close()
        self.__con_msg = "Game over, sending out offer requests..."


class Color:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PINK = '\033[35m'
    CYAN = '\033[36m'  # this is some kind of light blue
    BR_RED = '\033[91m'
    BR_GREEN = '\033[92m'
    BR_YELLOW = '\033[93m'
    BR_BLUE = '\033[94m'
    BR_PINK = '\033[95m'
    BR_CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    BLINK = '\033[5m'
    END_C = '\033[0m'


if __name__ == "__main__":
    Server().run()
