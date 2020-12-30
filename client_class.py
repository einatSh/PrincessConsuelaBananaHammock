# TODO: pynput may not work , look for something else
import msvcrt
from threading import Thread
from _thread import start_new_thread
from pynput.keyboard import Listener
from socket import *
import struct
import time


class Client:

    def __init__(self):
        self.__serverName = '127.0.0.1'
        self.__udp_port = 13117
        self.__serverPort = self.__udp_port
        # set tcp and udp sockets
        self.__clientTCPSocket = socket(AF_INET, SOCK_STREAM)
        # clientTCPSocket.setblocking(0)
        self.__clientUDPSocket = socket(AF_INET, SOCK_DGRAM)
        self.__con_msg = "Client started"
        self.__err_count = 0

    def reset(self):
        self.__clientUDPSocket = socket(AF_INET, SOCK_DGRAM)
        self.__clientTCPSocket = socket(AF_INET, SOCK_STREAM)

    def run(self):
        # self.set_env()
        self.reset()
        self.looking_for_server()
        self.connect_to_server()
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
            # reset the counter and set the server connection msg
            self.__err_count = 0
            self.__con_msg = "Server disconnected"
            return False

    def looking_for_server(self):
        """
            Look for server. We leave this state when we get an offer
        """
        # bind udp socket to server address (name, port)
        self.__clientUDPSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.__clientUDPSocket.bind((self.__serverName, self.__udp_port))

        while True:
            try:
                print(Color.CYAN + Color.BOLD + self.__con_msg + ", listening for offer requests..." + Color.END_C)
                msg, serverAddress = self.__clientUDPSocket.recvfrom(2048)
                # self.__serverName = serverAddress[0]
                self.__serverPort = struct.unpack('IbH', msg)[2]
                print(Color.CYAN + Color.BOLD + "Received offer from from: " + Color.PINK + serverAddress[0]
                      + Color.CYAN + Color.BOLD + ", attempting to connect..." + Color.END_C)
                break
            except error:
                # if any connection error occurs
                print(Color.BR_RED + "Error receiving offer from server. No worries mate, we'll try again!" + Color.END_C)
        self.__clientUDPSocket.close()

    def connect_to_server(self):
        """
            Connect to the server, We leave this state when we successfully connect via tcp to server.
        """
        while True:
            try:
                self.__clientTCPSocket.connect((self.__serverName, self.__serverPort))
                # send team name to the server
                team = input(Color.YELLOW + "Please enter team name: " + Color.END_C)
                msg = team + '\n'
                self.__clientTCPSocket.send(msg.encode('UTF-8'))
                break
            except error:
                error_msg = "Connection error...No worries master, Doby will try again!"
                if not self.print_error(error_msg):
                    self.run()

    def keyboard_whisperer(self):
        """
            Collect data from keyboard
        """
        with Listener(on_release=self.on_release) as listener:
            def time_out(period_sec: int):
                time.sleep(period_sec)  # Listen to keyboard for period_sec seconds
                listener.stop()
            Thread(target=time_out, args=(6,)).start()
            listener.join()

    def game_mode(self):
        """
            Collect chars from keyboard and send to server via tcp.
            Collect data from the network and print it on screen
        """
        # set timeout for socket
        self.__clientTCPSocket.settimeout(20)
        start_flag = True
        while True:
            try:
                # collect data from network
                serverData = self.__clientTCPSocket.recv(1024)
                print(Color.ITALIC + Color.BR_PINK + serverData.decode('UTF-8') + Color.END_C)
                if start_flag:
                    # after getting the welcome msg - start listening for keyboard strokes (only start once)
                    start_new_thread(self.keyboard_whisperer, ())
                    start_flag = False
            except error:
                error_msg = "Connection error...This wasn't the droid you're looking for!"
                if not self.print_error(error_msg):
                    self.run()

        # collect data from keyboard
        # TODO: char = getch.getch() works on linux
        # char = getch.getch()
        # char = msvcrt.getche()
        # print(char)

    def on_release(self, key):
        # print("Key released: {0}".format(key))
        try:
            if not str(key.char) == '':
                self.__clientTCPSocket.send(str(key.char).encode('UTF-8'))
        except AttributeError:
            pass


class Color:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PINK = '\033[35m'
    CYAN = '\033[36m' # this is some kind of light blue
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
    # if you wanna change colors - print and choose
    # print(Color.RED + "RED" + Color.END_C)
    # print(Color.BR_RED + "BR_RED" + Color.END_C)
    # print(Color.CYAN + "CYAN" + Color.END_C)
    # print(Color.BR_CYAN + "BR_CYAN" + Color.END_C)
    # print(Color.BLUE + "BLUE" + Color.END_C)
    # print(Color.BLUE + Color.BOLD+ "BLUE" + Color.END_C)
    # print(Color.BR_BLUE + "BR_BLUE" + Color.END_C)
    # print(Color.PINK + "PINK" + Color.END_C)
    # print(Color.BR_PINK + "BR_PINK" + Color.END_C)
    # print(Color.GREEN + "GREEN" + Color.END_C)
    # print(Color.BR_GREEN + "BR_GREEN" + Color.END_C)
    # print(Color.YELLOW + "YELLOW" + Color.END_C)
    # print(Color.BR_YELLOW + "BR_YELLOW" + Color.END_C)
    Client().run()
