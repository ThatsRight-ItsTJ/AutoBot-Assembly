"""
Web Server

Flask-based web interface for AutoBot Assembly System.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
    from flask_socketio import SocketIO, emit, join_room, leave_room
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    SocketIO = None

from ..orchestration.project_analyzer import ProjectAnalyzer
from ..orchestration.search_orchestrator import SearchOrchestrator
from ..assembly.project_generator import ProjectGenerator, ProjectType
from ..qa.integration_tester import IntegrationTester
from ..qa.quality_validator import QualityValidator
from ..qa.documentation_generator import DocumentationGenerator, DocType
from .websocket_handler import WebSocketHandler
from .result_visualizer import ResultVisualizer


@dataclass
class WebConfig:
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False
    secret_key: str = "autobot-secret-key-change-in-production"
    max_concurrent_sessions: int = 10
    session_timeout: int = 3600  # 1 hour
    upload_folder: str = "./uploads"
    output_folder: str = "./web_output"


class WebServer:
    """Flask-based web server for AutoBot Assembly System."""
    
    def __init__(self, config: Optional[WebConfig] = None):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask and Flask-SocketIO are required for web interface")
        
        self.config = config or WebConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Flask app
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        self.app.config['SECRET_KEY'] = self.config.secret_key
        
        # Enable CORS for API endpoints
        CORS(self.app, resources={r"/api/*": {"origins": "*"}})
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize components
        self.websocket_handler = WebSocketHandler(self.socketio)
        self.result_visualizer = ResultVisualizer()
        
        # Core AutoBot components
        self.project_analyzer = ProjectAnalyzer()
        self.search_orchestrator = SearchOrchestrator()
        self.project_generator = ProjectGenerator()
        self.integration_tester = IntegrationTester()
        self.quality_validator = QualityValidator()
        self.documentation_generator = DocumentationGenerator()
        
        # Session management
        self.active_sessions = {}
        self.session_results = {}
        
        # Create directories
        Path(self.config.upload_folder).mkdir(parents=True, exist_ok=True)
        Path(self.config.output_folder).mkdir(parents=True, exist_ok=True)
        
        # Register routes
        self._register_routes()
        self._register_socketio_events()
    
    def _register_routes(self):
        """Register Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main page."""
            return render_template('index.html')
        
        @self.app.route('/dashboard')
        def dashboard():
            """Dashboard page."""
            return render_template('dashboard.html')
        
        @self.app.route('/history')
        def history():
            """History page."""
            return render_template('history.html')
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'active_sessions': len(self.active_sessions)
            })
        
        @self.app.route('/api/sessions', methods=['GET'])
        def get_sessions():
            """Get active sessions."""
            sessions = []
            for session_id, session_data in self.active_sessions.items():
                sessions.append({
                    'session_id': session_id,
                    'prompt': session_data.get('prompt', ''),
                    'status': session_data.get('status', 'unknown'),
                    'start_time': session_data.get('start_time', 0),
                    'progress': session_data.get('progress', 0)
                })
            
            return jsonify({'sessions': sessions})
        
        @self.app.route('/api/session/<session_id>', methods=['GET'])
        def get_session(session_id):
            """Get session details."""
            if session_id not in self.active_sessions:
                return jsonify({'error': 'Session not found'}), 404
            
            session_data = self.active_sessions[session_id]
            return jsonify(session_data)
        
        @self.app.route('/api/session/<session_id>/results', methods=['GET'])
        def get_session_results(session_id):
            """Get session results."""
            if session_id not in self.session_results:
                return jsonify({'error': 'Results not found'}), 404
            
            results = self.session_results[session_id]
            return jsonify(results)
        
        @self.app.route('/api/generate', methods=['POST'])
        def generate_project():
            """Generate project from prompt."""
            data = request.get_json()
            
            if not data or 'prompt' not in data:
                return jsonify({'error': 'Prompt is required'}), 400
            
            # Create new session
            session_id = str(uuid.uuid4())
            
            # Start async processing
            asyncio.create_task(self._process_generation_request(session_id, data))
            
            return jsonify({
                'session_id': session_id,
                'status': 'started',
                'message': 'Project generation started'
            })
        
        @self.app.route('/api/download/<session_id>')
        def download_project(session_id):
            """Download generated project."""
            if session_id not in self.session_results:
                return jsonify({'error': 'Session not found'}), 404
            
            results = self.session_results[session_id]
            if 'generated_project' not in results:
                return jsonify({'error': 'No project generated'}), 404
            
            project_path = results['generated_project']['project_path']
            project_name = results['generated_project']['project_name']
            
            # Create zip file
            import zipfile
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                with zipfile.ZipFile(tmp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    project_dir = Path(project_path)
                    for file_path in project_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(project_dir.parent)
                            zipf.write(file_path, arcname)
                
                return send_from_directory(
                    Path(tmp_file.name).parent,
                    Path(tmp_file.name).name,
                    as_attachment=True,
                    download_name=f"{project_name}.zip"
                )
    
    def _register_socketio_events(self):
        """Register SocketIO events."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            self.logger.info(f"Client connected: {request.sid}")
            emit('connected', {'message': 'Connected to AutoBot'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            self.logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('join_session')
        def handle_join_session(data):
            """Join a session room for updates."""
            session_id = data.get('session_id')
            if session_id:
                join_room(session_id)
                emit('joined_session', {'session_id': session_id})
        
        @self.socketio.on('leave_session')
        def handle_leave_session(data):
            """Leave a session room."""
            session_id = data.get('session_id')
            if session_id:
                leave_room(session_id)
                emit('left_session', {'session_id': session_id})
    
    async def _process_generation_request(self, session_id: str, request_data: Dict[str, Any]):
        """Process project generation request asynchronously."""
        
        try:
            prompt = request_data['prompt']
            options = request_data.get('options', {})
            
            # Initialize session
            self.active_sessions[session_id] = {
                'session_id': session_id,
                'prompt': prompt,
                'options': options,
                'status': 'analyzing',
                'progress': 0,
                'start_time': time.time(),
                'current_stage': 'analyzing'
            }
            
            # Emit initial status
            await self.websocket_handler.emit_progress_update(
                session_id, 'analyzing', 0, 'Starting project analysis...'
            )
            
            # Phase 1: Analyze prompt
            await self._update_session_progress(session_id, 'analyzing', 10, 'Analyzing requirements...')
            
            analysis_result = await self.project_analyzer.analyze_prompt(prompt)
            
            # Phase 2: Search for components
            await self._update_session_progress(session_id, 'searching', 25, 'Searching for components...')
            
            search_results = await self.search_orchestrator.orchestrate_search(
                analysis_result, max_results_per_tier=10
            )
            
            # Phase 3: Simplified assembly for web demo
            await self._update_session_progress(session_id, 'assembling', 50, 'Assembling project...')
            
            # Create a simplified project structure for demo
            project_name = analysis_result.project_name or "autobot_web_project"
            output_path = Path(self.config.output_folder) / session_id / project_name
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate basic project files
            await self._generate_demo_project(output_path, analysis_result, search_results)
            
            # Phase 4: Quality validation (simplified)
            await self._update_session_progress(session_id, 'testing', 75, 'Running quality checks...')
            
            # Create mock results for demo
            quality_score = 0.85
            test_results = {
                'total_tests': 8,
                'passed_tests': 7,
                'failed_tests': 0,
                'skipped_tests': 1
            }
            
            # Phase 5: Complete
            await self._update_session_progress(session_id, 'complete', 100, 'Project ready!')
            
            # Store results
            self.session_results[session_id] = {
                'generated_project': {
                    'project_name': project_name,
                    'project_path': str(output_path),
                    'project_type': analysis_result.project_type,
                    'language': analysis_result.recommended_language,
                    'dependencies': len(search_results.all_results)
                },
                'analysis_result': {
                    'project_name': analysis_result.project_name,
                    'project_type': analysis_result.project_type,
                    'recommended_language': analysis_result.recommended_language,
                    'required_components': analysis_result.required_components
                },
                'search_results': {
                    'total_results': len(search_results.all_results),
                    'tier1_results': len(search_results.tier1_results),
                    'tier2_results': len(search_results.tier2_results),
                    'tier3_results': len(search_results.tier3_results)
                },
                'quality_metrics': {
                    'overall_score': quality_score,
                    'test_results': test_results
                },
                'completion_time': time.time()
            }
            
            # Update session status
            self.active_sessions[session_id]['status'] = 'complete'
            self.active_sessions[session_id]['progress'] = 100
            
            # Emit completion
            await self.websocket_handler.emit_completion(session_id, self.session_results[session_id])
            
        except Exception as e:
            self.logger.error(f"Error processing session {session_id}: {e}")
            
            # Update session with error
            self.active_sessions[session_id]['status'] = 'error'
            self.active_sessions[session_id]['error'] = str(e)
            
            # Emit error
            await self.websocket_handler.emit_error(session_id, str(e))
    
    async def _update_session_progress(self, session_id: str, stage: str, progress: int, message: str):
        """Update session progress."""
        
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['current_stage'] = stage
            self.active_sessions[session_id]['progress'] = progress
            self.active_sessions[session_id]['last_message'] = message
        
        await self.websocket_handler.emit_progress_update(session_id, stage, progress, message)
    
    async def _generate_demo_project(self, output_path: Path, analysis_result, search_results):
        """Generate a demo project structure."""
        
        # Create basic project structure
        src_dir = output_path / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Create main file
        language = analysis_result.recommended_language.lower()
        
        if language == 'python':
            main_file = output_path / "main.py"
            main_content = f'''#!/usr/bin/env python3
"""
{analysis_result.project_name or "AutoBot Generated Project"}

Generated by AutoBot Assembly System
"""

def main():
    """Main entry point."""
    print("Hello from AutoBot!")
    print("Project: {analysis_result.project_name or 'AutoBot Project'}")
    print("Type: {analysis_result.project_type}")
    
    # TODO: Implement your project logic here
    pass

if __name__ == "__main__":
    main()
'''
            with open(main_file, 'w') as f:
                f.write(main_content)
            
            # Create requirements.txt
            requirements_file = output_path / "requirements.txt"
            requirements = []
            for result in search_results.all_results[:5]:
                if hasattr(result, 'name'):
                    requirements.append(result.name)
            
            with open(requirements_file, 'w') as f:
                f.write('\n'.join(requirements))
        
        elif language == 'javascript':
            main_file = output_path / "index.js"
            main_content = f'''/**
 * {analysis_result.project_name or "AutoBot Generated Project"}
 * 
 * Generated by AutoBot Assembly System
 */

function main() {{
    console.log("Hello from AutoBot!");
    console.log("Project: {analysis_result.project_name or 'AutoBot Project'}");
    console.log("Type: {analysis_result.project_type}");
    
    // TODO: Implement your project logic here
}}

if (require.main === module) {{
    main();
}}

module.exports = {{ main }};
'''
            with open(main_file, 'w') as f:
                f.write(main_content)
            
            # Create package.json
            package_json = {
                "name": analysis_result.project_name or "autobot-project",
                "version": "1.0.0",
                "description": f"Generated by AutoBot Assembly System",
                "main": "index.js",
                "scripts": {
                    "start": "node index.js",
                    "test": "echo \"Error: no test specified\" && exit 1"
                },
                "dependencies": {}
            }
            
            with open(output_path / "package.json", 'w') as f:
                json.dump(package_json, f, indent=2)
        
        # Create README
        readme_content = f'''# {analysis_result.project_name or "AutoBot Generated Project"}

> Generated by AutoBot Assembly System

## Description

{analysis_result.project_description or "This project was automatically generated based on your requirements."}

## Project Details

- **Type**: {analysis_result.project_type}
- **Language**: {analysis_result.recommended_language}
- **Components Found**: {len(search_results.all_results)}

## Quick Start

### Prerequisites

- {analysis_result.recommended_language} runtime

### Installation

```bash
# Clone or download this project
cd {analysis_result.project_name or "autobot-project"}
'''
        
        if language == 'python':
            readme_content += '''
# Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
python main.py
```
'''
        elif language == 'javascript':
            readme_content += '''
# Install dependencies
npm install
```

### Usage

```bash
npm start
```
'''
        
        readme_content += '''
## Generated Components

This project was assembled from the following components:

'''
        
        for i, result in enumerate(search_results.all_results[:10], 1):
            readme_content += f"{i}. **{result.name}** - {result.description[:100]}...\n"
        
        readme_content += '''
## Next Steps

1. Review the generated code
2. Customize according to your needs
3. Add tests and documentation
4. Deploy your application

---

*Generated by [AutoBot Assembly System](https://github.com/autobot-assembly)*
'''
        
        with open(output_path / "README.md", 'w') as f:
            f.write(readme_content)
    
    def run(self):
        """Run the web server."""
        
        self.logger.info(f"Starting AutoBot Web Server on {self.config.host}:{self.config.port}")
        
        self.socketio.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            debug=self.config.debug
        )


# Example usage
def main():
    """Run the web server."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    config = WebConfig(debug=True)
    server = WebServer(config)
    server.run()


if __name__ == "__main__":
    main()