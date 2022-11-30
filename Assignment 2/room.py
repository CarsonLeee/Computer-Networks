#Name: clee887
#Date: Oct 11, 2022
#Prof: Prof. Katchabaw
#Description: Assignment 2

import sys
import argparse
import socket
import signal

# Server useful variables
players = [] # List of clients with players in the room
localIP = "localhost"
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
bufferSize = 1024

# Handler for interruption signal
def interrupt(num, frame):
    print("Interrupt received, shutting down ...")
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
def start(port, name, description, items):
    # Create full description message for room and create copy of items' list
    roomDescription = name + "\n\n" + description + "\n\n"
    avItems = items[:] # copy preferred to avoid changing original list

    # Bind server to address needed
    UDPServerSocket.bind((localIP, port))
    # Print initial message for server app and start listening for incoming client requests
    print("Room Starting Description:\n\n" + roomDescription + describeItems(avItems) + "\n")
    print("Room will wait for players at port:", port)
    while True:
        # Use try-except block in case any error occurs
        try:
            # Receive next incoming datagram, and get message and address from it
            bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
            message = bytesAddressPair[0].decode("utf-8")
            address = bytesAddressPair[1]

            # Check possible commands from client
            if message.startswith("join"):
                # New player has joined the room. Add it to list of players, print message within server side and send back the full description to client
                player = message.split()[1]
                players.append(player)
                print("User", player, "joined from address", address)
                bytesToSend = str.encode(roomDescription + describeItems(avItems))
            elif message == "look":
                # Send back the current room description
                bytesToSend = str.encode(roomDescription + describeItems(avItems))
            elif message.startswith("take"):
                # User wants to take an item. Check if available, and if so, take it and remove it from available items take apple
                item = message[5:]
                if item in avItems:
                    avItems.remove(item)
                    bytesToSend = str.encode(item + " taken")
                else:
                    bytesToSend = str.encode(item + " not available")
            elif message.startswith("drop"):
                # User wants to drop an item. Client side is in charge of checking the item has been taken by the user, so here we assume it can be dropped safely
                item = message[5:]
                avItems.append(item)
                bytesToSend = str.encode(item + " dropped")
            elif message.startswith("exit"):
                # Remove given player from current players in the room
                players.remove(message[5:])
                print("User", player, "left from address", address)
            else:
                bytesToSend = str.encode("error: invalid command")

        except Exception as e:
            bytesToSend = str.encode("error:", str(e))

        # Sending a reply to client
        UDPServerSocket.sendto(bytesToSend, address)

# Main entrypoint for the server
def main():
    # Check all commands needed were given
    if len(sys.argv) < 5:
        raise Exception("SERVER ERROR: Not enough input arguments to launch the server")
    # Get command line arguments to create the room
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int)
    parser.add_argument("name")
    parser.add_argument("description")
    parser.add_argument("items", nargs="+", default=[])

    # Set signal for interrupt action
    signal.signal(signal.SIGINT, interrupt)

    # Start server
    args = vars(parser.parse_args())
    start(**args)

if __name__ == "__main__":
    main()
