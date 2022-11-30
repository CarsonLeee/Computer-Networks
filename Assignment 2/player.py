#Name: clee887
#Date: Oct 11, 2022
#Prof: Prof. Katchabaw
#Description: Assignment 2

import sys
import argparse
import socket
import signal
from urllib.parse import urlparse

# Client useful variables
inventory = [] # List of taken items
localIP = "localhost"
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
bufferSize = 1024

# Notify the server the user is exiting the room
def exitRoom(name, address):
    # Drop all items
    for item in inventory:
        UDPClientSocket.sendto(str.encode("drop " + item), address)
    # Exit user from room
    UDPClientSocket.sendto(str.encode("exit " + name), address)
    # Close program
    sys.exit()

# Helper function that returns the description for the items available
def describeItems(items):
    if len(items) > 0:
        msg = "In this room, there are:\n"
        for item in items:
            msg += "  " + item + "\n"
    else:
        msg = "There are no items available."
    return msg.strip()

# Function that launches the server and waits for incoming connections
def start(name, host, port):
    # Set server address host and port
    serverAddressPort = (host, port)

    # Start connection with server and print first message
    UDPClientSocket.sendto(str.encode("join " + name), serverAddressPort)
    msgFromServer = UDPClientSocket.recvfrom(bufferSize)[0].decode("utf-8")
    print(msgFromServer)

    # Loop to input user commands as long as needed
    while True:
        # Use try-except block in case any error occurs
        try:
            command = input(">")
            # Differentiate between commands only in client side or in both
            if command not in ("inventory", "exit"):
                if command.startswith("take") or command == "look":
                    UDPClientSocket.sendto(str.encode(command), serverAddressPort)
                    response = UDPClientSocket.recvfrom(bufferSize)[0].decode("utf-8")
                    # If user wants to take an item, update inventory if possible
                    if command.startswith("take") and response.endswith("taken"):
                        inventory.append(command[5:])
                elif command.startswith("drop"):
                    # User wants to drop an item. If it exists within the inventory, drop it
                    if command[5:] in inventory:
                        inventory.remove(command[5:])
                        UDPClientSocket.sendto(str.encode(command), serverAddressPort)
                        response = UDPClientSocket.recvfrom(bufferSize)[0].decode("utf-8")
                    else:
                        response = "You are not holding " + command[5:]
                else:
                    response = "error: invalid command"
            elif command == "inventory":
                response = "You are holding:\n"
                for item in inventory:
                    response += "  " + item + "\n"
                response = response.strip()
            else:
                exitRoom(name, serverAddressPort)

        except Exception as e:
            response = "error:", str(e)

        # Printing result
        print(response)

# Main entrypoint for the client
def main():
    # Check all commands needed were given
    if len(sys.argv) < 3:
        raise Exception("CLIENT ERROR: Not enough input arguments to launch the client")
    # Get command line arguments to create the room
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("serverAddress")
    args = vars(parser.parse_args())

    # Parse server address provided
    res = urlparse(args["serverAddress"])
    if res.scheme != "room" or not res.port or not res.hostname:
        raise Exception("CLIENT ERROR: Invalid server address")
    host = res.hostname
    port = res.port

    # Set signal for interrupt action and handler for interruption signal
    def interrupt(num, frame):
        exitRoom(args["name"], (host, port))

    signal.signal(signal.SIGINT, interrupt)

    # Start client
    start(args["name"], host, port)

if __name__ == "__main__":
    main()
