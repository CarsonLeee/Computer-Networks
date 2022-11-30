#Name: clee887
#Date: October 31st, 2022
#Description: CS 3357 Assignment 3
#Prof: Prof. Katchabaw

import sys
import argparse
import socket
import signal

# Server useful variables
players = {}     # Dictionary of (player, address) 
otherRooms = {}  # Dictionary of (dir, roomAddress) of rooms connected to current one
directions = {"n": "north", "s": "south", "w": "west", "e":"east", "u": "up", "d": "down"}
localIP = "localhost"
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
bufferSize = 1024

# Handler for interruption signal
def interrupt(num, frame):
    # Before exiting, notify clients that server is shutting down
    print("Interrupt received, shutting down ...")
    # Now, we notify all players the message being said
    for roomPlayer in players:
        UDPServerSocket.sendto(str.encode("disconnect"), players[roomPlayer])
    sys.exit()

# Helper function that returns the description for the items available and players in the room
def describeItems(items, callerName):
    if len(items) > 0 or len(players) > 1:
        msg = "In this room, there are:\n"
        # Show items (if any)
        for item in items:
            msg += "  " + item + "\n"
        # Show players if other than the player requesting the description
        for player in players:
            msg += "  " + player + "\n" if player != callerName else ""
    else:
        msg = "There are no items available nor players in the room."
    return msg.strip()

# Function that launches the server and waits for incoming connections
def start(port, name, description, items, **kwargs):
    # Store other rooms' directions (if any)
    for direction, address in kwargs.items():
        if address:
            otherRooms[directions[direction]] = address

    # Create full description message for room and create copy of items list
    roomDescription = name + "\n\n" + description + "\n\n"
    avItems = items[:] # copy preferred to avoid changing original list

    # Bind server to address needed
    UDPServerSocket.bind((localIP, port))
    # Print initial message for server app and start listening for incoming client requests
    print("Room Starting Description:\n\n" + roomDescription + describeItems(avItems, "") + "\n")
    print("Room will wait for players at port:", port)
    while True:
        # Use try-except block in case any error occurs
        try:
            # Receive next incoming datagram, and get message and address from it
            bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
            message = bytesAddressPair[0].decode("utf-8")
            address = bytesAddressPair[1]

            # Check possible commands from client and different messages to send back to different clients
            bytesToSend = {}
            if message.startswith("join"):
                # New player has joined the room. Add it to dict of players, print message within server side
                # and send back the full description to client joining
                player = message.split()[1]
                players[player] = address
                print("User", player, "joined from address", address)
                bytesToSend[address] = str.encode(roomDescription + describeItems(avItems, player))
                # Now, we notify all players already in the room that a new player joined
                for roomPlayer in players:
                    if player != roomPlayer:
                        bytesToSend[players[roomPlayer]] = str.encode(player + " entered the room.")
            elif message.startswith("say"):
                # User wants to say something to all players in the room
                player = message.split()[1]
                msg = " ".join(message.split()[2:])
                # Now, we notify all players the message being said
                for roomPlayer in players:
                    if player != roomPlayer:
                        bytesToSend[players[roomPlayer]] = str.encode(player + " said \"" + msg + "\"")
            elif message.startswith("look"):
                # Send back the current room description
                player = message.split()[1]
                bytesToSend[address] = str.encode(roomDescription + describeItems(avItems, player))
            elif message.startswith("take"):
                # User wants to take an item. Check if available, and if so, take it and remove it
                # from available items take apple
                item = message[5:]
                if item in avItems:
                    avItems.remove(item)
                    bytesToSend[address] = str.encode(item + " taken")
                else:
                    bytesToSend[address] = str.encode(item + " not available")
            elif message.startswith("drop"):
                # User wants to drop an item. Client side is in charge of checking the item has been taken
                # by the user, so here we assume it can be dropped safely
                item = message[5:]
                avItems.append(item)
                bytesToSend[address] = str.encode(item + " dropped")
            elif message in directions.values():
                # User wants to leave the room and head into another one. Check if requested direction is available
                if message in otherRooms.keys():
                    # User can move to room requested. Send back the address to move into
                    bytesToSend[address] = str.encode(otherRooms[message])
                else:
                    # Direction doesn't lead to other connected room
                    bytesToSend[address] = str.encode(message + " doesn't lead to other room")
            elif message.startswith("leave") or message.startswith("exit"):
                # User is leaving the room
                vals = message.split()
                # First, we remove given player from current players in the room
                del players[vals[1]]
                print("User", vals[1], "left from address", address)
                # Now, we notify all players that the player is exiting the game or joining another room
                for roomPlayer in players:
                    if vals[1] != roomPlayer:
                        response = (vals[1] + " left the game." if message.startswith("exit")
                                else vals[1] + " left the room, heading " + vals[2] + ".")
                        bytesToSend[players[roomPlayer]] = str.encode(response)
            else:
                bytesToSend[address] = str.encode("error: invalid command")

        except Exception as e:
            bytesToSend[address] = str.encode("error:", str(e))

        # Sending all replies needed to clients
        for add, msg in bytesToSend.items():
            UDPServerSocket.sendto(msg, add)

# Main entrypoint for the server
def main():
    # Check all commands needed were given
    if len(sys.argv) < 5:
        raise Exception("SERVER ERROR: Not enough input arguments to launch the server")
    # Get command line arguments to create the room
    parser = argparse.ArgumentParser()
    parser.add_argument("-n")
    parser.add_argument("-s")
    parser.add_argument("-e")
    parser.add_argument("-w")
    parser.add_argument("-u")
    parser.add_argument("-d")
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
