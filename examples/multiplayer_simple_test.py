import sys
import os
import pygame
import time
import random
import threading
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui.elements import *
from lunaengine.backend.network import *
from lunaengine.backend import OpenGLRenderer


class PlayerPositionMessage(NetworkMessage):
    def __init__(self, x, y, player_id, timestamp=None):
        super().__init__()
        self.x = x
        self.y = y
        self.player_id = player_id
        self.timestamp = timestamp or time.time()
        self.version = 2


class PlayerInfoMessage(NetworkMessage):
    def __init__(self, player_name, color, position):
        super().__init__()
        self.player_name = player_name
        self.color = color
        self.position = position
        self.version = 1


class PlayersListMessage(NetworkMessage):
    def __init__(self, players_data):
        super().__init__()
        self.players = players_data
        self.version = 1


class WelcomeMessage(NetworkMessage):
    def __init__(self, player_id, players_data):
        super().__init__()
        self.player_id = player_id
        self.players = players_data
        self.version = 1


class CompleteMultiplayerGame(Scene):
    """Complete multiplayer game with stable connection and smooth movement"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Network
        self.server = None
        self.client = None
        self.is_host = False
        self.is_connected = False
        
        # Players with interpolation
        self.players = {}  # {player_id: player_data}
        self.my_id = None
        self.my_position = [400, 300]
        self.my_velocity = [0, 0]
        self.my_color = self.random_color()
        self.my_name = "Player_" + str(random.randint(100, 999))
        
        # Interpolators for each remote player
        self.interpolators = {}
        
        # Input buffer for client-side prediction
        self.input_buffer = []
        self.last_processed_input = 0
        self.input_sequence = 0
        
        # UI
        self.ui_visible = True  # Track UI visibility
        self.setup_ui()
        
        # Threads
        self.running = True
        self.position_update_thread = None
        
        # State
        self.last_position_sent = 0
        self.position_update_interval = 0.033  # 30 times per second (33ms)
        self.smooth_updates = True  # Enable smooth updates
        
        # Ping tracking
        self.ping = 0
        self.last_ping_update = 0
        
        @self.engine.on_event(pygame.KEYDOWN)
        def handle_input(event):
            """Handle keyboard input"""
            if event.type == pygame.KEYDOWN:
                # Tab to toggle UI visibility
                if event.key == pygame.K_TAB:
                    self.toggle_ui_visibility()
                    return True
        
    def random_color(self):
        """Generate random color"""
        return (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
    
    def random_position(self):
        """Generate random position on screen"""
        return [
            random.randint(50, self.engine.width - 50),
            random.randint(100, self.engine.height - 100)
        ]
    
    def setup_ui(self):
        """Setup interface"""
        w, h = self.engine.width, self.engine.height
        
        # ===== TITLE =====
        self.title = TextLabel(w//2, 30, "MULTIPLAYER TEST - SMOOTH MOVEMENT", 28, (255, 255, 0), root_point=(0.5, 0))
        self.add_ui_element(self.title)
        
        # ===== STATUS BAR =====
        self.status_label = TextLabel(w//2, 70, "Disconnected", 22, (255, 100, 100), root_point=(0.5, 0))
        self.add_ui_element(self.status_label)
        
        # Ping display
        self.ping_label = TextLabel(w - 100, 70, "Ping: 0ms", 16, (200, 200, 255), root_point=(1, 0))
        self.add_ui_element(self.ping_label)
        
        # ===== CONNECTION PANEL =====
        self.conn_panel = UiFrame(50, 120, 700, 200)
        self.conn_panel.set_background_color((40, 50, 70, 200))
        self.conn_panel.set_border((60, 70, 90), 2)
        self.add_ui_element(self.conn_panel)
        
        # Left Side - Host
        self.host_label = TextLabel(150, 140, "BE HOST", 24, (100, 255, 100))
        self.add_ui_element(self.host_label)
        
        self.host_btn = Button(100, 170, 200, 50, "START SERVER")
        self.host_btn.set_on_click(self.start_server)
        self.add_ui_element(self.host_btn)
        
        self.host_info = TextLabel(200, 230, "Port: 5555", 16, (200, 200, 255), root_point=(0.5, 0))
        self.add_ui_element(self.host_info)
        
        # Right Side - Client
        self.client_label = TextLabel(550, 140, "CONNECT", 24, (100, 200, 255))
        self.add_ui_element(self.client_label)
        
        self.ip_label = TextLabel(450, 170, "Server IP:", 16)
        self.add_ui_element(self.ip_label)
        
        self.ip_input = TextBox(450, 190, 200, 30, "127.0.0.1")
        self.add_ui_element(self.ip_input)
        
        self.connect_btn = Button(660, 190, 90, 30, "Connect")
        self.connect_btn.set_on_click(self.connect_as_client)
        self.add_ui_element(self.connect_btn)
        
        self.name_label = TextLabel(450, 230, "Your Name:", 16)
        self.add_ui_element(self.name_label)
        
        self.name_input = TextBox(450, 250, 200, 30, self.my_name)
        self.add_ui_element(self.name_input)
        
        # ===== PLAYERS PANEL =====
        self.players_panel = UiFrame(50, 340, 700, 200)
        self.players_panel.set_background_color((30, 40, 60))
        self.players_panel.set_border((60, 70, 90), 2)
        self.add_ui_element(self.players_panel)
        
        self.players_label = TextLabel(100, 350, "ONLINE PLAYERS:", 20, (255, 255, 200))
        self.add_ui_element(self.players_label)
        
        # Create ScrollingFrame for players list
        self.players_scroll_frame = ScrollingFrame(55, 370, 690, 160, 690, 160)
        self.players_scroll_frame.set_background_color((30, 40, 60, 0))
        self.add_ui_element(self.players_scroll_frame)
        
        # Initialize players container
        self.players_container = UiFrame(0, 0, 690, 160)
        self.players_container.set_background_color((30, 40, 60, 0))
        self.players_scroll_frame.add_child(self.players_container)
        
        # ===== SMOOTHING CONTROLS =====
        self.smooth_panel = UiFrame(50, 550, 700, 60)
        self.smooth_panel.set_background_color((40, 50, 70, 200))
        self.smooth_panel.set_border((60, 70, 90), 2)
        self.add_ui_element(self.smooth_panel)
        
        self.smooth_toggle = Button(100, 560, 200, 40, "SMOOTHING ACTIVE")
        self.smooth_toggle.set_background_color((100, 200, 100))
        self.smooth_toggle.set_on_click(self.toggle_smoothing)
        self.add_ui_element(self.smooth_toggle)
        
        self.smooth_info = TextLabel(400, 580, "Interpolation: 100ms | Updates: 30/sec", 14, (200, 200, 255), root_point=(0.5, 0))
        self.add_ui_element(self.smooth_info)
        
        # ===== SYSTEM LOG =====
        self.log_frame = UiFrame(50, 620, 700, 130)
        self.log_frame.set_background_color((30, 40, 60))
        self.log_frame.set_border((60, 70, 90), 2)
        self.add_ui_element(self.log_frame)
        
        self.log_title = TextLabel(100, 610, "SYSTEM LOG:", 14, (150, 255, 150))
        self.add_ui_element(self.log_title)
        
        # Create ScrollingFrame for log messages
        self.log_scroll_frame = ScrollingFrame(55, 630, 690, 110, 690, 110)
        self.log_scroll_frame.set_background_color((30, 40, 60, 0))
        self.add_ui_element(self.log_scroll_frame)
        
        # Initialize log container
        self.log_container = UiFrame(0, 0, 690, 110)
        self.log_container.set_background_color((30, 40, 60, 0))
        self.log_scroll_frame.add_child(self.log_container)
        
        # Store log messages
        self.log_messages = []
        
        # ===== UI VISIBILITY INDICATOR =====
        self.ui_indicator = TextLabel(w//2, h - 20, "Press TAB to toggle UI", 14, (150, 150, 200, 150), root_point=(0.5, 1))
        self.add_ui_element(self.ui_indicator)
    
    def toggle_ui_visibility(self):
        """Toggle UI visibility"""
        self.ui_visible = not self.ui_visible
        
        # Update indicator text
        if self.ui_visible:
            self.ui_indicator.set_text("Press TAB to hide UI")
            self.ui_indicator.set_text_color((150, 150, 200, 150))
        else:
            self.ui_indicator.set_text("Press TAB to show UI")
            self.ui_indicator.set_text_color((150, 150, 200, 100))
        
        # Toggle all UI elements (except the indicator itself)
        elements_to_toggle = [
            self.title,
            self.status_label,
            self.ping_label,
            self.conn_panel,
            self.host_label,
            self.host_btn,
            self.host_info,
            self.client_label,
            self.ip_label,
            self.ip_input,
            self.connect_btn,
            self.name_label,
            self.name_input,
            self.players_panel,
            self.players_label,
            self.players_scroll_frame,
            self.smooth_panel,
            self.smooth_toggle,
            self.smooth_info,
            self.log_frame,
            self.log_title,
            self.log_scroll_frame
        ]
        
        for element in elements_to_toggle:
            element.visible = self.ui_visible
        
        # Log the action
        self.log(f"UI {'shown' if self.ui_visible else 'hidden'}")
    
    def toggle_smoothing(self):
        """Toggle movement smoothing"""
        self.smooth_updates = not self.smooth_updates
        if self.smooth_updates:
            self.smooth_toggle.set_text("SMOOTHING ACTIVE")
            self.smooth_toggle.set_background_color((100, 200, 100))
            self.log("Smoothing enabled")
        else:
            self.smooth_toggle.set_text("SMOOTHING INACTIVE")
            self.smooth_toggle.set_background_color((200, 100, 100))
            self.log("Smoothing disabled")
    
    def log(self, message):
        """Add message to log"""
        print(f"LOG: {message}")
        
        # Create TextLabel for this log message
        time_str = time.strftime("%H:%M:%S", time.localtime())
        log_label = TextLabel(10, len(self.log_messages) * 18, 
                             f"[{time_str}] {message}", 
                             12, (150, 255, 150))
        
        # Add to log container
        self.log_container.add_child(log_label)
        
        # Store reference and update container height
        self.log_messages.append(log_label)
        
        # Update container height based on number of messages
        self.log_container.height = max(110, len(self.log_messages) * 18 + 10)
        
        # Auto-scroll to bottom
        self.log_scroll_frame.scroll_y = max(0, self.log_container.height - self.log_scroll_frame.height)
        
        # Keep only last 20 messages
        if len(self.log_messages) > 20:
            for _ in range(len(self.log_messages) - 20):
                if self.log_messages:
                    old_label = self.log_messages.pop(0)
                    self.log_container.remove_child(old_label)
    
    def update_players_list(self):
        """Update players list in UI"""
        # Clear existing player labels
        for child in list(self.players_container.children):
            self.players_container.remove_child(child)
        
        if not self.players:
            no_players_label = TextLabel(10, 10, "No players connected", 16, (200, 200, 200))
            self.players_container.add_child(no_players_label)
            return
        
        # Build players list
        y_pos = 10
        for player_id, player in sorted(self.players.items()):
            marker = "> " if player_id == self.my_id else "  "
            name = player.get('name', f'Player{player_id}')
            ping = player.get('ping', 0)
            
            # Color based on ping
            if ping < 50:
                color = (100, 255, 100)
            elif ping < 100:
                color = (255, 255, 100)
            elif ping < 200:
                color = (255, 150, 100)
            else:
                color = (255, 100, 100)
            
            # Create player label
            player_text = f"{marker}{name} (ID: {player_id}) - {ping}ms"
            player_label = TextLabel(10, y_pos, player_text, 14, color)
            self.players_container.add_child(player_label)
            
            y_pos += 20
        
        # Update container height
        self.players_container.height = max(160, y_pos + 10)
        
        # Auto-scroll if needed
        self.players_scroll_frame.scroll_y = max(0, self.players_container.height - self.players_scroll_frame.height)
    
    def start_server(self):
        """Start server"""
        try:
            if self.is_host:
                self.log("Server is already active")
                return
            
            self.log("Starting server on port 5555...")
            
            # Create server
            self.server = Server("0.0.0.0", 5555, max_clients=8)
            
            # Configure longer timeout to avoid disconnections
            self.server.timeout_threshold = 60
            self.server.heartbeat_interval = 3
            
            # Configure server events
            @self.server.on_event(NetworkEventType.CONNECT)
            def on_client_connect(event):
                client_id = event.client_id
                client_info = event.data
                username = 'Unknown'
                if hasattr(client_info, 'username'):
                    username = client_info.username
                elif isinstance(client_info, dict) and 'username' in client_info:
                    username = client_info['username']
                
                self.log(f"Player {client_id} connected: {username}")
                
                # Send random position to the new client
                position = self.random_position()
                
                # Add to local list
                self.players[client_id] = {
                    'position': position,
                    'color': self.random_color(),
                    'name': username,
                    'last_update': time.time(),
                    'ping': 0
                }
                
                # Create interpolator for this player
                self.interpolators[client_id] = NetworkInterpolator(interpolation_time=0.1)
                self.interpolators[client_id].add_position(position[0], position[1], time.time())
                
                # Send current game state to the new client
                self.send_welcome_package(client_id)
                
                self.update_players_list()
                self.update_status()
                
                # Send updated list to everyone
                self.broadcast_players_list()
            
            @self.server.on_event(NetworkEventType.DISCONNECT)
            def on_client_disconnect(event):
                client_id = event.client_id
                if client_id in self.players:
                    player_name = self.players[client_id].get('name', f'Player{client_id}')
                    self.log(f"Player {player_name} disconnected")
                    del self.players[client_id]
                
                if client_id in self.interpolators:
                    del self.interpolators[client_id]
                
                self.update_players_list()
                self.update_status()
                self.broadcast_players_list()
            
            @self.server.on_event(NetworkEventType.MESSAGE)
            def on_client_message(event):
                self.handle_server_message(event)
            
            @self.server.on_event(NetworkEventType.PING_UPDATE)
            def on_ping_update(event):
                client_id = event.client_id
                if client_id in self.players:
                    self.players[client_id]['ping'] = event.data.get('ping', 0)
                    self.update_players_list()
            
            # Start server
            if self.server.start():
                self.is_host = True
                self.my_id = 0  # Host is always ID 0
                
                # Add host to players list
                self.players[self.my_id] = {
                    'position': self.my_position.copy(),
                    'color': self.my_color,
                    'name': self.my_name,
                    'last_update': time.time(),
                    'ping': 0
                }
                
                # Create interpolator for host
                self.interpolators[self.my_id] = NetworkInterpolator(interpolation_time=0.1)
                
                self.update_status()
                self.update_players_list()
                
                self.host_btn.set_text("SERVER ACTIVE")
                self.host_btn.set_background_color((0, 150, 0))
                
                self.log("Server started successfully!")
                self.log("Waiting for players...")
                
                # Start sending host position
                self.start_position_updates()
            else:
                self.log("Failed to start server")
                
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def send_welcome_package(self, client_id):
        """Send welcome package to new client"""
        if not self.server:
            return
        
        # Prepare player data
        players_data = {}
        for pid, player in self.players.items():
            players_data[pid] = {
                'name': player['name'],
                'color': player['color'],
                'position': player['position'],
                'ping': player.get('ping', 0)
            }
        
        msg = WelcomeMessage(client_id, players_data)
        self.server.send_to_client(client_id, msg)
        self.log(f"Sent welcome package to player {client_id}")
    
    def connect_as_client(self):
        """Connect as client"""
        try:
            if self.is_connected:
                self.log("Already connected")
                return
            
            ip = self.ip_input.text.strip() or "127.0.0.1"
            self.my_name = self.name_input.text.strip() or self.my_name
            
            self.log(f"Connecting to {ip}:5555 as '{self.my_name}'...")
            
            # Create client
            self.client = NetworkClient(ip, 5555)
            
            # Configure timeout
            self.client.heartbeat_interval = 1  # More frequent heartbeat
            self.client.max_reconnect_attempts = 5
            
            # Configure client events
            @self.client.on_event(NetworkEventType.CONNECT)
            def on_connected(event):
                self.is_connected = True
                self.log("Connected to server!")
                self.update_status()
                
                self.connect_btn.set_text("CONNECTED")
                self.connect_btn.set_background_color((0, 150, 0))
                
                # Server will send ID and player list via WelcomeMessage
            
            @self.client.on_event(NetworkEventType.DISCONNECT)
            def on_disconnected(event):
                self.is_connected = False
                reason = 'Unknown'
                if hasattr(event, 'data') and event.data:
                    if isinstance(event.data, dict):
                        reason = event.data.get('reason', 'Unknown')
                    else:
                        reason = str(event.data)
                self.log(f"Disconnected: {reason}")
                self.update_status()
                
                self.connect_btn.set_text("Connect")
                self.connect_btn.set_background_color(None)
                self.players.clear()
                self.interpolators.clear()
                self.update_players_list()
            
            @self.client.on_event(NetworkEventType.MESSAGE)
            def on_message_received(event):
                self.handle_client_message(event.data)
            
            @self.client.on_event(NetworkEventType.PING_UPDATE)
            def on_ping_update(event):
                self.ping = event.data.get('ping', 0)
                self.last_ping_update = time.time()
                self.ping_label.set_text(f"Ping: {int(self.ping)}ms")
                
                # Update color based on ping
                if self.ping < 50:
                    color = (100, 255, 100)
                elif self.ping < 100:
                    color = (255, 255, 100)
                elif self.ping < 200:
                    color = (255, 150, 100)
                else:
                    color = (255, 100, 100)
                self.ping_label.set_text_color(color)
            
            # Connect
            if self.client.connect(self.my_name):
                self.log("Client configured, attempting connection...")
            else:
                self.log("Initial connection failed")
                self.client = None
                
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def send_player_info(self):
        """Send player information to server"""
        if not self.client or not self.is_connected:
            return
        
        msg = PlayerInfoMessage(self.my_name, self.my_color, self.my_position)
        self.client.send(msg)
        self.log(f"Sent player info: {self.my_name}")
    
    def send_player_position(self):
        """Send current player position with timestamp"""
        if (not self.client or not self.is_connected) and not self.is_host:
            return
        
        current_time = time.time()
        if current_time - self.last_position_sent < self.position_update_interval:
            return
        
        self.last_position_sent = current_time
        
        # Send position message with timestamp
        msg = PlayerPositionMessage(
            x=self.my_position[0],
            y=self.my_position[1],
            player_id=str(self.my_id or 0),
            timestamp=current_time
        )
        
        if self.is_host and self.server:
            # Host sends to all clients EXCEPT self
            self.server.broadcast(msg, exclude_client_id=self.my_id)
        elif self.client:
            # Client sends to server
            self.client.send(msg)
        
        # Update local interpolator
        if self.my_id in self.interpolators:
            self.interpolators[self.my_id].add_position(
                self.my_position[0], self.my_position[1], current_time
            )
    
    def start_position_updates(self):
        """Start periodic position sending"""
        def update_loop():
            while self.running and ((self.client and self.is_connected) or (self.is_host and self.server)):
                try:
                    self.send_player_position()
                    time.sleep(self.position_update_interval)
                except Exception as e:
                    print(f"Error in position loop: {e}")
                    break
        
        if not self.position_update_thread or not self.position_update_thread.is_alive():
            self.position_update_thread = threading.Thread(target=update_loop, daemon=True)
            self.position_update_thread.start()
    
    def broadcast_players_list(self):
        """Broadcast players list to everyone"""
        if not self.server or not self.is_host:
            return
        
        # Prepare player data
        players_data = {}
        for player_id, player in self.players.items():
            players_data[player_id] = {
                'name': player['name'],
                'color': player['color'],
                'position': player['position'],
                'ping': player.get('ping', 0)
            }
        
        msg = PlayersListMessage(players_data)
        self.server.broadcast(msg)
    
    def handle_server_message(self, event):
        """Handle messages on server"""
        message = event.data
        client_id = event.client_id
        
        if isinstance(message, PlayerPositionMessage):
            # Update player position
            if client_id in self.players:
                player = self.players[client_id]
                player['position'] = [message.x, message.y]
                player['last_update'] = time.time()
                
                # Update interpolator
                if client_id in self.interpolators:
                    self.interpolators[client_id].add_position(
                        message.x, message.y, message.timestamp
                    )
            
            # Resend to everyone (except sender)
            self.server.broadcast(message, exclude_client_id=client_id)
        
        elif isinstance(message, PlayerInfoMessage):
            # Update player information
            if client_id in self.players:
                self.players[client_id]['name'] = message.player_name
                self.players[client_id]['color'] = message.color
                self.players[client_id]['position'] = message.position
                self.log(f"Updated player {client_id}: {message.player_name}")
                self.update_players_list()
                self.broadcast_players_list()
    
    def handle_client_message(self, message):
        """Handle messages on client"""
        if isinstance(message, PlayerPositionMessage):
            # Update position of another player
            try:
                player_id = int(message.player_id)
                if player_id not in self.players:
                    # New player
                    self.players[player_id] = {
                        'position': [message.x, message.y],
                        'color': self.random_color(),
                        'name': f'Player{player_id}',
                        'last_update': time.time(),
                        'ping': 0
                    }
                    
                    # Create interpolator
                    self.interpolators[player_id] = NetworkInterpolator(interpolation_time=0.1)
                    self.interpolators[player_id].add_position(message.x, message.y, message.timestamp)
                    
                    self.update_players_list()
                else:
                    # Update existing position
                    player = self.players[player_id]
                    player['last_update'] = time.time()
                    
                    # Update interpolator
                    if player_id in self.interpolators:
                        self.interpolators[player_id].add_position(
                            message.x, message.y, message.timestamp
                        )
                    else:
                        # Create interpolator if doesn't exist
                        self.interpolators[player_id] = NetworkInterpolator(interpolation_time=0.1)
                        self.interpolators[player_id].add_position(message.x, message.y, message.timestamp)
            except Exception as e:
                print(f"Error processing PlayerPositionMessage: {e}")
        
        elif isinstance(message, PlayersListMessage):
            # Receive complete players list
            for player_id, player_data in message.players.items():
                try:
                    player_id_int = int(player_id)
                    position = player_data.get('position', self.random_position())
                    
                    if player_id_int not in self.players:
                        self.players[player_id_int] = {
                            'position': position,
                            'color': player_data.get('color', self.random_color()),
                            'name': player_data.get('name', f'Player{player_id}'),
                            'last_update': time.time(),
                            'ping': player_data.get('ping', 0)
                        }
                        
                        # Create interpolator
                        self.interpolators[player_id_int] = NetworkInterpolator(interpolation_time=0.1)
                        self.interpolators[player_id_int].add_position(position[0], position[1], time.time())
                except Exception as e:
                    print(f"Error processing player {player_id}: {e}")
                    continue
            self.update_players_list()
            self.log(f"Received players list: {len(self.players)} players")
        
        elif isinstance(message, WelcomeMessage):
            # Receive assigned ID and players list
            self.my_id = int(message.player_id)
            self.players = {}
            self.interpolators.clear()
            
            for player_id, player_data in message.players.items():
                try:
                    player_id_int = int(player_id)
                    position = player_data.get('position', self.random_position())
                    self.players[player_id_int] = {
                        'position': position,
                        'color': player_data.get('color', self.random_color()),
                        'name': player_data.get('name', f'Player{player_id}'),
                        'last_update': time.time(),
                        'ping': player_data.get('ping', 0)
                    }
                    
                    # Create interpolator
                    self.interpolators[player_id_int] = NetworkInterpolator(interpolation_time=0.1)
                    self.interpolators[player_id_int].add_position(position[0], position[1], time.time())
                except Exception as e:
                    print(f"Error processing welcome player {player_id}: {e}")
                    continue
            
            # Add local player if not in list
            if self.my_id not in self.players:
                self.players[self.my_id] = {
                    'position': self.my_position.copy(),
                    'color': self.my_color,
                    'name': self.my_name,
                    'last_update': time.time(),
                    'ping': 0
                }
                self.interpolators[self.my_id] = NetworkInterpolator(interpolation_time=0.1)
            
            # Send local player information
            self.send_player_info()
            
            # Start sending position
            self.start_position_updates()
            
            self.update_players_list()
            self.log(f"Welcome! My ID: {self.my_id}, Total players: {len(self.players)}")
    
    def update_status(self):
        """Update status in UI"""
        if self.is_host:
            client_count = len([p for p in self.players.keys() if p != self.my_id])
            self.status_label.set_text(f"HOST ({client_count} players connected)")
            self.status_label.set_text_color((100, 255, 100))
        elif self.is_connected:
            other_count = len([p for p in self.players.keys() if p != self.my_id])
            self.status_label.set_text(f"CONNECTED ({other_count} other players)")
            self.status_label.set_text_color((100, 255, 100))
        else:
            self.status_label.set_text("DISCONNECTED")
            self.status_label.set_text_color((255, 100, 100))
    
    def update(self, dt):
        """Update game logic with interpolation"""
        # Local player movement
        self.update_player_movement(dt)
        
        current_time = time.time()
        
        # Update interpolated positions of remote players
        for player_id, player in self.players.items():
            if player_id == self.my_id:
                continue
            
            if self.smooth_updates and player_id in self.interpolators:
                # Use interpolation for smooth movement
                x, y = self.interpolators[player_id].get_interpolated_position(current_time)
                player['position'] = [x, y]
            else:
                # No interpolation (instant movement)
                pass
        
        # Clean up inactive players (after 10 seconds without update)
        current_time = time.time()
        inactive_players = []
        for player_id, player in self.players.items():
            if player_id != self.my_id and current_time - player['last_update'] > 10:
                inactive_players.append(player_id)
        
        for player_id in inactive_players:
            if player_id in self.players:
                del self.players[player_id]
            if player_id in self.interpolators:
                del self.interpolators[player_id]
        
        if inactive_players:
            self.update_players_list()
    
    def update_player_movement(self, dt):
        """Update movement based on keys"""
        keys = pygame.key.get_pressed()
        speed = 300 * dt  # Increased to 300 pixels/second
        
        # Reset velocity
        self.my_velocity = [0, 0]
        
        # Movement
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.my_velocity[1] = -speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.my_velocity[1] = speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.my_velocity[0] = -speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.my_velocity[0] = speed
        
        # Normalize diagonal movement
        if self.my_velocity[0] != 0 and self.my_velocity[1] != 0:
            self.my_velocity[0] *= 0.7071  # 1/√2
            self.my_velocity[1] *= 0.7071
        
        # Apply movement
        self.my_position[0] += self.my_velocity[0]
        self.my_position[1] += self.my_velocity[1]
        
        # Screen bounds
        self.my_position[0] = max(20, min(self.engine.width - 20, self.my_position[0]))
        self.my_position[1] = max(20, min(self.engine.height - 20, self.my_position[1]))
        
        # Update local position in list
        if self.my_id is not None and self.my_id in self.players:
            self.players[self.my_id]['position'] = self.my_position.copy()
            self.players[self.my_id]['last_update'] = time.time()
    
    def render(self, renderer):
        """Render the game"""
        # Background
        renderer.fill_screen((40, 50, 70))
        
        # Background grid
        self.render_grid(renderer)
        
        # Render other players
        self.render_other_players(renderer)
        
        # Render local player
        self.render_local_player(renderer)
        
        # On-screen information (always visible, minimal)
        self.render_minimal_hud(renderer)
    
    def render_grid(self, renderer):
        """Render background grid"""
        for x in range(0, self.engine.width, 50):
            renderer.draw_line(x, 0, x, self.engine.height, (60, 70, 90, 100))
        for y in range(0, self.engine.height, 50):
            renderer.draw_line(0, y, self.engine.width, y, (60, 70, 90, 100))
    
    def render_local_player(self, renderer:OpenGLRenderer):
        """Render local player"""
        x, y = int(self.my_position[0]), int(self.my_position[1])
        
        # Shadow
        renderer.draw_circle(x + 3, y + 3, 15, (0, 0, 0, 100))
        
        # Player
        renderer.draw_circle(x, y, 15, self.my_color)
        
        # Border
        renderer.draw_circle(x, y, 15, (255, 255, 255), fill=False, border_width=2)
        
        # Movement direction (if moving)
        if self.my_velocity[0] != 0 or self.my_velocity[1] != 0:
            # Calculate movement angle
            angle = math.atan2(self.my_velocity[1], self.my_velocity[0])
            dx = math.cos(angle) * 20
            dy = math.sin(angle) * 20
            renderer.draw_line(x, y, x + dx, y + dy, (255, 255, 255, 200), width=2)
        
        # Name (always visible)
        font = pygame.font.SysFont("Arial", 14, bold=True)
        name = self.my_name
        you_text = " (You)" if self.my_id is not None else ""
        text = font.render(f"{name}{you_text}", True, (255, 255, 255))
        renderer.blit(text, (x - text.get_width()//2, y - 30))
        
        # Ping indicator (always visible)
        if self.is_connected and self.ping > 0:
            ping_font = pygame.font.SysFont("Arial", 10)
            ping_text = ping_font.render(f"{int(self.ping)}ms", True, (200, 200, 255))
            renderer.blit(ping_text, (x - ping_text.get_width()//2, y + 20))
    
    def render_other_players(self, renderer):
        """Render other players"""
        for player_id, player in self.players.items():
            if player_id == self.my_id:
                continue
            
            if 'position' not in player:
                continue
                
            try:
                # Ensure positions are numbers
                pos = player['position']
                if isinstance(pos, list) and len(pos) >= 2:
                    x = int(float(pos[0]))
                    y = int(float(pos[1]))
                else:
                    continue
            except (ValueError, TypeError, IndexError):
                continue
                
            color = player.get('color', (200, 200, 200))
            name = player.get('name', f'Player{player_id}')
            ping = player.get('ping', 0)
            
            # Shadow
            renderer.draw_circle(x + 2, y + 2, 12, (0, 0, 0, 100))
            
            # Player
            renderer.draw_circle(x, y, 12, color)
            
            # Interpolation indicator (if active)
            if self.smooth_updates and player_id in self.interpolators:
                renderer.draw_circle(x, y, 12, (255, 255, 255), fill=False, border_width=1)
            
            # Name (always visible)
            font = pygame.font.SysFont("Arial", 12)
            text = font.render(name, True, (255, 255, 255))
            renderer.blit(text, (x - text.get_width()//2, y - 25))
            
            # Ping (if available, always visible)
            if ping > 0:
                ping_font = pygame.font.SysFont("Arial", 9)
                ping_color = (100, 255, 100) if ping < 50 else (255, 255, 100) if ping < 100 else (255, 150, 100)
                ping_text = ping_font.render(f"{int(ping)}ms", True, ping_color)
                renderer.blit(ping_text, (x - ping_text.get_width()//2, y + 15))
    
    def render_minimal_hud(self, renderer):
        """Render minimal HUD information that's always visible"""
        w, h = self.engine.width, self.engine.height
        
        # Player counter in corner (always visible)
        font = pygame.font.SysFont("Arial", 18, bold=True)
        count = len(self.players)
        count_text = font.render(f"Players: {count}", True, (255, 255, 255))
        renderer.blit(count_text, (w - count_text.get_width() - 10, 10))
        
        # Connection status indicator (always visible)
        status_font = pygame.font.SysFont("Arial", 14)
        if self.is_host:
            status_text = "HOST"
            color = (100, 255, 100)
        elif self.is_connected:
            status_text = "CONNECTED"
            color = (100, 255, 100)
        else:
            status_text = "DISCONNECTED"
            color = (255, 100, 100)
        
        status_render = status_font.render(status_text, True, color)
        renderer.blit(status_render, (10, 10))
        
        # Smoothing status (always visible, small)
        smooth_font = pygame.font.SysFont("Arial", 12)
        smooth_text = "SMOOTH" if self.smooth_updates else "INSTANT"
        smooth_color = (100, 200, 100) if self.smooth_updates else (200, 100, 100)
        smooth_render = smooth_font.render(smooth_text, True, smooth_color)
        renderer.blit(smooth_render, (10, 30))
        
        # Controls hint at bottom (only when UI is hidden)
        if not self.ui_visible:
            controls_font = pygame.font.SysFont("Arial", 12)
            controls_text = "TAB: Show UI | WASD/Arrows: Move"
            controls_render = controls_font.render(controls_text, True, (200, 200, 255, 150))
            renderer.blit(controls_render, (w//2 - controls_render.get_width()//2, h - 30))
    
    def on_exit(self, next_scene: str = None):
        """Clean up on exit"""
        self.running = False
        
        if self.server:
            self.server.stop()
            self.server = None
        
        if self.client:
            self.client.disconnect()
            self.client = None


def main():
    """Main function"""
    engine = LunaEngine("Complete Multiplayer - Stable and Smooth Connection", 1024, 768)
    engine.add_scene("game", CompleteMultiplayerGame)
    engine.set_scene("game")
    
    print("=" * 70)
    print("COMPLETE MULTIPLAYER - STABLE AND SMOOTH CONNECTION")
    print("=" * 70)
    print("HOW TO PLAY:")
    print("1. Open TWO windows of this program")
    print("2. In FIRST: Click 'START SERVER'")
    print("3. In SECOND: Use IP '127.0.0.1' and click 'Connect'")
    print("4. Use WASD or ARROWS to move in BOTH windows")
    print("5. See the other player move in real time!")
    print("=" * 70)
    print("CONTROLS:")
    print("- TAB: Toggle UI visibility (hide/show menus)")
    print("- WASD/Arrows: Move player")
    print("- Click buttons: Interact with UI")
    print("=" * 70)
    print("FEATURES:")
    print("- Movement interpolation (smoothing)")
    print("- Updates at 30/second")
    print("- Real-time ping")
    print("- Client-side prediction")
    print("=" * 70)
    
    engine.run()


if __name__ == "__main__":
    main()