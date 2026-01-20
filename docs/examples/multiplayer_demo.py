from lunaengine.core import LunaEngine, Scene
from lunaengine.backend.network import NetworkClient, NetworkHost, NetworkServer
from lunaengine.backend.network import MessageType, NetworkMessage, UserType
from lunaengine.ui import *
import pygame as pg
import time
import random

class NetworkInfo:
    def __init__(self):
        self.host = None
        self.server = None
        self.client = None
        self.is_connected = False
        self.is_host = False
        self.messages = []
        self.player_id = None

class MainScene(Scene):
    def on_enter(self, previous_scene = None):
        print("=== Multiplayer Demo ===")
        print("1. For host: Check 'Is Host', click 'Start Host'")
        print("2. For client: Uncheck 'Is Host', enter host IP, click 'Connect'")
        print("3. Click 'Play' to enter game")
        return super().on_enter(previous_scene)
    
    def on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.network_info = None
        self.connection_status = "Not connected"
        self.setup_ui()
        
    def setup_ui(self):
        screen_width, screen_height = self.engine.width, self.engine.height
        
        # Title
        self.add_ui_element(TextLabel(512, 30, "LunaEngine - Multiplayer Demo", 36, (255, 255, 255), root_point=(0.5, 0)))
        
        # Connection Frame
        self.frame = UiFrame(40, 150, 600, 400, root_point=(0, 0))
        self.frame.set_background_color((60, 60, 80))
        self.add_ui_element(self.frame)
        
        # Network Settings
        self.frame.add_child(TextLabel(50, 30, "Network Settings", 28, (255, 255, 200), root_point=(0, 0)))
        
        # Host/IP Input
        self.frame.add_child(TextLabel(50, 80, "Host / IP:", 20, (200, 230, 255), root_point=(0, 0)))
        self.host_input = TextBox(150, 75, 200, 35, '127.0.0.1', 18, root_point=(0, 0))
        self.host_input.set_text("127.0.0.1")
        self.frame.add_child(self.host_input)
        
        # Port Input
        self.frame.add_child(TextLabel(50, 130, "Port:", 20, (200, 230, 255), root_point=(0, 0)))
        self.port_input = NumberSelector(150, 125, 120, 35, 1024, 65535, 4723, 4, 4, root_point=(0, 0))
        self.frame.add_child(self.port_input)
        
        # Is Host Checkbox
        self.is_host_check = Checkbox(50, 180, 30, 30, False, "Run as Host (Server + Client)")
        self.frame.add_child(self.is_host_check)
        
        # Connection Status
        self.status_label = TextLabel(300, 225, "Status: Not connected", 20, (255, 100, 100), root_point=(0, 0))
        self.frame.add_child(self.status_label)
        
        # Action Buttons Frame
        button_frame = UiFrame(screen_width-40, 150, 240, 355, root_point=(1, 0))
        button_frame.set_background_color((80, 80, 100))
        self.add_ui_element(button_frame)
        
        # Start Host Button
        self.start_host_btn = Button(120, 20, 200, 30, "Start Host", 24, root_point=(0.5, 0))
        self.start_host_btn.set_on_click(self.start_host)
        button_frame.add_child(self.start_host_btn)
        
        # Connect Button
        self.connect_btn = Button(120, 65, 200, 30, "Connect", 24, root_point=(0.5, 0))
        self.connect_btn.set_on_click(self.connect_as_client)
        button_frame.add_child(self.connect_btn)
        
        self.play_btn = Button(120, 110, 200, 40, "Play", 32, root_point=(0.5, 0))
        self.play_btn.set_on_click(self.go_to_game)
        self.play_btn.set_enabled(False)
        button_frame.add_child(self.play_btn)
        
        # Exit Button
        self.exit_btn = Button(120, 160, 200, 35, "Exit", 24, root_point=(0.5, 0))
        self.exit_btn.set_on_click(lambda: setattr(self.engine, 'running', False))
        button_frame.add_child(self.exit_btn)
        
        # Instructions
        instructions = [
            "INSTRUCTIONS:",
            "1. To host: Check 'Run as Host', click 'Start Host'",
            "2. To join: Enter host IP, click 'Connect'",
            "3. When connected, click 'Play' to start game",
            "",
            "Default host IP: 127.0.0.1 (localhost)",
            "Default port: 4723"
        ]
        
        for i, text in enumerate(instructions):
            color = (255, 255, 200) if i == 0 else (180, 230, 255)
            self.add_ui_element(TextLabel(20, 600 + i * 25, text, 16, color, root_point=(0, 0)))
    
    def start_host(self):
        """Start as host (server + client)"""
        host = self.host_input.get_text()
        port = self.port_input.get_value()
        
        print(f"Starting host on {host}:{port}...")
        self.status_label.set_text("Starting host...")
        self.status_label.color = (255, 200, 100)
        
        # Create network info
        self.network_info = NetworkInfo()
        self.network_info.is_host = True
        
        try:
            # Start host
            self.network_info.host = NetworkHost(host=host, port=port)
            if self.network_info.host.start():
                self.network_info.is_connected = True
                self.network_info.player_id = self.network_info.host.client.client_id
                
                print(f"Host started successfully! Player ID: {self.network_info.player_id}")
                self.status_label.set_text(f"Host running on {host}:{port}")
                self.status_label.color = (100, 255, 100)
                
                # Setup message handler for host
                def handle_host_message(msg):
                    if msg and len(msg) > 0:
                        source = msg[0]
                        if source == "client":
                            # Message from server to our client component
                            message = msg[1]
                            if message.message_type == MessageType.DATA:
                                print(f"Host client received: {message.payload}")
                                # Forward to game scene if it exists
                                if hasattr(self, 'network_info'):
                                    self.network_info.messages.append(message)
                        elif source == "server":
                            # Message from a client to our server component
                            client_id, message = msg[1], msg[2]
                            if message.message_type == MessageType.DATA:
                                print(f"Host server received from {client_id}: {message.payload}")
                                # Broadcast to all other clients (including ourselves)
                                if self.network_info.host:
                                    # Create broadcast message
                                    broadcast_data = {
                                        "message_id": message.message_id,
                                        "message_type": MessageType.DATA.value,
                                        "sender_id": client_id,
                                        "sender_type": message.sender_type.value,
                                        "timestamp": message.timestamp,
                                        "payload": message.payload
                                    }
                                    # Broadcast to all except sender
                                    self.network_info.host.server.broadcast(broadcast_data, exclude=[client_id])
                                    # Also store for our own client
                                    if hasattr(self, 'network_info'):
                                        self.network_info.messages.append(message)
                
                # Store in engine for other scenes to access
                self.engine.network_info = self.network_info
                
                # Enable play button
                self.play_btn.set_enabled(True)
                self.start_host_btn.set_enabled(False)
                self.connect_btn.set_enabled(False)
                
                print("Host setup complete")
            else:
                self.status_label.set_text("Failed to start host")
                self.status_label.color = (255, 100, 100)
                self.network_info = None
                
        except Exception as e:
            print(f"Error starting host: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.set_text(f"Error: {str(e)}")
            self.status_label.color = (255, 100, 100)
            self.network_info = None
    
    def connect_as_client(self):
        """Connect to server as client"""
        host = self.host_input.get_text()
        port = self.port_input.get_value()
        
        print(f"Connecting to {host}:{port}...")
        self.status_label.set_text(f"Connecting to {host}:{port}...")
        self.status_label.color = (255, 200, 100)
        
        # Create network info
        self.network_info = NetworkInfo()
        self.network_info.is_host = False
        
        try:
            # Connect as client
            self.network_info.client = NetworkClient()
            if self.network_info.client.connect(host, port, timeout=5):
                self.network_info.is_connected = True
                self.network_info.player_id = self.network_info.client.client_id
                
                print(f"Connected to server! Player ID: {self.network_info.player_id}")
                self.status_label.set_text(f"Connected to {host}:{port}")
                self.status_label.color = (100, 255, 100)
                
                # Setup message handler for client
                def handle_client_message(msg: NetworkMessage):
                    print(f"Client received: {msg.message_type} - {msg.payload}")
                    self.handle_network_message(msg)
                
                # Register callback for data messages
                self.network_info.client.register_callback(MessageType.DATA, handle_client_message)
                
                # Store in engine
                self.engine.network_info = self.network_info
                
                # Enable play button
                self.play_btn.set_enabled(True)
                self.start_host_btn.set_enabled(False)
                self.connect_btn.set_enabled(False)
                
                print("Client setup complete")
            else:
                self.status_label.set_text("Connection failed")
                self.status_label.color = (255, 100, 100)
                self.network_info = None
                
        except Exception as e:
            print(f"Connection error: {e}")
            self.status_label.set_text(f"Error: {str(e)}")
            self.status_label.color = (255, 100, 100)
            self.network_info = None
    
    def handle_network_message(self, message, sender_id=None):
        """Handle incoming network messages"""
        if isinstance(message, NetworkMessage):
            print(f"Received: {message.message_type} from {sender_id or message.sender_id}")
            if hasattr(self, 'network_info'):
                self.network_info.messages.append(message)
    
    def go_to_game(self):
        """Go to the game scene"""
        if self.network_info and self.network_info.is_connected:
            print("Going to game scene...")
            self.engine.set_scene("InGame")
        else:
            self.status_label.set_text("Not connected!")
            self.status_label.color = (255, 100, 100)
    
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
    
    def update(self, dt):
        # Update connection status display
        if self.network_info and self.network_info.is_connected:
            if self.network_info.is_host:
                if self.network_info.host:
                    player_count = self.network_info.host.get_client_count()
                    self.status_label.set_text(f"Host: {player_count} clients connected")
                else:
                    self.status_label.set_text("Host running")
            else:
                if self.network_info.client and self.network_info.client.connected:
                    self.status_label.set_text("Connected to server")
                else:
                    self.status_label.set_text("Disconnected")
        
        return super().update(dt)

class Player:
    def __init__(self, x, y, player_id, name="Player", color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.id = player_id
        self.name = name
        self.width = 40
        self.height = 40
        self.color = color
        self.velocity = [0, 0]
        self.speed = 250
        self.last_update = 0

class InGameScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.players = {}  # player_id: Player
        self.local_player = None
        self.chat_messages = []  # Store chat messages
        self.setup_ui()
        self.network_update_timer = 0
        self.network_update_interval = 0.05  # 20 updates per second
        self.last_player_update = 0
        
    def on_enter(self, previous_scene=None):
        print("Entering game scene...")
        
        # Get network info from engine
        if hasattr(self.engine, 'network_info'):
            self.network_info = self.engine.network_info
            
            if self.network_info and self.network_info.is_connected:
                # Create local player
                player_name = f"Player_{self.network_info.player_id[:4]}"
                player_color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                )
                
                self.local_player = Player(
                    x=512, y=360,
                    player_id=self.network_info.player_id,
                    name=player_name,
                    color=player_color
                )
                self.players[self.network_info.player_id] = self.local_player
                
                # Send player join message
                self.send_player_join()
                print(f"Local player created: {player_name}")
                
                # If host, send existing players to new clients
                if self.network_info.is_host and self.network_info.host:
                    print("Host: Will broadcast player list to new clients")
            else:
                print("Not connected to network!")
                self.engine.set_scene("main")
        else:
            print("No network info found!")
            self.engine.set_scene("main")
    
    def on_exit(self, next_scene=None):
        # Send player leave message
        if hasattr(self, 'local_player') and self.local_player:
            self.send_player_leave()
        
        # Clear players
        self.players.clear()
        return super().on_exit(next_scene)
    
    def setup_ui(self):
        # Game UI (hidden by default)
        self.ui_frame = UiFrame(512, 300, 400, 375,root_point=(0.5, 0))
        self.ui_frame.set_background_color((60, 60, 80, 200))
        self.ui_frame.add_group('game_ui')
        self.add_ui_element(self.ui_frame)
        
        # UI Title
        self.ui_frame.add_child(TextLabel(200, 20, "Multiplayer Game", 28, (255, 255, 200), root_point=(0.5, 0)))
        
        # Player List
        self.player_list_label = TextLabel(20, 60, "Players:", 22, (200, 230, 255))
        self.ui_frame.add_child(self.player_list_label)
        
        # Chat Display Label
        self.chat_display_label = TextLabel(20, 120, "Chat:", 22, (200, 230, 255))
        self.ui_frame.add_child(self.chat_display_label)
        
        # Chat Scrolling Frame - FIXED: Proper ScrollingFrame setup
        self.chat_scrolling = ScrollingFrame(200, 150, 340, 100, 340, 200, root_point=(0.5, 0))
        self.chat_scrolling.set_background_color((40, 40, 50, 200))
        self.ui_frame.add_child(self.chat_scrolling)
        
        # Chat Input
        self.chat_input = TextBox(20, 280, 250, 35, "Type message...", 16)
        self.ui_frame.add_child(self.chat_input)
        
        # Send Chat Button
        self.send_chat_btn = Button(280, 280, 80, 35, "Send", 16)
        self.send_chat_btn.set_on_click(self.send_chat)
        self.ui_frame.add_child(self.send_chat_btn)
        
        # Disconnect Button
        self.disconnect_btn = Button(200, 320, 120, 40, "Disconnect", 20, root_point=(0.5, 0))
        self.disconnect_btn.set_on_click(self.disconnect)
        self.ui_frame.add_child(self.disconnect_btn)
        
        # Hide UI by default
        self.ui_visible = False
        self.toggle_element_group('game_ui', self.ui_visible)
        
        # Add ESC key handler to toggle UI
        @self.engine.on_event(pg.KEYDOWN)
        def on_keydown(event):
            if event.key == pg.K_ESCAPE:
                self.ui_visible = not self.ui_visible
                self.toggle_element_group('game_ui', self.ui_visible)
            elif event.key == pg.K_RETURN and self.chat_input.has_focus():
                self.send_chat()
    
    def send_player_join(self):
        """Send player join message"""
        if not self.local_player or not hasattr(self, 'network_info'):
            return
        
        join_data = {
            'type': 'player_join',
            'player_id': self.local_player.id,
            'name': self.local_player.name,
            'position': [self.local_player.x, self.local_player.y],
            'color': self.local_player.color
        }
        
        self.send_network_message(join_data)
        print(f"Sent player join: {self.local_player.name}")
    
    def send_player_leave(self):
        """Send player leave message"""
        if not self.local_player or not hasattr(self, 'network_info'):
            return
        
        leave_data = {
            'type': 'player_leave',
            'player_id': self.local_player.id
        }
        
        self.send_network_message(leave_data)
        print(f"Sent player leave: {self.local_player.name}")
    
    def send_player_update(self):
        """Send player position update"""
        if not self.local_player or not hasattr(self, 'network_info'):
            return
        
        # Only send update if position changed significantly
        current_time = time.time()
        if current_time - self.last_player_update < 0.1:  # Limit to 10 updates per second
            return
        
        update_data = {
            'type': 'player_update',
            'player_id': self.local_player.id,
            'position': [self.local_player.x, self.local_player.y],
            'velocity': self.local_player.velocity
        }
        
        self.send_network_message(update_data)
        self.last_player_update = current_time
    
    def send_chat(self):
        """Send chat message"""
        message = self.chat_input.get_text().strip()
        if not message or not hasattr(self, 'network_info'):
            return
        
        chat_data = {
            'type': 'chat',
            'player_id': self.local_player.id,
            'player_name': self.local_player.name,
            'message': message,
            'timestamp': time.time()
        }
        
        self.send_network_message(chat_data)
        
        # Add to local chat immediately
        self.add_chat_message(self.local_player.name, message)
        
        # Clear input
        self.chat_input.set_text("")
    
    def send_network_message(self, data):
        """Send network message based on connection type"""
        if not hasattr(self, 'network_info') or not self.network_info.is_connected:
            return False
        
        try:
            if self.network_info.is_host:
                # As host, send through our client component
                if self.network_info.host and self.network_info.host.client:
                    return self.network_info.host.send_as_host(MessageType.DATA, data)
            else:
                # As client, send directly
                if self.network_info.client and self.network_info.client.connected:
                    return self.network_info.client.send(MessageType.DATA, data)
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
        
        return False
    
    def process_network_messages(self):
        """Process incoming network messages"""
        if not hasattr(self, 'network_info') or not self.network_info.is_connected:
            return
        
        try:
            if self.network_info.is_host:
                # Process host messages
                if self.network_info.host:
                    msg = self.network_info.host.get_message(timeout=0)
                    while msg:
                        source = msg[0]
                        if source == "client":
                            # Message from server to our client
                            message = msg[1]
                            self.handle_network_message(message)
                        elif source == "server":
                            # Message from a client to our server
                            client_id, message = msg[1], msg[2]
                            print(f"Host server received from {client_id}: {message.payload}")
                            
                            # Handle the message locally
                            self.handle_network_message(message, client_id)
                            
                            # If it's a player join/update/chat, broadcast to all except sender
                            if message.message_type == MessageType.DATA:
                                data = message.payload
                                if isinstance(data, dict) and data.get('type') in ['player_join', 'player_update', 'chat']:
                                    # Don't broadcast our own messages back to ourselves
                                    if client_id != self.network_info.player_id:
                                        # Broadcast to all other clients
                                        broadcast_msg = {
                                            "message_id": message.message_id,
                                            "message_type": MessageType.DATA.value,
                                            "sender_id": client_id,
                                            "sender_type": message.sender_type.value,
                                            "timestamp": message.timestamp,
                                            "payload": data
                                        }
                                        self.network_info.host.server.broadcast(broadcast_msg, exclude=[client_id])
                        
                        msg = self.network_info.host.get_message(timeout=0)
            else:
                # Process client messages
                if self.network_info.client:
                    msg = self.network_info.client.get_message(timeout=0)
                    while msg:
                        self.handle_network_message(msg)
                        msg = self.network_info.client.get_message(timeout=0)
        except Exception as e:
            print(f"Error processing messages: {e}")
    
    def handle_network_message(self, message, sender_id=None):
        """Handle a network message"""
        if not isinstance(message, NetworkMessage) or message.message_type != MessageType.DATA:
            return
        
        data = message.payload
        if not isinstance(data, dict):
            return
        
        msg_type = data.get('type')
        player_id = data.get('player_id')
        
        # Handle different message types
        if msg_type == 'player_join':
            # New player joined
            if player_id and player_id != self.local_player.id:
                player_name = data.get('name', f'Player_{player_id[:4]}')
                position = data.get('position', [512, 360])
                color = data.get('color', (255, 255, 255))
                
                if player_id not in self.players:
                    self.players[player_id] = Player(
                        x=position[0], y=position[1],
                        player_id=player_id,
                        name=player_name,
                        color=color
                    )
                    
                    self.add_chat_message("System", f"{player_name} joined the game")
                    print(f"Player joined: {player_name}")
        
        elif msg_type == 'player_leave':
            # Player left
            if player_id in self.players:
                player_name = self.players[player_id].name
                del self.players[player_id]
                self.add_chat_message("System", f"{player_name} left the game")
                print(f"Player left: {player_name}")
        
        elif msg_type == 'player_update':
            # Player position update
            if player_id in self.players and player_id != self.local_player.id:
                position = data.get('position')
                if position:
                    self.players[player_id].x = position[0]
                    self.players[player_id].y = position[1]
                    # Update velocity if provided
                    velocity = data.get('velocity')
                    if velocity:
                        self.players[player_id].velocity = velocity
        
        elif msg_type == 'chat':
            # Chat message
            player_name = data.get('player_name', f'Player_{player_id[:4]}')
            message_text = data.get('message', '')
            self.add_chat_message(player_name, message_text)
            print(f"Chat from {player_name}: {message_text}")
    
    def add_chat_message(self, sender, message):
        """Add chat message to ScrollingFrame"""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {sender}: {message}"
        
        # Add to our list
        self.chat_messages.append(full_message)
        
        # Keep only last 10 messages
        if len(self.chat_messages) > 10:
            self.chat_messages.pop(0)
        
        # Update the ScrollingFrame
        self.update_chat_scrolling()
    
    def update_chat_scrolling(self):
        """Update the chat ScrollingFrame with current messages"""
        # Clear existing chat labels
        self.chat_scrolling.clear_children()
        
        # Add each message as a TextLabel
        for i, msg in enumerate(self.chat_messages):
            # Calculate position (starting from bottom)
            y_pos = 5 + (len(self.chat_messages) - i - 1) * 25
            
            # Create text label
            chat_label = TextLabel(5, y_pos, msg, 16, (230, 230, 255))
            self.chat_scrolling.add_child(chat_label)
    
    def update_player_movement(self, dt):
        """Update local player movement"""
        if not self.local_player:
            return
        
        keys = pg.key.get_pressed()
        old_velocity = self.local_player.velocity.copy()
        self.local_player.velocity = [0, 0]
        
        if keys[pg.K_w] or keys[pg.K_UP]:
            self.local_player.velocity[1] = -1
        if keys[pg.K_s] or keys[pg.K_DOWN]:
            self.local_player.velocity[1] = 1
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            self.local_player.velocity[0] = -1
        if keys[pg.K_d] or keys[pg.K_RIGHT]:
            self.local_player.velocity[0] = 1
        
        # Normalize diagonal movement
        if self.local_player.velocity[0] != 0 and self.local_player.velocity[1] != 0:
            self.local_player.velocity[0] *= 0.7071
            self.local_player.velocity[1] *= 0.7071
        
        # Only send update if velocity changed significantly
        velocity_changed = (
            abs(old_velocity[0] - self.local_player.velocity[0]) > 0.1 or
            abs(old_velocity[1] - self.local_player.velocity[1]) > 0.1
        )
        
        # Update position
        self.local_player.x += self.local_player.velocity[0] * self.local_player.speed * dt
        self.local_player.y += self.local_player.velocity[1] * self.local_player.speed * dt
        
        # Keep player in bounds
        self.local_player.x = max(20, min(1004, self.local_player.x))
        self.local_player.y = max(20, min(700, self.local_player.y))
        
        # Send update if moving or velocity changed
        if velocity_changed or self.local_player.velocity != [0, 0]:
            self.send_player_update()
    
    def update_player_list(self):
        """Update player list UI"""
        player_text = f"Players ({len(self.players)}):\n"
        for player_id, player in self.players.items():
            is_local = "★ " if player_id == self.local_player.id else "  "
            player_text += f"{is_local}{player.name}\n"
        
        self.player_list_label.set_text(player_text)
    
    def disconnect(self):
        """Disconnect from network and return to main menu"""
        print("Disconnecting...")
        
        # Clean up network connections
        if hasattr(self, 'network_info'):
            if self.network_info.is_host and self.network_info.host:
                self.network_info.host.stop()
            elif self.network_info.client:
                self.network_info.client.disconnect()
        
        # Clear engine network info
        if hasattr(self.engine, 'network_info'):
            self.engine.network_info = None
        
        # Go back to main menu
        self.engine.set_scene("main")
    
    def update(self, dt):
        # Process network messages
        self.process_network_messages()
        
        # Update player movement
        self.update_player_movement(dt)
        
        # Update UI
        self.update_player_list()
        
        return super().update(dt)
    
    def render(self, renderer):
        # Draw background
        renderer.fill_screen((30, 30, 40))
        
        # Draw grid
        grid_color = (50, 50, 60)
        for x in range(0, 1024, 50):
            renderer.draw_line(x, 0, x, 720, grid_color, 1)
        for y in range(0, 720, 50):
            renderer.draw_line(0, y, 1024, y, grid_color, 1)
        
        # Draw center point
        renderer.draw_circle(512, 360, 5, (100, 100, 150))
        
        # Draw all players
        for player_id, player in self.players.items():
            # Draw player body
            renderer.draw_rect(
                player.x - player.width/2,
                player.y - player.height/2,
                player.width,
                player.height,
                player.color
            )
            
            # Draw player name
            renderer.draw_text(str(player.name), player.x, player.y - 30,(255, 255, 255) if player_id != self.local_player.id else (255, 255, 0), FontManager.get_font(None, 16), anchor_point=(0.5, 0.5))
            
            # Draw local player indicator
            if player_id == self.local_player.id:
                renderer.draw_circle(player.x, player.y - 40, 5, (255, 255, 0))
                
                # Draw velocity indicator
                if player.velocity != [0, 0]:
                    end_x = player.x + player.velocity[0] * 30
                    end_y = player.y + player.velocity[1] * 30
                    renderer.draw_line(player.x, player.y, end_x, end_y, (255, 255, 0, 150), 2)
        
        # Draw instructions
        if not self.ui_visible:
            font = pg.font.SysFont("Arial", 18)
            instructions = [
                "WASD or Arrow Keys - Move",
                "ESC - Toggle UI",
                "ENTER - Send chat message",
                "Click Disconnect to leave"
            ]
            
            for i, text in enumerate(instructions):
                text_surface = font.render(text, True, (200, 230, 255))
                renderer.blit(text_surface, (20, 20 + i * 30))
            
            # Draw connection info
            if hasattr(self, 'network_info') and self.network_info:
                mode = "Host" if self.network_info.is_host else "Client"
                info = f"Connected as {mode} | Players: {len(self.players)}"
                info_surface = font.render(info, True, (100, 255, 100))
                renderer.blit(info_surface, (20, 680))
        
        # Draw network status
        font = pg.font.SysFont("Arial", 14)
        if hasattr(self, 'network_info') and self.network_info:
            if self.network_info.is_host:
                if self.network_info.host:
                    client_count = self.network_info.host.get_client_count()
                    status_text = f"Hosting | Clients: {client_count}"
                else:
                    status_text = "Host (disconnected)"
            else:
                if self.network_info.client and self.network_info.client.connected:
                    status_text = "Connected to server"
                else:
                    status_text = "Disconnected"
        else:
            status_text = "No connection"
        
        status_surface = font.render(status_text, True, (200, 200, 200))
        renderer.blit(status_surface, (1024 - status_surface.get_width() - 20, 680))

def main():
    engine = LunaEngine('LunaEngine - Multiplayer Demo', 1024, 720, False)
    
    engine.add_scene('main', MainScene)
    engine.add_scene('InGame', InGameScene)
    engine.set_scene('main')
    
    print("=== LunaEngine Multiplayer Demo ===")
    print("Instructions:")
    print("1. For HOST: Check 'Run as Host', click 'Start Host'")
    print("2. For CLIENT: Enter host IP (127.0.0.1 for local), click 'Connect'")
    print("3. Click 'Play' to enter game")
    print("4. In game: WASD to move, ESC to toggle UI, ENTER to chat")
    
    engine.run()

if __name__ == "__main__":
    main()