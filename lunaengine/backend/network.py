# lunaengine/backend/network.py
"""
Network backend module for LunaEngine.

This module provides comprehensive multiplayer networking functionality
including server, client, host-client hybrid, network discovery, and
performance monitoring.

Features:
- Server with password protection and scripting
- Network client with reconnection capabilities
- Host-Client hybrid for peer-to-peer gaming
- Network discovery for local game finding
- Performance monitoring and connection quality analysis
- Region detection based on IP geolocation
- Thread-safe message handling and event system
"""

import sys, sys, os, time, socket, threading, queue, json, struct, hashlib, pickle, select, errno, random, math, uuid
from typing import Dict, List, Tuple, Optional, Any, Callable, Union
from enum import Enum, auto
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

# For region detection (optional external)
try:
    import urllib.request
    import urllib.error
    EXTERNAL_NETWORK_AVAILABLE = True
except ImportError:
    EXTERNAL_NETWORK_AVAILABLE = False


class NetworkEventType(Enum):
    """Enumeration of network event types."""
    CONNECT = auto()           # Client connected
    DISCONNECT = auto()        # Client disconnected
    MESSAGE = auto()           # Message received
    ERROR = auto()             # Network error occurred
    PING_UPDATE = auto()       # Ping measurement updated
    AUTH_SUCCESS = auto()      # Authentication successful
    AUTH_FAILED = auto()       # Authentication failed
    SERVER_SCRIPT = auto()     # Server script executed
    QUALITY_UPDATE = auto()    # Connection quality updated
    BANDWIDTH_UPDATE = auto() # Bandwidth usage updated


@dataclass
class NetworkEvent:
    """Represents a network event with associated data."""
    event_type: NetworkEventType
    client_id: Optional[int] = None
    data: Any = None
    timestamp: float = field(default_factory=time.time)


class HostClientMode(Enum):
    """Operating modes for HostClient."""
    DISCONNECTED = auto()  # Not connected
    HOST = auto()          # Acting as host/server
    CLIENT = auto()        # Connected as client


class ConnectionQuality(Enum):
    """Connection quality levels."""
    EXCELLENT = auto()  # < 50ms ping, < 1% packet loss
    GOOD = auto()       # < 100ms ping, < 3% packet loss
    FAIR = auto()       # < 200ms ping, < 5% packet loss
    POOR = auto()       # < 500ms ping, < 10% packet loss
    UNUSABLE = auto()   # > 500ms ping or > 10% packet loss


@dataclass
class NetworkMetrics:
    """Container for network performance metrics."""
    ping: float = 0.0                 # Round-trip time in milliseconds
    jitter: float = 0.0               # Ping variation in milliseconds
    packet_loss: float = 0.0          # Percentage of lost packets
    bandwidth_up: float = 0.0         # Upload bandwidth in KB/s
    bandwidth_down: float = 0.0       # Download bandwidth in KB/s
    uptime: float = 0.0               # Connection uptime in seconds
    messages_sent: int = 0            # Total messages sent
    messages_received: int = 0        # Total messages received
    last_update: float = field(default_factory=time.time)
    
    def get_quality(self) -> ConnectionQuality:
        """Determine connection quality based on metrics."""
        if self.ping <= 0:
            return ConnectionQuality.UNUSABLE
        
        if self.ping < 50 and self.packet_loss < 1:
            return ConnectionQuality.EXCELLENT
        elif self.ping < 100 and self.packet_loss < 3:
            return ConnectionQuality.GOOD
        elif self.ping < 200 and self.packet_loss < 5:
            return ConnectionQuality.FAIR
        elif self.ping < 500 and self.packet_loss < 10:
            return ConnectionQuality.POOR
        else:
            return ConnectionQuality.UNUSABLE


class NetworkMessage:
    """Base class for all network messages."""
    
    def __init__(self):
        self.message_id = str(uuid.uuid4())
        self.timestamp = time.time()
        self.version = 1
    
    def serialize(self) -> bytes:
        """Convert message to bytes for transmission."""
        return pickle.dumps(self)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'NetworkMessage':
        """Create message from bytes."""
        return pickle.loads(data)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.message_id[:8]})"


class ChatMessage(NetworkMessage):
    """Message for chat communication."""
    
    def __init__(self, message: str = "", player_id: str = "", sender_name: str = ""):
        super().__init__()
        self.message = message
        self.player_id = player_id
        self.sender_name = sender_name
        self.version = 1


class PlayerPositionMessage(NetworkMessage):
    """Message for player position updates."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0, player_id: str = ""):
        super().__init__()
        self.x = x
        self.y = y
        self.player_id = player_id
        self.version = 1


class GameStateMessage(NetworkMessage):
    """Message for complete game state synchronization."""
    
    def __init__(self, game_state: Dict[str, Any] = None):
        super().__init__()
        self.game_state = game_state or {}
        self.version = 1


class PlayerInfoMessage(NetworkMessage):
    """Message for player information updates."""
    
    def __init__(self, player_name: str = "", player_id: str = ""):
        super().__init__()
        self.player_name = player_name
        self.player_id = player_id
        self.version = 1


class PlayersListMessage(NetworkMessage):
    """Message for sending list of all players."""
    
    def __init__(self, players_data: Dict[int, Dict] = None):
        super().__init__()
        self.players = players_data or {}
        self.version = 1


class WelcomeMessage(NetworkMessage):
    """Welcome message for new clients."""
    
    def __init__(self, player_id: int = 0, players_data: Dict[int, Dict] = None):
        super().__init__()
        self.player_id = player_id
        self.players = players_data or {}
        self.version = 1


@dataclass
class ClientInfo:
    """Information about a connected client."""
    client_id: int
    address: Tuple[str, int]
    connected_at: float = field(default_factory=time.time)
    last_message: float = field(default_factory=time.time)
    authenticated: bool = False
    username: str = ""
    ping: float = 0.0
    bandwidth_usage: float = 0.0
    disconnected: bool = False
    
    @property
    def connection_time(self) -> float:
        """Get connection duration in seconds."""
        return time.time() - self.connected_at


@dataclass
class ServerScript:
    """Represents a server-side script that runs periodically."""
    name: str
    interval: float  # Seconds between executions
    function: Callable[[Any], Any]
    last_execution: float = 0.0
    enabled: bool = True
    
    def should_execute(self) -> bool:
        """Check if script should execute now."""
        if not self.enabled:
            return False
        return time.time() - self.last_execution >= self.interval
    
    def execute(self, server: Any) -> Any:
        """Execute the script."""
        if self.should_execute():
            try:
                result = self.function(server)
                self.last_execution = time.time()
                return result
            except Exception as e:
                print(f"Server script '{self.name}' error: {e}")
                return None
        return None


class PerformanceMonitor:
    """Monitors network performance metrics."""
    
    def __init__(self):
        self.ping_history: List[float] = []
        self.packet_loss_history: List[float] = []
        self.bandwidth_up_history: List[float] = []
        self.bandwidth_down_history: List[float] = []
        self.start_time = time.time()
        self.max_history = 100
        
        self.bytes_sent = 0
        self.bytes_received = 0
        self.last_bandwidth_update = time.time()
    
    def update_ping(self, ping: float):
        """Update ping measurement."""
        self.ping_history.append(ping)
        if len(self.ping_history) > self.max_history:
            self.ping_history.pop(0)
    
    def update_packet_loss(self, loss: float):
        """Update packet loss measurement."""
        self.packet_loss_history.append(loss)
        if len(self.packet_loss_history) > self.max_history:
            self.packet_loss_history.pop(0)
    
    def update_bandwidth(self, bytes_sent: int, bytes_received: int):
        """Update bandwidth measurements."""
        current_time = time.time()
        time_diff = current_time - self.last_bandwidth_update
        
        if time_diff > 0:
            up_kbps = (bytes_sent - self.bytes_sent) / time_diff / 1024
            down_kbps = (bytes_received - self.bytes_received) / time_diff / 1024
            
            self.bandwidth_up_history.append(up_kbps)
            self.bandwidth_down_history.append(down_kbps)
            
            if len(self.bandwidth_up_history) > self.max_history:
                self.bandwidth_up_history.pop(0)
            if len(self.bandwidth_down_history) > self.max_history:
                self.bandwidth_down_history.pop(0)
        
        self.bytes_sent = bytes_sent
        self.bytes_received = bytes_received
        self.last_bandwidth_update = current_time
    
    def get_metrics(self) -> NetworkMetrics:
        """Get current network metrics."""
        ping_avg = 0.0
        if self.ping_history:
            ping_avg = sum(self.ping_history) / len(self.ping_history)
        
        loss_avg = 0.0
        if self.packet_loss_history:
            loss_avg = sum(self.packet_loss_history) / len(self.packet_loss_history)
        
        bandwidth_up_avg = 0.0
        if self.bandwidth_up_history:
            bandwidth_up_avg = sum(self.bandwidth_up_history) / len(self.bandwidth_up_history)
        
        bandwidth_down_avg = 0.0
        if self.bandwidth_down_history:
            bandwidth_down_avg = sum(self.bandwidth_down_history) / len(self.bandwidth_down_history)
        
        jitter = 0.0
        if len(self.ping_history) >= 2:
            # Calculate jitter as standard deviation
            mean = ping_avg
            variance = sum((x - mean) ** 2 for x in self.ping_history) / len(self.ping_history)
            jitter = math.sqrt(variance)
        
        return NetworkMetrics(
            ping=ping_avg,
            jitter=jitter,
            packet_loss=loss_avg,
            bandwidth_up=bandwidth_up_avg,
            bandwidth_down=bandwidth_down_avg,
            uptime=time.time() - self.start_time,
            last_update=time.time()
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all performance metrics."""
        metrics = self.get_metrics()
        return {
            'average_ping': metrics.ping,
            'ping_jitter': metrics.jitter,
            'packet_loss': metrics.packet_loss,
            'bandwidth_up': metrics.bandwidth_up,
            'bandwidth_down': metrics.bandwidth_down,
            'connection_quality': metrics.get_quality().name,
            'uptime': metrics.uptime,
            'ping_samples': len(self.ping_history)
        }


class RegionDetector:
    """Detects geographic region/country based on IP address."""
    
    @staticmethod
    def detect_region(ip_address: str = None) -> str:
        """
        Detect geographic region based on IP address.
        
        Args:
            ip_address: IP address to check. If None, uses local public IP.
            
        Returns:
            Detected region/country name or 'Unknown'
        """
        if not EXTERNAL_NETWORK_AVAILABLE:
            return RegionDetector.get_local_region()
        
        if ip_address is None:
            ip_address = RegionDetector.get_public_ip()
        
        if not ip_address or ip_address.startswith(('127.', '192.168.', '10.', '172.')):
            return RegionDetector.get_local_region()
        
        # Try public geolocation API
        try:
            url = f"http://ip-api.com/json/{ip_address}?fields=country,regionName,city"
            with urllib.request.urlopen(url, timeout=3) as response:
                data = json.loads(response.read().decode())
                if data.get('country'):
                    region = f"{data['country']}"
                    if data.get('regionName'):
                        region += f", {data['regionName']}"
                    if data.get('city'):
                        region += f", {data['city']}"
                    return region
        except Exception:
            pass
        
        return RegionDetector.get_local_region()
    
    @staticmethod
    def get_public_ip() -> Optional[str]:
        """Get the public IP address of the current machine."""
        if not EXTERNAL_NETWORK_AVAILABLE:
            return None
        
        try:
            services = [
                "https://api.ipify.org",
                "https://checkip.amazonaws.com",
                "https://icanhazip.com"
            ]
            
            for service in services:
                try:
                    with urllib.request.urlopen(service, timeout=3) as response:
                        ip = response.read().decode().strip()
                        if ip and len(ip.split('.')) == 4:
                            return ip
                except:
                    continue
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def get_local_region() -> str:
        """Attempt to determine region from local network settings."""
        try:
            import locale
            import platform
            
            if platform.system() == 'Windows':
                import ctypes
                windll = ctypes.windll.kernel32
                locale_code = windll.GetUserDefaultUILanguage()
                locale_map = {
                    1033: "United States",
                    1046: "Brazil",
                    3082: "Spain",
                    1036: "France",
                    1031: "Germany",
                    1040: "Italy",
                    1041: "Japan",
                    1042: "Korea",
                    2052: "China",
                    1028: "Taiwan"
                }
                return locale_map.get(locale_code, "Unknown")
            else:
                loc = locale.getdefaultlocale()
                if loc and len(loc) > 0:
                    lang = loc[0].lower()
                    if 'en_us' in lang:
                        return "United States"
                    elif 'pt_br' in lang:
                        return "Brazil"
                    elif 'es_' in lang:
                        return "Spain"
                    elif 'fr_' in lang:
                        return "France"
                    elif 'de_' in lang:
                        return "Germany"
                    elif 'it_' in lang:
                        return "Italy"
                    elif 'ja_' in lang:
                        return "Japan"
                    elif 'ko_' in lang:
                        return "Korea"
                    elif 'zh_cn' in lang:
                        return "China"
                    elif 'zh_tw' in lang:
                        return "Taiwan"
        except Exception:
            pass
        
        return "Local Network"


class Server:
    """Network server for multiplayer games."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5555, 
                 max_clients: int = 8, password: str = None):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.password_hash = hashlib.sha256(password.encode()).hexdigest() if password else None
        
        self.socket = None
        self.running = False
        self.clients: Dict[int, ClientInfo] = {}
        self.client_sockets: Dict[int, socket.socket] = {}
        
        self.event_handlers: Dict[NetworkEventType, List[Callable]] = {et: [] for et in NetworkEventType}
        self.message_handlers: Dict[type, List[Callable]] = {}
        
        self.scripts: Dict[str, ServerScript] = {}
        self.performance_monitor = PerformanceMonitor()
        
        self.next_client_id = 1
        self.timeout_threshold = 30.0
        self.heartbeat_interval = 5.0
        self.last_heartbeat = 0.0
        
        self._lock = threading.RLock()
        self._event_queue = queue.Queue()
    
    def start(self) -> bool:
        """Start the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(self.max_clients)
            self.socket.setblocking(False)
            
            self.running = True
            
            # Start server threads
            threading.Thread(target=self._accept_thread, daemon=True).start()
            threading.Thread(target=self._receive_thread, daemon=True).start()
            threading.Thread(target=self._processing_thread, daemon=True).start()
            
            print(f"Server started on {self.host}:{self.port}")
            self._queue_event(NetworkEventType.CONNECT, 0, None)
            return True
            
        except Exception as e:
            print(f"Failed to start server: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop the server and disconnect all clients."""
        self.running = False
        
        with self._lock:
            # Disconnect all clients
            for client_id, client_sock in list(self.client_sockets.items()):
                try:
                    client_sock.shutdown(socket.SHUT_RDWR)
                    client_sock.close()
                except:
                    pass
            
            self.client_sockets.clear()
            self.clients.clear()
            
            # Close server socket
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
        
        print("Server stopped")
    
    def _accept_thread(self):
        """Thread for accepting new client connections."""
        while self.running:
            try:
                readable, _, _ = select.select([self.socket], [], [], 0.1)
                if self.socket in readable:
                    client_socket, address = self.socket.accept()
                    client_socket.setblocking(False)
                    
                    with self._lock:
                        if len(self.clients) >= self.max_clients:
                            client_socket.close()
                            continue
                        
                        client_id = self.next_client_id
                        self.next_client_id += 1
                        
                        self.client_sockets[client_id] = client_socket
                        self.clients[client_id] = ClientInfo(
                            client_id=client_id,
                            address=address
                        )
                        
                        print(f"Client {client_id} connected from {address}")
                        self._queue_event(NetworkEventType.CONNECT, client_id, {
                            'client_id': client_id,
                            'address': address
                        })
                        
            except Exception as e:
                if self.running:
                    print(f"Accept thread error: {e}")
    
    def _receive_thread(self):
        """Thread for receiving data from clients."""
        while self.running:
            with self._lock:
                sockets_to_check = list(self.client_sockets.values())
            
            if not sockets_to_check:
                time.sleep(0.01)
                continue
            
            try:
                readable, _, exceptional = select.select(
                    sockets_to_check, [], sockets_to_check, 0.1
                )
                
                for sock in readable:
                    try:
                        # Find client_id for this socket
                        client_id = None
                        with self._lock:
                            for cid, csock in self.client_sockets.items():
                                if csock == sock:
                                    client_id = cid
                                    break
                        
                        if client_id is None:
                            continue
                        
                        # Receive data
                        data = b""
                        while True:
                            try:
                                chunk = sock.recv(4096)
                                if not chunk:
                                    break
                                data += chunk
                                if len(chunk) < 4096:
                                    break
                            except socket.error as e:
                                if e.errno == errno.EWOULDBLOCK:
                                    break
                                else:
                                    raise
                        
                        if data:
                            self._process_received_data(client_id, data)
                        
                    except Exception as e:
                        print(f"Error receiving from client {client_id}: {e}")
                        self._disconnect_client(client_id, str(e))
                
                # Handle exceptional conditions
                for sock in exceptional:
                    client_id = None
                    with self._lock:
                        for cid, csock in self.client_sockets.items():
                            if csock == sock:
                                client_id = cid
                                break
                    
                    if client_id:
                        self._disconnect_client(client_id, "Socket error")
                        
            except Exception as e:
                if self.running:
                    print(f"Receive thread error: {e}")
    
    def _process_received_data(self, client_id: int, data: bytes):
        """Process received data from a client."""
        try:
            # Deserialize message
            message = pickle.loads(data)
            
            # Update client info
            with self._lock:
                if client_id in self.clients:
                    self.clients[client_id].last_message = time.time()
            
            # Handle authentication
            if not self.clients[client_id].authenticated:
                if isinstance(message, dict) and message.get('type') == 'auth':
                    if self._authenticate_client(client_id, message):
                        self.clients[client_id].authenticated = True
                        self.clients[client_id].username = message.get('username', '')
                        self._queue_event(NetworkEventType.AUTH_SUCCESS, client_id, 
                                         {'username': self.clients[client_id].username})
                    else:
                        self._queue_event(NetworkEventType.AUTH_FAILED, client_id, None)
                        self._disconnect_client(client_id, "Authentication failed")
                    return
            
            # Queue message for processing
            self._queue_event(NetworkEventType.MESSAGE, client_id, message)
            
        except Exception as e:
            print(f"Error processing data from client {client_id}: {e}")
    
    def _authenticate_client(self, client_id: int, auth_data: Dict) -> bool:
        """Authenticate a client."""
        if self.password_hash is None:
            return True  # No password required
        
        password_hash = auth_data.get('password_hash')
        return password_hash == self.password_hash
    
    def _processing_thread(self):
        """Thread for processing events and running scripts."""
        while self.running:
            # Process queued events
            try:
                while True:
                    event = self._event_queue.get_nowait()
                    self._handle_event(event)
            except queue.Empty:
                pass
            
            # Run server scripts
            self._run_scripts()
            
            # Send heartbeats
            current_time = time.time()
            if current_time - self.last_heartbeat >= self.heartbeat_interval:
                self._send_heartbeats()
                self.last_heartbeat = current_time
            
            # Check for timeouts
            self._check_timeouts()
            
            time.sleep(0.01)
    
    def _handle_event(self, event: NetworkEvent):
        """Handle a network event."""
        # Call event handlers
        for handler in self.event_handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")
        
        # Call message handlers for MESSAGE events
        if event.event_type == NetworkEventType.MESSAGE and event.data:
            message_type = type(event.data)
            for handler in self.message_handlers.get(message_type, []):
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in message handler: {e}")
    
    def _run_scripts(self):
        """Execute server scripts."""
        for script_name, script in self.scripts.items():
            result = script.execute(self)
            if result:
                self._queue_event(NetworkEventType.SERVER_SCRIPT, 0, 
                                 {'script_name': script_name, 'result': result})
    
    def _send_heartbeats(self):
        """Send heartbeat messages to all clients."""
        heartbeat_msg = {'type': 'heartbeat', 'timestamp': time.time()}
        self.broadcast(heartbeat_msg)
    
    def _check_timeouts(self):
        """Check for client timeouts."""
        current_time = time.time()
        clients_to_disconnect = []
        
        with self._lock:
            for client_id, client_info in self.clients.items():
                if current_time - client_info.last_message > self.timeout_threshold:
                    clients_to_disconnect.append(client_id)
        
        for client_id in clients_to_disconnect:
            self._disconnect_client(client_id, "Timeout")
    
    def _disconnect_client(self, client_id: int, reason: str = "Disconnected"):
        """Disconnect a client."""
        with self._lock:
            if client_id in self.client_sockets:
                try:
                    self.client_sockets[client_id].shutdown(socket.SHUT_RDWR)
                    self.client_sockets[client_id].close()
                except:
                    pass
                
                del self.client_sockets[client_id]
            
            if client_id in self.clients:
                client_info = self.clients[client_id]
                client_info.disconnected = True
                del self.clients[client_id]
        
        print(f"Client {client_id} disconnected: {reason}")
        self._queue_event(NetworkEventType.DISCONNECT, client_id, {'reason': reason})
    
    def _queue_event(self, event_type: NetworkEventType, client_id: Optional[int], data: Any):
        """Queue an event for processing."""
        self._event_queue.put(NetworkEvent(event_type, client_id, data))
    
    def broadcast(self, message: Any, exclude_client_id: int = None):
        """Broadcast a message to all connected clients."""
        serialized = pickle.dumps(message)
        
        with self._lock:
            for client_id, client_sock in self.client_sockets.items():
                if client_id == exclude_client_id:
                    continue
                
                try:
                    client_sock.sendall(serialized)
                except Exception as e:
                    print(f"Error broadcasting to client {client_id}: {e}")
    
    def send_to_client(self, client_id: int, message: Any):
        """Send a message to a specific client."""
        serialized = pickle.dumps(message)
        
        with self._lock:
            if client_id in self.client_sockets:
                try:
                    self.client_sockets[client_id].sendall(serialized)
                except Exception as e:
                    print(f"Error sending to client {client_id}: {e}")
    
    def on_event(self, event_type: NetworkEventType):
        """Decorator for registering event handlers."""
        def decorator(func):
            self.event_handlers[event_type].append(func)
            return func
        return decorator
    
    def on_message(self, message_type: type):
        """Decorator for registering message handlers."""
        def decorator(func):
            if message_type not in self.message_handlers:
                self.message_handlers[message_type] = []
            self.message_handlers[message_type].append(func)
            return func
        return decorator
    
    def add_server_script(self, name: str, interval: float, function: Callable):
        """Add a server script."""
        self.scripts[name] = ServerScript(name, interval, function)
    
    def remove_server_script(self, name: str):
        """Remove a server script."""
        if name in self.scripts:
            del self.scripts[name]
    
    def toggle_server_scripts(self, enabled: bool):
        """Enable or disable all server scripts."""
        for script in self.scripts.values():
            script.enabled = enabled
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        with self._lock:
            return {
                'total_clients': len(self.clients),
                'connected_clients': len([c for c in self.clients.values() if not c.disconnected]),
                'max_clients': self.max_clients,
                'uptime': self.performance_monitor.get_metrics().uptime,
                'scripts_count': len(self.scripts),
                'active_scripts': len([s for s in self.scripts.values() if s.enabled]),
                'average_ping': sum(c.ping for c in self.clients.values()) / max(len(self.clients), 1)
            }
    
    def kick_client(self, client_id: int, reason: str = "Kicked by server") -> bool:
        """Kick a client from the server."""
        if client_id not in self.clients:
            return False
        
        self._disconnect_client(client_id, reason)
        return True


class NetworkClient:
    """Network client for connecting to servers."""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 5555):
        self.server_host = server_host
        self.server_port = server_port
        self.username = "Player"
        self.password = None
        
        self.socket = None
        self.connected = False
        self.client_id = None
        
        self.event_handlers: Dict[NetworkEventType, List[Callable]] = {et: [] for et in NetworkEventType}
        self.message_handlers: Dict[type, List[Callable]] = {}
        
        self.performance_monitor = PerformanceMonitor()
        self.receive_thread = None
        self.running = False
        
        self._lock = threading.RLock()
        self._event_queue = queue.Queue()
        self._send_queue = queue.Queue()
    
    def connect(self, username: str = None, password: str = None) -> bool:
        """Connect to the server."""
        if username:
            self.username = username
        if password:
            self.password = password
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.server_host, self.server_port))
            self.socket.setblocking(False)
            
            self.connected = True
            self.running = True
            
            # Start threads
            self.receive_thread = threading.Thread(target=self._receive_thread, daemon=True)
            self.receive_thread.start()
            
            threading.Thread(target=self._processing_thread, daemon=True).start()
            threading.Thread(target=self._send_thread, daemon=True).start()
            
            # Send authentication
            auth_data = {
                'type': 'auth',
                'username': self.username,
                'password_hash': hashlib.sha256(self.password.encode()).hexdigest() if self.password else None
            }
            self.send(auth_data)
            
            print(f"Connected to server at {self.server_host}:{self.server_port}")
            self._queue_event(NetworkEventType.CONNECT, 0, None)
            return True
            
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.disconnect()
            return False
    
    def disconnect(self, reason: str = "Client disconnected"):
        """Disconnect from the server."""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print(f"Disconnected from server: {reason}")
        self._queue_event(NetworkEventType.DISCONNECT, 0, {'reason': reason})
    
    def _receive_thread(self):
        """Thread for receiving data from server."""
        while self.running and self.connected:
            try:
                readable, _, exceptional = select.select([self.socket], [], [self.socket], 0.1)
                
                if self.socket in readable:
                    data = b""
                    while True:
                        try:
                            chunk = self.socket.recv(4096)
                            if not chunk:
                                self.disconnect("Connection closed by server")
                                break
                            data += chunk
                            if len(chunk) < 4096:
                                break
                        except socket.error as e:
                            if e.errno == errno.EWOULDBLOCK:
                                break
                            else:
                                raise
                    
                    if data:
                        self._process_received_data(data)
                
                if self.socket in exceptional:
                    self.disconnect("Socket error")
                    
            except Exception as e:
                if self.running and self.connected:
                    print(f"Receive thread error: {e}")
                    self.disconnect(str(e))
    
    def _process_received_data(self, data: bytes):
        """Process received data from server."""
        try:
            message = pickle.loads(data)
            
            # Handle heartbeat
            if isinstance(message, dict) and message.get('type') == 'heartbeat':
                # Update ping
                server_time = message.get('timestamp', 0)
                ping = (time.time() - server_time) * 1000
                self.performance_monitor.update_ping(ping)
                self._queue_event(NetworkEventType.PING_UPDATE, 0, {'ping': ping})
                return
            
            # Queue message for processing
            self._queue_event(NetworkEventType.MESSAGE, 0, message)
            
        except Exception as e:
            print(f"Error processing received data: {e}")
    
    def _send_thread(self):
        """Thread for sending data to server."""
        while self.running and self.connected:
            try:
                message = self._send_queue.get(timeout=0.1)
                serialized = pickle.dumps(message)
                
                try:
                    self.socket.sendall(serialized)
                except Exception as e:
                    print(f"Error sending message: {e}")
                    self.disconnect(str(e))
                    
            except queue.Empty:
                continue
            except Exception as e:
                if self.running:
                    print(f"Send thread error: {e}")
    
    def _processing_thread(self):
        """Thread for processing events."""
        while self.running:
            try:
                while True:
                    event = self._event_queue.get_nowait()
                    self._handle_event(event)
            except queue.Empty:
                pass
            
            time.sleep(0.01)
    
    def _handle_event(self, event: NetworkEvent):
        """Handle a network event."""
        # Call event handlers
        for handler in self.event_handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")
        
        # Call message handlers for MESSAGE events
        if event.event_type == NetworkEventType.MESSAGE and event.data:
            message_type = type(event.data)
            for handler in self.message_handlers.get(message_type, []):
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in message handler: {e}")
    
    def _queue_event(self, event_type: NetworkEventType, client_id: Optional[int], data: Any):
        """Queue an event for processing."""
        self._event_queue.put(NetworkEvent(event_type, client_id, data))
    
    def send(self, message: Any):
        """Send a message to the server."""
        if self.connected and self.running:
            self._send_queue.put(message)
    
    def on_event(self, event_type: NetworkEventType):
        """Decorator for registering event handlers."""
        def decorator(func):
            self.event_handlers[event_type].append(func)
            return func
        return decorator
    
    def on_message(self, message_type: type):
        """Decorator for registering message handlers."""
        def decorator(func):
            if message_type not in self.message_handlers:
                self.message_handlers[message_type] = []
            self.message_handlers[message_type].append(func)
            return func
        return decorator


class HostClient:
    """Hybrid host-client that can act as both server and client."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5555, 
                 max_peers: int = 8, password: str = None):
        self.host = host
        self.port = port
        self.max_peers = max_peers
        self.password = password
        
        self.mode = HostClientMode.DISCONNECTED
        self.server = None
        self.client = None
        self.local_peer_id = 0
        
        self.event_handlers: Dict[NetworkEventType, List[Callable]] = {et: [] for et in NetworkEventType}
        self.message_handlers: Dict[type, List[Callable]] = {}
        
        self.peers: Dict[int, ClientInfo] = {}
        self.running = False
        
        self._lock = threading.RLock()
    
    def start_as_host(self) -> bool:
        """Start as host (server + local client)."""
        if self.mode != HostClientMode.DISCONNECTED:
            return False
        
        try:
            self.server = Server(self.host, self.port, self.max_peers, self.password)
            self.client = NetworkClient(self.host, self.port)
            
            if not self.server.start():
                return False
            
            # Wait a moment for server to start
            time.sleep(0.5)
            
            if not self.client.connect("Host", self.password):
                self.server.stop()
                return False
            
            self.mode = HostClientMode.HOST
            self.local_peer_id = 0
            self.running = True
            
            # Setup event forwarding
            self._setup_event_forwarding()
            
            print(f"Host started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"Failed to start as host: {e}")
            self.stop()
            return False
    
    def connect_as_client(self, server_host: str, server_port: int, 
                         password: str = None) -> bool:
        """Connect to a host as client."""
        if self.mode != HostClientMode.DISCONNECTED:
            return False
        
        try:
            self.client = NetworkClient(server_host, server_port)
            
            if not self.client.connect("Client", password):
                return False
            
            self.mode = HostClientMode.CLIENT
            self.running = True
            
            # Setup event forwarding
            self._setup_event_forwarding()
            
            print(f"Connected as client to {server_host}:{server_port}")
            return True
            
        except Exception as e:
            print(f"Failed to connect as client: {e}")
            self.stop()
            return False
    
    def _setup_event_forwarding(self):
        """Setup event forwarding from server/client to unified handlers."""
        if self.server:
            for event_type in NetworkEventType:
                @self.server.on_event(event_type)
                def forward_server_event(event):
                    self._handle_event(event)
        
        if self.client:
            for event_type in NetworkEventType:
                @self.client.on_event(event_type)
                def forward_client_event(event):
                    self._handle_event(event)
    
    def _handle_event(self, event: NetworkEvent):
        """Handle events from server or client."""
        # Update peer info for CONNECT/DISCONNECT events
        if event.event_type == NetworkEventType.CONNECT:
            with self._lock:
                if event.client_id not in self.peers:
                    self.peers[event.client_id] = ClientInfo(
                        client_id=event.client_id,
                        address=('localhost', self.port) if self.mode == HostClientMode.HOST else None
                    )
        elif event.event_type == NetworkEventType.DISCONNECT:
            with self._lock:
                if event.client_id in self.peers:
                    del self.peers[event.client_id]
        
        # Call registered handlers
        for handler in self.event_handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")
    
    def send_to_all(self, message: Any, exclude_self: bool = False):
        """Send message to all peers."""
        if self.mode == HostClientMode.HOST and self.server:
            exclude_id = 0 if exclude_self else None
            self.server.broadcast(message, exclude_client_id=exclude_id)
        
        elif self.mode == HostClientMode.CLIENT and self.client:
            self.client.send(message)
    
    def send_to_peer(self, peer_id: int, message: Any):
        """Send message to specific peer."""
        if self.mode == HostClientMode.HOST and self.server:
            self.server.send_to_client(peer_id, message)
        
        elif self.mode == HostClientMode.CLIENT and self.client:
            # Clients can only send to server
            self.client.send(message)
    
    def disconnect(self, reason: str = "Disconnected"):
        """Disconnect from network."""
        self.running = False
        
        if self.server:
            self.server.stop()
            self.server = None
        
        if self.client:
            self.client.disconnect(reason)
            self.client = None
        
        self.mode = HostClientMode.DISCONNECTED
        self.peers.clear()
        
        print(f"Disconnected: {reason}")
    
    def on_event(self, event_type: NetworkEventType):
        """Decorator for registering event handlers."""
        def decorator(func):
            self.event_handlers[event_type].append(func)
            return func
        return decorator
    
    def on_message(self, message_type: type):
        """Decorator for registering message handlers."""
        def decorator(func):
            if message_type not in self.message_handlers:
                self.message_handlers[message_type] = []
            self.message_handlers[message_type].append(func)
            return func
        return decorator
    
    def get_peer_count(self) -> int:
        """Get number of connected peers."""
        with self._lock:
            return len(self.peers)
    
    def kick_peer(self, peer_id: int, reason: str = "Kicked") -> bool:
        """Kick a peer (host only)."""
        if self.mode != HostClientMode.HOST or not self.server:
            return False
        
        return self.server.kick_client(peer_id, reason)
    
    def toggle_server_scripts(self, enabled: bool):
        """Toggle server scripts (host only)."""
        if self.mode == HostClientMode.HOST and self.server:
            self.server.toggle_server_scripts(enabled)
    
    def add_server_script(self, name: str, interval: float, function: Callable):
        """Add a server script (host only)."""
        if self.mode == HostClientMode.HOST and self.server:
            self.server.add_server_script(name, interval, function)
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics (host only)."""
        if self.mode == HostClientMode.HOST and self.server:
            return self.server.get_server_stats()
        return {}


class NetworkDiscovery:
    """Discovers network games on local network."""
    
    def __init__(self, broadcast_port: int = 55555, discovery_port: int = 55556):
        self.broadcast_port = broadcast_port
        self.discovery_port = discovery_port
        self.broadcast_socket = None
        self.discovery_socket = None
        self.running = False
    
    def broadcast_presence(self, game_name: str, game_port: int, interval: float = 2.0):
        """Broadcast game presence on local network."""
        try:
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.broadcast_socket.settimeout(0.1)
            
            message = json.dumps({
                'game_name': game_name,
                'game_port': game_port,
                'host_ip': get_local_ip(),
                'timestamp': time.time()
            }).encode('utf-8')
            
            while True:
                try:
                    self.broadcast_socket.sendto(
                        message, 
                        ('<broadcast>', self.broadcast_port)
                    )
                    time.sleep(interval)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Broadcast error: {e}")
                    break
                    
        finally:
            if self.broadcast_socket:
                self.broadcast_socket.close()
    
    def discover_hosts(self, timeout: float = 5.0) -> List[Tuple[str, int, str]]:
        """Discover available hosts on local network."""
        try:
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.discovery_socket.settimeout(timeout)
            self.discovery_socket.bind(('', self.discovery_port))
            
            discovered_hosts = []
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    data, addr = self.discovery_socket.recvfrom(1024)
                    message = json.loads(data.decode('utf-8'))
                    
                    host_ip = message.get('host_ip', addr[0])
                    game_port = message.get('game_port', 5555)
                    game_name = message.get('game_name', 'Unknown Game')
                    
                    discovered_hosts.append((host_ip, game_port, game_name))
                    
                except socket.timeout:
                    break
                except Exception as e:
                    print(f"Discovery error: {e}")
                    continue
            
            # Remove duplicates
            unique_hosts = []
            seen = set()
            for host in discovered_hosts:
                key = (host[0], host[1])
                if key not in seen:
                    seen.add(key)
                    unique_hosts.append(host)
            
            return unique_hosts
            
        finally:
            if self.discovery_socket:
                self.discovery_socket.close()


# Network utility functions

def get_local_ip() -> str:
    """Get the local IP address of this machine."""
    try:
        # Create a socket to find local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        
        try:
            # Doesn't need to be reachable
            s.connect(('10.254.254.254', 1))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            s.close()
        
        return local_ip
        
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return '127.0.0.1'


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """Check if a port is available for binding."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.close()
        return True
    except socket.error:
        return False


def find_available_port(start_port: int = 5555, end_port: int = 5655, 
                       host: str = "0.0.0.0") -> Optional[int]:
    """Find an available port in the specified range."""
    for port in range(start_port, end_port + 1):
        if is_port_available(port, host):
            return port
    return None


# Convenience classes for common message types

class NetworkMessages:
    """Factory for common network messages."""
    
    @staticmethod
    def create_chat(message: str, player_id: str = "", sender_name: str = "") -> ChatMessage:
        """Create a chat message."""
        return ChatMessage(message, player_id, sender_name)
    
    @staticmethod
    def create_player_position(x: float, y: float, player_id: str) -> PlayerPositionMessage:
        """Create a player position message."""
        return PlayerPositionMessage(x, y, player_id)
    
    @staticmethod
    def create_game_state(game_state: Dict[str, Any]) -> GameStateMessage:
        """Create a game state synchronization message."""
        return GameStateMessage(game_state)
    
    @staticmethod
    def create_player_info(player_name: str, player_id: str) -> PlayerInfoMessage:
        """Create a player information message."""
        return PlayerInfoMessage(player_name, player_id)
    
class SmoothPositionMessage(NetworkMessage):
    """Mensagem para atualização suave de posição com timestamp"""
    
    def __init__(self, x: float = 0.0, y: float = 0.0, player_id: str = "", 
                 velocity_x: float = 0.0, velocity_y: float = 0.0,
                 timestamp: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y
        self.player_id = player_id
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.timestamp = timestamp or time.time()
        self.version = 2


class PlayerInputMessage(NetworkMessage):
    """Mensagem para envio de inputs do jogador (mais eficiente)"""
    
    def __init__(self, inputs: Dict[str, bool] = None, player_id: str = "",
                 timestamp: float = 0.0):
        super().__init__()
        self.inputs = inputs or {}
        self.player_id = player_id
        self.timestamp = timestamp or time.time()
        self.version = 1


# Adicione esta classe para interpolação
class NetworkInterpolator:
    """Interpola posições para movimento suave"""
    
    def __init__(self, interpolation_time: float = 0.1):
        self.interpolation_time = interpolation_time  # 100ms de interpolação
        self.position_buffer: List[Tuple[float, float, float]] = []  # (x, y, timestamp)
        self.max_buffer_size = 10
        
    def add_position(self, x: float, y: float, timestamp: float):
        """Adiciona uma nova posição ao buffer"""
        self.position_buffer.append((x, y, timestamp))
        
        # Manter buffer ordenado por timestamp
        self.position_buffer.sort(key=lambda p: p[2])
        
        # Limitar tamanho do buffer
        if len(self.position_buffer) > self.max_buffer_size:
            self.position_buffer.pop(0)
    
    def get_interpolated_position(self, current_time: float):
        """Obtém posição interpolada para o tempo atual"""
        if len(self.position_buffer) < 2:
            if self.position_buffer:
                return self.position_buffer[-1][0], self.position_buffer[-1][1]
            return 0, 0
        
        # Encontrar posições para interpolar
        target_time = current_time - self.interpolation_time
        
        # Se target_time for mais antigo que a posição mais velha, usar a mais velha
        if target_time <= self.position_buffer[0][2]:
            return self.position_buffer[0][0], self.position_buffer[0][1]
        
        # Encontrar as duas posições entre as quais interpolar
        for i in range(len(self.position_buffer) - 1):
            t1 = self.position_buffer[i][2]
            t2 = self.position_buffer[i + 1][2]
            
            if t1 <= target_time <= t2:
                # Interpolar linearmente
                alpha = (target_time - t1) / (t2 - t1)
                x1, y1 = self.position_buffer[i][0], self.position_buffer[i][1]
                x2, y2 = self.position_buffer[i + 1][0], self.position_buffer[i + 1][1]
                
                x = x1 + (x2 - x1) * alpha
                y = y1 + (y2 - y1) * alpha
                return x, y
        
        # Se target_time for mais novo que a posição mais recente, usar extrapolação
        x1, y1, t1 = self.position_buffer[-2]
        x2, y2, t2 = self.position_buffer[-1]
        
        if t2 > t1:
            # Extrapolar baseado na velocidade
            dt = target_time - t2
            dx = x2 - x1
            dy = y2 - y1
            dt_prev = t2 - t1
            
            if dt_prev > 0:
                vx = dx / dt_prev
                vy = dy / dt_prev
                x = x2 + vx * dt
                y = y2 + vy * dt
                return x, y
        
        return self.position_buffer[-1][0], self.position_buffer[-1][1]
    
    def clear(self):
        """Limpa o buffer"""
        self.position_buffer.clear()