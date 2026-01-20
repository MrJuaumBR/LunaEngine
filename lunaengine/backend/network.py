# lunaengine/backend/network.py
"""
Network module for client-server communication with proper architecture.
Uses JSON for safe serialization and implements a clean protocol.
FIXED: Server now properly responds to ping messages
ADDED: Host class that runs server in thread and connects as client
"""

import socket
import json
import threading
import time
import queue
import uuid
import logging
import select
from typing import Dict, List, Optional, Any, Callable, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Protocol Definitions ====================

class MessageType(Enum):
    """Types of messages in the protocol"""
    HANDSHAKE = "handshake"
    AUTHENTICATION = "auth"
    DATA = "data"
    COMMAND = "command"
    EVENT = "event"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    DISCONNECT = "disconnect"

class UserType(Enum):
    """Types of network users"""
    SERVER = "server"
    CLIENT = "client"
    HOST = "host"

@dataclass
class NetworkMessage:
    """Standard message format for network communication"""
    message_id: str
    message_type: MessageType
    sender_id: str
    sender_type: UserType  # Added sender type
    timestamp: float
    payload: Optional[Any] = None
    target: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        data['sender_type'] = self.sender_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkMessage':
        """Create from dictionary"""
        data['message_type'] = MessageType(data['message_type'])
        data['sender_type'] = UserType(data['sender_type'])
        return cls(**data)

# ==================== Utility Functions ====================

def generate_id() -> str:
    """Generate unique ID for clients/messages"""
    return str(uuid.uuid4())

def validate_port(port: int) -> bool:
    """Validate port number"""
    return 1024 <= port <= 65535

def safe_json_dumps(data: Any) -> bytes:
    """Safely serialize data to JSON bytes"""
    return json.dumps(data, default=str).encode('utf-8')

def safe_json_loads(data: bytes) -> Any:
    """Safely deserialize JSON bytes"""
    return json.loads(data.decode('utf-8'))

# ==================== Client Class ====================

class NetworkClient:
    """Client for connecting to network server"""
    
    def __init__(self, client_id: Optional[str] = None):
        self.client_id = client_id or generate_id()
        self.user_type = UserType.CLIENT  # Default type
        self.socket: Optional[socket.socket] = None
        self.connected: bool = False
        self.server_address: Optional[tuple] = None
        self.receive_thread: Optional[threading.Thread] = None
        self.callbacks: Dict[str, Callable] = {}
        self.message_queue = queue.Queue()
        self.running = False
        self.ping_interval = 30  # seconds
        self.last_pong = time.time()
        self.ping_timeout = 60  # Time to wait before declaring connection dead
        
    def connect(self, host: str, port: int, timeout: int = 5) -> bool:
        """Connect to server with timeout"""
        if self.connected:
            logger.warning("Client already connected")
            return True
            
        try:
            if not validate_port(port):
                logger.error(f"Invalid port: {port}")
                return False
                
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((host, port))
            self.server_address = (host, port)
            self.connected = True
            
            # Start receiving thread
            self.running = True
            self.receive_thread = threading.Thread(
                target=self._receive_loop,
                daemon=True
            )
            self.receive_thread.start()
            
            # Start ping thread
            threading.Thread(
                target=self._ping_loop,
                daemon=True
            ).start()
            
            logger.info(f"{self.user_type.value.capitalize()} connected to {host}:{port}")
            return True
            
        except socket.timeout:
            logger.error(f"Connection timeout to {host}:{port}")
        except ConnectionRefusedError:
            logger.error(f"Connection refused to {host}:{port}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        
        return False
    
    def disconnect(self) -> None:
        """Disconnect from server"""
        if not self.connected:
            return
            
        self.running = False
        self.connected = False
        
        # Send disconnect message
        if self.socket:
            try:
                msg = NetworkMessage(
                    message_id=generate_id(),
                    message_type=MessageType.DISCONNECT,
                    sender_id=self.client_id,
                    sender_type=self.user_type,
                    timestamp=time.time()
                )
                self._send_raw(msg.to_dict())
            except:
                pass
            
            try:
                self.socket.close()
            except:
                pass
        
        logger.info(f"{self.user_type.value.capitalize()} disconnected from server")
    
    def send(self, message_type: MessageType, payload: Any = None, 
             target: Optional[str] = None) -> bool:
        """Send message to server"""
        if not self.connected:
            logger.error("Not connected to server")
            return False
            
        try:
            msg = NetworkMessage(
                message_id=generate_id(),
                message_type=message_type,
                sender_id=self.client_id,
                sender_type=self.user_type,
                timestamp=time.time(),
                payload=payload,
                target=target
            )
            
            return self._send_raw(msg.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def _send_raw(self, data: Dict[str, Any]) -> bool:
        """Send raw data to server"""
        try:
            # Add message size header
            json_data = safe_json_dumps(data)
            size_header = len(json_data).to_bytes(4, 'big')
            self.socket.sendall(size_header + json_data)
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.connected = False
            return False
    
    def _receive_loop(self) -> None:
        """Receive messages in a loop"""
        buffer = b""
        expected_size = None
        
        while self.running and self.connected:
            try:
                # Use select to check if data is available (non-blocking check)
                ready_to_read, _, _ = select.select([self.socket], [], [], 0.1)
                if not ready_to_read:
                    continue
                
                # Receive data
                chunk = self.socket.recv(4096)
                if not chunk:
                    logger.warning(f"Connection closed by server")
                    self.connected = False
                    break
                    
                buffer += chunk
                
                # Process complete messages
                while len(buffer) >= 4:
                    # Read message size
                    if expected_size is None:
                        expected_size = int.from_bytes(buffer[:4], 'big')
                        buffer = buffer[4:]
                    
                    # Check if we have enough data
                    if len(buffer) >= expected_size:
                        json_data = buffer[:expected_size]
                        buffer = buffer[expected_size:]
                        
                        try:
                            data = safe_json_loads(json_data)
                            self._handle_message(data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON: {e}")
                        
                        expected_size = None
                    else:
                        break
                        
            except socket.timeout:
                continue
            except ConnectionError:
                logger.warning("Connection lost")
                self.connected = False
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")
                self.connected = False
                break
    
    def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle incoming message"""
        try:
            msg = NetworkMessage.from_dict(data)
            
            # Handle ping/pong
            if msg.message_type == MessageType.PING:
                self._send_pong(msg.message_id)
                return
            elif msg.message_type == MessageType.PONG:
                self.last_pong = time.time()
                logger.debug(f"Received pong from server, last_pong updated")
                return
            
            # Call registered callback
            callback = self.callbacks.get(msg.message_type.value)
            if callback:
                callback(msg)
            else:
                # Default: put in queue
                self.message_queue.put(msg)
                
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    def _ping_loop(self) -> None:
        """Send periodic ping to keep connection alive"""
        while self.running and self.connected:
            time.sleep(self.ping_interval)
            
            # Check last pong time
            current_time = time.time()
            time_since_last_pong = current_time - self.last_pong
            
            if time_since_last_pong > self.ping_timeout:
                logger.warning(f"No pong received for {time_since_last_pong:.1f}s, connection may be dead")
                self.connected = False
                break
            
            if self.connected:
                # Send ping with current timestamp
                logger.debug(f"Sending ping to server")
                self.send(MessageType.PING, {"client_time": current_time})
    
    def _send_pong(self, ping_message_id: str) -> None:
        """Send pong response to a ping"""
        pong_msg = NetworkMessage(
            message_id=generate_id(),
            message_type=MessageType.PONG,
            sender_id=self.client_id,
            sender_type=self.user_type,
            timestamp=time.time(),
            payload={"responding_to": ping_message_id}
        )
        self._send_raw(pong_msg.to_dict())
    
    def register_callback(self, message_type: MessageType, 
                         callback: Callable) -> None:
        """Register callback for specific message type"""
        self.callbacks[message_type.value] = callback
    
    def get_message(self, timeout: Optional[float] = None) -> Optional[NetworkMessage]:
        """Get message from queue with timeout"""
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

# ==================== Server Class ====================

class NetworkServer:
    """Server for handling multiple client connections"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 4723, 
                 max_clients: int = 10):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.user_type = UserType.SERVER
        
        self.server_socket: Optional[socket.socket] = None
        self.clients: Dict[str, socket.socket] = {}
        self.client_info: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.accept_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()  # Using RLock for reentrant locking
        self.callbacks: Dict[str, Callable] = {}
        self.message_queue = queue.Queue()
        
        # Thread pools for handling clients
        self.client_threads: Dict[str, threading.Thread] = {}
        self.thread_pool = []
        
        # Authentication
        self.require_auth = False
        self.auth_tokens = set()
        
    def start(self) -> bool:
        """Start the server"""
        if self.running:
            logger.warning("Server already running")
            return True
            
        if not validate_port(self.port):
            logger.error(f"Invalid port: {self.port}")
            return False
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            self.server_socket.setblocking(False)  # Non-blocking for accept
            
            self.running = True
            
            # Start accept thread
            self.accept_thread = threading.Thread(
                target=self._accept_connections,
                daemon=True
            )
            self.accept_thread.start()
            
            logger.info(f"Server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the server"""
        if not self.running:
            return
            
        self.running = False
        
        # Disconnect all clients
        with self.lock:
            client_ids = list(self.clients.keys())
            for client_id in client_ids:
                self._disconnect_client(client_id, send_notification=False)
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Wait for threads to finish
        for thread in self.thread_pool:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        logger.info("Server stopped")
    
    def _accept_connections(self) -> None:
        """Accept incoming connections (non-blocking)"""
        while self.running:
            try:
                # Use select to check for new connections
                ready_to_read, _, _ = select.select([self.server_socket], [], [], 0.5)
                if not ready_to_read:
                    continue
                    
                client_socket, client_address = self.server_socket.accept()
                client_socket.setblocking(False)  # Non-blocking for client socket
                
                # Generate client ID
                client_id = generate_id()
                
                with self.lock:
                    self.clients[client_id] = client_socket
                    self.client_info[client_id] = {
                        "address": client_address,
                        "connected_at": time.time(),
                        "authenticated": not self.require_auth,  # Auto-auth if no auth required
                        "last_activity": time.time()
                    }
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_id, client_socket),
                    daemon=True
                )
                self.client_threads[client_id] = client_thread
                self.thread_pool.append(client_thread)
                client_thread.start()
                
                logger.info(f"New connection from {client_address}, ID: {client_id}")
                
            except BlockingIOError:
                # No connection pending, continue
                continue
            except OSError:
                # Socket closed during accept
                if self.running:
                    logger.error("Server socket error")
                break
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_id: str, client_socket: socket.socket) -> None:
        """Handle communication with a single client"""
        buffer = b""
        expected_size = None
        
        try:
            while self.running:
                try:
                    # Use select to check if data is available
                    ready_to_read, _, _ = select.select([client_socket], [], [], 0.5)
                    if not ready_to_read:
                        # Check for client timeout
                        with self.lock:
                            if client_id in self.client_info:
                                last_activity = self.client_info[client_id].get("last_activity", 0)
                                if time.time() - last_activity > 300:  # 5 minutes timeout
                                    logger.info(f"Client {client_id} timeout")
                                    break
                        continue
                    
                    # Receive data
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    
                    # Update last activity
                    with self.lock:
                        if client_id in self.client_info:
                            self.client_info[client_id]["last_activity"] = time.time()
                    
                    buffer += chunk
                    
                    # Process complete messages
                    while len(buffer) >= 4:
                        # Read message size
                        if expected_size is None:
                            expected_size = int.from_bytes(buffer[:4], 'big')
                            buffer = buffer[4:]
                        
                        # Check if we have enough data
                        if len(buffer) >= expected_size:
                            json_data = buffer[:expected_size]
                            buffer = buffer[expected_size:]
                            
                            try:
                                data = safe_json_loads(json_data)
                                self._process_client_message(client_id, data)
                            except json.JSONDecodeError as e:
                                logger.error(f"Invalid JSON from {client_id}: {e}")
                                self._send_error(client_id, "Invalid message format")
                            
                            expected_size = None
                        else:
                            break
                            
                except BlockingIOError:
                    # No data available, continue
                    continue
                except ConnectionError:
                    break
                except Exception as e:
                    logger.error(f"Error with client {client_id}: {e}")
                    break
                    
        finally:
            # Clean up client
            self._disconnect_client(client_id)
    
    def _process_client_message(self, client_id: str, data: Dict[str, Any]) -> None:
        """Process message from client"""
        try:
            msg = NetworkMessage.from_dict(data)
            
            # Update last activity
            with self.lock:
                if client_id in self.client_info:
                    self.client_info[client_id]["last_activity"] = time.time()
            
            # Check authentication if required
            if (self.require_auth and 
                not self.client_info[client_id]["authenticated"] and
                msg.message_type != MessageType.AUTHENTICATION):
                self._send_error(client_id, "Authentication required")
                return
            
            # Handle different message types
            if msg.message_type == MessageType.AUTHENTICATION:
                self._handle_auth(client_id, msg.payload)
            elif msg.message_type == MessageType.PING:
                # Respond to ping immediately with pong
                self._send_pong(client_id, msg)
            elif msg.message_type == MessageType.DISCONNECT:
                self._disconnect_client(client_id)
            else:
                # Call registered callback or put in queue
                callback = self.callbacks.get(msg.message_type.value)
                if callback:
                    callback(client_id, msg)
                else:
                    self.message_queue.put((client_id, msg))
                    
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            self._send_error(client_id, "Message processing failed")
    
    def _handle_auth(self, client_id: str, payload: Any) -> None:
        """Handle client authentication"""
        if not self.require_auth:
            with self.lock:
                self.client_info[client_id]["authenticated"] = True
            self._send_to_client(client_id, {
                "message_id": generate_id(),
                "message_type": MessageType.AUTHENTICATION.value,
                "sender_id": "server",
                "sender_type": self.user_type.value,
                "timestamp": time.time(),
                "payload": {
                    "success": True,
                    "message": "Authentication not required"
                }
            })
            return
        
        # Check token
        token = payload.get("token") if isinstance(payload, dict) else payload
        if token in self.auth_tokens:
            with self.lock:
                self.client_info[client_id]["authenticated"] = True
                self.auth_tokens.remove(token)  # One-time use token
            
            self._send_to_client(client_id, {
                "message_id": generate_id(),
                "message_type": MessageType.AUTHENTICATION.value,
                "sender_id": "server",
                "sender_type": self.user_type.value,
                "timestamp": time.time(),
                "payload": {
                    "success": True,
                    "client_id": client_id,
                    "message": "Authentication successful"
                }
            })
            logger.info(f"Client {client_id} authenticated")
        else:
            self._send_to_client(client_id, {
                "message_id": generate_id(),
                "message_type": MessageType.AUTHENTICATION.value,
                "sender_id": "server",
                "sender_type": self.user_type.value,
                "timestamp": time.time(),
                "payload": {
                    "success": False,
                    "message": "Invalid authentication token"
                }
            })
    
    def _send_pong(self, client_id: str, ping_message: NetworkMessage) -> None:
        """Send pong response to client ping"""
        pong_msg = {
            "message_id": generate_id(),
            "message_type": MessageType.PONG.value,
            "sender_id": "server",
            "sender_type": self.user_type.value,
            "timestamp": time.time(),
            "payload": {
                "responding_to": ping_message.message_id,
                "server_time": time.time()
            }
        }
        self._send_to_client(client_id, pong_msg)
    
    def _send_to_client(self, client_id: str, data: Dict[str, Any]) -> bool:
        """Send data to specific client"""
        with self.lock:
            if client_id not in self.clients:
                return False
            
            try:
                json_data = safe_json_dumps(data)
                size_header = len(json_data).to_bytes(4, 'big')
                self.clients[client_id].sendall(size_header + json_data)
                return True
            except (ConnectionError, OSError) as e:
                logger.error(f"Failed to send to client {client_id}: {e}")
                # Mark client for disconnection
                threading.Thread(
                    target=self._disconnect_client,
                    args=(client_id,),
                    daemon=True
                ).start()
                return False
            except Exception as e:
                logger.error(f"Unexpected error sending to client {client_id}: {e}")
                return False
    
    def broadcast(self, data: Dict[str, Any], 
                  exclude: Optional[List[str]] = None) -> int:
        """Broadcast data to all connected clients"""
        exclude = exclude or []
        success_count = 0
        
        with self.lock:
            client_ids = list(self.clients.keys())
            
        for client_id in client_ids:
            if client_id not in exclude:
                if self._send_to_client(client_id, data):
                    success_count += 1
        
        return success_count
    
    def _send_error(self, client_id: str, message: str) -> None:
        """Send error message to client"""
        self._send_to_client(client_id, {
            "message_id": generate_id(),
            "message_type": MessageType.ERROR.value,
            "sender_id": "server",
            "sender_type": self.user_type.value,
            "timestamp": time.time(),
            "payload": {
                "error": message
            }
        })
    
    def _disconnect_client(self, client_id: str, send_notification: bool = True) -> None:
        """Disconnect and clean up client"""
        with self.lock:
            if client_id not in self.clients:
                return
            
            # Send disconnect notification if requested
            if send_notification:
                try:
                    self._send_to_client(client_id, {
                        "message_id": generate_id(),
                        "message_type": MessageType.DISCONNECT.value,
                        "sender_id": "server",
                        "sender_type": self.user_type.value,
                        "timestamp": time.time(),
                        "payload": {
                            "message": "Disconnected by server"
                        }
                    })
                except:
                    pass
            
            # Close socket
            try:
                self.clients[client_id].close()
            except:
                pass
            
            # Remove from client lists
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.client_info:
                del self.client_info[client_id]
            if client_id in self.client_threads:
                del self.client_threads[client_id]
        
        logger.info(f"Client {client_id} disconnected")
    
    def get_client_count(self) -> int:
        """Get number of connected clients"""
        with self.lock:
            return len(self.clients)
    
    def get_client_ids(self) -> List[str]:
        """Get list of connected client IDs"""
        with self.lock:
            return list(self.clients.keys())
    
    def register_callback(self, message_type: MessageType, 
                         callback: Callable) -> None:
        """Register callback for specific message type"""
        self.callbacks[message_type.value] = callback
    
    def get_message(self, timeout: Optional[float] = None) -> Optional[tuple]:
        """Get message from queue with timeout"""
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def enable_auth(self, tokens: List[str]) -> None:
        """Enable authentication with provided tokens"""
        self.require_auth = True
        self.auth_tokens = set(tokens)
    
    def generate_auth_token(self) -> str:
        """Generate a new authentication token"""
        token = generate_id()
        self.auth_tokens.add(token)
        return token
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

# ==================== Host Class ====================

class NetworkHost:
    """Host class that runs a server in thread and connects as a client"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 4723, 
                 max_clients: int = 10):
        self.user_type = UserType.HOST
        self.host = host
        self.port = port
        self.max_clients = max_clients
        
        # Server component
        self.server = NetworkServer(host, port, max_clients)
        self.server_thread: Optional[threading.Thread] = None
        
        # Client component (connected to our own server)
        self.client = NetworkClient()
        self.client.user_type = self.user_type
        
        # Combined message queue
        self.message_queue = queue.Queue()
        
        # Track if running
        self.running = False
        
    def start(self) -> bool:
        """Start the host (server + connect as client)"""
        if self.running:
            logger.warning("Host already running")
            return True
        
        try:
            # Start the server in a separate thread
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            
            # Wait for server to start
            time.sleep(1)
            
            # Connect client to server
            if not self.client.connect(self.host, self.port):
                logger.error("Failed to connect client to local server")
                return False
            
            # Register callbacks to forward messages to queue
            def forward_to_queue(msg: NetworkMessage):
                self.message_queue.put(("client", msg))
            
            self.client.register_callback(MessageType.DATA, forward_to_queue)
            self.client.register_callback(MessageType.EVENT, forward_to_queue)
            self.client.register_callback(MessageType.COMMAND, forward_to_queue)
            
            # Also forward server messages
            def forward_server_message(client_id: str, msg: NetworkMessage):
                # Don't forward messages from our own client
                if client_id != self.client.client_id:
                    self.message_queue.put(("server", client_id, msg))
            
            self.server.register_callback(MessageType.DATA, forward_server_message)
            self.server.register_callback(MessageType.EVENT, forward_server_message)
            self.server.register_callback(MessageType.COMMAND, forward_server_message)
            
            self.running = True
            logger.info(f"Host started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start host: {e}")
            return False
    
    def _run_server(self):
        """Run the server (called in thread)"""
        self.server.start()
        
        # Keep server running
        try:
            while self.running:
                # Process server messages
                server_msg = self.server.get_message(timeout=1)
                if server_msg:
                    client_id, msg = server_msg
                    # Forward to queue if not already handled by callback
                    if msg.message_type not in [MessageType.PING, MessageType.PONG, 
                                               MessageType.AUTHENTICATION]:
                        self.message_queue.put(("server", client_id, msg))
                        
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Server thread error: {e}")
    
    def stop(self):
        """Stop the host"""
        if not self.running:
            return
            
        self.running = False
        
        # Disconnect client
        self.client.disconnect()
        
        # Stop server
        self.server.stop()
        
        # Wait for server thread
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2.0)
        
        logger.info("Host stopped")
    
    def send_as_host(self, message_type: MessageType, payload: Any = None,
                    target: Optional[str] = None) -> bool:
        """Send message as host client"""
        return self.client.send(message_type, payload, target)
    
    def broadcast_as_server(self, data: Dict[str, Any], 
                           exclude: Optional[List[str]] = None) -> int:
        """Broadcast message as server to all clients"""
        # Convert to proper message format
        message = {
            "message_id": generate_id(),
            "message_type": MessageType.DATA.value,
            "sender_id": "host_server",
            "sender_type": self.user_type.value,
            "timestamp": time.time(),
            "payload": data
        }
        return self.server.broadcast(message, exclude)
    
    def send_to_client(self, client_id: str, message_type: MessageType, 
                      payload: Any = None) -> bool:
        """Send message to specific client as server"""
        message = {
            "message_id": generate_id(),
            "message_type": message_type.value,
            "sender_id": "host_server",
            "sender_type": self.user_type.value,
            "timestamp": time.time(),
            "payload": payload
        }
        return self.server._send_to_client(client_id, message)
    
    def get_message(self, timeout: Optional[float] = None) -> Optional[tuple]:
        """Get message from queue with timeout"""
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_client_count(self) -> int:
        """Get number of connected clients (excluding host client)"""
        count = self.server.get_client_count()
        # Exclude our own client if connected
        if self.client.connected:
            count = max(0, count - 1)
        return count
    
    def get_client_ids(self) -> List[str]:
        """Get list of connected client IDs (excluding host client)"""
        client_ids = self.server.get_client_ids()
        # Remove our own client ID if present
        if self.client.client_id in client_ids:
            client_ids.remove(self.client.client_id)
        return client_ids
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

# ==================== Example Usage ====================

if __name__ == "__main__":
    import sys
    
    def example_server():
        """Example server implementation"""
        server = NetworkServer(host="127.0.0.1", port=4723)
        
        def handle_client_data(client_id: str, message: NetworkMessage):
            print(f"Server received from {client_id} ({message.sender_type.value}): {message.payload}")
            
            # Echo back to all clients
            response_msg = {
                "message_id": generate_id(),
                "message_type": MessageType.DATA.value,
                "sender_id": "server",
                "sender_type": server.user_type.value,
                "timestamp": time.time(),
                "payload": f"Client {client_id} said: {message.payload}"
            }
            server.broadcast(response_msg, exclude=[client_id])
        
        server.register_callback(MessageType.DATA, handle_client_data)
        
        with server:
            print("Server running. Press Ctrl+C to stop.")
            try:
                while True:
                    # Process messages from queue
                    msg = server.get_message(timeout=1)
                    if msg:
                        client_id, message = msg
                        print(f"Queued message from {client_id}: {message.payload}")
                    
                    # Show client count periodically
                    print(f"Clients connected: {server.get_client_count()}")
                    time.sleep(5)
                    
            except KeyboardInterrupt:
                print("\nShutting down server...")
    
    def example_client():
        """Example client implementation"""
        client = NetworkClient()
        
        def handle_server_message(message: NetworkMessage):
            if message.message_type == MessageType.DATA:
                print(f"Client received from {message.sender_id} ({message.sender_type.value}): {message.payload}")
        
        client.register_callback(MessageType.DATA, handle_server_message)
        
        if client.connect("127.0.0.1", 4723):
            print(f"{client.user_type.value.capitalize()} connected. Type messages to send, 'exit' to quit.")
            
            try:
                while True:
                    user_input = input("> ")
                    if user_input.lower() == 'exit':
                        break
                    
                    client.send(MessageType.DATA, user_input)
                    
                    # Check for incoming messages
                    msg = client.get_message(timeout=0.1)
                    while msg:
                        print(f"Queued: {msg.payload}")
                        msg = client.get_message(timeout=0.1)
                        
            except KeyboardInterrupt:
                print("\nDisconnecting...")
            finally:
                client.disconnect()
        else:
            print("Failed to connect to server")
    
    def example_host():
        """Example host implementation"""
        host = NetworkHost(host="127.0.0.1", port=4723)
        
        if host.start():
            print(f"Host started. Type messages to send as host, 'broadcast' to send to all, or 'exit' to quit.")
            
            try:
                while True:
                    user_input = input("> ")
                    if user_input.lower() == 'exit':
                        break
                    elif user_input.lower() == 'broadcast':
                        # Broadcast to all clients
                        host.broadcast_as_server({"message": "Broadcast from host"})
                        print("Broadcast sent to all clients")
                    else:
                        # Send as host client
                        host.send_as_host(MessageType.DATA, user_input)
                    
                    # Check for incoming messages
                    msg = host.get_message(timeout=0.1)
                    while msg:
                        source = msg[0]
                        if source == "client":
                            # Message from server to our client
                            message = msg[1]
                            print(f"Host received as client: {message.payload}")
                        elif source == "server":
                            # Message from a client to our server
                            client_id, message = msg[1], msg[2]
                            print(f"Host server received from {client_id}: {message.payload}")
                            
                            # Echo back
                            host.send_to_client(client_id, MessageType.DATA, 
                                              f"Echo: {message.payload}")
                        
                        msg = host.get_message(timeout=0.1)
                        
                    # Show client count
                    print(f"Clients connected (excluding host): {host.get_client_count()}")
                        
            except KeyboardInterrupt:
                print("\nShutting down host...")
            finally:
                host.stop()
        else:
            print("Failed to start host")
    
    # Run example
    if len(sys.argv) > 1:
        if sys.argv[1] == "server":
            example_server()
        elif sys.argv[1] == "host":
            example_host()
        else:
            example_client()
    else:
        example_client()