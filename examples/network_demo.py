"""
network_demo.py - Network System Demo with Chat and Statistics

This demo showcases the network system with real-time chat functionality
and comprehensive network statistics display.
"""

import sys
import os
import pygame
import time
import threading
import random
from collections import deque
from typing import Tuple, Optional, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui.elements import *
from lunaengine.backend.network import *
from lunaengine.backend import OpenGLRenderer

# ============================================================================
# NETWORK MESSAGE CLASSES
# ============================================================================

class ChatMessage(NetworkMessage):
    """Message for sending chat text between clients"""
    def __init__(self, sender_id, sender_name, message, timestamp=None):
        super().__init__()
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.message = message
        self.timestamp = timestamp or time.time()
        self.version = 1


class NetworkStatsMessage(NetworkMessage):
    """Message for broadcasting network statistics"""
    def __init__(self, stats_data):
        super().__init__()
        self.stats = stats_data  # Dict with various stats
        self.version = 1


class ServerInfoMessage(NetworkMessage):
    """Message with server information for clients"""
    def __init__(self, max_players, server_name, uptime):
        super().__init__()
        self.max_players = max_players
        self.server_name = server_name
        self.uptime = uptime
        self.version = 1


class PlayerJoinMessage(NetworkMessage):
    """Message when a player joins/leaves the server"""
    def __init__(self, player_id, player_name, action):
        super().__init__()
        self.player_id = player_id
        self.player_name = player_name
        self.action = action  # 'join' or 'leave'
        self.timestamp = time.time()
        self.version = 1


# ============================================================================
# NETWORK DEMO SCENE
# ============================================================================

class NetworkDemoScene(Scene):
    """
    Network demo scene with real-time chat and comprehensive network statistics.
    
    Features:
    - Real-time chat with message history
    - Network statistics (ping, packet loss, bandwidth)
    - Player list with connection status
    - Server/client connection management
    - Visual network graph
    """
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Network components
        self.server = None
        self.client = None
        self.is_host = False
        self.is_connected = False
        
        # Player info
        self.my_id = None
        self.my_name = "User_" + str(hash(time.time()) % 1000)
        self.players = {}  # {player_id: player_data}
        
        # Chat system
        self.chat_messages = deque(maxlen=100)  # Last 100 messages
        self.chat_input = ""
        self.chat_input_active = False
        self.last_chat_sent = 0
        self.chat_cooldown = 0.5  # Seconds between messages
        
        # Network statistics
        self.network_stats = {
            'ping': 0,
            'packet_loss': 0.0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'packets_sent': 0,
            'packets_received': 0,
            'connection_time': 0,
            'latency_history': deque(maxlen=50),  # Last 50 ping measurements
            'bandwidth_history': deque(maxlen=30)  # Last 30 bandwidth measurements
        }
        
        # Server statistics (host only)
        self.server_stats = {
            'uptime': 0,
            'total_clients': 0,
            'max_clients': 8,
            'total_messages': 0,
            'total_bytes': 0,
            'start_time': time.time()
        }
        
        # Network graph data
        self.ping_graph_data = deque(maxlen=100)
        self.bandwidth_graph_data = deque(maxlen=100)
        
        # UI state
        self.selected_tab = "chat"  # "chat", "stats", or "players"
        self.auto_scroll_chat = True
        self.show_network_graph = True
        
        # Threads
        self.running = True
        self.stats_update_thread = None
        
        # Initialize
        self.setup_ui()
        self.log_system("Network demo initialized")
        
    def setup_ui(self):
        """Setup all UI elements for the network demo"""
        w, h = self.engine.width, self.engine.height
        
        # ===== TITLE =====
        title = TextLabel(w//2, 20, "NETWORK DEMO - CHAT & STATISTICS", 32, 
                         (255, 200, 0), root_point=(0.5, 0))
        self.add_ui_element(title)
        
        subtitle = TextLabel(w//2, 55, "Real-time chat with network monitoring", 16,
                           (200, 200, 200), root_point=(0.5, 0))
        self.add_ui_element(subtitle)
        
        # ===== CONNECTION PANEL =====
        conn_panel = UiFrame(20, 80, w-40, 100)
        conn_panel.set_background_color((40, 45, 60, 220))
        conn_panel.set_border((60, 70, 90), 2)
        self.add_ui_element(conn_panel)
        
        # Status indicator
        self.status_indicator = UiFrame(30, 90, 10, 10)
        self.status_indicator.set_background_color((255, 50, 50))
        self.add_ui_element(self.status_indicator)
        
        self.status_label = TextLabel(50, 90, "Disconnected", 20, (255, 100, 100))
        self.add_ui_element(self.status_label)
        
        # Connection buttons
        self.host_btn = Button(30, 120, 150, 40, "START SERVER")
        self.host_btn.set_on_click(self.start_server)
        self.host_btn.set_simple_tooltip("Host a server on port 5555")
        self.add_ui_element(self.host_btn)
        
        # Client connection section
        ip_label = TextLabel(200, 120, "Server IP:", 16)
        self.add_ui_element(ip_label)
        
        self.ip_input = TextBox(200, 140, 150, 30, "127.0.0.1")
        self.add_ui_element(self.ip_input)
        
        name_label = TextLabel(360, 120, "Your Name:", 16)
        self.add_ui_element(name_label)
        
        self.name_input = TextBox(360, 140, 150, 30, self.my_name)
        self.add_ui_element(self.name_input)
        
        self.connect_btn = Button(520, 140, 120, 30, "CONNECT")
        self.connect_btn.set_on_click(self.connect_as_client)
        self.connect_btn.set_simple_tooltip("Connect to server as client")
        self.add_ui_element(self.connect_btn)
        
        self.disconnect_btn = Button(650, 140, 120, 30, "DISCONNECT")
        self.disconnect_btn.set_on_click(self.disconnect)
        self.disconnect_btn.set_background_color((200, 100, 100))
        self.disconnect_btn.enabled = False
        self.add_ui_element(self.disconnect_btn)
        
        # ===== MAIN CONTENT TABS =====
        tab_panel = UiFrame(20, 190, w-40, h-240)
        tab_panel.set_background_color((35, 40, 55, 240))
        tab_panel.set_border((60, 70, 90), 2)
        self.add_ui_element(tab_panel)
        
        # Tab buttons
        self.chat_tab_btn = Button(30, 200, 120, 40, "CHAT")
        self.chat_tab_btn.set_on_click(lambda: self.set_tab("chat"))
        self.chat_tab_btn.set_background_color((70, 100, 150))
        self.add_ui_element(self.chat_tab_btn)
        
        self.stats_tab_btn = Button(160, 200, 120, 40, "STATS")
        self.stats_tab_btn.set_on_click(lambda: self.set_tab("stats"))
        self.stats_tab_btn.set_background_color((50, 50, 50))
        self.add_ui_element(self.stats_tab_btn)
        
        self.players_tab_btn = Button(290, 200, 120, 40, "PLAYERS")
        self.players_tab_btn.set_on_click(lambda: self.set_tab("players"))
        self.players_tab_btn.set_background_color((50, 50, 50))
        self.add_ui_element(self.players_tab_btn)
        
        # ===== CHAT TAB CONTENT =====
        # Chat history display using ScrollingFrame
        chat_frame = UiFrame(30, 250, w-80, h-350)
        chat_frame.set_background_color((25, 30, 40))
        chat_frame.set_border((60, 70, 90), 2)
        self.add_ui_element(chat_frame)
        
        # Create ScrollingFrame for chat messages
        self.chat_scroll_frame = ScrollingFrame(35, 255, w-90, h-360, w-90, h-360)
        self.chat_scroll_frame.set_background_color((25, 30, 40, 0))
        self.add_ui_element(self.chat_scroll_frame)
        
        # Initialize chat container
        self.chat_container = UiFrame(0, 0, w-90, h-360)
        self.chat_container.set_background_color((25, 30, 40, 0))
        self.chat_scroll_frame.add_child(self.chat_container)
        
        # Chat input
        self.chat_input_box = TextBox(30, h-90, w-160, 30, "Type your message...")
        self.add_ui_element(self.chat_input_box)
        
        self.send_chat_btn = Button(w-120, h-90, 90, 30, "SEND")
        self.send_chat_btn.set_on_click(self.send_chat_message)
        self.send_chat_btn.enabled = False
        self.add_ui_element(self.send_chat_btn)
        
        # ===== STATISTICS TAB CONTENT =====
        # Network stats display
        self.stats_panel = UiFrame(30, 250, w-80, h-350)
        self.stats_panel.set_background_color((25, 30, 40))
        self.stats_panel.set_border((60, 70, 90), 2)
        self.stats_panel.visible = False
        self.add_ui_element(self.stats_panel)
        
        # Stats labels
        self.ping_label = TextLabel(40, 260, "Ping: -- ms", 18, (150, 200, 255))
        self.add_ui_element(self.ping_label)
        
        self.packet_loss_label = TextLabel(40, 290, "Packet Loss: 0.0%", 18, (150, 200, 255))
        self.add_ui_element(self.packet_loss_label)
        
        self.bandwidth_label = TextLabel(40, 320, "Bandwidth: 0 B/s", 18, (150, 200, 255))
        self.add_ui_element(self.bandwidth_label)
        
        self.connection_label = TextLabel(40, 350, "Connection Time: 0s", 18, (150, 200, 255))
        self.add_ui_element(self.connection_label)
        
        # Server stats (host only)
        self.server_stats_label = TextLabel(w//2, 380, "SERVER STATISTICS", 20, (255, 200, 100), root_point=(0.5, 0))
        self.server_stats_label.visible = False
        self.add_ui_element(self.server_stats_label)
        
        self.clients_label = TextLabel(40, 410, "Connected Clients: 0/8", 16, (200, 200, 200))
        self.clients_label.visible = False
        self.add_ui_element(self.clients_label)
        
        self.uptime_label = TextLabel(40, 440, "Server Uptime: 0s", 16, (200, 200, 200))
        self.uptime_label.visible = False
        self.add_ui_element(self.uptime_label)
        
        self.messages_label = TextLabel(40, 470, "Total Messages: 0", 16, (200, 200, 200))
        self.messages_label.visible = False
        self.add_ui_element(self.messages_label)
        
        # Network graph toggle
        self.graph_toggle = Button(w-150, 260, 120, 30, "SHOW GRAPH")
        self.graph_toggle.set_on_click(self.toggle_network_graph)
        self.graph_toggle.visible = False
        self.add_ui_element(self.graph_toggle)
        
        # ===== PLAYERS TAB CONTENT =====
        self.players_panel = UiFrame(30, 250, w-80, h-350)
        self.players_panel.set_background_color((25, 30, 40))
        self.players_panel.set_border((60, 70, 90), 2)
        self.players_panel.visible = False
        self.add_ui_element(self.players_panel)
        
        # Create ScrollingFrame for players list
        self.players_scroll_frame = ScrollingFrame(35, 255, w-90, h-360, w-90, h-360)
        self.players_scroll_frame.set_background_color((25, 30, 40, 0))
        self.players_scroll_frame.visible = False
        self.add_ui_element(self.players_scroll_frame)
        
        # Initialize players container
        self.players_container = UiFrame(0, 0, w-90, h-360)
        self.players_container.set_background_color((25, 30, 40, 0))
        self.players_scroll_frame.add_child(self.players_container)
        
        # ===== FOOTER INFO =====
        footer = TextLabel(w//2, h-30, 
                          "Press TAB to focus chat • F1: Clear Chat • F2: Reset Stats • F3: Test Connection",
                          14, (150, 150, 200), root_point=(0.5, 1))
        self.add_ui_element(footer)
        
        # Update initial UI state
        self.update_tab_buttons()
        
    def set_tab(self, tab_name):
        """Switch between main content tabs"""
        self.selected_tab = tab_name
        
        # Update visibility
        chat_frame = self.chat_scroll_frame
        while chat_frame.parent is not None:
            chat_frame = chat_frame.parent
        
        chat_frame.visible = (tab_name == "chat")
        self.chat_input_box.visible = (tab_name == "chat")
        self.send_chat_btn.visible = (tab_name == "chat")
        
        self.stats_panel.visible = (tab_name == "stats")
        self.ping_label.visible = (tab_name == "stats")
        self.packet_loss_label.visible = (tab_name == "stats")
        self.bandwidth_label.visible = (tab_name == "stats")
        self.connection_label.visible = (tab_name == "stats")
        self.server_stats_label.visible = (tab_name == "stats" and self.is_host)
        self.clients_label.visible = (tab_name == "stats" and self.is_host)
        self.uptime_label.visible = (tab_name == "stats" and self.is_host)
        self.messages_label.visible = (tab_name == "stats" and self.is_host)
        self.graph_toggle.visible = (tab_name == "stats")
        
        self.players_panel.visible = (tab_name == "players")
        self.players_scroll_frame.visible = (tab_name == "players")
        
        # Update tab button colors
        self.update_tab_buttons()
        
    def update_tab_buttons(self):
        """Update tab button appearance based on selected tab"""
        active_color = (70, 100, 150)
        inactive_color = (50, 50, 50)
        
        self.chat_tab_btn.set_background_color(
            active_color if self.selected_tab == "chat" else inactive_color
        )
        self.stats_tab_btn.set_background_color(
            active_color if self.selected_tab == "stats" else inactive_color
        )
        self.players_tab_btn.set_background_color(
            active_color if self.selected_tab == "players" else inactive_color
        )
    
    def on_chat_focus(self):
        """Called when chat input box is focused"""
        self.chat_input_active = True
        if self.chat_input_box.text == "Type your message...":
            self.chat_input_box.set_text("")
        self.send_chat_btn.enabled = True
    
    def on_chat_blur(self):
        """Called when chat input box loses focus"""
        self.chat_input_active = False
        if self.chat_input_box.text.strip() == "":
            self.chat_input_box.set_text("Type your message...")
    
    def start_server(self):
        """Start a network server"""
        try:
            if self.is_host:
                self.log_system("Server already running")
                return
            
            self.log_system("Starting server on port 5555...")
            
            # Create server
            self.server = Server("0.0.0.0", 5555, max_clients=8)
            self.server.timeout_threshold = 30
            self.server.heartbeat_interval = 2
            
            # Setup server event handlers
            @self.server.on_event(NetworkEventType.CONNECT)
            def on_client_connect(event):
                client_id = event.client_id
                client_info = event.data
                
                username = 'Unknown'
                if hasattr(client_info, 'username'):
                    username = client_info.username
                elif isinstance(client_info, dict) and 'username' in client_info:
                    username = client_info['username']
                
                # Add to players list
                self.players[client_id] = {
                    'name': username,
                    'join_time': time.time(),
                    'ping': 0,
                    'message_count': 0
                }
                
                # Send join notification
                join_msg = PlayerJoinMessage(client_id, username, 'join')
                self.server.broadcast(join_msg)
                
                # Update UI
                self.update_players_list()
                self.server_stats['total_clients'] = len(self.players) - 1  # Exclude host
                
                self.log_chat(f"{username} joined the server")
                self.log_system(f"Player {client_id} connected: {username}")
            
            @self.server.on_event(NetworkEventType.DISCONNECT)
            def on_client_disconnect(event):
                client_id = event.client_id
                if client_id in self.players:
                    player_name = self.players[client_id]['name']
                    
                    # Send leave notification
                    leave_msg = PlayerJoinMessage(client_id, player_name, 'leave')
                    self.server.broadcast(leave_msg)
                    
                    # Remove from list
                    del self.players[client_id]
                    
                    # Update UI
                    self.update_players_list()
                    self.server_stats['total_clients'] = len(self.players) - 1
                    
                    self.log_chat(f"{player_name} left the server")
                    self.log_system(f"Player {client_id} disconnected: {player_name}")
            
            @self.server.on_event(NetworkEventType.MESSAGE)
            def on_client_message(event):
                message = event.data
                client_id = event.client_id
                
                if isinstance(message, ChatMessage):
                    # Track message count
                    if client_id in self.players:
                        self.players[client_id]['message_count'] += 1
                    
                    # Increment server stats
                    self.server_stats['total_messages'] += 1
                    
                    # Broadcast to all clients EXCEPT the sender
                    self.server.broadcast(message, exclude_client_id=client_id)
                    
                    # Display locally only if it's not from the host
                    if client_id != self.my_id:
                        self.display_chat_message(message)
                    else:
                        # Host already displayed the message when sending
                        pass
                
                elif isinstance(message, NetworkStatsMessage):
                    # Update player ping in stats
                    if client_id in self.players and 'ping' in message.stats:
                        self.players[client_id]['ping'] = message.stats['ping']
                        self.update_players_list()
            
            @self.server.on_event(NetworkEventType.PING_UPDATE)
            def on_ping_update(event):
                client_id = event.client_id
                if client_id in self.players:
                    self.players[client_id]['ping'] = event.data.get('ping', 0)
                    self.update_players_list()
            
            # Start server
            if self.server.start():
                self.is_host = True
                self.my_id = 0  # Host is ID 0
                self.my_name = self.name_input.text.strip() or self.my_name
                
                # Add host to players list
                self.players[self.my_id] = {
                    'name': self.my_name,
                    'join_time': time.time(),
                    'ping': 0,
                    'message_count': 0
                }
                
                # Update UI
                self.update_status()
                self.update_players_list()
                self.host_btn.set_text("SERVER RUNNING")
                self.host_btn.set_background_color((0, 150, 0))
                self.disconnect_btn.enabled = True
                
                self.log_system("Server started successfully!")
                self.log_chat(f"Welcome to the chat server, {self.my_name}!")
                
                # Start stats update thread
                self.start_stats_updates()
            else:
                self.log_system("Failed to start server")
                
        except Exception as e:
            self.log_system(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def connect_as_client(self):
        """Connect to a server as a client"""
        try:
            if self.is_connected:
                self.log_system("Already connected")
                return
            
            ip = self.ip_input.text.strip() or "127.0.0.1"
            self.my_name = self.name_input.text.strip() or self.my_name
            
            self.log_system(f"Connecting to {ip}:5555 as '{self.my_name}'...")
            
            # Create client
            self.client = NetworkClient(ip, 5555)
            self.client.heartbeat_interval = 1
            self.client.max_reconnect_attempts = 3
            
            # Setup client event handlers
            @self.client.on_event(NetworkEventType.CONNECT)
            def on_connected(event):
                self.is_connected = True
                self.my_id = None  # Will be set by WelcomeMessage
                self.log_system("Connected to server!")
                
                # Update UI
                self.update_status()
                self.connect_btn.set_text("CONNECTED")
                self.connect_btn.set_background_color((0, 150, 0))
                self.disconnect_btn.enabled = True
                self.send_chat_btn.enabled = True
                
                # Start stats updates
                self.start_stats_updates()
            
            @self.client.on_event(NetworkEventType.DISCONNECT)
            def on_disconnected(event):
                self.is_connected = False
                reason = 'Unknown'
                if hasattr(event, 'data') and event.data:
                    reason = str(event.data)
                
                self.log_system(f"Disconnected: {reason}")
                self.update_status()
                
                self.connect_btn.set_text("CONNECT")
                self.connect_btn.set_background_color(None)
                self.disconnect_btn.enabled = False
                self.send_chat_btn.enabled = False
                
                # Clear players list
                self.players.clear()
                self.update_players_list()
                
                self.log_chat("Disconnected from server")
            
            @self.client.on_event(NetworkEventType.MESSAGE)
            def on_message_received(event):
                message = event.data
                self.handle_network_message(message)
            
            @self.client.on_event(NetworkEventType.PING_UPDATE)
            def on_ping_update(event):
                self.network_stats['ping'] = event.data.get('ping', 0)
                self.network_stats['latency_history'].append(self.network_stats['ping'])
                self.ping_graph_data.append(self.network_stats['ping'])
                
                # Update display if on stats tab
                if self.selected_tab == "stats":
                    self.update_stats_display()
            
            # Connect
            if self.client.connect(self.my_name):
                self.log_system("Client configured, attempting connection...")
            else:
                self.log_system("Initial connection failed")
                self.client = None
                
        except Exception as e:
            self.log_system(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def disconnect(self):
        """Disconnect from server or stop server"""
        self.log_system("Disconnecting...")
        
        if self.is_host and self.server:
            self.server.stop()
            self.server = None
            self.is_host = False
            
            # Clear players except host
            host_id = self.my_id
            self.players = {k: v for k, v in self.players.items() if k == host_id}
            
            self.log_chat("Server stopped")
        
        elif self.is_connected and self.client:
            self.client.disconnect()
            self.client = None
            self.is_connected = False
        
        # Update UI
        self.update_status()
        self.update_players_list()
        self.host_btn.set_text("START SERVER")
        self.host_btn.set_background_color(None)
        self.connect_btn.set_text("CONNECT")
        self.connect_btn.set_background_color(None)
        self.disconnect_btn.enabled = False
        self.send_chat_btn.enabled = False
        
        self.log_system("Disconnected")
    
    def request_player_list(self):
        """Request player list from server (client only)"""
        if self.client and self.is_connected:
            # Send a simple request message
            class PlayerListRequest(NetworkMessage):
                def __init__(self):
                    super().__init__()
                    self.request = "player_list"
                    self.version = 1
            
            self.client.send(PlayerListRequest())
    
    def handle_network_message(self, message):
        """Handle incoming network messages"""
        if isinstance(message, ChatMessage):
            self.display_chat_message(message)
            
        elif isinstance(message, PlayerJoinMessage):
            if message.action == 'join':
                self.players[message.player_id] = {
                    'name': message.player_name,
                    'join_time': message.timestamp,
                    'ping': 0,
                    'message_count': 0
                }
                self.log_chat(f"{message.player_name} joined the chat")
            elif message.action == 'leave':
                if message.player_id in self.players:
                    self.log_chat(f"{message.player_name} left the chat")
                    del self.players[message.player_id]
            
            self.update_players_list()
        
        elif isinstance(message, NetworkStatsMessage):
            # Update network stats from server
            if 'bandwidth' in message.stats:
                self.bandwidth_graph_data.append(message.stats['bandwidth'])
        
        elif isinstance(message, ServerInfoMessage):
            # Update server info display
            self.server_stats['max_clients'] = message.max_players
            self.update_stats_display()
        
        elif isinstance(message, WelcomeMessage):
            # Handle welcome message to get player ID
            self.my_id = message.player_id
            # Update players list from welcome message data
            if hasattr(message, 'players'):
                for player_id, player_data in message.players.items():
                    self.players[player_id] = {
                        'name': player_data.get('name', f'Player{player_id}'),
                        'join_time': time.time(),
                        'ping': player_data.get('ping', 0),
                        'message_count': 0
                    }
            self.update_players_list()
            self.log_chat(f"{self.my_name} joined the chat")
    
    def send_chat_message(self):
        """Send chat message to server"""
        if not self.is_connected and not self.is_host:
            self.log_system("Not connected to send message")
            return
        
        current_time = time.time()
        if current_time - self.last_chat_sent < self.chat_cooldown:
            return
        
        message_text = self.chat_input_box.text.strip()
        if not message_text or message_text == "Type your message...":
            return
        
        # Create chat message
        chat_msg = ChatMessage(
            sender_id=self.my_id,
            sender_name=self.my_name,
            message=message_text,
            timestamp=current_time
        )
        
        # Display message immediately for the sender
        self.display_chat_message(chat_msg)
        
        # Send message
        if self.is_host and self.server:
            # Host broadcasts to all clients except self
            self.server.broadcast(chat_msg, exclude_client_id=self.my_id)
        elif self.client and self.is_connected:
            # Client sends to server
            self.client.send(chat_msg)
        
        # Update stats
        self.network_stats['packets_sent'] += 1
        self.last_chat_sent = current_time
        
        # Clear input
        self.chat_input_box.set_text("")
        
        # Refocus input
        self.chat_input_box.has_focus = True
    
    def display_chat_message(self, chat_msg):
        """Display a chat message in the chat history"""
        # Format timestamp
        time_str = time.strftime("%H:%M:%S", time.localtime(chat_msg.timestamp))
        
        # Format message with color based on sender
        if chat_msg.sender_id == self.my_id:
            prefix = f"[{time_str}] You:"
            color = (100, 200, 255)
        elif chat_msg.sender_id == -1:  # System message
            prefix = f"[{time_str}] System:"
            color = (255, 200, 100)
        else:
            prefix = f"[{time_str}] {chat_msg.sender_name}:"
            color = (200, 200, 200)
        
        # Create TextLabel for this message
        message_label = TextLabel(10, len(self.chat_messages) * 25, 
                                 f"{prefix} {chat_msg.message}", 
                                 14, color)
        
        # Add to chat container
        self.chat_container.add_child(message_label)
        
        # Store reference and update container height
        self.chat_messages.append(message_label)
        
        # Update container height based on number of messages
        self.chat_container.height = max(400, len(self.chat_messages) * 25 + 20)
        
        # Auto-scroll to bottom
        if self.auto_scroll_chat:
            self.chat_scroll_frame.scroll_y = max(0, self.chat_container.height - self.chat_scroll_frame.height)
    
    def update_players_list(self):
        """Update the players list display"""
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
            marker = "HOST " if player_id == self.my_id else "PLAYER "
            name = player.get('name', f'Player{player_id}')
            ping = player.get('ping', 0)
            msg_count = player.get('message_count', 0)
            
            # Color code based on ping
            if ping < 50:
                ping_indicator = "LOW"
                color = (100, 255, 100)
            elif ping < 100:
                ping_indicator = "MED"
                color = (255, 255, 100)
            elif ping < 200:
                ping_indicator = "HIGH"
                color = (255, 150, 100)
            else:
                ping_indicator = "VHIGH"
                color = (255, 100, 100)
            
            # Create player label
            player_text = f"{marker}{name} | {ping_indicator} {ping}ms | MSG {msg_count}"
            player_label = TextLabel(10, y_pos, player_text, 16, color)
            self.players_container.add_child(player_label)
            
            y_pos += 25
        
        # Update container height
        self.players_container.height = max(400, y_pos + 10)
        
        # Update server stats if host
        if self.is_host:
            self.clients_label.set_text(f"Connected Clients: {len(self.players)-1}/{self.server_stats['max_clients']}")
    
    def start_stats_updates(self):
        """Start periodic statistics updates"""
        def stats_loop():
            while self.running and (self.is_connected or self.is_host):
                try:
                    self.update_network_stats()
                    time.sleep(1.0)  # Update every second
                except Exception as e:
                    print(f"Error in stats loop: {e}")
                    break
        
        if not self.stats_update_thread or not self.stats_update_thread.is_alive():
            self.stats_update_thread = threading.Thread(target=stats_loop, daemon=True)
            self.stats_update_thread.start()
    
    def update_network_stats(self):
        """Update network statistics"""
        current_time = time.time()
        
        # Update connection time
        if self.is_connected or self.is_host:
            self.network_stats['connection_time'] = current_time - self.server_stats.get('start_time', current_time)
        
        # Update server stats if host
        if self.is_host:
            self.server_stats['uptime'] = current_time - self.server_stats['start_time']
        
        # Calculate bandwidth (simulated for demo)
        if len(self.bandwidth_graph_data) > 1:
            recent_bandwidth = sum(self.bandwidth_graph_data) / len(self.bandwidth_graph_data)
            self.network_stats['bandwidth_history'].append(recent_bandwidth)
        
        # Update UI
        self.update_stats_display()
        
        # Send stats update if connected
        if self.is_connected and self.client:
            stats_msg = NetworkStatsMessage({
                'ping': self.network_stats['ping'],
                'connection_time': self.network_stats['connection_time']
            })
            self.client.send(stats_msg)
    
    def update_stats_display(self):
        """Update statistics display labels"""
        # Ping
        ping = self.network_stats['ping']
        if ping < 50:
            color = (100, 255, 100)
        elif ping < 100:
            color = (255, 255, 100)
        elif ping < 200:
            color = (255, 150, 100)
        else:
            color = (255, 100, 100)
        
        self.ping_label.set_text(f"Ping: {ping} ms")
        self.ping_label.set_text_color(color)
        
        # Packet loss (simulated)
        packet_loss = self.network_stats['packet_loss']
        self.packet_loss_label.set_text(f"Packet Loss: {packet_loss:.1f}%")
        
        # Bandwidth
        if self.network_stats['bandwidth_history']:
            avg_bandwidth = sum(self.network_stats['bandwidth_history']) / len(self.network_stats['bandwidth_history'])
            if avg_bandwidth < 1024:
                bw_text = f"Bandwidth: {avg_bandwidth:.0f} B/s"
            elif avg_bandwidth < 1024*1024:
                bw_text = f"Bandwidth: {avg_bandwidth/1024:.1f} KB/s"
            else:
                bw_text = f"Bandwidth: {avg_bandwidth/(1024*1024):.1f} MB/s"
            self.bandwidth_label.set_text(bw_text)
        
        # Connection time
        conn_time = int(self.network_stats['connection_time'])
        hours = conn_time // 3600
        minutes = (conn_time % 3600) // 60
        seconds = conn_time % 60
        
        if hours > 0:
            time_text = f"Connection Time: {hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            time_text = f"Connection Time: {minutes}m {seconds}s"
        else:
            time_text = f"Connection Time: {seconds}s"
        
        self.connection_label.set_text(time_text)
        
        # Server stats (host only)
        if self.is_host:
            uptime = int(self.server_stats['uptime'])
            uptime_hours = uptime // 3600
            uptime_minutes = (uptime % 3600) // 60
            uptime_seconds = uptime % 60
            
            if uptime_hours > 0:
                uptime_text = f"Server Uptime: {uptime_hours}h {uptime_minutes}m {uptime_seconds}s"
            elif uptime_minutes > 0:
                uptime_text = f"Server Uptime: {uptime_minutes}m {uptime_seconds}s"
            else:
                uptime_text = f"Server Uptime: {uptime_seconds}s"
            
            self.uptime_label.set_text(uptime_text)
            self.messages_label.set_text(f"Total Messages: {self.server_stats['total_messages']}")
    
    def toggle_network_graph(self):
        """Toggle network graph visibility"""
        self.show_network_graph = not self.show_network_graph
        self.graph_toggle.set_text("HIDE GRAPH" if self.show_network_graph else "SHOW GRAPH")
        self.log_system(f"Network graph {'enabled' if self.show_network_graph else 'disabled'}")
    
    def update_status(self):
        """Update connection status indicator"""
        if self.is_host:
            self.status_label.set_text("HOST SERVER")
            self.status_label.set_text_color((100, 255, 100))
            self.status_indicator.set_background_color((0, 255, 0))
        elif self.is_connected:
            self.status_label.set_text("CONNECTED")
            self.status_label.set_text_color((100, 255, 100))
            self.status_indicator.set_background_color((0, 255, 0))
        else:
            self.status_label.set_text("DISCONNECTED")
            self.status_label.set_text_color((255, 100, 100))
            self.status_indicator.set_background_color((255, 50, 50))
    
    def log_system(self, message):
        """Log system message to console and chat"""
        print(f"[SYSTEM] {message}")
    
    def log_chat(self, message):
        """Log message to chat display"""
        chat_msg = ChatMessage(
            sender_id=-1,  # System ID
            sender_name="System",
            message=message,
            timestamp=time.time()
        )
        self.display_chat_message(chat_msg)
    
    def handle_input(self, event):
        """Handle keyboard input"""
        if event.type == pygame.KEYDOWN:
            # Tab to focus chat
            if event.key == pygame.K_TAB and self.selected_tab == "chat":
                self.chat_input_box.has_focus = True
                pygame.key.set_repeat(500, 50)  # Enable key repeat for typing
                return True
            
            # Enter to send message
            elif event.key == pygame.K_RETURN and self.chat_input_active:
                self.send_chat_message()
                return True
            
            # Function keys
            elif event.key == pygame.K_F1:
                # Clear chat
                for child in list(self.chat_container.children):
                    self.chat_container.remove_child(child)
                self.chat_messages.clear()
                self.log_system("Chat cleared")
                return True
            
            elif event.key == pygame.K_F2:
                # Reset stats
                self.network_stats['latency_history'].clear()
                self.network_stats['bandwidth_history'].clear()
                self.ping_graph_data.clear()
                self.bandwidth_graph_data.clear()
                self.log_system("Statistics reset")
                return True
            
            elif event.key == pygame.K_F3:
                # Test connection
                if self.is_connected or self.is_host:
                    self.log_chat("Testing connection...")
                    # Send a test ping
                    if self.is_host and self.server:
                        self.server.broadcast(ChatMessage(-1, "System", "Connection test from host"), exclude_client_id=self.my_id)
                    elif self.client:
                        self.client.send(ChatMessage(self.my_id, self.my_name, "Connection test"))
                return True
        
        return super().handle_input(event)
    
    def update(self, dt):
        """Update scene logic"""
        # Update network stats in real-time
        if self.is_connected or self.is_host:
            # Simulate some network activity for demo
            if random.random() < 0.1:  # 10% chance per frame
                self.network_stats['packets_received'] += 1
            
            # Update graph data
            if len(self.ping_graph_data) < 100:
                self.ping_graph_data.append(self.network_stats['ping'])
    
    def render(self, renderer):
        """Render the scene"""
        # Background
        renderer.fill_screen((30, 35, 50))
        
        # Draw network graph if enabled and on stats tab
        if self.show_network_graph and self.selected_tab == "stats":
            self.render_network_graph(renderer)
        
        # Render UI elements (handled by parent class)
        super().render(renderer)
    
    def render_network_graph(self, renderer):
        """Render network statistics graph"""
        graph_x, graph_y = 400, 260
        graph_width, graph_height = 400, 200
        
        # Graph background
        renderer.draw_rect(graph_x, graph_y, graph_width, graph_height, (20, 25, 35, 200))
        renderer.draw_rect(graph_x, graph_y, graph_width, graph_height, (60, 70, 90), fill=False, border_width=1)
        
        # Graph title
        font = pygame.font.SysFont("Arial", 14, bold=True)
        title = font.render("Network Performance", True, (200, 200, 255))
        renderer.blit(title, (graph_x + graph_width//2 - title.get_width()//2, graph_y - 20))
        
        if not self.ping_graph_data:
            return
        
        # Draw grid lines
        for i in range(1, 5):
            y = graph_y + graph_height * i // 5
            renderer.draw_line(graph_x, y, graph_x + graph_width, y, (40, 45, 60, 100))
        
        # Draw ping graph
        max_ping = max(self.ping_graph_data) if self.ping_graph_data else 100
        max_ping = max(max_ping, 100)  # Ensure minimum scale
        
        points = []
        for i, ping in enumerate(self.ping_graph_data):
            x = graph_x + (i / (len(self.ping_graph_data) - 1)) * graph_width if len(self.ping_graph_data) > 1 else graph_x
            y = graph_y + graph_height - (ping / max_ping) * graph_height * 0.8
            points.append((x, y))
        
        # Draw ping line
        if len(points) > 1:
            for i in range(len(points) - 1):
                renderer.draw_line(points[i][0], points[i][1], 
                                 points[i+1][0], points[i+1][1], 
                                 (100, 200, 255, 200), width=2)
        
        # Draw current ping indicator
        if self.ping_graph_data:
            last_ping = self.ping_graph_data[-1]
            last_x = points[-1][0] if points else graph_x + graph_width
            last_y = points[-1][1] if points else graph_y + graph_height
            
            # Ping value label
            ping_font = pygame.font.SysFont("Arial", 12)
            ping_text = ping_font.render(f"{last_ping}ms", True, (100, 200, 255))
            renderer.blit(ping_text, (last_x + 5, last_y - 10))
            
            # Dot at current value
            renderer.draw_circle(last_x, last_y, 4, (100, 200, 255))
        
        # Y-axis labels
        label_font = pygame.font.SysFont("Arial", 10)
        for i in range(0, 6):
            y = graph_y + graph_height - (graph_height * i // 5)
            ping_value = (max_ping * i // 5)
            label = label_font.render(f"{ping_value}ms", True, (150, 150, 200))
            renderer.blit(label, (graph_x - 30, y - 6))
    
    def on_exit(self, next_scene: str = None):
        """Clean up resources"""
        self.running = False
        self.disconnect()


def main():
    """Main function to run the network demo"""
    engine = LunaEngine("Network Demo - Chat & Statistics", 1024, 768)
    engine.add_scene("network_demo", NetworkDemoScene)
    engine.set_scene("network_demo")
    
    print("=" * 70)
    print("NETWORK DEMO - CHAT & STATISTICS")
    print("=" * 70)
    print("FEATURES:")
    print("- Real-time chat with multiple users")
    print("- Network statistics (ping, bandwidth, packet loss)")
    print("- Player list with connection status")
    print("- Server hosting and client connection")
    print("- Visual network performance graph")
    print("=" * 70)
    print("CONTROLS:")
    print("1. HOST: Click 'START SERVER' to host")
    print("2. CLIENT: Enter IP and name, click 'CONNECT'")
    print("3. CHAT: Type in chat box, press ENTER to send")
    print("4. TABS: Switch between Chat, Stats, Players")
    print("5. KEYS: TAB (focus chat), F1 (clear), F2 (reset stats), F3 (test)")
    print("=" * 70)
    print("TIP: Open two instances to test server-client communication!")
    print("=" * 70)
    
    engine.run()


if __name__ == "__main__":
    main()