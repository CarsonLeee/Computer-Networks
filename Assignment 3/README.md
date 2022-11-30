# Description:
The general purpose of this assignment is to continue to explore network programming and more advanced concepts by a extending the text adventure game built in Assignment #2.  This assignment is designed to give you further experience in:
- writing networked applications
- the socket API in Python
- writing software supporting a simple protocol

# How to run:
Room.py:
	To connect:
		python3 room.py “-n, e, s, w” room://localhost:444 5555 Foyer “description” “items” “items”


player.py:
	To connect:
		python3 player.py “name” room://localhost:7777


To move between rooms:
	This only works if you have setup the server to that said room:
		“north” or “south” or “east” or “west” 
		“up” or “down”
	

To type to other players:
	Type:
		say
		say *message*


To terminate game: 
	In server terminal:
		ctrl + c
