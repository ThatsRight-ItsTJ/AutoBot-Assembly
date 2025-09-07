"""
WebSocket Handler

Real-time communication handler for web interface.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

try:
    from flask_socketio import SocketIO, emit
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    SocketIO = None


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    
    session_id: str
    client_id: str
    connect_time: float
    last_activity: float
    subscribed_sessions: Set[str]


class ConnectionManager:
    """Manages WebSocket connections and rooms."""
    
    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.session_subscribers: Dict[str, Set[str]] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_connection(self, client_id: str) -> ConnectionInfo:
        """Add a new connection."""
        
        connection = ConnectionInfo(
            session_id="",
            client_id=client_id,
            connect_time=time.time(),
            last_activity=time.time(),
            subscribed_sessions=set()
        )
        
        self.connections[client_id] = connection
        self.logger.info(f"New connection: {client_id}")
        
        return connection
    
    def remove_connection(self, client_id: str):
        """Remove a connection."""
        
        if client_id in self.connections:
            connection = self.connections[client_id]
            
            # Unsubscribe from all sessions
            for session_id in connection.subscribed_sessions:
                self.unsubscribe_from_session(client_id, session_id)
            
            del self.connections[client_id]
            self.logger.info(f"Connection removed: {client_id}")
    
    def subscribe_to_session(self, client_id: str, session_id: str):
        """Subscribe a client to session updates."""
        
        if client_id not in self.connections:
            return False
        
        connection = self.connections[client_id]
        connection.subscribed_sessions.add(session_id)
        
        if session_id not in self.session_subscribers:
            self.session_subscribers[session_id] = set()
        
        self.session_subscribers[session_id].add(client_id)
        self.logger.info(f"Client {client_id} subscribed to session {session_id}")
        
        return True
    
    def unsubscribe_from_session(self, client_id: str, session_id: str):
        """Unsubscribe a client from session updates."""
        
        if client_id in self.connections:
            self.connections[client_id].subscribed_sessions.discard(session_id)
        
        if session_id in self.session_subscribers:
            self.session_subscribers[session_id].discard(client_id)
            
            # Clean up empty session subscriber sets
            if not self.session_subscribers[session_id]:
                del self.session_subscribers[session_id]
        
        self.logger.info(f"Client {client_id} unsubscribed from session {session_id}")
    
    def get_session_subscribers(self, session_id: str) -> Set[str]:
        """Get all clients subscribed to a session."""
        return self.session_subscribers.get(session_id, set())
    
    def update_activity(self, client_id: str):
        """Update last activity time for a connection."""
        
        if client_id in self.connections:
            self.connections[client_id].last_activity = time.time()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        
        now = time.time()
        active_connections = len(self.connections)
        total_sessions = len(self.session_subscribers)
        
        # Calculate average connection duration
        if self.connections:
            avg_duration = sum(
                now - conn.connect_time 
                for conn in self.connections.values()
            ) / len(self.connections)
        else:
            avg_duration = 0
        
        return {
            'active_connections': active_connections,
            'total_sessions': total_sessions,
            'average_connection_duration': avg_duration
        }


class WebSocketHandler:
    """Handles WebSocket communication for AutoBot web interface."""
    
    def __init__(self, socketio: Optional[SocketIO] = None):
        if not SOCKETIO_AVAILABLE:
            raise ImportError("Flask-SocketIO is required for WebSocket functionality")
        
        self.socketio = socketio
        self.connection_manager = ConnectionManager()
        self.logger = logging.getLogger(__name__)
        
        # Message types
        self.MESSAGE_TYPES = {
            'PROGRESS_UPDATE': 'progress_update',
            'STAGE_CHANGE': 'stage_change',
            'ERROR': 'error',
            'WARNING': 'warning',
            'SUCCESS': 'success',
            'COMPLETION': 'completion',
            'RESULTS': 'results'
        }
    
    async def emit_to_session(self, session_id: str, event: str, data: Dict[str, Any]):
        """Emit message to all clients subscribed to a session."""
        
        if not self.socketio:
            return
        
        subscribers = self.connection_manager.get_session_subscribers(session_id)
        
        if subscribers:
            # Add metadata
            message_data = {
                'session_id': session_id,
                'timestamp': time.time(),
                **data
            }
            
            # Emit to session room
            self.socketio.emit(event, message_data, room=session_id)
            
            self.logger.debug(f"Emitted {event} to session {session_id} ({len(subscribers)} subscribers)")
    
    async def emit_progress_update(self, session_id: str, stage: str, progress: int, message: str):
        """Emit progress update to session subscribers."""
        
        await self.emit_to_session(session_id, self.MESSAGE_TYPES['PROGRESS_UPDATE'], {
            'stage': stage,
            'progress': progress,
            'message': message
        })
    
    async def emit_stage_change(self, session_id: str, old_stage: str, new_stage: str, message: str = ""):
        """Emit stage change notification."""
        
        await self.emit_to_session(session_id, self.MESSAGE_TYPES['STAGE_CHANGE'], {
            'old_stage': old_stage,
            'new_stage': new_stage,
            'message': message
        })
    
    async def emit_error(self, session_id: str, error_message: str, error_details: Optional[Dict] = None):
        """Emit error message to session subscribers."""
        
        await self.emit_to_session(session_id, self.MESSAGE_TYPES['ERROR'], {
            'error_message': error_message,
            'error_details': error_details or {}
        })
    
    async def emit_warning(self, session_id: str, warning_message: str, warning_details: Optional[Dict] = None):
        """Emit warning message to session subscribers."""
        
        await self.emit_to_session(session_id, self.MESSAGE_TYPES['WARNING'], {
            'warning_message': warning_message,
            'warning_details': warning_details or {}
        })
    
    async def emit_success(self, session_id: str, success_message: str, success_details: Optional[Dict] = None):
        """Emit success message to session subscribers."""
        
        await self.emit_to_session(session_id, self.MESSAGE_TYPES['SUCCESS'], {
            'success_message': success_message,
            'success_details': success_details or {}
        })
    
    async def emit_completion(self, session_id: str, results: Dict[str, Any]):
        """Emit completion notification with results."""
        
        await self.emit_to_session(session_id, self.MESSAGE_TYPES['COMPLETION'], {
            'results': results,
            'completion_time': time.time()
        })
    
    async def emit_results(self, session_id: str, results: Dict[str, Any]):
        """Emit detailed results to session subscribers."""
        
        await self.emit_to_session(session_id, self.MESSAGE_TYPES['RESULTS'], {
            'results': results
        })
    
    async def broadcast_system_message(self, message: str, message_type: str = 'info'):
        """Broadcast system message to all connected clients."""
        
        if not self.socketio:
            return
        
        self.socketio.emit('system_message', {
            'message': message,
            'type': message_type,
            'timestamp': time.time()
        })
        
        self.logger.info(f"Broadcasted system message: {message}")
    
    def handle_connection(self, client_id: str):
        """Handle new client connection."""
        
        connection = self.connection_manager.add_connection(client_id)
        
        # Send welcome message
        if self.socketio:
            self.socketio.emit('welcome', {
                'message': 'Connected to AutoBot Assembly System',
                'client_id': client_id,
                'server_time': time.time()
            }, room=client_id)
    
    def handle_disconnection(self, client_id: str):
        """Handle client disconnection."""
        
        self.connection_manager.remove_connection(client_id)
    
    def handle_join_session(self, client_id: str, session_id: str):
        """Handle client joining a session."""
        
        success = self.connection_manager.subscribe_to_session(client_id, session_id)
        
        if self.socketio:
            if success:
                self.socketio.emit('session_joined', {
                    'session_id': session_id,
                    'status': 'success'
                }, room=client_id)
            else:
                self.socketio.emit('session_join_failed', {
                    'session_id': session_id,
                    'error': 'Failed to join session'
                }, room=client_id)
    
    def handle_leave_session(self, client_id: str, session_id: str):
        """Handle client leaving a session."""
        
        self.connection_manager.unsubscribe_from_session(client_id, session_id)
        
        if self.socketio:
            self.socketio.emit('session_left', {
                'session_id': session_id,
                'status': 'success'
            }, room=client_id)
    
    def handle_ping(self, client_id: str):
        """Handle ping from client."""
        
        self.connection_manager.update_activity(client_id)
        
        if self.socketio:
            self.socketio.emit('pong', {
                'timestamp': time.time()
            }, room=client_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        
        return self.connection_manager.get_connection_stats()
    
    async def cleanup_inactive_connections(self, timeout_seconds: int = 3600):
        """Clean up inactive connections."""
        
        now = time.time()
        inactive_clients = []
        
        for client_id, connection in self.connection_manager.connections.items():
            if now - connection.last_activity > timeout_seconds:
                inactive_clients.append(client_id)
        
        for client_id in inactive_clients:
            self.logger.info(f"Cleaning up inactive connection: {client_id}")
            self.connection_manager.remove_connection(client_id)
        
        return len(inactive_clients)


# Example usage and testing
async def test_websocket_handler():
    """Test the WebSocket handler."""
    
    print("WebSocket handler test - would require actual SocketIO instance")
    print("Handler is ready for integration with Flask-SocketIO")


if __name__ == "__main__":
    asyncio.run(test_websocket_handler())