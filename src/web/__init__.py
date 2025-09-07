"""
Web Interface

Browser-based interface for the AutoBot Assembly System:
- Web Server: Flask/FastAPI web application
- Real-time Updates: WebSocket support for progress tracking
- Result Visualization: Interactive project results and metrics
"""

from .web_server import WebServer, WebConfig
from .websocket_handler import WebSocketHandler, ConnectionManager
from .result_visualizer import ResultVisualizer, ChartType

__all__ = [
    'WebServer', 'WebConfig',
    'WebSocketHandler', 'ConnectionManager',
    'ResultVisualizer', 'ChartType'
]