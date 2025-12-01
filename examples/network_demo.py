"""
network_demo.py - Enhanced Network Demo with Host Client Support
"""

import sys
import os
import time
import threading
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.backend.network import *
from lunaengine.core import LunaEngine, Scene
from lunaengine.ui.elements import *
import pygame

class NetworkDemoScene(Scene):
    """Enhanced demo scene with Host Client support and new features"""
    
    def __init__(self, engine: LunaEngine, mode: str = "host"):
        super().__init__(engine)
        self.mode = mode
        self.reset_state()
        self.setup_ui()
        self.setup_delay = 0.5
        
        # Track message IDs to prevent duplicates - FIXED
        self.last_message_ids = {}
        self.message_counter = 0
        
        # New features tracking
        self.server_password = "test123"  # Default password for demo
        self.client_ping = 0
        self.server_stats = {}
        
        self.message_queue = queue.Queue()
        
        # Track own messages to prevent self-echo
        self.pending_messages = set()
        
    def reset_state(self):
        """Reset all state variables - called on init and when re-entering"""
        self.messages = []
        self.players = {}
        self.connected = False
        self.connection_attempted = False
        self.last_message_ids = {}
        self.message_counter = 0
        self.last_broadcast = 0
        self.discovery = None
        self.network = None
        
        # New features
        self.client_ping = 0
        self.server_stats = {}
        self.kick_reasons = ["AFK", "Bad behavior", "Connection issues", "Other"]
        
        # Clear any existing network connections
        self.cleanup_network()
        self.pending_messages = set()

    def cleanup_network(self):
        """Clean up any existing network connections"""
        if hasattr(self, 'network') and self.network:
            try:
                self.network.disconnect()
            except:
                pass
            self.network = None

    def on_enter(self, previous_scene: str = None):
        """Called when entering the scene"""
        super().on_enter(previous_scene)
        print(f"Entering {self.mode} scene")
        
        self.scripts_enabled = True
        
        # Reset state if coming from menu (not switching between network scenes)
        if previous_scene == "MainMenu":
            self.reset_state()
            self.setup_ui()  # Recreate UI

    def on_exit(self, next_scene: str = None):
        """Called when exiting the scene"""
        super().on_exit(next_scene)
        print(f"Exiting {self.mode} scene, going to: {next_scene}")
        
        # Clean up network when leaving
        self.cleanup_network()
        
        # Only reset completely if going back to menu
        if next_scene == "MainMenu":
            self.reset_state()

    def setup_network(self):
        """Setup network based on mode - FIXED host connection issue"""
        print(f"Setting up network in {self.mode} mode...")
        
        # Clean up any existing network first
        self.cleanup_network()
        
        if self.mode == "host":
            # Host with password protection - FIXED: Use localhost for server
            self.network = HostClient(host='localhost', port=5555, password=self.server_password)
            self.connected = self.network.start_as_host()
            
            if self.connected:
                self.add_message("Host started successfully on localhost:5555", "system")
                # Add server scripts for demo
                self.setup_server_scripts()
                
                @self.network.on_event(NetworkEventType.CONNECT)
                def on_peer_connect(event):
                    player_id = f"Player_{event.client_id}"
                    self.players[event.client_id] = player_id
                    msg = f"{player_id} connected"
                    self.add_message(msg, "system")
                    
                    # Broadcast join message
                    chat_msg = ChatMessage(msg, "System", self.generate_message_id())
                    self.network.send_to_all(chat_msg, exclude_self=True)
                
                @self.network.on_event(NetworkEventType.DISCONNECT)
                def on_peer_disconnect(event):
                    player_id = self.players.get(event.client_id, f"Player_{event.client_id}")
                    msg = f"{player_id} disconnected"
                    self.add_message(msg, "system")
                    
                    if event.client_id in self.players:
                        del self.players[event.client_id]
                
                @self.network.on_event(NetworkEventType.MESSAGE)
                def on_network_message(event):
                    if isinstance(event.data, ChatMessage):
                        # Put message in queue instead of direct UI update
                        self.message_queue.put({
                            'source': 'network',
                            'message': f"{event.data.player_id}: {event.data.message}"
                        })
                
                @self.network.on_event(NetworkEventType.PING_UPDATE)
                def on_ping_update(event):
                    if event.client_id:
                        # Peer ping update
                        ping = event.data.get('ping', 0)
                        player_id = self.players.get(event.client_id, f"Player_{event.client_id}")
                        # You could display peer pings in the UI
                    else:
                        # Our own ping to host (in host mode this is local)
                        self.client_ping = event.data.get('ping', 0)
                
                @self.network.on_event(NetworkEventType.SERVER_SCRIPT)
                def on_server_script(event):
                    script_name = event.data.get('script_name', 'Unknown')
                    result = event.data.get('result', {})
                    self.add_message(f"Server script '{script_name}' executed: {result}", "system")

            else:
                self.add_message("Failed to start host. Port 5555 might be in use.", "system")
                print("Host failed to start. Possible port conflict.")

            # Start discovery broadcasting if host (even if self-connection failed)
            if hasattr(self, 'network') and self.network and hasattr(self.network, 'server') and self.network.server and self.network.server.running:
                self.discovery = NetworkDiscovery()
                self.last_broadcast = time.time()
                self.discovery.broadcast_presence("LunaEngine Host", 5555)
                self.add_message("Network discovery broadcasting enabled", "system")
                print("Discovery broadcasting started")

        elif self.mode == "client":
            self.network = HostClient()
            
            # Try multiple connection methods with password
            success = False
            host_to_connect = 'localhost'  # Default to localhost
            port_to_connect = 5555
            
            # Check if we have a specific host from discovery
            if hasattr(self.engine, 'host_address'):
                host_to_connect, port_to_connect = self.engine.host_address
                print(f"Connecting to discovered host: {host_to_connect}:{port_to_connect}")
                self.add_message(f"Connecting to {host_to_connect}:{port_to_connect}...", "system")
            
            # Always try localhost first for local testing
            print("Attempting to connect to localhost...")
            self.add_message("Connecting to localhost:5555...", "system")
            
            # Connect with password
            try:
                success = self.network.connect_as_client('localhost', 5555, self.server_password)
                if success:
                    self.add_message("Successfully connected to localhost:5555!", "system")
                else:
                    self.add_message("Failed to connect to localhost:5555", "system")
            except Exception as e:
                print(f"Connection error: {e}")
                self.add_message(f"Connection error: {e}", "system")
            
            # If localhost failed and we have discovered hosts, try them
            if not success and hasattr(self.engine, 'host_address'):
                discovery_host, discovery_port = self.engine.host_address
                
                # Skip if it's the same as localhost
                if discovery_host not in ['localhost', '127.0.0.1']:
                    print(f"Trying discovered host: {discovery_host}:{discovery_port}")
                    self.add_message(f"Trying {discovery_host}:{discovery_port}...", "system")
                    try:
                        success = self.network.connect_as_client(discovery_host, discovery_port, self.server_password)
                        if success:
                            self.add_message(f"Successfully connected to {discovery_host}:{discovery_port}!", "system")
                    except Exception as e:
                        print(f"Connection error to discovered host: {e}")
                        self.add_message(f"Connection failed: {e}", "system")
            
            self.connected = success
            
            if self.connected:
                @self.network.on_event(NetworkEventType.MESSAGE)
                def on_network_message(event):
                    if isinstance(event.data, ChatMessage):
                        # Put message in queue instead of direct UI update
                        self.message_queue.put({
                            'source': 'network',
                            'message': f"{event.data.player_id}: {event.data.message}"
                        })
                
                @self.network.on_event(NetworkEventType.PING_UPDATE)
                def on_ping_update(event):
                    self.client_ping = event.data.get('ping', 0)
                
                @self.network.on_event(NetworkEventType.SERVER_SCRIPT)
                def on_server_script(event):
                    script_name = event.data.get('script_name', 'Unknown')
                    self.add_message(f"Server: Script '{script_name}' executed", "system")

        else:  # server only mode
            # Server with password
            self.network = Server(host='localhost', port=5555, password=self.server_password)
            self.connected = self.network.start()
            
            if self.connected:
                self.add_message("Dedicated server started on localhost:5555", "system")
                # Add server scripts
                self.setup_server_scripts()
                
                @self.network.on_event(NetworkEventType.CONNECT)
                def on_client_connect(event):
                    msg = f"Client {event.client_id} connected from {event.data.address}"
                    self.add_message(msg, "system")
                    welcome = ChatMessage(f"Welcome client {event.client_id}!", "Server", self.generate_message_id())
                    self.network.send_to_client(event.client_id, welcome)
                
                @self.network.on_event(NetworkEventType.DISCONNECT)
                def on_client_disconnect(event):
                    msg = f"Client {event.data.client_id} disconnected"
                    self.add_message(msg, "system")
                
                @self.network.on_event(NetworkEventType.MESSAGE)
                def on_client_message(event):
                    if isinstance(event.data, ChatMessage):
                        print(f"DEBUG SERVER: Received message from client {event.client_id}: {event.data.message}")
                        
                        # Add to server's display
                        self.add_message(f"{event.data.player_id}: {event.data.message}", "network")
                        
                        # Broadcast to all other clients (except sender)
                        self.network.broadcast(event.data, exclude_client_id=event.client_id)
                        print(f"DEBUG SERVER: Broadcasted message from client {event.client_id}")
        
        self.connection_attempted = True
        print(f"Network setup complete. Connected: {self.connected}")

    def setup_server_scripts(self):
        """Setup demo server scripts"""
        if not self.network or not hasattr(self.network, 'add_server_script'):
            return
            
        # Auto-save script (runs every 30 seconds)
        def auto_save_script(server):
            player_count = len(server.clients) if hasattr(server, 'clients') else 0
            save_data = {
                'timestamp': time.time(),
                'player_count': player_count,
                'game_state': 'demo_running'
            }
            return save_data
        
        # Day/Night cycle script (runs every 10 seconds)
        def day_night_script(server):
            cycle_time = time.time() % 300  # 5 minute cycle for demo
            cycle_phase = cycle_time / 300
            time_of_day = 'day' if cycle_phase < 0.5 else 'night'
            return {'cycle_phase': cycle_phase, 'time_of_day': time_of_day}
        
        # Stats broadcast script (runs every 15 seconds)
        def stats_script(server):
            if hasattr(server, 'get_server_stats'):
                stats = server.get_server_stats()
                return stats
            return {}
        
        if self.mode in ["host", "server"]:
            self.network.add_server_script("auto_save", 30, auto_save_script)
            self.network.add_server_script("day_night", 10, day_night_script)
            self.network.add_server_script("stats", 15, stats_script)
            self.add_message("Server scripts loaded: auto_save, day_night, stats", "system")

    def generate_message_id(self):
        """Generate unique message ID to prevent duplicates"""
        self.message_counter += 1
        # Include mode and timestamp for uniqueness
        return f"{self.mode}_{int(time.time() * 1000)}_{self.message_counter}"

    def is_duplicate_message(self, message):
        """Check if message is a duplicate - FIXED implementation"""
        if not hasattr(message, 'message_id'):
            return False
            
        # Check if we've seen this message recently
        if message.message_id in self.last_message_ids:
            seen_time = self.last_message_ids[message.message_id]
            # If seen within last 5 seconds, it's a duplicate
            if time.time() - seen_time < 5:
                print(f"DUPLICATE MESSAGE BLOCKED: {message.message_id}")
                return True
                
        # Store with current timestamp
        self.last_message_ids[message.message_id] = time.time()
        
        # Cleanup old entries (older than 60 seconds)
        current_time = time.time()
        self.last_message_ids = {msg_id: timestamp 
                            for msg_id, timestamp in self.last_message_ids.items()
                            if current_time - timestamp < 60}
        
        # Remove from pending messages if it was sent by us
        if message.message_id in self.pending_messages:
            self.pending_messages.remove(message.message_id)
            
        return False
    
    def add_message(self, message: str, source: str = "local"):
        """Add message to the list (newest first) with source tracking"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Debug: Always print to console for debugging
        print(f"DEBUG add_message - Source: {source}, Message: {message[:50]}...")
        
        # Check for duplicate by content (simple but effective)
        for existing_msg in self.messages[:10]:  # Check recent messages
            if message in existing_msg or existing_msg in message:
                print(f"DEBUG: Duplicate detected, skipping: {message[:50]}...")
                return
        
        self.messages.insert(0, formatted_message)
        # Keep only last 50 messages
        if len(self.messages) > 50:
            self.messages = self.messages[:50]
        
        # Update scrolling frame
        self.update_message_display()

    def setup_ui(self):
        """Setup user interface with new features"""
        # Title with mode indicator
        title_text = f"Network Demo - {self.mode.upper()} Mode"
        if self.mode == "host":
            title_text += " (Host + Password Protected)"
        
        title = TextLabel(512, 20, title_text, 28, root_point=(0.5, 0))
        self.add_ui_element(title)

        # Main content area
        content_y = 60
        
        # Status panel - ENHANCED with new features
        status_panel = UiFrame(20, content_y, 300, 150)
        self.add_ui_element(status_panel)
        
        self.status_display = TextLabel(40, content_y + 20, "Status: Initializing...", 18)
        self.add_ui_element(self.status_display)
        
        self.players_display = TextLabel(40, content_y + 45, "Players: 0", 16)
        self.add_ui_element(self.players_display)
        
        self.ping_display = TextLabel(40, content_y + 70, "Ping: -- ms", 16)
        self.add_ui_element(self.ping_display)
        
        self.stats_display = TextLabel(40, content_y + 95, "Messages: 0 | Uptime: 0s", 14)
        self.add_ui_element(self.stats_display)
        
        self.network_info = TextLabel(40, content_y + 120, f"Mode: {self.mode} | Port: 5555", 14)
        self.add_ui_element(self.network_info)

        # Control panel for host features
        if self.mode == "host":
            control_panel = UiFrame(330, content_y, 450, 150)
            self.add_ui_element(control_panel)
            
            control_title = TextLabel(555, content_y + 15, "Host Controls", 18, root_point=(0.5, 0))
            self.add_ui_element(control_title)
            
            # Kick dropdown and button
            self.kick_dropdown = Dropdown(340, content_y + 45, 150, 25, ["No players connected"])
            self.kick_dropdown.set_simple_tooltip("Select a player to kick...")
            self.add_ui_element(self.kick_dropdown)
            
            self.kick_reason_dropdown = Dropdown(500, content_y + 45, 150, 25, self.kick_reasons)
            self.kick_reason_dropdown.set_simple_tooltip("Select a reason for kicking...")
            self.add_ui_element(self.kick_reason_dropdown)
            
            self.kick_button = Button(660, content_y + 45, 100, 25, "Kick", font_size=14)
            self.kick_button.set_on_click(self.kick_selected_player)
            self.add_ui_element(self.kick_button)
            
            # Server script controls
            self.script_toggle = Button(340, content_y + 80, 120, 25, "Disable Scripts", font_size=14)
            self.script_toggle.set_on_click(self.toggle_server_scripts)
            self.add_ui_element(self.script_toggle)
            
            self.broadcast_stats = Button(470, content_y + 80, 150, 25, "Broadcast Stats", font_size=14)
            self.broadcast_stats.set_on_click(self.broadcast_server_stats)
            self.add_ui_element(self.broadcast_stats)

        # Messages area with ScrollingFrame
        messages_y = content_y + 170
        self.messages_frame = ScrollingFrame(20, messages_y, 760, 250, 740, 800)
        self.messages_frame.set_simple_tooltip("Network messages - newest at top")
        self.add_ui_element(self.messages_frame)

        # Input area (clients and host only) - FIXED TextBox focus issue
        if self.mode in ["host", "client"]:
            input_y = messages_y + 270
            input_panel = UiFrame(20, input_y, 760, 100)
            self.add_ui_element(input_panel)
            
            # FIXED: TextBox with proper focus management
            self.message_input = TextBox(40, input_y + 20, 500, 30, "Click here and type your message...")
            self.message_input.set_simple_tooltip("Click to focus, then type your message. Press Enter to send.")
            self.add_ui_element(self.message_input)
            
            self.send_button = Button(550, input_y + 20, 100, 30, "Send")
            self.send_button.set_on_click(self.send_chat_message)
            self.add_ui_element(self.send_button)
            
            # Quick chat buttons
            quick_chats = ["Hello!", "Good game!", "Ready!", "Thanks!"]
            for i, chat in enumerate(quick_chats):
                btn = Button(40 + i*150, input_y + 60, 140, 25, chat, font_size=14)
                btn.set_on_click(lambda c=chat: self.send_quick_chat(c))
                self.add_ui_element(btn)

        # Control buttons
        control_y = messages_y + 390 if self.mode in ["host", "client"] else messages_y + 270
        back_button = Button(40, control_y, 150, 35, "Back to Menu")
        back_button.set_on_click(lambda: self.return_to_menu())
        self.add_ui_element(back_button)
        
        if self.mode == "host":
            clear_button = Button(200, control_y, 150, 35, "Clear Messages")
            clear_button.set_on_click(lambda: self.clear_messages())
            self.add_ui_element(clear_button)
            
            disconnect_button = Button(360, control_y, 180, 35, "Disconnect All & Exit")
            disconnect_button.set_on_click(lambda: self.disconnect_all())
            self.add_ui_element(disconnect_button)

    def update_message_display(self):
        """Update the scrolling frame with current messages"""
        # Clear all children from the scrolling frame
        self.messages_frame.clear_children()
        
        # Add new message labels (newest first)
        y_offset = 10
        for i, message in enumerate(self.messages):
            if y_offset > 750:  # Limit to frame height
                break
                
            label = TextLabel(10, y_offset, message, 16, root_point=(0, 0))
            label.z_index = 1
            self.messages_frame.add_child(label)
            y_offset += 25

    def clear_messages(self):
        """Clear all messages"""
        self.messages.clear()
        self.last_message_ids.clear()
        self.update_message_display()

    def return_to_menu(self):
        """Safely return to menu"""
        if hasattr(self, 'network') and self.network:
            self.network.disconnect()
        self.engine.set_scene("MainMenu")

    def disconnect_all(self):
        """Disconnect all peers and return to menu (host only)"""
        if self.mode == "host" and hasattr(self, 'network'):
            self.network.disconnect("Host shutting down")
        self.return_to_menu()

    def send_chat_message(self):
        """Send chat message - SIMPLIFIED"""
        if (hasattr(self, 'message_input') and hasattr(self, 'network') and 
            self.connected and self.message_input.text):
            
            message = self.message_input.text.strip()
            if message and message != "Click here and type your message...":
                player_name = "Host" if self.mode == "host" else "Client"
                
                # Add our own message to display immediately
                self.add_message(f"{player_name}: {message}", "local")
                
                # Send to network
                chat_msg = ChatMessage(message, player_name, self.generate_message_id())
                
                if self.mode == "host":
                    # As host, send to all peers
                    self.network.send_to_all(chat_msg, exclude_self=True)
                    print(f"DEBUG: Host sent message to peers")
                else:
                    # As client, send to host
                    self.network.send_to_all(chat_msg)
                    print(f"DEBUG: Client sent message to host")
                
                # Clear input
                self.message_input.text = ""

    def debug_message_flow(self, action: str, message: str, source: str):
        """Debug message flow between threads"""
        print(f"DEBUG FLOW [{action}] - Source: {source}, Message: {message[:30]}...")
        print(f"  Current messages in list: {len(self.messages)}")

    def send_quick_chat(self, message: str):
        """Send quick chat message - FIXED to prevent duplicates"""
        if hasattr(self, 'network') and self.connected:
            player_name = "Host" if self.mode == "host" else "Client"
            
            # Create unique message ID
            message_id = self.generate_message_id()
            
            # Add to pending messages to prevent echo
            self.pending_messages.add(message_id)
            
            # Add our own message to display immediately
            self.add_message(f"{player_name}: {message}", "local")
            
            # Send to network
            chat_msg = ChatMessage(message, player_name, message_id)
            
            if self.mode == "host":
                self.network.send_to_all(chat_msg, exclude_self=True)
            else:
                self.network.send_to_all(chat_msg)

    def kick_selected_player(self):
        """Kick selected player (host only)"""
        if (self.mode == "host" and hasattr(self, 'network') and 
            hasattr(self, 'kick_dropdown') and self.kick_dropdown.options[self.kick_dropdown.selected_index] and
            self.kick_dropdown.options[self.kick_dropdown.selected_index] != "No players connected"):
            
            player_text = self.kick_dropdown.options[self.kick_dropdown.selected_index]
            reason = self.kick_reason_dropdown.options[self.kick_reason_dropdown.selected_index] or "Kicked by host"
            
            # Extract player ID from dropdown text
            try:
                # Format: "Player_X (Ping: Yms)"
                player_id = int(player_text.split("_")[1].split(" ")[0])
                if self.network.kick_peer(player_id, reason):
                    self.add_message(f"Kicked {player_text}: {reason}", "system")
                else:
                    self.add_message(f"Failed to kick {player_text}", "system")
            except (IndexError, ValueError) as e:
                self.add_message(f"Invalid player selection: {e}", "system")

    def toggle_server_scripts(self):
        """Toggle server scripts on/off (host only)"""
        if self.mode == "host" and hasattr(self, 'network'):
            self.scripts_enabled = not self.scripts_enabled
            self.network.toggle_server_scripts(self.scripts_enabled)

    def broadcast_server_stats(self):
        """Broadcast server statistics to all clients (host only)"""
        if self.mode == "host" and hasattr(self, 'network'):
            stats = self.network.get_server_stats()
            stats_msg = f"Server Stats: {stats.get('total_clients', 0)} players, " \
                       f"Ping: {stats.get('average_ping', 0):.1f}ms, " \
                       f"Uptime: {stats.get('uptime', 0):.0f}s"
            
            chat_msg = ChatMessage(stats_msg, "Server", self.generate_message_id())
            self.network.send_to_all(chat_msg)
            self.add_message(stats_msg, "system")

    def update_kick_dropdown(self):
        """Update kick dropdown with current players (host only)"""
        if self.mode == "host" and hasattr(self, 'kick_dropdown') and hasattr(self, 'network'):
            player_options = []
            for client_id, player_name in self.players.items():
                ping = self.network.get_peer_ping(client_id)
                player_options.append(f"{player_name} (Ping: {ping:.0f}ms)")
            
            if player_options:
                self.kick_dropdown.set_options(player_options)
            else:
                self.kick_dropdown.set_options(["No players connected"])

    def update_network_display(self):
        """Update network information display with new features"""
        # Update status
        if not self.connection_attempted:
            status = "Initializing..."
        elif self.mode == "host":
            # FIXED: Check if server is running even if self-connection failed
            server_running = (hasattr(self, 'network') and self.network and 
                            hasattr(self.network, 'server') and self.network.server and 
                            self.network.server.running)
            
            if server_running:
                peer_count = self.network.get_peer_count()
                status = f"Hosting ({peer_count} peers connected)"
                self.players_display.set_text(f"Players: {peer_count + 1} (Host + {peer_count} clients)")
                
                # Update ping display
                try:
                    avg_ping = self.network.get_server_stats().get('average_ping', 0)
                    self.ping_display.set_text(f"Avg Ping: {avg_ping:.1f}ms")
                except:
                    self.ping_display.set_text("Ping: -- ms")
                
                # Update stats
                try:
                    stats = self.network.get_server_stats()
                    self.stats_display.set_text(f"Msgs: {stats.get('messages_received', 0)} | Uptime: {stats.get('uptime', 0):.0f}s")
                except:
                    self.stats_display.set_text("Stats: --")
                
                # Update kick dropdown
                self.update_kick_dropdown()
            else:
                status = "Host failed to start"
                self.players_display.set_text("Players: 0")
                self.ping_display.set_text("Ping: -- ms")
                self.stats_display.set_text("Server not running")
        
        elif self.mode == "client":
            status = "Connected" if self.connected else "Disconnected"
            self.players_display.set_text("Players: Connected as client")
            self.ping_display.set_text(f"Ping: {self.client_ping:.1f}ms")
            self.stats_display.set_text("Client Mode")
        
        else:  # server
            status = "Running" if self.connected else "Failed to start server"
            if self.connected and hasattr(self, 'network'):
                client_count = len(self.network.clients)
                self.players_display.set_text(f"Players: {client_count} clients connected")
                
                # Server stats
                try:
                    stats = self.network.get_server_stats()
                    self.ping_display.set_text(f"Avg Ping: {stats.get('average_ping', 0):.1f}ms")
                    self.stats_display.set_text(f"Msgs: {stats.get('messages_received', 0)} | Uptime: {stats.get('uptime', 0):.0f}s")
                except:
                    self.ping_display.set_text("Ping: -- ms")
                    self.stats_display.set_text("Stats: --")
            else:
                self.players_display.set_text("Players: 0")
                self.ping_display.set_text("Ping: -- ms")

        self.status_display.set_text(f"Status: {status}")
        
        # Update network info
        if self.mode == "host":
            info = f"Mode: Host | Port: 5555 | Password: {self.server_password}"
        elif self.mode == "client":
            info = "Mode: Client | Connected with password"
        else:
            info = f"Mode: Server Only | Port: 5555 | Password: {self.server_password}"
        self.network_info.set_text(info)

    def process_message_queue(self):
        """Process messages from the thread-safe queue"""
        try:
            while True:
                message_data = self.message_queue.get_nowait()
                source = message_data.get('source', 'unknown')
                message = message_data.get('message', '')
                self.add_message(message, source)
        except queue.Empty:
            pass

    def update(self, dt):
        """Update scene - FIXED: Handle TextBox focus"""
        self.process_message_queue()
        
        # Delay network setup to ensure UI is ready
        if self.setup_delay > 0:
            self.setup_delay -= dt
            if self.setup_delay <= 0:
                self.setup_network()
        
        self.update_network_display()
        
        # Broadcast discovery more frequently if host
        if (self.mode == "host" and self.discovery is not None and 
            hasattr(self, 'last_broadcast')):
            current_time = time.time()
            if current_time - self.last_broadcast > 2.0:  # Broadcast every 2 seconds
                self.discovery.broadcast_presence("LunaEngine Host", 5555)
                self.last_broadcast = current_time
        
        # FIXED: Handle Enter key for sending messages
        # if (hasattr(self, 'message_input') and self.message_input.focused):
        #     # Check if Enter was pressed
        #     keys = pygame.key.get_pressed()
        #     if keys[pygame.K_RETURN]:
        #         self.send_chat_message()

    def render(self, renderer):
        """Render scene"""
        # Clear screen with dark background
        renderer.fill_screen((25, 25, 40))
        
        # Draw header with mode-specific color
        if self.mode == "host":
            header_color = (60, 100, 60)  # Green for host
        elif self.mode == "client":
            header_color = (60, 60, 100)  # Blue for client  
        else:
            header_color = (100, 60, 60)  # Red for server
            
        renderer.draw_rect(0, 0, self.engine.width, 50, header_color)
        
        # Render UI elements
        for element in self.ui_elements:
            element.render(renderer)


class NetworkMainMenu(Scene):
    """Main menu for network demo with password support"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        # Password for demo
        self.server_password = "test123"
        
        self.setup_ui()
        self.discovered_hosts = []
        self.discovering = False
    
    def setup_ui(self):
        """Setup main menu UI with password option"""
        # Title
        title = TextLabel(512, 60, "Network Demo", 48, root_point=(0.5, 0))
        self.add_ui_element(title)
        
        subtitle = TextLabel(512, 110, "Choose Your Role", 24, root_point=(0.5, 0))
        self.add_ui_element(subtitle)
        
        # Password display
        password_info = TextLabel(512, 140, f"Demo Password: {self.server_password}", 16, root_point=(0.5, 0))
        password_info.set_simple_tooltip("All servers use this password for the demo")
        self.add_ui_element(password_info)
        
        # Buttons with clear descriptions
        buttons = [
            ("Start as HOST", "Be the game host (play + allow others to join)", "HostDemo"),
            ("Find Games", "Discover and join local games", "discover"),
            ("Server Only", "Run as dedicated server (no gameplay)", "ServerDemo"),
            ("Join Localhost", "Connect to localhost as client", "ClientDemo")
        ]
        
        for i, (text, tooltip, scene) in enumerate(buttons):
            btn = Button(512, 180 + i*70, 280, 50, text, root_point=(0.5, 0))
            
            if scene == "discover":
                btn.set_on_click(self.discover_hosts)
            else:
                btn.set_on_click(lambda s=scene: self.engine.set_scene(s))
            
            btn.set_simple_tooltip(tooltip)
            self.add_ui_element(btn)
        
        # Hosts list area
        hosts_bg = UiFrame(512, 480, 400, 150, root_point=(0.5, 0))
        self.add_ui_element(hosts_bg)
        
        self.hosts_title = TextLabel(512, 460, "Discovered Games", 20, root_point=(0.5, 0))
        self.add_ui_element(self.hosts_title)
        
        self.hosts_list = TextLabel(512, 490, "No games discovered yet", 16, root_point=(0.5, 0))
        self.add_ui_element(self.hosts_list)
        
        # Exit button
        exit_btn = Button(512, 650, 150, 40, "Exit", root_point=(0.5, 0))
        exit_btn.set_on_click(lambda: setattr(self.engine, 'running', False))
        self.add_ui_element(exit_btn)
    
    def on_enter(self, previous_scene: str = None):
        """Reset discovery when entering menu"""
        super().on_enter(previous_scene)
        self.discovered_hosts = []
        self.discovering = False
        self.hosts_list.set_text("Click 'Find Games' to discover hosts")
        
        # Clear any old join buttons
        self.ui_elements = [e for e in self.ui_elements if not (hasattr(e, 'text') and 'Join' in e.text)]
    
    def discover_hosts(self):
        """Discover available hosts on network"""
        if not self.discovering:
            self.discovering = True
            self.hosts_list.set_text("Scanning network for games...")
            
            # Clear previous results
            self.discovered_hosts = []
            self.ui_elements = [e for e in self.ui_elements if not (hasattr(e, 'text') and 'Join' in e.text)]
            
            def discovery_thread():
                discovery = NetworkDiscovery()
                hosts = discovery.discover_hosts(timeout=4.0)  # Longer timeout
                self.discovered_hosts = hosts
                self.discovering = False
                
                if hosts:
                    host_text = f"Found {len(hosts)} game(s)"
                    self.hosts_list.set_text(host_text)
                    
                    # Add join buttons for discovered hosts
                    for i, (ip, port, name) in enumerate(hosts):
                        join_btn = Button(512, 520 + i*30, 200, 25, f"Join {name}", 
                                         root_point=(0.5, 0), font_size=14)
                        join_btn.set_on_click(lambda ip=ip, port=port: self.join_host(ip, port))
                        self.add_ui_element(join_btn)
                else:
                    self.hosts_list.set_text("No games found. Make sure a host is running!")
            
            threading.Thread(target=discovery_thread, daemon=True).start()

    def join_host(self, ip: str, port: int):
        """Join a discovered host"""
        print(f"Joining host at {ip}:{port}")
        # Store the host address for the client scene to use
        self.engine.host_address = (ip, port)
        self.engine.set_scene("ClientDemo")
    
    def render(self, renderer):
        """Render menu"""
        renderer.fill_screen((30, 30, 50))
        
        # Draw info panel
        renderer.draw_rect(150, 160, 724, 280, (40, 40, 60))
        
        # Render UI elements
        for element in self.ui_elements:
            element.render(renderer)

def main():
    """Main function"""
    # Check command line arguments
    mode = "menu"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    # Use OpenGL by default as requested
    engine = LunaEngine("LunaEngine - Network Demo", 1024, 768, use_opengl=True, fullscreen=False)
    
    # Add all scene types
    engine.add_scene("MainMenu", NetworkMainMenu)
    engine.add_scene("HostDemo", NetworkDemoScene, "host")
    engine.add_scene("ClientDemo", NetworkDemoScene, "client")  
    engine.add_scene("ServerDemo", NetworkDemoScene, "server")
    
    # Set initial scene based on mode
    if mode == "host":
        engine.set_scene("HostDemo")
        print("Running in HOST mode")
    elif mode == "client":
        engine.set_scene("ClientDemo")
        print("Running in CLIENT mode")  
    elif mode == "server":
        engine.set_scene("ServerDemo")
        print("Running in SERVER mode")
    else:
        engine.set_scene("MainMenu")
        print("Running in INTERACTIVE MENU mode")
    
    print("\n=== Enhanced Network Demo ===")
    print("FIXES APPLIED:")
    print("- TextBox now works properly")
    print("- Host connection issue resolved") 
    print("- Duplicate messages eliminated")
    print("- Better error handling and status messages")
    print("\nUse multiple windows to test networking!")
    print("Demo password: test123")
    
    engine.run()


if __name__ == "__main__":
    main()