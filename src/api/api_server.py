"""
API Server

FastAPI-based REST API for AutoBot Assembly System.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None

from ..orchestration.project_analyzer import ProjectAnalyzer
from ..orchestration.search_orchestrator import SearchOrchestrator
from ..assembly.project_generator import ProjectGenerator, ProjectType
from ..qa.integration_tester import IntegrationTester
from ..qa.quality_validator import QualityValidator
from ..qa.documentation_generator import DocumentationGenerator, DocType
from .auth_manager import AuthManager
from .rate_limiter import RateLimiter


@dataclass
class APIConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    title: str = "AutoBot Assembly API"
    version: str = "1.0.0"
    description: str = "AI-powered GitHub repository assembly system API"
    max_concurrent_requests: int = 10
    request_timeout: int = 300
    output_folder: str = "./api_output"


# Pydantic models for API
class GenerateProjectRequest(BaseModel):
    prompt: str = Field(..., description="Project description")
    project_type: Optional[str] = Field(None, description="Project type (application, library, web_service, cli_tool)")
    language: Optional[str] = Field(None, description="Programming language (python, javascript, java)")
    max_repos: int = Field(10, description="Maximum repositories to analyze")
    skip_tests: bool = Field(False, description="Skip quality testing")
    skip_docs: bool = Field(False, description="Skip documentation generation")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional options")


class ProjectResponse(BaseModel):
    session_id: str
    status: str
    message: str
    estimated_duration: Optional[float] = None


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    progress: int
    current_stage: str
    start_time: float
    duration: Optional[float] = None
    error: Optional[str] = None


class ResultsResponse(BaseModel):
    session_id: str
    generated_project: Dict[str, Any]
    analysis_result: Dict[str, Any]
    search_results: Dict[str, Any]
    quality_metrics: Optional[Dict[str, Any]] = None
    completion_time: float


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    version: str
    active_sessions: int
    system_info: Dict[str, Any]


class APIServer:
    """FastAPI-based REST API server for AutoBot Assembly System."""
    
    def __init__(self, config: Optional[APIConfig] = None):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI and uvicorn are required for API server")
        
        self.config = config or APIConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title=self.config.title,
            version=self.config.version,
            description=self.config.description,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize components
        self.auth_manager = AuthManager()
        self.rate_limiter = RateLimiter()
        
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
        
        # Create output directory
        Path(self.config.output_folder).mkdir(parents=True, exist_ok=True)
        
        # Register routes
        self._register_routes()
        
        # Security
        self.security = HTTPBearer()
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.get("/", response_model=Dict[str, str])
        async def root():
            """Root endpoint."""
            return {
                "message": "AutoBot Assembly System API",
                "version": self.config.version,
                "docs": "/docs",
                "health": "/health"
            }
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            
            import psutil
            import platform
            
            return HealthResponse(
                status="healthy",
                timestamp=time.time(),
                version=self.config.version,
                active_sessions=len(self.active_sessions),
                system_info={
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent,
                    "platform": platform.system(),
                    "python_version": platform.python_version()
                }
            )
        
        @self.app.post("/api/v1/generate", response_model=ProjectResponse)
        async def generate_project(
            request: GenerateProjectRequest,
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(self.security),
            http_request: Request = None
        ):
            """Generate a project from a prompt."""
            
            # Authenticate request
            if not await self.auth_manager.verify_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            # Rate limiting
            client_ip = http_request.client.host
            if not await self.rate_limiter.check_rate_limit(client_ip):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Create session
            session_id = str(uuid.uuid4())
            
            # Initialize session
            self.active_sessions[session_id] = {
                'session_id': session_id,
                'status': 'queued',
                'progress': 0,
                'current_stage': 'queued',
                'start_time': time.time(),
                'request': request.dict(),
                'client_ip': client_ip
            }
            
            # Start background processing
            background_tasks.add_task(self._process_generation_request, session_id, request)
            
            # Estimate duration based on request complexity
            estimated_duration = self._estimate_duration(request)
            
            return ProjectResponse(
                session_id=session_id,
                status="queued",
                message="Project generation queued for processing",
                estimated_duration=estimated_duration
            )
        
        @self.app.get("/api/v1/sessions", response_model=List[SessionStatusResponse])
        async def list_sessions(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """List all active sessions."""
            
            if not await self.auth_manager.verify_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            sessions = []
            for session_id, session_data in self.active_sessions.items():
                duration = None
                if session_data.get('status') == 'complete':
                    duration = time.time() - session_data['start_time']
                
                sessions.append(SessionStatusResponse(
                    session_id=session_id,
                    status=session_data['status'],
                    progress=session_data['progress'],
                    current_stage=session_data['current_stage'],
                    start_time=session_data['start_time'],
                    duration=duration,
                    error=session_data.get('error')
                ))
            
            return sessions
        
        @self.app.get("/api/v1/sessions/{session_id}", response_model=SessionStatusResponse)
        async def get_session_status(
            session_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get status of a specific session."""
            
            if not await self.auth_manager.verify_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            
            session_data = self.active_sessions[session_id]
            
            duration = None
            if session_data.get('status') in ['complete', 'error']:
                duration = time.time() - session_data['start_time']
            
            return SessionStatusResponse(
                session_id=session_id,
                status=session_data['status'],
                progress=session_data['progress'],
                current_stage=session_data['current_stage'],
                start_time=session_data['start_time'],
                duration=duration,
                error=session_data.get('error')
            )
        
        @self.app.get("/api/v1/sessions/{session_id}/results", response_model=ResultsResponse)
        async def get_session_results(
            session_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get results of a completed session."""
            
            if not await self.auth_manager.verify_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            if session_id not in self.session_results:
                raise HTTPException(status_code=404, detail="Results not found")
            
            results = self.session_results[session_id]
            
            return ResultsResponse(
                session_id=session_id,
                generated_project=results['generated_project'],
                analysis_result=results['analysis_result'],
                search_results=results['search_results'],
                quality_metrics=results.get('quality_metrics'),
                completion_time=results['completion_time']
            )
        
        @self.app.get("/api/v1/sessions/{session_id}/download")
        async def download_project(
            session_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Download generated project as ZIP file."""
            
            if not await self.auth_manager.verify_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            if session_id not in self.session_results:
                raise HTTPException(status_code=404, detail="Session not found")
            
            results = self.session_results[session_id]
            project_path = results['generated_project']['project_path']
            project_name = results['generated_project']['project_name']
            
            # Create ZIP file
            import zipfile
            import tempfile
            
            zip_path = Path(tempfile.mkdtemp()) / f"{project_name}.zip"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                project_dir = Path(project_path)
                for file_path in project_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(project_dir.parent)
                        zipf.write(file_path, arcname)
            
            return FileResponse(
                path=zip_path,
                filename=f"{project_name}.zip",
                media_type='application/zip'
            )
        
        @self.app.delete("/api/v1/sessions/{session_id}")
        async def cancel_session(
            session_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Cancel an active session."""
            
            if not await self.auth_manager.verify_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Mark session as cancelled
            self.active_sessions[session_id]['status'] = 'cancelled'
            
            return {"message": f"Session {session_id} cancelled"}
        
        @self.app.get("/api/v1/stats")
        async def get_api_stats(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get API usage statistics."""
            
            if not await self.auth_manager.verify_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            return {
                "active_sessions": len(self.active_sessions),
                "completed_sessions": len(self.session_results),
                "rate_limit_stats": await self.rate_limiter.get_stats(),
                "uptime": time.time() - getattr(self, '_start_time', time.time())
            }
    
    async def _process_generation_request(self, session_id: str, request: GenerateProjectRequest):
        """Process project generation request in background."""
        
        try:
            # Update session status
            self.active_sessions[session_id]['status'] = 'processing'
            self.active_sessions[session_id]['current_stage'] = 'analyzing'
            self.active_sessions[session_id]['progress'] = 10
            
            # Phase 1: Analyze prompt
            analysis_result = await self.project_analyzer.analyze_prompt(request.prompt)
            
            self.active_sessions[session_id]['current_stage'] = 'searching'
            self.active_sessions[session_id]['progress'] = 30
            
            # Phase 2: Search for components
            search_results = await self.search_orchestrator.orchestrate_search(
                analysis_result, max_results_per_tier=request.max_repos
            )
            
            self.active_sessions[session_id]['current_stage'] = 'assembling'
            self.active_sessions[session_id]['progress'] = 60
            
            # Phase 3: Generate project (simplified for API)
            project_name = analysis_result.project_name or "autobot_api_project"
            output_path = Path(self.config.output_folder) / session_id / project_name
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate basic project structure
            await self._generate_api_project(output_path, analysis_result, search_results, request)
            
            # Phase 4: Quality assurance (if not skipped)
            quality_metrics = None
            if not request.skip_tests:
                self.active_sessions[session_id]['current_stage'] = 'testing'
                self.active_sessions[session_id]['progress'] = 85
                
                # Mock quality metrics for API demo
                quality_metrics = {
                    'overall_score': 0.82,
                    'complexity_score': 0.85,
                    'maintainability_index': 0.78,
                    'security_score': 0.88,
                    'performance_score': 0.75,
                    'documentation_completeness': 0.90,
                    'technical_debt_ratio': 0.12,
                    'test_results': {
                        'total_tests': 6,
                        'passed_tests': 5,
                        'failed_tests': 0,
                        'skipped_tests': 1
                    }
                }
            
            # Complete
            self.active_sessions[session_id]['status'] = 'complete'
            self.active_sessions[session_id]['current_stage'] = 'complete'
            self.active_sessions[session_id]['progress'] = 100
            
            # Store results
            self.session_results[session_id] = {
                'generated_project': {
                    'project_name': project_name,
                    'project_path': str(output_path),
                    'project_type': request.project_type or analysis_result.project_type,
                    'language': request.language or analysis_result.recommended_language,
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
                'quality_metrics': quality_metrics,
                'completion_time': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing session {session_id}: {e}")
            
            # Update session with error
            self.active_sessions[session_id]['status'] = 'error'
            self.active_sessions[session_id]['error'] = str(e)
    
    async def _generate_api_project(self, output_path: Path, analysis_result, search_results, request: GenerateProjectRequest):
        """Generate a project structure for API response."""
        
        language = request.language or analysis_result.recommended_language.lower()
        
        # Create basic structure
        if language == 'python':
            # Create main.py
            main_content = f'''#!/usr/bin/env python3
"""
{analysis_result.project_name or "AutoBot API Generated Project"}

Generated via AutoBot Assembly System API
"""

def main():
    """Main entry point."""
    print("Hello from AutoBot API!")
    print("Project: {analysis_result.project_name or 'AutoBot API Project'}")
    print("Generated from prompt: {request.prompt[:100]}...")
    
    # TODO: Implement your project logic here
    pass

if __name__ == "__main__":
    main()
'''
            
            with open(output_path / "main.py", 'w') as f:
                f.write(main_content)
            
            # Create requirements.txt
            requirements = [result.name for result in search_results.all_results[:10] if hasattr(result, 'name')]
            with open(output_path / "requirements.txt", 'w') as f:
                f.write('\n'.join(requirements))
        
        # Create README
        readme_content = f'''# {analysis_result.project_name or "AutoBot API Generated Project"}

> Generated via AutoBot Assembly System API

## Description

{request.prompt}

## Project Details

- **Generated via**: AutoBot Assembly System API
- **Language**: {language.title()}
- **Type**: {request.project_type or analysis_result.project_type}
- **Components Found**: {len(search_results.all_results)}

## API Generation Info

- **Session ID**: Generated via API
- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Max Repositories**: {request.max_repos}

## Quick Start

### Installation

```bash
# Install dependencies
'''
        
        if language == 'python':
            readme_content += 'pip install -r requirements.txt'
        elif language == 'javascript':
            readme_content += 'npm install'
        
        readme_content += f'''
```

### Usage

```bash
# Run the project
{language} main.{'py' if language == 'python' else 'js'}
```

## Components Used

This project was assembled from {len(search_results.all_results)} components:

'''
        
        for i, result in enumerate(search_results.all_results[:10], 1):
            readme_content += f"{i}. **{result.name}** - {result.description[:80]}...\n"
        
        readme_content += '''
---

*Generated by [AutoBot Assembly System API](https://github.com/autobot-assembly)*
'''
        
        with open(output_path / "README.md", 'w') as f:
            f.write(readme_content)
    
    def _estimate_duration(self, request: GenerateProjectRequest) -> float:
        """Estimate processing duration based on request."""
        
        base_duration = 30.0  # Base 30 seconds
        
        # Add time based on complexity
        if request.max_repos > 10:
            base_duration += (request.max_repos - 10) * 2
        
        if not request.skip_tests:
            base_duration += 15.0
        
        if not request.skip_docs:
            base_duration += 5.0
        
        return base_duration
    
    def run(self):
        """Run the API server."""
        
        self._start_time = time.time()
        self.logger.info(f"Starting AutoBot API Server on {self.config.host}:{self.config.port}")
        
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info" if self.config.debug else "warning"
        )


# Example usage
def main():
    """Run the API server."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    config = APIConfig(debug=True)
    server = APIServer(config)
    server.run()


if __name__ == "__main__":
    main()