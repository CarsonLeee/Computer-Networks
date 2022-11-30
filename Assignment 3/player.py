#Name: clee887
#Date: October 31st, 2022
#Description: CS 3357 Assignment 3
#Prof: Prof. Katchabaw

import sys
import argparse
import socket
import signal
import selectors
from urllib.parse import urlparse

# Client useful variables
inventory = [] # List of taken items
localIP = "localhost"
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
directions = {"north", "south", "west", "east", "up", "down"}
bufferSize = 1024

# Notify the server the user is exiting the room, so exiting the game
def exitGame(name, address):
    # Drop all items
    for item in inventory:
        UDPClientSocket.sendto(str.encode("drop " + item), address)
    # Exit user from room
    UDPClientSocket.sendto(str.encode("exit " + name), address)
    # Close program
    sys.exit()

# Helper function that parses the given room address
def parseRoomURL(serverAddress):
    # Parse server address provided
    res = urlparse(serverAddress)
    if res.scheme != "room" or not res.port or not res.hostname:
        raise Exception("CLIENT ERROR: Invalid server address")
    return res.hostname, res.port

# Helper function that returns the description for the items available
def describeItems(items):
    if len(items) > 0:
        msg = "In this room, there are:\n"
        for item in items:
            msg += "  " + item + "\n"
    else:
        msg = "There are no items available."
    return msg.strip()

# Helper function that makes the user join a new room
def joinRoom(name, serverAddressPort):
    UDPClientSocket.sendto(str.encode("join " + name), serverAddressPort)
    msgFromServer = UDPClientSocket.recvfrom(bufferSize)[0].decode("utf-8")
    return msgFromServer

# Function that launches the client and interacts with the server
def start(name, host, port):
    # Set server address host and port
    serverAddressPort = (host, port)

    # Start connection with server and print first message
    print(joinRoom(name, serverAddressPort))

    # Create selectors object and make it ready to listen both user input and client's socket
    sel = selectors.SelectSelector()
    sel.register(UDPClientSocket, selectors.EVENT_READ)
    sel.register(sys.stdin, selectors.EVENT_READ)

    # Loop to input user commands as long as needed
    while True:
        # Use try-except block in case any error occurs
        try:
            print(">", end="", flush=True)
            for key, event in sel.select():
                if key.fileobj == UDPClientSocket:
                    # Message received from server, just print it
                    response = "\n" + UDPClientSocket.recvfrom(bufferSize)[0].decode("utf-8")
                    # Check if message is that server is shutting down
                    if response.endswith("disconnect"):
                        response = "\n" + "Disconnected from server ... exiting!"
                else:
                    # User input, handle command properly
                    command = sys.stdin.readline().strip()
                    # Differentiate between commands only in client side or in both
                    if command not in ("inventory", "exit"):
                        if command.startswith("take") or command == "look" or command in directions:
                            # If command is "look", we also add the name of the player
                            if command == "look":
                                command += " " + name
                            UDPClientSocket.sendto(str.encode(command), serverAddressPort)
                            response = UDPClientSocket.recvfrom(bufferSize)[0].decode("utf-8")
                            # If user wants to take an item, update inventory if possible
                            if command.startswith("take") and response.endswith("taken"):
                                inventory.append(command[5:])
                            # If command is any of the directions, we check if there's a room at requested direction
                            if command in directions and response.startswith("room"):
                                # User can move. We disconnect it from current room and join it with new room
                                UDPClientSocket.sendto(str.encode("leave " + name + " " + command), serverAddressPort)
                                host, port = parseRoomURL(response)
                                serverAddressPort = (host, port)
                                response = joinRoom(name, serverAddressPort)
                                # Set new signal for interrupt action
                                def interrupt(num, frame):
                                    exitGame(name, (host, port))
                                signal.signal(signal.SIGINT, interrupt)
                        elif command.startswith("drop"):
                            # User wants to drop an item. If it exists within the inventory, drop it
                            if command[5:] in inventory:
                                inventory.remove(command[5:])
                                UDPClientSocket.sendto(str.encode(command), serverAddressPort)
                                response = UDPClientSocket.recvfrom(bufferSize)[0].decode("utf-8")
                            else:
                                response = "You are not holding " + command[5:]
                        elif command.startswith("say"):
                            # User wants to say something for all players in the room
                            if command == "say":
                                response = "What did you want to say?"
                            else:
                                response = "You said \"" + command[4:] + "\"."
                                command = "say " + name + " " + command[4:] # append name of player
                                UDPClientSocket.sendto(str.encode(command), serverAddressPort)
                        else:
                            response = "error: invalid command"
                    elif command == "inventory":
                        response = "You are holding:\n"
                        for item in inventory:
                            response += "  " + item + "\n"
                        response = response.strip()
                    else:
                        exitGame(name, serverAddressPort)

        except Exception as e:
            response = "error:", str(e)

        # Printing result
        print(response)
        # Exit game if needed
        if response.endswith("exiting!"):
            sys.exit()

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
    host, port = parseRoomURL(args["serverAddress"])

    # Set signal for interrupt action
    # Handler for interruption signal
    def interrupt(num, frame):
        exitGame(args["name"], (host, port))

    signal.signal(signal.SIGINT, interrupt)

    # Start client
    start(args["name"], host, port)

if __name__ == "__main__":
    main()
