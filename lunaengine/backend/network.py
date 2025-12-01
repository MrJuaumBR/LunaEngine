"""
lunaengine.backend.network module

DESCRIPTION:
Enhanced networking system with Host Client support - allowing a client to also
act as a server for peer-to-peer multiplayer games.

NEW FEATURES:
- HostClient class that combines server and client functionality
- Automatic port forwarding handling
- Local network discovery
- Seamless migration between client and host modes
- Server password protection
- Ping/latency measurement
- Client kick functionality
- Server script callbacks for automated tasks
"""

import pickle
import socket
import threading
import time
import queue
from typing import List, Dict, Callable, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class NetworkEventType(Enum):
    """Types of network events"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    MESSAGE = "message"
    ERROR = "error"
    PING_UPDATE = "ping_update"
    SERVER_SCRIPT = "server_script"


@dataclass
class NetworkEvent:
    """Network event container"""
    event_type: NetworkEventType
    data: Any
    client_id: Optional[int] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class NetworkMessage:
    """
    Base class for network messages with serialization capabilities
    """
    def to_bytes(self) -> bytes:
        """Convert message to bytes for transmission"""
        return pickle.dumps(self)
    
    @classmethod
    def from_bytes(cls, data: bytes):
        """Create message from bytes"""
        try:
            return pickle.loads(data)
        except Exception as e:
            print(f"Error deserializing message: {e}")
            return None


@dataclass
class ClientInfo:
    """Client information container with enhanced tracking"""
    client_id: int
    address: tuple
    username: str = "Unknown"
    connected: bool = False
    last_heartbeat: float = 0
    ping: float = 0
    last_ping_time: float = 0
    join_time: float = None

    def __post_init__(self):
        if self.join_time is None:
            self.join_time = time.time()


class Client(NetworkMessage):
    """
    Represents a connected client in the network system with ping tracking
    """
    def __init__(self, client_id: int, address: tuple, username: str = "Unknown"):
        self.client_id = client_id
        self.address = address
        self.username = username
        self.connected = True
        self.last_heartbeat = time.time()
        self.ping = 0
        self.last_ping_time = 0
        self.join_time = time.time()
        self.socket = None
    
    def update_heartbeat(self):
        """Update the last heartbeat time"""
        self.last_heartbeat = time.time()
    
    def update_ping(self, ping: float):
        """Update client ping"""
        self.ping = ping
        self.last_ping_time = time.time()
    
    def is_timeout(self, timeout_seconds: float = 30) -> bool:
        """Check if client has timed out"""
        return time.time() - self.last_heartbeat > timeout_seconds


class ServerScript:
    """
    Server script for automated tasks like auto-save, day/night cycle, etc.
    """
    def __init__(self, name: str, interval: float, callback: Callable, 
                 enabled: bool = True, one_shot: bool = False):
        self.name = name
        self.interval = interval
        self.callback = callback
        self.enabled = enabled
        self.one_shot = one_shot
        self.last_execution = 0
        self.execution_count = 0
    
    def should_execute(self) -> bool:
        """Check if script should execute based on interval"""
        if not self.enabled:
            return False
        
        current_time = time.time()
        if current_time - self.last_execution >= self.interval:
            self.last_execution = current_time
            self.execution_count += 1
            return True
        return False
    
    def execute(self, server: 'Server', *args, **kwargs):
        """Execute the script callback"""
        if self.enabled and self.should_execute():
            try:
                result = self.callback(server, *args, **kwargs)
                if self.one_shot:
                    self.enabled = False
                return result
            except Exception as e:
                print(f"Error executing server script '{self.name}': {e}")
                return None


class Server:
    """
    Network server for handling multiple client connections with enhanced features
    
    Parameters:
        host: Server host address (default: 'localhost')
        port: Server port (default: 5555)
        max_clients: Maximum number of simultaneous clients (default: 8)
        password[Optional]: Optional password for client authentication (default: None)
    """
    
    def __init__(self, host: str = 'localhost', port: int = 5555, 
                 max_clients: int = 8, password: str = None):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.password = password
        self.clients: Dict[int, Client] = {}
        self.client_sockets: Dict[int, socket.socket] = {}
        self.running = False
        self.server_socket = None
        self.client_counter = 0
        self.event_queue = queue.Queue()
        self.event_handlers: Dict[NetworkEventType, List[Callable]] = {}
        
        # Threading
        self.accept_thread = None
        self.process_thread = None
        self.scripts_thread = None
        
        # Server settings
        self.heartbeat_interval = 10  # seconds
        self.timeout_threshold = 30   # seconds
        
        # Server scripts for automated tasks
        self.scripts: Dict[str, ServerScript] = {}
        self.scripts_running: Dict[str, bool] = {}
        
        # Performance tracking
        self.start_time = time.time()
        self.total_messages_sent = 0
        self.total_messages_received = 0
        
        # Graceful shutdown control
        self._shutting_down = False
        self._shutdown_reason = "Server shutdown"
    
    def toggle_scripts_execution(self, enabled: bool, key:str=None):
        """
        Enable or disable server scripts execution
        
        Args:
            enabled: Whether to enable or disable scripts
            key: Specific script name to toggle, if None toggles all scripts
        """
        if key:
            if key in self.scripts:
                self.scripts[key].enabled = enabled
                status = "enabled" if enabled else "disabled"
                print(f"Server script '{key}' {status}")
        else:
            for script in self.scripts.values():
                script.enabled = enabled
            status = "enabled" if enabled else "disabled"
            print(f"All server scripts {status}")
    
    def disconnect_client(self, client_id: int, reason: str = "Disconnected by server", 
                         send_message: bool = True):
        """
        Gracefully disconnect a specific client
        
        Args:
            client_id: ID of client to disconnect
            reason: Reason for disconnection
            send_message: Whether to send a disconnect message to the client
        """
        if client_id in self.client_sockets:
            try:
                if send_message:
                    # Send graceful disconnect message
                    disconnect_msg = KickMessage(reason=reason)
                    self.client_sockets[client_id].send(disconnect_msg.to_bytes())
                    self.total_messages_sent += 1
                    time.sleep(0.1)  # Give time for message to be sent
            except:
                pass  # Client might already be disconnected
            
            # Close the connection
            self.client_sockets[client_id].close()
            
            # Remove from tracking
            if client_id in self.client_sockets:
                del self.client_sockets[client_id]
            
            self._disconnect_client(client_id)
            print(f"Disconnected client {client_id}: {reason}")
            return True
        return False
    
    def disconnect(self, reason: str = "Server shutdown", delay: float = 2.0):
        """
        Disconnect all clients and shutdown the server gracefully
        
        Args:
            reason: Reason for disconnection
            delay: Time to wait before forcing shutdown
        """
        self.graceful_shutdown(reason, delay)
        self.stop()
    
    def graceful_shutdown(self, reason: str = "Server shutdown", delay: float = 2.0):
        """
        Gracefully shutdown the server, notifying all clients first
        
        Args:
            reason: Reason for shutdown
            delay: Time to wait before forcing shutdown
        """
        if self._shutting_down:
            return
            
        self._shutting_down = True
        self._shutdown_reason = reason
        
        print(f"Starting graceful server shutdown: {reason}")
        
        # Notify all clients about impending shutdown
        shutdown_msg = ServerShutdownMessage(reason=reason, graceful=True)
        self.broadcast(shutdown_msg)
        
        # Give clients time to process the shutdown message
        print(f"Waiting {delay} seconds for clients to process shutdown...")
        time.sleep(delay)
        
        # Disconnect all clients gracefully
        client_ids = list(self.client_sockets.keys())
        for client_id in client_ids:
            self.disconnect_client(client_id, reason, send_message=False)
        
        # Stop the server
        self.stop()
        
        print("Server shutdown complete")
    
    def emergency_shutdown(self, reason: str = "Server emergency shutdown"):
        """
        Immediately shutdown the server without notifying clients
        """
        print(f"EMERGENCY SERVER SHUTDOWN: {reason}")
        self._shutting_down = True
        self._shutdown_reason = reason
        self.stop()
    
    def start(self):
        """Start the server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            self.server_socket.settimeout(1.0)  # Non-blocking with timeout
            
            self.running = True
            
            # Start threads
            self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.process_thread = threading.Thread(target=self._process_events, daemon=True)
            self.scripts_thread = threading.Thread(target=self._run_scripts, daemon=True)
            
            self.accept_thread.start()
            self.process_thread.start()
            self.scripts_thread.start()
            
            print(f"Server started on {self.host}:{self.port} (Password: {'Yes' if self.password else 'No'})")
            return True
            
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the server"""
        self.running = False
        
        # Close all client connections
        for client_id, client_socket in self.client_sockets.items():
            try:
                client_socket.close()
            except:
                pass
        
        if self.server_socket:
            self.server_socket.close()
        
        print("Server stopped")
    
    def add_script(self, name: str, interval: float, callback: Callable, 
                   enabled: bool = True, one_shot: bool = False):
        """
        Add a server script for automated tasks
        
        Args:
            name: Unique name for the script
            interval: Execution interval in seconds
            callback: Function to call (will receive server instance as first argument)
            enabled: Whether the script is enabled
            one_shot: If True, script will only run once
        """
        self.scripts[name] = ServerScript(name, interval, callback, enabled, one_shot)
        print(f"Added server script: {name} (interval: {interval}s)")
    
    def remove_script(self, name: str):
        """Remove a server script"""
        if name in self.scripts:
            del self.scripts[name]
            print(f"Removed server script: {name}")
    
    def enable_script(self, name: str):
        """Enable a server script"""
        if name in self.scripts:
            self.scripts[name].enabled = True
    
    def disable_script(self, name: str):
        """Disable a server script"""
        if name in self.scripts:
            self.scripts[name].enabled = False
    
    def _run_scripts(self):
        """Execute server scripts at their intervals"""
        while self.running:
            try:
                for script in self.scripts.values():
                    result = script.execute(self)
                    if result is not None:
                        # Queue script result as event
                        self._queue_event(NetworkEventType.SERVER_SCRIPT, {
                            'script_name': script.name,
                            'result': result,
                            'execution_count': script.execution_count
                        })
                
                time.sleep(0.1)  # Small sleep to prevent busy waiting
            except Exception as e:
                print(f"Error in script execution: {e}")
    
    def _accept_connections(self):
        """Accept incoming client connections with password verification"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_socket.settimeout(1.0)
                
                # Check if we have room for more clients
                current_clients = len(self.clients)
                if current_clients >= self.max_clients:
                    print(f"Max clients reached ({self.max_clients}), rejecting connection from {address}")
                    client_socket.close()
                    continue
                
                # Handle password authentication
                if self.password:
                    try:
                        # Wait for auth message
                        auth_data = client_socket.recv(256)
                        auth_msg = NetworkMessage.from_bytes(auth_data)
                        
                        if not isinstance(auth_msg, AuthMessage) or auth_msg.password != self.password:
                            # Send rejection and close connection
                            rejection = AuthResultMessage(success=False, reason="Invalid password")
                            client_socket.send(rejection.to_bytes())
                            client_socket.close()
                            print(f"Rejected connection from {address} - invalid password")
                            continue
                        
                        # Send success
                        success = AuthResultMessage(success=True)
                        client_socket.send(success.to_bytes())
                        
                    except Exception as e:
                        print(f"Authentication error with {address}: {e}")
                        client_socket.close()
                        continue
                
                # Create new client
                self.client_counter += 1
                client_id = self.client_counter
                
                client = Client(client_id, address)
                self.clients[client_id] = client
                self.client_sockets[client_id] = client_socket
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, client),
                    daemon=True
                )
                client_thread.start()
                
                # Notify about new connection
                self._queue_event(NetworkEventType.CONNECT, client, client_id)
                print(f"Client {client_id} connected from {address}. Total clients: {len(self.clients)}")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client: Client):
        """
        Handle communication with a single client with ping measurement
        
        Parameters:
            client_socket: Socket connected to the client
            client: Client instance representing the connected client
        """
        try:
            while self.running and client.connected and not self._shutting_down:
                try:
                    # Receive data
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    self.total_messages_received += 1
                    
                    # Parse message
                    message = NetworkMessage.from_bytes(data)
                    if message is None:
                        continue
                    
                    # Handle heartbeat
                    if isinstance(message, HeartbeatMessage):
                        client.update_heartbeat()
                        # Calculate ping
                        if hasattr(message, 'send_time'):
                            ping = (time.time() - message.send_time) * 1000  # Convert to ms
                            client.update_ping(ping)
                            
                            # Queue ping update event
                            self._queue_event(NetworkEventType.PING_UPDATE, {
                                'client_id': client.client_id,
                                'ping': ping,
                                'address': client.address
                            })
                        
                        # Send heartbeat response
                        response = HeartbeatMessage()
                        response.send_time = time.time()
                        client_socket.send(response.to_bytes())
                        self.total_messages_sent += 1
                        continue
                    
                    # Queue message for processing
                    self._queue_event(NetworkEventType.MESSAGE, message, client.client_id)
                    
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
                except Exception as e:
                    if not self._shutting_down:  # Only log errors if not during shutdown
                        print(f"Error handling client {client.client_id}: {e}")
                    break
        
        except Exception as e:
            if not self._shutting_down:  # Only log errors if not during shutdown
                print(f"Client handler error: {e}")
        finally:
            if not self._shutting_down:  # Only cleanup if this is an unexpected disconnect
                client_socket.close()
                if client.client_id in self.client_sockets:
                    del self.client_sockets[client.client_id]
                self._disconnect_client(client.client_id)
    
    def _disconnect_client(self, client_id: int):
        """Disconnect a client"""
        if client_id in self.clients:
            client = self.clients[client_id]
            client.connected = False
            del self.clients[client_id]
            self._queue_event(NetworkEventType.DISCONNECT, client, client_id)
            print(f"Client {client_id} disconnected")
    
    def kick_client(self, client_id: int, reason: str = "Kicked by server"):
        """
        Kick a client from the server
        
        Args:
            client_id: ID of client to kick
            reason: Reason for kicking (sent to client)
        """
        if client_id in self.client_sockets:
            try:
                # Send kick message
                kick_msg = KickMessage(reason=reason)
                self.client_sockets[client_id].send(kick_msg.to_bytes())
                self.total_messages_sent += 1
            except:
                pass
            
            # Close connection
            self.client_sockets[client_id].close()
            self._disconnect_client(client_id)
            print(f"Kicked client {client_id}: {reason}")
            return True
        return False
    
    def get_client_ping(self, client_id: int) -> float:
        """Get ping of a specific client in milliseconds"""
        if client_id in self.clients:
            return self.clients[client_id].ping
        return -1
    
    def get_average_ping(self) -> float:
        """Get average ping of all connected clients"""
        if not self.clients:
            return 0
        
        total_ping = sum(client.ping for client in self.clients.values())
        return total_ping / len(self.clients)
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            'uptime': time.time() - self.start_time,
            'total_clients': len(self.clients),
            'max_clients': self.max_clients,
            'messages_sent': self.total_messages_sent,
            'messages_received': self.total_messages_received,
            'average_ping': self.get_average_ping(),
            'active_scripts': len([s for s in self.scripts.values() if s.enabled])
        }
    
    def _queue_event(self, event_type: NetworkEventType, data: Any, client_id: int = None):
        """Add event to processing queue"""
        event = NetworkEvent(event_type, data, client_id)
        self.event_queue.put(event)
    
    def _process_events(self):
        """Process queued events"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1.0)
                self._handle_event(event)
            except queue.Empty:
                self._check_timeouts()
                continue
    
    def _handle_event(self, event: NetworkEvent):
        """Handle a network event"""
        # Call registered handlers
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    def _check_timeouts(self):
        """Check for timed out clients"""
        current_time = time.time()
        timed_out_clients = []
        
        for client_id, client in self.clients.items():
            if client.is_timeout(self.timeout_threshold):
                timed_out_clients.append(client_id)
        
        for client_id in timed_out_clients:
            print(f"Client {client_id} timed out")
            self._disconnect_client(client_id)
    
    def broadcast(self, message: NetworkMessage, exclude_client_id: int = None):
        """Broadcast message to all connected clients"""
        for client_id, client_socket in self.client_sockets.items():
            if client_id == exclude_client_id:
                continue
                
            # Additional check: skip if this message has a sender_id that matches the client
            if hasattr(message, 'sender_id') and message.sender_id == client_id:
                continue
                
            try:
                data = message.to_bytes()
                client_socket.send(data)
                self.total_messages_sent += 1
            except Exception as e:
                print(f"Error sending to client {client_id}: {e}")
                self._disconnect_client(client_id)
    
    def send_to_client(self, client_id: int, message: NetworkMessage):
        """Send message to specific client"""
        if client_id in self.client_sockets:
            try:
                data = message.to_bytes()
                self.client_sockets[client_id].send(data)
                self.total_messages_sent += 1
            except Exception as e:
                print(f"Error sending to client {client_id}: {e}")
                self._disconnect_client(client_id)
    
    def on_event(self, event_type: NetworkEventType):
        """Decorator to register event handlers"""
        def decorator(func):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func
        return decorator


class NetworkClient:
    """
    Network client for connecting to server with enhanced features
    """
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 5555):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        self.running = False
        self.client_id = None
        self.ping = 0
        self.last_ping_time = 0
        
        self.event_queue = queue.Queue()
        self.event_handlers: Dict[NetworkEventType, List[Callable]] = {}
        
        # Threading
        self.receive_thread = None
        self.process_thread = None
        self.heartbeat_thread = None
        
        # Connection settings
        self.heartbeat_interval = 5  # seconds
        
        # Server shutdown handling
        self._server_shutting_down = False
    
    def _receive_messages(self):
        """Receive messages from server with shutdown handling"""
        while self.running and self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    if not self._server_shutting_down:
                        print("Server closed connection unexpectedly")
                    break
                
                message = NetworkMessage.from_bytes(data)
                if message is None:
                    continue
                
                # Handle server shutdown message
                if isinstance(message, ServerShutdownMessage):
                    self._server_shutting_down = True
                    print(f"Server is shutting down: {message.reason}")
                    self._queue_event(NetworkEventType.DISCONNECT, {
                        'reason': message.reason,
                        'graceful': message.graceful,
                        'shutdown_time': message.shutdown_time
                    })
                    break
                
                # Handle kick message
                if isinstance(message, KickMessage):
                    print(f"Kicked from server: {message.reason}")
                    self._queue_event(NetworkEventType.DISCONNECT, {
                        'reason': message.reason,
                        'graceful': False
                    })
                    self.disconnect()
                    break
                
                # Handle heartbeat response and calculate ping
                if isinstance(message, HeartbeatMessage) and hasattr(message, 'send_time'):
                    self.ping = (time.time() - message.send_time) * 1000
                    self.last_ping_time = time.time()
                    self._queue_event(NetworkEventType.PING_UPDATE, {'ping': self.ping})
                    continue
                
                self._queue_event(NetworkEventType.MESSAGE, message)
                
            except socket.timeout:
                continue
            except ConnectionResetError:
                if not self._server_shutting_down:
                    print("Connection reset by server")
                break
            except Exception as e:
                if self.running and not self._server_shutting_down:
                    print(f"Error receiving message: {e}")
                break
        
        self.disconnect()
    
    def connect(self, username: str = "Player", password: str = None) -> bool:
        """Connect to server with optional password"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(1.0)
            self.socket.connect((self.server_host, self.server_port))
            
            # Handle password authentication if required
            if password is not None:
                auth_msg = AuthMessage(password=password)
                self.socket.send(auth_msg.to_bytes())
                
                # Wait for auth response
                response_data = self.socket.recv(256)
                auth_result = NetworkMessage.from_bytes(response_data)
                
                if not isinstance(auth_result, AuthResultMessage) or not auth_result.success:
                    print(f"Authentication failed: {getattr(auth_result, 'reason', 'Unknown error')}")
                    self.socket.close()
                    return False
            
            self.connected = True
            self.running = True
            self.username = username
            
            # Start threads
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.process_thread = threading.Thread(target=self._process_events, daemon=True)
            self.heartbeat_thread = threading.Thread(target=self._send_heartbeats, daemon=True)
            
            self.receive_thread.start()
            self.process_thread.start()
            self.heartbeat_thread.start()
            
            print(f"Connected to server {self.server_host}:{self.server_port}")
            return True
            
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        self.running = False
        self.connected = False
        
        if self.socket:
            self.socket.close()
        
        print("Disconnected from server")
    
    def get_ping(self) -> float:
        """Get current ping to server in milliseconds"""
        return self.ping
    
    def send(self, message: NetworkMessage):
        """Send message to server"""
        if self.connected and self.socket:
            try:
                data = message.to_bytes()
                self.socket.send(data)
            except Exception as e:
                print(f"Error sending message: {e}")
                self.disconnect()
    
    def _send_heartbeats(self):
        """Send periodic heartbeats to server for ping measurement"""
        while self.running and self.connected:
            try:
                heartbeat = HeartbeatMessage()
                heartbeat.send_time = time.time()
                self.send(heartbeat)
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                if self.running:
                    print(f"Heartbeat error: {e}")
                    break
    
    def _queue_event(self, event_type: NetworkEventType, data: Any):
        """Add event to processing queue"""
        event = NetworkEvent(event_type, data)
        self.event_queue.put(event)
    
    def _process_events(self):
        """Process queued events"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1.0)
                self._handle_event(event)
            except queue.Empty:
                continue
    
    def _handle_event(self, event: NetworkEvent):
        """Handle a network event"""
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    def on_event(self, event_type: NetworkEventType):
        """Decorator to register event handlers"""
        def decorator(func):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func
        return decorator

class HostClient:
    """
    Hybrid client that can also act as a server for other clients
    Perfect for player-hosted multiplayer games with enhanced features
    """
    
    def __init__(self, host: str = 'localhost', port: int = 5555, max_peers: int = 4, password: str = None):
        self.host = host
        self.port = port
        self.max_peers = max_peers
        self.password = password
        self.is_host = False
        self.connected_to_host = False
        
        # Server components
        self.server = None
        self.peers: Dict[int, Client] = {}
        
        # Client components  
        self.client = None
        self.host_address = None
        
        # Shared event system
        self.event_queue = queue.Queue()
        self.event_handlers: Dict[NetworkEventType, List[Callable]] = {}
        
        # Threading
        self.running = False
        self.process_thread = None
        
        # Auto-kick settings
        self.auto_kick_on_host_leave = True
        self.host_migration_enabled = False  # Future feature
        
    def toggle_server_scripts(self, enabled: bool, key:str=None):
        """
        Enable or disable server scripts execution (host mode only)
        
        Args:
            enabled: Whether to enable or disable scripts
            key: Specific script name to toggle, if None toggles all scripts
        """
        if not self.is_host or not self.server:
            return
        
        self.server.toggle_scripts_execution(enabled, key)
    
    def disconnect(self, reason: str = "Host disconnected", notify_peers: bool = True):
        """
        Disconnect from network with optional peer notification
        
        Args:
            reason: Reason for disconnection
            notify_peers: Whether to notify peers before disconnecting (host mode only)
        """
        if self.running and self.is_host and notify_peers and self.server:
            # As host, notify all peers before shutting down
            print(f"Host disconnecting, notifying {self.get_peer_count()} peers...")
            
            # Send shutdown notification to all peers
            shutdown_msg = ServerShutdownMessage(
                reason=reason, 
                graceful=True
            )
            self.server.broadcast(shutdown_msg)
            
            # Give a small delay for messages to be sent
            time.sleep(0.5)
            
            # Kick all peers if auto-kick is enabled
            if self.auto_kick_on_host_leave:
                self._kick_all_peers(reason)
        
        # Stop the network components
        self.running = False
        self.connected_to_host = False
        
        if self.server:
            self.server.stop()
        if self.client:
            self.client.disconnect()
        
        print(f"HostClient disconnected: {reason}")
    
    def _kick_all_peers(self, reason: str = "Host left the game"):
        """
        Kick all connected peers (host mode only)
        
        Args:
            reason: Reason for kicking all peers
        """
        if not self.is_host or not self.server:
            return
        
        peer_ids = list(self.server.clients.keys())
        kicked_count = 0
        
        print(f"Kicking {len(peer_ids)} peers: {reason}")
        
        for peer_id in peer_ids:
            if self.server.kick_client(peer_id, reason):
                kicked_count += 1
        
        print(f"Successfully kicked {kicked_count} peers")
    
    def emergency_disconnect(self):
        """
        Immediately disconnect without notifying peers
        Use this only in emergency situations
        """
        print("EMERGENCY DISCONNECT - No peer notification")
        self.running = False
        self.connected_to_host = False
        
        if self.server:
            self.server.emergency_shutdown("Host emergency disconnect")
        if self.client:
            self.client.disconnect()
    
    def set_auto_kick_on_leave(self, enabled: bool):
        """
        Enable or disable auto-kick when host leaves
        
        Args:
            enabled: Whether to automatically kick peers when host disconnects
        """
        self.auto_kick_on_host_leave = enabled
        status = "enabled" if enabled else "disabled"
        print(f"Auto-kick on host leave: {status}")
    
    def start_as_host(self) -> bool:
        """Start as host (server + client) with password protection"""
        try:
            # Start server component with password
            self.server = Server(self.host, self.port, self.max_peers, self.password)
            if not self.server.start():
                return False
            
            # Connect to ourselves as client (no password needed for self-connection)
            self.client = NetworkClient(self.host, self.port)
            if not self.client.connect("Host"):
                self.server.stop()
                return False
            
            self.is_host = True
            self.connected_to_host = True
            self.running = True
            
            # Forward server events
            @self.server.on_event(NetworkEventType.CONNECT)
            def on_peer_connect(event):
                self._queue_event(NetworkEventType.CONNECT, event.data, event.client_id)
            
            @self.server.on_event(NetworkEventType.DISCONNECT) 
            def on_peer_disconnect(event):
                self._queue_event(NetworkEventType.DISCONNECT, event.data, event.client_id)
            
            @self.server.on_event(NetworkEventType.MESSAGE)
            def on_peer_message(event):
                self._queue_event(NetworkEventType.MESSAGE, event.data, event.client_id)
            
            @self.server.on_event(NetworkEventType.PING_UPDATE)
            def on_ping_update(event):
                self._queue_event(NetworkEventType.PING_UPDATE, event.data, event.client_id)
            
            @self.server.on_event(NetworkEventType.SERVER_SCRIPT)
            def on_server_script(event):
                self._queue_event(NetworkEventType.SERVER_SCRIPT, event.data)
            
            # Forward client events
            @self.client.on_event(NetworkEventType.MESSAGE)
            def on_host_message(event):
                self._queue_event(NetworkEventType.MESSAGE, event.data)
            
            @self.client.on_event(NetworkEventType.PING_UPDATE)
            def on_client_ping_update(event):
                self._queue_event(NetworkEventType.PING_UPDATE, event.data)
            
            # Start event processor
            self.process_thread = threading.Thread(target=self._process_events, daemon=True)
            self.process_thread.start()
            
            print(f"Started as HOST on port {self.port} (Password: {'Yes' if self.password else 'No'})")
            return True
            
        except Exception as e:
            print(f"Failed to start as host: {e}")
            return False
    
    def connect_as_client(self, host_address: str, port: int = 5555, password: str = None) -> bool:
        """Connect as client to existing host with password"""
        try:
            self.client = NetworkClient(host_address, port)
            if not self.client.connect("Client", password):
                return False
            
            self.is_host = False
            self.connected_to_host = True
            self.host_address = (host_address, port)
            self.running = True
            
            # Forward client events
            @self.client.on_event(NetworkEventType.MESSAGE)
            def on_host_message(event):
                self._queue_event(NetworkEventType.MESSAGE, event.data)
            
            @self.client.on_event(NetworkEventType.PING_UPDATE)
            def on_ping_update(event):
                self._queue_event(NetworkEventType.PING_UPDATE, event.data)
            
            # Start event processor
            self.process_thread = threading.Thread(target=self._process_events, daemon=True)
            self.process_thread.start()
            
            print(f"Connected as CLIENT to {host_address}:{port}")
            return True
            
        except Exception as e:
            print(f"Failed to connect as client: {e}")
            return False
    
    def add_server_script(self, name: str, interval: float, callback: Callable, 
                         enabled: bool = True, one_shot: bool = False):
        """Add a server script (host only)"""
        if self.is_host and self.server:
            self.server.add_script(name, interval, callback, enabled, one_shot)
    
    def remove_server_script(self, name: str):
        """Remove a server script (host only)"""
        if self.is_host and self.server:
            self.server.remove_script(name)
    
    def kick_peer(self, peer_id: int, reason: str = "Kicked by host"):
        """Kick a peer from the server (host only)"""
        if self.is_host and self.server:
            return self.server.kick_client(peer_id, reason)
        return False
    
    def get_peer_ping(self, peer_id: int) -> float:
        """Get ping of a specific peer (host only)"""
        if self.is_host and self.server:
            return self.server.get_client_ping(peer_id)
        return -1
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics (host only)"""
        if self.is_host and self.server:
            return self.server.get_server_stats()
        return {}
    
    def get_ping(self) -> float:
        """Get current ping to host (client mode only)"""
        if not self.is_host and self.client:
            return self.client.get_ping()
        return 0
    
    def send_to_all(self, message: NetworkMessage, exclude_self: bool = False):
        """Send message to all connected peers (if host) and to host (if client)"""
        if self.is_host and self.server:
            # As host, broadcast to all peers EXCEPT ourselves
            exclude_client_id = self.client.client_id if exclude_self and hasattr(self, 'client') else None
            self.server.broadcast(message, exclude_client_id=exclude_client_id)
            
            # Process locally if not excluding self
            if not exclude_self:
                self._queue_event(NetworkEventType.MESSAGE, message)
                
        elif self.connected_to_host and self.client:
            # As client, send to host
            self.client.send(message)
    
    def send_to_peer(self, peer_id: int, message: NetworkMessage):
        """Send message to specific peer (host only)"""
        if self.is_host and self.server:
            self.server.send_to_client(peer_id, message)
    
    def get_peer_count(self) -> int:
        """Get number of connected peers (host only)"""
        if self.is_host and self.server and hasattr(self.server, 'clients'):
            return len(self.server.clients)
        return 0
    
    def get_peer_list(self) -> List[int]:
        """Get list of connected peer IDs (host only)"""
        if self.is_host and self.server:
            return list(self.server.clients.keys())
        return []
    
    def _queue_event(self, event_type: NetworkEventType, data: Any, client_id: int = None):
        """Add event to processing queue"""
        event = NetworkEvent(event_type, data, client_id)
        self.event_queue.put(event)
    
    def _process_events(self):
        """Process queued events"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1.0)
                self._handle_event(event)
            except queue.Empty:
                continue
    
    def _handle_event(self, event: NetworkEvent):
        """Handle a network event"""
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    def on_event(self, event_type: NetworkEventType):
        """Decorator to register event handlers"""
        def decorator(func):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func
        return decorator


# NetworkDiscovery class remains the same as original...
class NetworkDiscovery:
    """
    Simple network discovery for finding local hosts
    """
    
    def __init__(self, discovery_port: int = 5556):
        self.discovery_port = discovery_port
        self.running = False
        self.discovered_hosts = []
    
    def broadcast_presence(self, game_name: str = "LunaEngine Game", port: int = 5555):
        """Broadcast host presence on local network"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.5)
            
            message = f"LUNAENGINE_HOST:{game_name}:{port}"
            sock.sendto(message.encode(), ('255.255.255.255', self.discovery_port))
            sock.close()
            print(f"Broadcasted presence: {game_name} on port {port}")
            return True
        except Exception as e:
            print(f"Broadcast error: {e}")
            return False
    
    def discover_hosts(self, timeout: float = 3.0) -> List[tuple]:
        """Discover hosts on local network"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(timeout)
            sock.bind(('0.0.0.0', self.discovery_port))
            
            hosts = []
            end_time = time.time() + timeout
            
            print(f"Discovering hosts on port {self.discovery_port}...")
            
            while time.time() < end_time:
                try:
                    data, addr = sock.recvfrom(1024)
                    message = data.decode()
                    
                    if message.startswith("LUNAENGINE_HOST:"):
                        parts = message.split(":")
                        if len(parts) >= 3:
                            game_name = parts[1]
                            port = int(parts[2])
                            host_info = (addr[0], port, game_name)
                            
                            # Avoid duplicates
                            if host_info not in hosts:
                                hosts.append(host_info)
                                print(f"Discovered host: {game_name} at {addr[0]}:{port}")
                            
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error in discovery: {e}")
                    continue
            
            sock.close()
            print(f"Discovery complete. Found {len(hosts)} hosts.")
            return hosts
            
        except Exception as e:
            print(f"Discovery setup error: {e}")
            return []


# New message classes for enhanced functionality
class HeartbeatMessage(NetworkMessage):
    """Heartbeat message for connection monitoring with ping measurement"""
    def __init__(self):
        self.send_time = time.time()


class AuthMessage(NetworkMessage):
    """Authentication message for password-protected servers"""
    def __init__(self, password: str):
        self.password = password


class AuthResultMessage(NetworkMessage):
    """Authentication result message"""
    def __init__(self, success: bool, reason: str = ""):
        self.success = success
        self.reason = reason


class KickMessage(NetworkMessage):
    """Kick message for removing clients from server"""
    def __init__(self, reason: str = "Kicked by server"):
        self.reason = reason


class PlayerPositionMessage(NetworkMessage):
    """Player position update message"""
    def __init__(self, x: float, y: float, player_id: str):
        self.x = x
        self.y = y
        self.player_id = player_id


class ChatMessage(NetworkMessage):
    """Chat message with better duplicate prevention"""
    def __init__(self, message: str, player_id: str, message_id: str = None):
        self.message = message
        self.player_id = player_id
        self.message_id = message_id or f"{player_id}_{int(time.time() * 1000)}"
        self.timestamp = time.time()


class GameStateMessage(NetworkMessage):
    """Game state synchronization message"""
    def __init__(self, game_state: Dict):
        self.game_state = game_state


class ServerScriptMessage(NetworkMessage):
    """Server script execution result message"""
    def __init__(self, script_name: str, result: Any, execution_count: int):
        self.script_name = script_name
        self.result = result
        self.execution_count = execution_count
        
class ServerShutdownMessage(NetworkMessage):
    """Message sent to all clients when server is shutting down"""
    def __init__(self, reason: str = "Server shutdown", graceful: bool = True):
        self.reason = reason
        self.graceful = graceful
        self.shutdown_time = time.time()


class HostMigrationMessage(NetworkMessage):
    """Message for host migration scenarios"""
    def __init__(self, new_host: str = None, migration_possible: bool = False):
        self.new_host = new_host
        self.migration_possible = migration_possible
        self.timestamp = time.time()

# Messages container class
class NetworkMessages:
    HeartbeatMessage: NetworkMessage = HeartbeatMessage
    PlayerPositionMessage: NetworkMessage = PlayerPositionMessage
    ChatMessage: NetworkMessage = ChatMessage
    GameStateMessage: NetworkMessage = GameStateMessage
    AuthMessage: NetworkMessage = AuthMessage
    AuthResultMessage: NetworkMessage = AuthResultMessage
    KickMessage: NetworkMessage = KickMessage
    ServerScriptMessage: NetworkMessage = ServerScriptMessage
    ServerShutdownMessage: NetworkMessage = ServerShutdownMessage
    HostMigrationMessage: NetworkMessage = HostMigrationMessage