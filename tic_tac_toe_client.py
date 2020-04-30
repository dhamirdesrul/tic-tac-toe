# Import the GUI library Tkinter
import tkinter
# Import the messagebox module explicitly
from tkinter import messagebox
# Import multi-threading module
import threading
# Import socket
import socket
import webbrowser
import logging

# Constants 
C_WINDOW_WIDTH = 640;
C_WINDOW_HEIGHT = 480;
C_WINDOW_MIN_WIDTH = 480;
C_WINDOW_MIN_HEIGHT = 360;

C_COLOR_BLACK = "#000000"
C_COLOR_WHITE = "#ffffff"

C_COLOR_HOVER = "#424242"
C_COLOR_NORMAL = "#E0E0E0"

C_COLOR_X = "#FF6F00"
C_COLOR_O = "#1E88E5"

C_COLOR_BLUE_LIGHT = "#e4f1fe";
C_COLOR_BLUE_DARK = "#304e62";
C_COLOR_BLUE = "#a8d4f2";

# Set up logging to file
logging.basicConfig(level=logging.DEBUG,
	format='[%(asctime)s] %(levelname)s: %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S',
	filename='client.txt');
# Define a Handler which writes INFO messages or higher to the sys.stderr
# This will print all the INFO messages or higer at the same time
console = logging.StreamHandler();
console.setLevel(logging.INFO);
# Add the handler to the root logger
logging.getLogger('').addHandler(console);

class TTTClient:
	"""TTTClient deals with networking and communication with the TTTServer."""

	def __init__(self):
		"""Initializes the client and create a client socket."""
		# Create a TCP/IP socket
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);

	def connect(self, address, port_number):
		"""Keeps repeating connecting to the server and returns True if 
		connected successfully."""
		while True:
			try:
				print("Connecting to the game server...");
				# Connection time out 60 seconds
				self.client_socket.settimeout(60);
				# Connect to the specified host and port 
				self.client_socket.connect((address, int(port_number)));
				logging.info("port " + str(port_number));
				# Return True if connected successfully
				return True;
			except:
				# Caught an error
				logging.warning("There is an error when trying to bind " +
								str(port_number));
				print("There is an error when trying to connect to " + 
					str(address) + "::" + str(port_number));
				self.__connect_failed__();
		return False;

	def __connect_failed__(self):
		"""(Private) This function will be called when the attempt to connect
		failed. This function might be overridden by the GUI program."""
		# Ask the user what to do with the error
		choice = input("[A]bort, [C]hange address and port, or [R]etry?");
		if(choice.lower() == "a"):
			exit();
		elif(choice.lower() == "c"):
			address = input("Please enter the address: ");
			port_number = input("Please enter the port: ");

	def s_send(self, command_type, msg):
		"""Sends a message to the server with an agreed command type token 
		to ensure the message is delivered safely."""
		# A 1 byte command_type character is put at the front of the message
		# as a communication convention
		try:
			self.client_socket.send((command_type + msg).encode());
		except:
			# If any error occurred, the connection might be lost
			self.__connection_lost();

	def s_recv(self, size, expected_type):
		"""Receives a packet with specified size from the server and check 
		its integrity by comparing its command type token with the expected
		one."""
		try:
			msg = self.client_socket.recv(size).decode();
			# If received a quit signal from the server
			if(msg[0] == "Q"):
				why_quit = "";
				try:
					# Try receiving the whole reason why quit
					why_quit = self.client_socket.recv(1024).decode();
				except:
					pass;
				# Print the resaon
				print(msg[1:] + why_quit);
				# Throw an error
				raise Exception;
			# If received an echo signal from the server
			elif(msg[0] == "E"):
				# Echo the message back to the server
				self.s_send("e", msg[1:]);
				# Recursively retrive the desired message
				return self.s_recv(size, expected_type);
			# If the command type token is not the expected type
			elif(msg[0] != expected_type):
				print("The received command type \"" + msg[0] + "\" does not " + 
					"match the expected type \"" + expected_type + "\".");
				# Connection lost
				self.__connection_lost();
			# If received an integer from the server
			elif(msg[0] == "I"):
				# Return the integer
				return int(msg[1:]);
			# In other case
			else:
				# Return the message
				return msg[1:];
			# Simply return the raw message if anything unexpected happended 
			# because it shouldn't matter any more
			return msg;
		except:
			# If any error occurred, the connection might be lost
			self.__connection_lost();
		return None;

	def __connection_lost(self):
		"""(Private) This function will be called when the connection is lost."""
		print("Error: connection lost.");
		try:
			# Try and send a message back to the server to notify connection lost
			self.client_socket.send("q".encode());
		except:
			pass;
		# Raise an error to finish 
		raise Exception;

	def close(self):	
		"""Shut down the socket and close it"""
		# Shut down the socket to prevent further sends/receives
		self.client_socket.shutdown(socket.SHUT_RDWR);
		# Close the socket
		self.client_socket.close();

class TTTClientGame(TTTClient):
	"""TTTClientGame deals with the game logic on the client side."""

	def __init__(self):
		"""Initializes the client game object."""
		TTTClient.__init__(self);

	def start_game(self, password, score, scoreopponent):
		"""Starts the game and gets basic game information from the server."""
		# Receive the player's ID from the server
		self.score = score
		self.scoreopponent = scoreopponent
		self.player_id = int(self.s_recv(128, "A"));
		# Confirm the ID has been received
		self.s_send("c","1");

		# Send the match's password
		self.s_send("o",str(password));

		# Tell the user that connection has been established
		self.__connected__();

		# Receive the assigned role from the server
		self.role = str(self.s_recv(2, "R"));
		# Confirm the assigned role has been received
		self.s_send("c","2");

		# Receive the mactched player's ID from the server
		self.match_id = int(self.s_recv(128, "I"));
		# Confirm the mactched player's ID has been received
		self.s_send("c","3");

		print(("You are now matched with " + str(self.match_id) 
			+ "\nYou are the \"" + self.role + "\""));

		# Call the __game_started() function, which might be implemented by
		# the GUI program to interact with the user interface.
		self.__game_started__();

		# Start the main loop
		self.__main_loop();

	def __connected__(self):
		"""(Private) This function is called when the client is successfully
		connected to the server. This might be overridden by the GUI program."""
		# Welcome the user
		print("Welcome to Tic Tac Toe online, player " + str(self.player_id) 
			+ "\nPlease wait for another player to join the game...");

	def __game_started__(self):
		"""(Private) This function is called when the game is getting started."""
		# This is a virtual function
		# The actual implementation is in the subclass (the GUI program)
		return;

	def __main_loop(self):
		"""The main game loop."""
		while True:
			# Get the board content from the server
			board_content = self.s_recv(10, "B");
			# Get the command from the server 
			command = self.s_recv(2, "C");
			# Update the board
			self.__update_board__(command, board_content);
			logging.info("Received connection from " + str(board_content));

			if(command == "Y"):
				# If it's this player's turn to move
				self.__player_move__(board_content);
			elif(command == "N"):
				# If the player needs to just wait
				self.__player_wait__();
				# Get the move the other player made from the server 
				move = self.s_recv(2, "I");
				self.__opponent_move_made__(move);
			elif(command == "D"):
				# If the result is a draw
				print("It's a draw.");
				break;
			elif(command == "W"):
				# If this player wins
				print("You WIN!");
				# Draw winning path
				self.__draw_winning_path__(self.s_recv(4, "P"));
				# Break the loop and finish
				break;
			elif(command == "L"):
				# If this player loses
				print("You lose.");
				# Draw winning path
				self.__draw_winning_path__(self.s_recv(4, "P"));
				# Break the loop and finish
				break;
			else:
				# If the server sends back anything unrecognizable
				# Simply print it
				logging.error("Error: unknown message was sent from the server");
				print("Error: unknown message was sent from the server");
				# And finish
				break;

	def __update_board__(self, command, board_string):
		"""(Private) Updates the board. This function might be overridden by
		the GUI program."""
		if(command == "Y"):
			# If it's this player's turn to move, print out the current 
			# board with " " converted to the corresponding position number
			print("Current board:\n" + TTTClientGame.format_board(
				TTTClientGame.show_board_pos(board_string)));
			logging.info(str(TTTClientGame.format_board(TTTClientGame.show_board_pos(board_string))));
		else:
			# Print out the current board
			print("Current board:\n" + TTTClientGame.format_board(
				board_string));
			logging.info(str(TTTClientGame.format_board(TTTClientGame.show_board_pos(board_string))));

	def __player_move__(self, board_string):
		"""(Private) Lets the user input the move and sends it back to the
		server. This function might be overridden by the GUI program."""
		while True:
			# Prompt the user to enter a position
			try:
				position = int(input('Please enter the position (1~9):'));
			except:
				print("Invalid input.");
				continue;

			# Ensure user-input data is valid
			if(position >= 1 and position <= 9):
				# If the position is between 1 and 9
				if(board_string[position - 1] != " "):
					# If the position is already been taken,
					# Print out a warning
					print("That position has already been taken." + 
						"Please choose another one.");
				else:
					# If the user input is valid, break the loop
					break;
			else:
				print("Please enter a value between 1 and 9 that" + 
					"corresponds to the position on the grid board.");
			# Loop until the user enters a valid value

		# Send the position back to the server
		self.s_send("i", str(position));

	def __player_wait__(self):
		"""(Private) Lets the user know it's waiting for the other player to
		make a move. This function might be overridden by the GUI program."""
		print("Waiting for the other player to make a move...");

	def __opponent_move_made__(self, move):
		"""(Private) Shows the user the move that the other player has taken. 
		This function might be overridden by the GUI program."""
		print("Your opponent took up number " + str(move));

	def __draw_winning_path__(self, winning_path):
		"""(Private) Shows to the user the path that has caused the game to 
		win or lose. This function might be overridden by the GUI program."""
		# Generate a new human readable path string
		readable_path = "";
		for c in winning_path:
			readable_path += str(int(c) + 1) + ", "

		print("The path is: " + readable_path[:-2]);


	def show_board_pos(s):
		"""(Static) Converts the empty positions " " (a space) in the board 
		string to its corresponding position index number."""

		new_s = list("123456789");
		for i in range(0, 8):
			if(s[i] != " "):
				new_s[i] = s[i];
		return "".join(new_s);

	def format_board(s):
		"""(Static) Formats the grid board."""

		# If the length of the string is not 9
		if(len(s) != 9):
			# Then print out an error message
			print("Error: there should be 9 symbols.");
			# Throw an error 
			raise Exception;

		# Draw the grid board
		#print("|1|2|3|");
		#print("|4|5|6|");
		#print("|7|8|9|");
		return("|" + s[0] + "|" + s[1]  + "|" + s[2] + "|\n" 
			+ "|" + s[3] + "|" + s[4]  + "|" + s[5] + "|\n" 
			+ "|" + s[6] + "|" + s[7]  + "|" + s[8] + "|\n");

class CanvasWidget:
	"""(Abstract) The base class for all the canvas widgets."""

	__count = 0; # Count the number of widgets initialized

	def __init__(self, canvas):
		"""Initializes the widget."""
		self.canvas = canvas;
		# Generate a unique id for each widget (for tags)
		self.id = str(CanvasWidget.__count);
		CanvasWidget.__count = CanvasWidget.__count + 1;
		# Generate a unique tag for each widget
		self.tag_name = self.__class__.__name__ + self.id;
		# Initialize instance variables
		self.__disabled__ = False;
		# Set default colors
		self.normal_color = C_COLOR_NORMAL; 
		self.hovered_color = C_COLOR_HOVER;

	def set_clickable(self, clickable):
		"""Sets if the widget can be clicked."""
		if(clickable):
			self.canvas.tag_bind(self.tag_name, "<Button-1>", 
				self.__on_click__);
		else:
			self.canvas.tag_unbind(self.tag_name, "<Button-1>");

	def __on_click__(self, event):
		"""(Private) This function will be called when the user clicks on 
		the widget."""
		if(self.__disabled__):
			return False;
		if self.command is not None:
			self.command();
			return True;
		else:
			print("Error: " + self.__class__.__name__ + " " + 
				self.id + " does not have a command");
			raise AttributeError;
		return False;

	def set_hoverable(self, hoverable):
		"""Sets if the widget can be hovered."""
		if(hoverable):
			self.canvas.tag_bind(self.tag_name, "<Enter>", 
				self.__on_enter__);
			self.canvas.tag_bind(self.tag_name, "<Leave>", 
				self.__on_leave__);
		else:
			self.canvas.tag_unbind(self.tag_name, "<Enter>");
			self.canvas.tag_unbind(self.tag_name, "<Leave>");

	def __on_enter__(self, event):
		"""(Private) This function will be called when the mouse enters
		into the widget."""
		if(self.__disabled__):
			return False;
		self.canvas.itemconfig(self.tag_name, fill=self.hovered_color);
		return True;

	def __on_leave__(self, event):
		"""(Private) This function will be called when the mouse leaves
		the widget."""
		if(self.__disabled__):
			return False;
		self.canvas.itemconfig(self.tag_name, fill=self.normal_color);
		return True;

	def disable(self):
		"""Disables the widget so it won't respond to any events."""
		self.__disabled__ = True;

	def enable(self):
		"""Enables the widget so it starts to respond to events."""
		self.__disabled__ = False;

	def is_enabled(self):
		"""Returns True if the widget is disabled."""
		return self.__disabled__;

	def config(self, **kwargs):
		"""Configures the widget's options."""
		return self.canvas.itemconfig(self.tag_name, **kwargs);

	def delete(self):
		self.canvas.delete(self.tag_name);

class CanvasClickableLabel(CanvasWidget):
	"""A clickable label that shows text and can respond to user 
	click events."""

	def __init__(self, canvas, x, y, label_text, normal_color, 
		hovered_color):
		"""Initializes the clickable label object."""

		# Initialize super class
		CanvasWidget.__init__(self, canvas);

		# Set color scheme for different states
		self.normal_color = normal_color;
		self.hovered_color = hovered_color;
		
		# Create the clickable label text
		canvas.create_text(x, y, font="Helvetica 14 underline", 
			text=label_text, fill=self.normal_color, tags=(self.tag_name));
		
		# Bind events
		self.set_hoverable(True);
		self.set_clickable(True);

class CanvasButton(CanvasWidget):
	"""A button that responds to mouse clicks."""

	# Define constant width and height
	WIDTH = 196;
	HEIGHT = 32;

	def __init__(self, canvas, x, y, button_text, normal_color, 
		hovered_color, normal_text_color, hovered_text_color):
		"""Initialize the button object."""

		# Initialize super class
		CanvasWidget.__init__(self, canvas);

		# Set color scheme for different states
		self.normal_color = normal_color;
		self.hovered_color = hovered_color;
		self.normal_text_color = normal_text_color;
		self.hovered_text_color = hovered_text_color;

		# Create the rectangle background
		canvas.create_rectangle(x - self.WIDTH/2 + self.HEIGHT/2, 
			y - self.HEIGHT/2, x + self.WIDTH/2 - self.HEIGHT/2, 
			y + self.HEIGHT/2, fill=self.normal_color, outline="", 
			tags=(self.tag_name, "rect" + self.id));

		# Create the button text
		canvas.create_text(x, y, font="Helvetica 16 bold", 
			text=button_text, fill=self.normal_text_color, 
			tags=(self.tag_name, "text" + self.id));

		# Bind events
		self.set_hoverable(True);
		self.set_clickable(True);

	def __on_enter__(self, event):
		"""(Override) Change the text to a different color when the 
		enter event is triggered."""
		if(super().__on_enter__(event)):
			self.canvas.itemconfig("text" + self.id, 
				fill=self.hovered_text_color);

	def __on_leave__(self, event):
		"""(Override) Change the text to a different color when the 
		leave event is triggered."""
		if(super().__on_leave__(event)):
			self.canvas.itemconfig("text" + self.id, 
				fill=self.normal_text_color);

class CanvasSquare(CanvasWidget):
	"""A square that responds to mouse click event. This is for the grid
	board."""

	def __init__(self, canvas, x, y, width, normal_color, hovered_color, 
		disabled_color):
		"""Initialize the square object."""

		# Initialize super class
		CanvasWidget.__init__(self, canvas);

		# Set color scheme for different states
		self.normal_color = normal_color;
		self.hovered_color = hovered_color;
		self.disabled_color = disabled_color;

		# Create the circle background
		canvas.create_rectangle(x - width/2, y - width/2, x + width/2, 
			y + width/2, fill=self.normal_color, outline="", 
			tags=(self.tag_name, "oval" + self.id));

		# Bind events
		self.set_hoverable(True);
		self.set_clickable(True);

	def disable(self):
		"""(Override) Change the color when the square is disabled."""
		super().disable();
		self.canvas.itemconfig(self.tag_name, fill=self.disabled_color);

	def enable(self):
		"""(Override) Change the color back to normal when the square 
		is disabled."""
		super().enable();
		self.canvas.itemconfig(self.tag_name, fill=self.normal_color);

	def set_temp_color(self, color):
		self.canvas.itemconfig(self.tag_name, fill=color);

class BaseScene(tkinter.Canvas):
	"""(Abstract) The base class for all scenes. BaseScene deals with
	general widgets and handles window resizing event."""

	def __init__(self, parent):
		"""Initializes the scene."""

		# Initialize the superclass Canvas
		tkinter.Canvas.__init__(self, parent, bg=C_COLOR_WHITE, 
			width=C_WINDOW_WIDTH, height=C_WINDOW_HEIGHT);

		# Bind the window-resizing event
		self.bind("<Configure>", self.__on_resize__);

		# Set self.width and self.height for later use
		self.width = C_WINDOW_WIDTH; 
		self.height = C_WINDOW_HEIGHT; 

	def __on_resize__(self, event):
		"""(Private) This function is called when the window is being
		resied."""

		# Determine the ratio of old width/height to new width/height
		self.wscale = float(event.width)/self.width;
		self.hscale = float(event.height)/self.height;
		self.width = event.width;
		self.height = event.height;

		# Resize the canvas 
		self.config(width=self.width, height=self.height);

		# Rescale all the objects tagged with the "all" tag
		self.scale("all", 0, 0, self.wscale, self.hscale);

	def create_button(self, x, y, button_text, 
		normal_color=C_COLOR_WHITE, hovered_color=C_COLOR_HOVER, 
		normal_text_color=C_COLOR_BLACK, 
		hovered_text_color=C_COLOR_WHITE):
		"""Creates a button widget and returns it. Note this will
		return a CanvasButton object, not the ID as other standard 
		Tkinter canvas widgets usually returns."""

		return CanvasButton(self, x, y, button_text, 
			normal_color, hovered_color, 
			normal_text_color, hovered_text_color);

	def create_square(self, x, y, width,
		normal_color=C_COLOR_NORMAL, hovered_color=C_COLOR_HOVER, 
		disabled_color=C_COLOR_NORMAL):
		"""Creates a square widget and returns it. Note this will
		return a CanvasSquare object, not the ID as other standard 
		Tkinter canvas widgets usually returns."""

		return CanvasSquare(self, x, y, width,
			normal_color, hovered_color, disabled_color);

	def create_clickable_label(self, x, y, button_text, 
		normal_color=C_COLOR_BLACK, hovered_color=C_COLOR_WHITE):
		"""Creates a clickable label widget and returns it. Note this
		will return a CanvasClickableLabel object, not the ID as other 
		standard Tkinter canvas widgets usually returns."""

		return CanvasClickableLabel(self, x, y, button_text, 
			normal_color, hovered_color);



class WelcomeScene(BaseScene):
    """WelcomeScene is the first scene to show when the GUI starts."""

    def __init__(self, parent):
        """Initializes the welcome scene."""

        # Initialize BaseScene
        super().__init__(parent);

        # Create a blue arch at the top of the canvas
        self.create_arc((-64, -368, C_WINDOW_WIDTH + 64, 192),
                        start=0, extent=-180, fill=C_COLOR_BLUE, outline="");

        # try:
        # 	# From the logo image file create a PhotoImage object
        # 	self.logo_image = tkinter.PhotoImage(file="res/icon.png");
        # 	# Create the logo image at the center of the canvas
        # 	logo = self.create_image((C_WINDOW_WIDTH / 2,
        # 							  C_WINDOW_HEIGHT / 2 - 96), image=self.logo_image);
        # 	# From the title image file create a PhotoImage object
        # 	self.title_image = tkinter.PhotoImage(file="res/title.png");
        # 	# Create the logo image at the center of the canvas
        # 	title = self.create_image((C_WINDOW_WIDTH / 2,
        # 							   C_WINDOW_HEIGHT / 2 + 48), image=self.title_image);
        # except:
        # 	# An error has been caught when creating the logo image
        # 	tkinter.messagebox.showerror("Error", "Can't create images.\n" +
        # 								 "Please make sure the res folder is in the same directory" +
        # 								 " as this script.");

        # Create the Play button
        play_btn = self.create_button(C_WINDOW_WIDTH / 2,
                                      C_WINDOW_HEIGHT / 2 + 136, "Play");
        play_btn.command = self.__on_play_clicked__;
        # Create the About button
        about_btn = self.create_button(C_WINDOW_WIDTH / 2,
                                       C_WINDOW_HEIGHT / 2 + 192, "About");
        about_btn.command = self.__on_about_clicked__;

        # Tag all of the drawn widgets for later reference
        self.addtag_all("all");

    def __on_play_clicked__(self):
        """(Private) Switches to the main game scene when the play
        button is clicked."""
        self.pack_forget();
        self.main_game_scene.pack();

    def __on_about_clicked__(self):
        """(Private) Switches to the about scene when the about	button
        is clicked."""
        self.pack_forget();
        self.about_scene.pack();


class AboutScene(BaseScene):
    """AboutScene shows the developer and copyright information."""

    def __init__(self, parent):
        """Initializes the about scene object."""

        # Initialize the base scene
        super().__init__(parent);

        # Create a blue arch at the bottom of the canvas
        self.create_arc((-128, C_WINDOW_HEIGHT - 128,
                         C_WINDOW_WIDTH + 128, C_WINDOW_HEIGHT + 368),
                        start=0, extent=180, fill=C_COLOR_BLUE, outline="");

        # try:
        # 	# From the Charmy image file create a PhotoImage object
        # 	self.charmy_image = tkinter.PhotoImage(file="res/charmy.png");
        # 	# Create the logo image on the left of the canvas
        # 	logo = self.create_image((C_WINDOW_WIDTH / 2 - 192,
        # 							  C_WINDOW_HEIGHT / 2 - 48), image=self.charmy_image);
        # 	# From the title image file create a PhotoImage object
        # 	self.title_image = tkinter.PhotoImage(file="res/title.png");
        # 	# Resize the image to make it smaller
        # 	self.title_image = self.title_image.subsample(2, 2);
        # 	# Create the logo image at the center of the canvas
        # 	title = self.create_image((C_WINDOW_WIDTH / 2 + 64,
        # 							   C_WINDOW_HEIGHT / 2 - 160), image=self.title_image);
        # except:
        # 	# An error has been caught when creating the logo image
        # 	tkinter.messagebox.showerror("Error", "Can't create images.\n" +
        # 								 "Please make sure the res folder is in the same directory" +
        # 								 " as this script.");

        self.create_text(C_WINDOW_WIDTH / 2 - 80, C_WINDOW_HEIGHT / 2 - 96,
                         font="Helvetica 14", text="Developed by Augi, Dhamir, Gigas, Tigor",
                         anchor="w", fill=C_COLOR_BLUE_DARK);

        link_charmysoft = self.create_clickable_label(C_WINDOW_WIDTH / 2 - 80,
                                                      C_WINDOW_HEIGHT / 2 - 64, "kepo.com", "#CC2200");
        link_charmysoft.config(anchor="w");
        link_charmysoft.command = self.__on_charmysoft_clicked__;

        self.create_text(C_WINDOW_WIDTH / 2 - 80, C_WINDOW_HEIGHT / 2,
                         anchor="w", font="Helvetica 14", fill=C_COLOR_BLUE_DARK,
                         text="Tic Tac Toe Online in Python is \n" +
                              "Hura hura");

        link_project = self.create_clickable_label(C_WINDOW_WIDTH / 2 - 80,
                                                   C_WINDOW_HEIGHT / 2 + 40, "kepo.com",
                                                   "#0B0080", "#CC2200");
        link_project.config(anchor="w");
        link_project.command = self.__on_project_link_clicked__;

        self.create_text(C_WINDOW_WIDTH / 2 + 64, C_WINDOW_HEIGHT / 2 + 96,
                         font="Helvetica 16", text="Copyright (c) TEL_U YA INI SAYA",
                         fill=C_COLOR_BLUE_DARK);

        # Create the OK button
        ok_btn = self.create_button(C_WINDOW_WIDTH / 2, C_WINDOW_HEIGHT / 2 + 160,
                                    "OK", C_COLOR_BLUE_DARK, C_COLOR_BLUE_LIGHT, C_COLOR_BLUE_LIGHT,
                                    C_COLOR_BLUE_DARK);
        ok_btn.command = self.__on_ok_clicked__;

        # Tag all of the drawn widgets for later reference
        self.addtag_all("all");

    def __on_ok_clicked__(self):
        """(Private) Switches back to the welcome scene when the ok button
        is clicked."""
        self.pack_forget();
        self.welcome_scene.pack();

    def __on_charmysoft_clicked__(self):
        """(Private) Opens CharmySoft.com in the system default browser
        when the CharmySoft.com link is clicked."""
        webbrowser.open("https://igracias.telkomuniversity.ac.id");

    def __on_project_link_clicked__(self):
        """(Private) Opens the project link in the system default browser
        when it is clicked."""
        webbrowser.open("https://igracias.telkomuniversity.ac.id");


class WelcomeScene(BaseScene):
	"""WelcomeScene is the first scene to show when the GUI starts."""

	def __init__(self, parent):
		"""Initializes the welcome scene."""

		# Initialize BaseScene
		super().__init__(parent);

		# Create the Play button
		play_btn = self.create_button(C_WINDOW_WIDTH / 2,
									  C_WINDOW_HEIGHT / 2 - 30  , "Play");
		play_btn.command = self.__on_play_clicked__;
		# Create the About button
		about_btn = self.create_button(C_WINDOW_WIDTH / 2 ,
									   C_WINDOW_HEIGHT / 2 + 30, "About");
		about_btn.command = self.__on_about_clicked__;

		# Tag all of the drawn widgets for later reference
		self.addtag_all("all");

	def __on_play_clicked__(self):
		"""(Private) Switches to the main game scene when the play
		button is clicked."""
		self.pack_forget();
		self.main_game_scene.pack();

	def __on_about_clicked__(self):
		"""(Private) Switches to the about scene when the about	button
		is clicked."""
		self.pack_forget();
		self.about_scene.pack();


class AboutScene(BaseScene):
	"""AboutScene shows the developer and copyright information."""

	def __init__(self, parent):
		"""Initializes the about scene object."""

		# Initialize the base scene
		super().__init__(parent);

		self.create_text(C_WINDOW_WIDTH / 2 - 220, C_WINDOW_HEIGHT / 2 - 90,
						 font="Helvetica 18", text="Developed by Augi, Dhamir, Gigas, Tigor",
						 anchor="w", fill=C_COLOR_BLACK);

		link_c = self.create_clickable_label(C_WINDOW_WIDTH/ 2 - 45,
													  C_WINDOW_HEIGHT / 2 + 25, "gitlab.com", "#CC2200");
		link_c.config(anchor="w");
		link_c.command = self.__on_gitlab_clicked__;

		self.create_text(C_WINDOW_WIDTH / 2, C_WINDOW_HEIGHT / 2 - 30,
						 font="Helvetica 16", text="Copyright (c) TEL_U YA INI SAYA",
						 fill=C_COLOR_BLACK);

		# Create the OK button
		ok_btn = self.create_button(C_WINDOW_WIDTH / 2, C_WINDOW_HEIGHT / 2 + 90,
									"OK", C_COLOR_BLACK, C_COLOR_WHITE, C_COLOR_WHITE, C_COLOR_BLACK);
		ok_btn.command = self.__on_ok_clicked__;

		# Tag all of the drawn widgets for later reference
		self.addtag_all("all");

	def __on_ok_clicked__(self):
		"""(Private) Switches back to the welcome scene when the ok button
		is clicked."""
		self.pack_forget();
		self.welcome_scene.pack();

	def __on_gitlab_clicked__(self):
		"""(Private) Opens CharmySoft.com in the system default browser
		when the CharmySoft.com link is clicked."""
		webbrowser.open("https://gitlab.com/Augipf/tic-tac-toe");
		
class MainGameScene(BaseScene):
	"""MainGameScene deals with the game logic."""

	def __init__(self, parent):
		"""Initializes the main game scene object."""

		# Initialize the base scene
		super().__init__(parent);

		# Initialize instance variables
		self.board_grids_power = 3; # Make it a 3x3 grid board
		self.board_width = 256; # The board is 256x256 wide

		self.draw_board();
		title_text = self.create_text(C_WINDOW_WIDTH/2, 32, font="Helvetica 16", 
			fill=C_COLOR_BLACK, tags=("title_text"), anchor="n");
		# Create the player_self_text
		player_self_text = self.create_text(96, 128, font="Helvetica 16", 
		fill=C_COLOR_X, tags=("player_self_text"), anchor="n");
		# Create the player_match_text
		player_match_text = self.create_text(C_WINDOW_WIDTH - 96, 128, 
		font="Helvetica 16", fill=C_COLOR_O, 
		tags=("player_match_text"), anchor="n");
		player_self_text_alt = self.create_text(96, 128, font="Helvetica 16", 
		fill=C_COLOR_O, tags=("player_self_text_alt"), anchor="n");
		# Create the player_match_text
		player_match_text_alt = self.create_text(C_WINDOW_WIDTH - 96, 128, 
		font="Helvetica 16", fill=C_COLOR_X, 
		tags=("player_match_text_alt"), anchor="n");

		# Create the notif text
		notif_text = self.create_text(8, C_WINDOW_HEIGHT-8, anchor="sw",
			font="Helvetica 16", fill=C_COLOR_BLACK, tags=("notif_text"));

		# Set restart button to None so it won't raise AttributeError
		self.restart_btn = None;

		# Tag all of the drawn widgets for later reference
		self.addtag_all("all");
		self.host = ""
		self.port = ""

	def pack(self):
		"""(Override) When the scene packs, start the client thread."""
		super().pack();
		# Start a new thread to deal with the client communication
		threading.Thread(target=self.__start_client__, args=(0, 0)).start();

	def draw_board(self, board_line_width = 4):
		"""Draws the board at the center of the screen, parameter 
		board_line_width determines the border line width."""

		# Create squares for the grid board
		self.squares = [None] * self.board_grids_power ** 2;
		for i in range(0, self.board_grids_power):
			for j in range(0, self.board_grids_power):
				self.squares[i+j*3] = self.create_square(
					(C_WINDOW_WIDTH - self.board_width)/2 + 
					self.board_width/self.board_grids_power * i + 
					self.board_width / self.board_grids_power / 2,
					(C_WINDOW_HEIGHT - self.board_width)/2 + 
					self.board_width/self.board_grids_power * j + 
					self.board_width / self.board_grids_power / 2,
					self.board_width / self.board_grids_power);
				# Disable those squares to make them unclickable
				self.squares[i+j*3].disable();

		# Draw the border lines
		for i in range(1, self.board_grids_power):
			# Draw horizontal lines
			self.create_line((C_WINDOW_WIDTH - self.board_width)/2, 
				(C_WINDOW_HEIGHT - self.board_width)/2 + 
				self.board_width/self.board_grids_power * i, 
				(C_WINDOW_WIDTH + self.board_width)/2, 
				(C_WINDOW_HEIGHT - self.board_width)/2 + 
				self.board_width/self.board_grids_power * i, 
				fill=C_COLOR_BLACK, width=board_line_width);
			# Draw vertical lines
			self.create_line((C_WINDOW_WIDTH - self.board_width)/2 + 
				self.board_width/self.board_grids_power * i, 
				(C_WINDOW_HEIGHT - self.board_width)/2, 
				(C_WINDOW_WIDTH - self.board_width)/2 + 
				self.board_width/self.board_grids_power * i, 
				(C_WINDOW_HEIGHT + self.board_width)/2, 
				fill=C_COLOR_BLACK, width=board_line_width);

	def __start_client__(self, score, scoreopponent):
		"""(Private) Starts the client side."""
		# Initialize the client object
		self.client = TTTClientGameGUI();
		# Gives the client a reference to self 
		self.client.canvas = self;
		try:
			# Get the host IP address
			if(self.host == "" and self.port == ""):
				self.host = input("Please input address: ")
				self.port = input("Please input port: ")
				self.password = input("Please input match's password (optional): ")
		except:
			# If can't get the host IP from the domain
			tkinter.messagebox.showerror("Error", "Failed to get the game "+ 
				"host address.\n" + 
				"Plase check your connection.");
			return;
		# Set the notif text
		self.set_notif_text("Connecting to the game server " + self.host + "...");
		# Connect to the server
		if(self.client.connect(self.host, self.port)):
			# If connected to the server
			# Start the game
			self.client.start_game(self.password, score, scoreopponent);
			# Close the client
			self.client.close();

	def set_notif_text(self, text):
		"""Sets the notification text."""
		self.itemconfig("notif_text", text=text);

	def update_board_content(self, board_string):
		"""Redraws the board content with new board_string."""
		if(len(board_string) != self.board_grids_power ** 2):
			# If board_string is in valid
			print("The board string should be " + 
				str(self.board_grids_power ** 2) + " characters long.");
			# Throw an error
			raise Exception;

		# Delete everything on the board
		self.delete("board_content");

		p = 16; # Padding

		# Draw the board content
		for i in range(0, self.board_grids_power):
			for j in range(0, self.board_grids_power):

				if(board_string[i+j*3] == "O"):
					# If this is an "O"
					self.create_oval(
						(C_WINDOW_WIDTH - self.board_width)/2 + 
						self.board_width/self.board_grids_power * i + p,
						(C_WINDOW_HEIGHT - self.board_width)/2 + 
						self.board_width/self.board_grids_power * j + p,
						(C_WINDOW_WIDTH - self.board_width)/2 + 
						self.board_width/self.board_grids_power * (i + 1) - p,
						(C_WINDOW_HEIGHT - self.board_width)/2 + 
						self.board_width/self.board_grids_power * (j + 1) - p,
						fill="", outline=C_COLOR_O, width=4,
						tags="board_content");
				elif(board_string[i+j*3] == "X"):
					# If this is an "X"
					self.create_line(
						(C_WINDOW_WIDTH - self.board_width)/2 + 
						self.board_width/self.board_grids_power * i + p,
						(C_WINDOW_HEIGHT - self.board_width)/2 + 
						self.board_width/self.board_grids_power * j + p,
						(C_WINDOW_WIDTH - self.board_width)/2 + 
						self.board_width/self.board_grids_power * (i + 1) - p,
						(C_WINDOW_HEIGHT - self.board_width)/2 + 
						self.board_width/self.board_grids_power * (j + 1) - p,
						fill=C_COLOR_X, width=4,
						tags="board_content");
					self.create_line(
						(C_WINDOW_WIDTH - self.board_width)/2 + 
						self.board_width/self.board_grids_power * (i + 1) - p,
						(C_WINDOW_HEIGHT - self.board_width)/2 + 
						self.board_width/self.board_grids_power * j + p,
						(C_WINDOW_WIDTH - self.board_width)/2 + 
						self.board_width/self.board_grids_power * i + p,
						(C_WINDOW_HEIGHT - self.board_width)/2 + 
						self.board_width/self.board_grids_power * (j + 1) - p,
						fill=C_COLOR_X, width=4,
						tags="board_content");

	def draw_winning_path(self, winning_path):
		"""Marks on the board the path that leads to the win result."""
		# Loop through the board
		for i in range(0, self.board_grids_power ** 2):
			if str(i) in winning_path: 
				# If the current item is in the winning path
				self.squares[i].set_temp_color("#db2631");

	def show_restart(self, score, scoreopponent):
		"""Creates a restart button for the user to choose to restart a 
		new game."""
		self.restart_btn = self.create_button(C_WINDOW_WIDTH/2, C_WINDOW_HEIGHT - 32, 
			"Restart", C_COLOR_BLACK, C_COLOR_WHITE, C_COLOR_WHITE, 
			C_COLOR_BLACK);
		self.restart_btn.command = (lambda self=self, score=score, scoreopponent=scoreopponent: 
					self.__on_restart_clicked__(score, scoreopponent));

		# Create the return button
		return_btn = self.create_button(C_WINDOW_WIDTH - 128, 32, "Go back");
		return_btn.command = self.__on_return_clicked__;

	def __clear_screen(self):
		"""(Private) Clears all the existing content from the old game."""
		# Clear everything from the past game
		for i in range(0, self.board_grids_power ** 2):
			self.squares[i].disable();
			self.squares[i].set_temp_color(C_COLOR_NORMAL);
		self.update_board_content(" " * self.board_grids_power ** 2);
		self.itemconfig("player_self_text", text="");
		self.itemconfig("player_match_text", text="");
		self.itemconfig("player_self_text_alt", text="");
		self.itemconfig("player_match_text_alt", text="");
		# Delete the button from the scene
		if self.restart_btn is not None:
			self.restart_btn.delete();
			self.restart_btn = None;

	def __on_restart_clicked__(self, score, scoreopponent):
		"""(Private) Switches back to the welcome scene when the return 
		button is clicked."""
		# Clear screen
		self.__clear_screen();
		# Start a new thread to deal with the client communication
		threading.Thread(target=self.__start_client__, kwargs={'score':score, 'scoreopponent':scoreopponent}).start();
		upload_file();

		def __on_return_clicked__(self):
			"""(Private) Switches back to the welcome scene when the return
            button is clicked."""
			# Clear screen
			self.__clear_screen();
			# Set the client to None so the client thread will stop due to error
			self.client.client_socket = None;
			self.client = None;
			# Switch to the welcome scene
			self.pack_forget();
			self.welcome_scene.pack();


class TTTClientGameGUI(TTTClientGame):
	"""The client implemented with GUI."""

	def __connect_failed__(self):
		"""(Override) Updates the GUI to notify the user that the connection
		couldn't be established."""
		# Write the notif text
		self.canvas.set_notif_text("Can't connect to the game server.\n" + 
			"It might be down or blocked by your firewall.");
		# Throw an error and finish the client thread
		raise Exception;

	def __connected__(self):
		"""(Override) Updates the GUI to notify the user that the connection
		has been established."""
		self.canvas.set_notif_text("Server connected. \n" +
			"Waiting for other players to join...");

	def __game_started__(self):
		"""(Override) Updates the GUI to notify the user that the game is
		getting started."""
		self.canvas.itemconfig("title_text", 
			text="TIC TAC TOE");
		self.canvas.set_notif_text("Game started. " + 
			"You are the \"" + self.role + "\"");
		if self.role == "X":
			self.canvas.itemconfig("player_self_text", 
			text="You:"+ 
			"\n\nRole: " + self.role +
			"\n\nScore: " + str(self.score));
			self.canvas.itemconfig("player_match_text", 
			text="Opponent:"+ 
			"\n\nRole: " + ("O" if self.role == "X" else "X") +
			"\n\nScore: " + str(self.scoreopponent));
		else:
			self.canvas.itemconfig("player_self_text_alt", 
			text="You:"+ 
			"\n\nRole: " + self.role +
			"\n\nScore: " + str(self.score));
			self.canvas.itemconfig("player_match_text_alt", 
			text="Opponent:"+ 
			"\n\nRole: " + ("O" if self.role == "X" else "X") +
			"\n\nScore: " + str(self.scoreopponent));

	def __update_board__(self, command, board_string):
		"""(Override) Updates the board."""
		# Print the command-line board for debugging purpose
		super().__update_board__(command, board_string);
		# Draw the GUI board
		self.canvas.update_board_content(board_string);
		if(command == "D"):
			# If the result is a draw
			self.canvas.set_notif_text("It's a draw.");
			# Show the restart button
			self.canvas.show_restart(self.score, self.scoreopponent);
		elif(command == "W"):
			# If this player wins
			self.canvas.set_notif_text("You WIN!");
			# Show the restart button
			self.score += 1
			self.canvas.show_restart(self.score, self.scoreopponent);
		elif(command == "L"):
			# If this player loses
			self.canvas.set_notif_text("You lose.");
			# Show the restart button
			self.scoreopponent += 1
			self.canvas.show_restart(self.score, self.scoreopponent);

	def __player_move__(self, board_string):
		"""(Override) Lets the user to make a move and sends it back to the
		server."""

		# Set user making move to be true
		self.making_move = True;

		for i in range(0, self.canvas.board_grids_power ** 2):
			# Check the board content and see if it's empty
			if(board_string[i] == " "):
				# Enable those squares to make them clickable
				self.canvas.squares[i].enable();
				# Bind their commands
				self.canvas.squares[i].command = (lambda self=self, i=i: 
					self.__move_made__(i));

		while self.making_move:
			# Wait until the user has clicked on something
			pass;

	def __player_wait__(self):
		"""(Override) Lets the user know it's waiting for the other player 
		to make a move."""
		# Print the command-line notif for debugging purpose
		super().__player_wait__();
		# Set the notif text on the GUI
		self.canvas.set_notif_text("Waiting for the other player to make a move...");

	def __opponent_move_made__(self, move):
		"""(Override) Shows the user the move that the other player has taken."""
		# Print the command-line notif for debugging purpose
		super().__opponent_move_made__(move);
		# Set the notif text on the GUI
		self.canvas.set_notif_text("Your opponent took up number " + str(move) + ".\n"
			"It's now your turn, please make a move.");

	def __move_made__(self, index):
		"""(Private) This function is called when the user clicks on the 
		board to make a move."""

		print("User chose " + str(index + 1));

		for i in range(0, self.canvas.board_grids_power ** 2):
			# Disable those squares to make them unclickable
			self.canvas.squares[i].disable();
			# Remove their commands
			self.canvas.squares[i].command = None;

		# Send the position back to the server
		self.s_send("i", str(index + 1));

		# Set user making move to be false
		self.making_move = False;

	def __draw_winning_path__(self, winning_path):
		"""(Override) Shows to the user the path that has caused the game to 
		win or lose."""
		# Print the command-line winning path for debugging purpose
		super().__draw_winning_path__(winning_path);
		# Draw GUI the winning path
		self.canvas.draw_winning_path(winning_path);
		
# Define the main program
def main():
	# Create a Tkinter object
	root = tkinter.Tk();
	# Set window title
	root.title("Tic Tac Toe");
	# Set window minimun size
	root.minsize(C_WINDOW_MIN_WIDTH, C_WINDOW_MIN_HEIGHT);
	# Set window size
	root.geometry(str(C_WINDOW_WIDTH) + "x" + str(C_WINDOW_HEIGHT));
	try:
		# Set window icon
		root.iconbitmap("res/icon.ico");
	except:
		# An error has been caught when setting the icon
		# tkinter.messagebox.showerror("Error", "Can't set the window icon.");
		print("Can't set the window icon.");

	# Initialize the welcome scene
	welcome_scene = WelcomeScene(root);
	# Initialize the about scene
	about_scene = AboutScene(root);

	upload_file()

	# Initialize the welcome scene
	welcome_scene = WelcomeScene(root);
	# Initialize the about scene
	about_scene = AboutScene(root);
	# Initialize the main game scene
	main_game_scene = MainGameScene(root);

	welcome_scene.about_scene = about_scene;
	welcome_scene.main_game_scene = main_game_scene;
	about_scene.welcome_scene = welcome_scene;
	main_game_scene.welcome_scene = welcome_scene;

	# Start showing the welcome scene
	welcome_scene.pack();
	    
	# Main loop
	root.mainloop();

def upload_file():
    # import library socket karena menggunakan IPC socket
    import socket

    # definisikan IP server tujuan file akan diupload
    ip = '127.0.0.1'

    # definisikan port number proses di server
    port = 8080

    # definisikan ukuran buffer untuk mengirim
    buffer_size = 2000

    # buat socket (apakah bertipe UDP atau TCP?)
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # lakukan koneksi ke server
    c.connect((ip, port))

    # buka file bernama "file_diupload.txt bertipe byte
    # masih hard code, file harus ada dalam folder yang sama dengan script python
    file = open("client.txt", errors='ignore')

    try:
        # baca file tersebut sebesar buffer
        byte = file.read(2000).encode()

        # selama tidak END OF FILE; pada pyhton EOF adalah b''
        while byte != b'':
            # kirim hasil pembacaan file
            c.send(byte)

            # baca sisa file hingga EOF
            byte = file.read(2000).encode()

            # print(byte)
            print(byte)
    finally:
        print("end sending")

        # tutup file jika semua file telah  dibaca
        file.close()

    # tutup koneksi setelah file terkirim
    c.close()

if __name__ == "__main__":
	# If this script is running as a standalone program,
	# start the main program.
	main();