"""
Progress Reporter

Real-time progress tracking and status updates for CLI operations.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ProgressStage(str, Enum):
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    SEARCHING = "searching"
    SCORING = "scoring"
    COMPATIBILITY = "compatibility"
    ASSEMBLING = "assembling"
    TESTING = "testing"
    DOCUMENTING = "documenting"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class StageInfo:
    name: str
    description: str
    emoji: str
    estimated_duration: float  # seconds


class ProgressReporter:
    """Real-time progress tracking and reporting."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or (Console() if RICH_AVAILABLE else None)
        self.current_session = None
        self.session_start_time = None
        self.current_stage = None
        self.stage_start_time = None
        self.progress = None
        self.live = None
        
        # Stage definitions
        self.stages = {
            ProgressStage.INITIALIZING: StageInfo(
                "Initializing", "Setting up AutoBot components", "🚀", 2.0
            ),
            ProgressStage.ANALYZING: StageInfo(
                "Analyzing", "Understanding your requirements", "🔍", 5.0
            ),
            ProgressStage.SEARCHING: StageInfo(
                "Searching", "Finding relevant components", "🔎", 15.0
            ),
            ProgressStage.SCORING: StageInfo(
                "Scoring", "Analyzing component quality", "📊", 20.0
            ),
            ProgressStage.COMPATIBILITY: StageInfo(
                "Compatibility", "Checking component compatibility", "🔗", 10.0
            ),
            ProgressStage.ASSEMBLING: StageInfo(
                "Assembling", "Building your project", "🔧", 30.0
            ),
            ProgressStage.TESTING: StageInfo(
                "Testing", "Running quality assurance", "🧪", 25.0
            ),
            ProgressStage.DOCUMENTING: StageInfo(
                "Documenting", "Generating documentation", "📚", 8.0
            ),
            ProgressStage.COMPLETE: StageInfo(
                "Complete", "Project ready!", "✅", 0.0
            ),
            ProgressStage.ERROR: StageInfo(
                "Error", "Something went wrong", "❌", 0.0
            )
        }
        
        self.stage_order = [
            ProgressStage.INITIALIZING,
            ProgressStage.ANALYZING,
            ProgressStage.SEARCHING,
            ProgressStage.SCORING,
            ProgressStage.COMPATIBILITY,
            ProgressStage.ASSEMBLING,
            ProgressStage.TESTING,
            ProgressStage.DOCUMENTING,
            ProgressStage.COMPLETE
        ]
    
    async def start_session(self, session_id: str, session_name: str):
        """Start a new progress tracking session."""
        
        self.current_session = session_id
        self.session_start_time = time.time()
        self.current_stage = None
        
        if self.console and RICH_AVAILABLE:
            # Create progress display
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=self.console
            )
            
            # Add main task
            self.main_task = self.progress.add_task(
                f"🤖 {session_name}", 
                total=len(self.stage_order) - 1  # Exclude COMPLETE stage
            )
            
            # Start live display
            self.live = Live(self.progress, console=self.console, refresh_per_second=4)
            self.live.start()
        
        else:
            # Fallback for no Rich
            print(f"🤖 Starting {session_name}...")
    
    async def update_stage(self, stage: ProgressStage, message: Optional[str] = None):
        """Update current stage."""
        
        if self.current_stage == stage:
            return  # Already in this stage
        
        self.current_stage = stage
        self.stage_start_time = time.time()
        
        stage_info = self.stages[stage]
        
        if self.console and RICH_AVAILABLE and self.progress:
            # Update main progress
            stage_index = self.stage_order.index(stage) if stage in self.stage_order else 0
            self.progress.update(
                self.main_task,
                completed=stage_index,
                description=f"🤖 AutoBot Assembly - {stage_info.emoji} {stage_info.name}"
            )
            
            # Add stage-specific message if provided
            if message:
                self.console.print(f"   💬 {message}", style="dim")
        
        else:
            # Fallback for no Rich
            status_msg = f"{stage_info.emoji} {stage_info.name}: {stage_info.description}"
            if message:
                status_msg += f" - {message}"
            print(status_msg)
    
    async def update_progress(self, progress_percent: float, message: Optional[str] = None):
        """Update progress within current stage."""
        
        if not self.current_stage:
            return
        
        if self.console and RICH_AVAILABLE and self.progress:
            if message:
                self.console.print(f"   📝 {message}", style="dim cyan")
        else:
            if message:
                print(f"   {message}")
    
    async def add_detail(self, message: str, style: str = "dim"):
        """Add a detailed message."""
        
        if self.console and RICH_AVAILABLE:
            self.console.print(f"   📋 {message}", style=style)
        else:
            print(f"   {message}")
    
    async def add_warning(self, message: str):
        """Add a warning message."""
        
        if self.console and RICH_AVAILABLE:
            self.console.print(f"   ⚠️ {message}", style="yellow")
        else:
            print(f"   ⚠️ WARNING: {message}")
    
    async def add_error(self, message: str):
        """Add an error message."""
        
        if self.console and RICH_AVAILABLE:
            self.console.print(f"   ❌ {message}", style="red")
        else:
            print(f"   ❌ ERROR: {message}")
    
    async def add_success(self, message: str):
        """Add a success message."""
        
        if self.console and RICH_AVAILABLE:
            self.console.print(f"   ✅ {message}", style="green")
        else:
            print(f"   ✅ {message}")
    
    def get_session_duration(self) -> float:
        """Get total session duration."""
        
        if not self.session_start_time:
            return 0.0
        
        return time.time() - self.session_start_time
    
    def get_stage_duration(self) -> float:
        """Get current stage duration."""
        
        if not self.stage_start_time:
            return 0.0
        
        return time.time() - self.stage_start_time
    
    def get_estimated_remaining_time(self) -> float:
        """Get estimated remaining time."""
        
        if not self.current_stage or self.current_stage not in self.stage_order:
            return 0.0
        
        current_index = self.stage_order.index(self.current_stage)
        remaining_stages = self.stage_order[current_index + 1:]
        
        estimated_time = sum(
            self.stages[stage].estimated_duration 
            for stage in remaining_stages 
            if stage != ProgressStage.COMPLETE
        )
        
        return estimated_time
    
    async def end_session(self):
        """End the current session."""
        
        if self.live:
            self.live.stop()
            self.live = None
        
        if self.progress:
            self.progress = None
        
        total_duration = self.get_session_duration()
        
        if self.console and RICH_AVAILABLE:
            self.console.print(f"\n⏱️ Total time: {total_duration:.1f} seconds", style="dim")
        else:
            print(f"\n⏱️ Total time: {total_duration:.1f} seconds")
        
        self.current_session = None
        self.session_start_time = None
        self.current_stage = None
        self.stage_start_time = None
    
    def create_summary_table(self) -> Optional[Table]:
        """Create a summary table of the session."""
        
        if not self.console or not RICH_AVAILABLE:
            return None
        
        table = Table(title="AutoBot Session Summary")
        table.add_column("Stage", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        
        # This would be populated with actual stage data
        # For now, just return the empty table structure
        return table


# Simple progress reporter for non-Rich environments
class SimpleProgressReporter:
    """Simple text-based progress reporter."""
    
    def __init__(self):
        self.current_stage = None
        self.session_start_time = None
        self.stage_descriptions = {
            ProgressStage.INITIALIZING: "🚀 Initializing AutoBot...",
            ProgressStage.ANALYZING: "🔍 Analyzing requirements...",
            ProgressStage.SEARCHING: "🔎 Searching for components...",
            ProgressStage.SCORING: "📊 Scoring components...",
            ProgressStage.COMPATIBILITY: "🔗 Checking compatibility...",
            ProgressStage.ASSEMBLING: "🔧 Assembling project...",
            ProgressStage.TESTING: "🧪 Running tests...",
            ProgressStage.DOCUMENTING: "📚 Generating docs...",
            ProgressStage.COMPLETE: "✅ Complete!",
            ProgressStage.ERROR: "❌ Error occurred"
        }
    
    async def start_session(self, session_id: str, session_name: str):
        self.session_start_time = time.time()
        print(f"🤖 Starting {session_name}...")
    
    async def update_stage(self, stage: ProgressStage, message: Optional[str] = None):
        self.current_stage = stage
        description = self.stage_descriptions.get(stage, str(stage))
        print(f"\n{description}")
        if message:
            print(f"   {message}")
    
    async def update_progress(self, progress_percent: float, message: Optional[str] = None):
        if message:
            print(f"   {message}")
    
    async def add_detail(self, message: str, style: str = "dim"):
        print(f"   📋 {message}")
    
    async def add_warning(self, message: str):
        print(f"   ⚠️ WARNING: {message}")
    
    async def add_error(self, message: str):
        print(f"   ❌ ERROR: {message}")
    
    async def add_success(self, message: str):
        print(f"   ✅ {message}")
    
    async def end_session(self):
        if self.session_start_time:
            duration = time.time() - self.session_start_time
            print(f"\n⏱️ Total time: {duration:.1f} seconds")


# Example usage
async def demo_progress():
    """Demo the progress reporter."""
    
    reporter = ProgressReporter()
    
    await reporter.start_session("demo", "Demo Session")
    
    stages = [
        (ProgressStage.INITIALIZING, "Setting up components"),
        (ProgressStage.ANALYZING, "Processing your request"),
        (ProgressStage.SEARCHING, "Finding 15 repositories"),
        (ProgressStage.SCORING, "Analyzing code quality"),
        (ProgressStage.COMPATIBILITY, "Checking licenses"),
        (ProgressStage.ASSEMBLING, "Generating project structure"),
        (ProgressStage.TESTING, "Running integration tests"),
        (ProgressStage.DOCUMENTING, "Creating README and docs"),
        (ProgressStage.COMPLETE, "All done!")
    ]
    
    for stage, message in stages:
        await reporter.update_stage(stage, message)
        
        # Simulate some work
        await asyncio.sleep(1.0)
        
        # Add some details
        if stage == ProgressStage.SEARCHING:
            await reporter.add_detail("Found 12 Python packages")
            await reporter.add_detail("Found 8 GitHub repositories")
        elif stage == ProgressStage.TESTING:
            await reporter.add_success("All tests passed")
    
    await reporter.end_session()


if __name__ == "__main__":
    asyncio.run(demo_progress())