"""
Repository Cloner

Handles Git repository cloning, branch management, and repository operations.
"""

import asyncio
import logging
import shutil
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
import json


class CloneStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class CloneResult:
    repository_url: str
    local_path: str
    status: CloneStatus
    branch: Optional[str]
    commit_hash: Optional[str]
    size_mb: float
    file_count: int
    error_message: Optional[str] = None


@dataclass
class RepositoryInfo:
    url: str
    name: str
    branch: Optional[str] = None
    tag: Optional[str] = None
    shallow: bool = True
    max_size_mb: float = 100.0


class RepositoryCloner:
    """Handles repository cloning and management operations."""
    
    def __init__(self, base_clone_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Set up base directory for clones
        if base_clone_dir:
            self.base_clone_dir = Path(base_clone_dir)
        else:
            self.base_clone_dir = Path(tempfile.gettempdir()) / "autobot_clones"
        
        self.base_clone_dir.mkdir(parents=True, exist_ok=True)
        
        # Clone configuration
        self.default_timeout = 300  # 5 minutes
        self.max_repo_size_mb = 500.0
        self.shallow_depth = 1
        
        # Git configuration
        self.git_config = {
            'user.name': 'AutoBot Assembly',
            'user.email': 'autobot@assembly.local'
        }
    
    async def clone_repositories(self, repositories: List[Any]) -> Dict[str, CloneResult]:
        """
        Clone multiple repositories concurrently.
        
        Args:
            repositories: List of repository objects with URL information
            
        Returns:
            Dict mapping repository names to clone results
        """
        
        # Convert repository objects to RepositoryInfo
        repo_infos = []
        for repo in repositories:
            repo_info = self._extract_repository_info(repo)
            if repo_info:
                repo_infos.append(repo_info)
        
        self.logger.info(f"Cloning {len(repo_infos)} repositories...")
        
        # Clone repositories concurrently (with limit)
        semaphore = asyncio.Semaphore(3)  # Limit concurrent clones
        tasks = []
        
        for repo_info in repo_infos:
            task = self._clone_with_semaphore(semaphore, repo_info)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        clone_results = {}
        for i, result in enumerate(results):
            repo_info = repo_infos[i]
            
            if isinstance(result, Exception):
                self.logger.error(f"Clone failed for {repo_info.name}: {result}")
                clone_results[repo_info.name] = CloneResult(
                    repository_url=repo_info.url,
                    local_path="",
                    status=CloneStatus.FAILED,
                    branch=None,
                    commit_hash=None,
                    size_mb=0.0,
                    file_count=0,
                    error_message=str(result)
                )
            else:
                clone_results[repo_info.name] = result
        
        return clone_results
    
    async def _clone_with_semaphore(self, semaphore: asyncio.Semaphore, 
                                  repo_info: RepositoryInfo) -> CloneResult:
        """Clone repository with semaphore for concurrency control."""
        
        async with semaphore:
            return await self._clone_single_repository(repo_info)
    
    async def _clone_single_repository(self, repo_info: RepositoryInfo) -> CloneResult:
        """Clone a single repository."""
        
        self.logger.info(f"Cloning {repo_info.name} from {repo_info.url}")
        
        # Create local directory
        local_path = self.base_clone_dir / repo_info.name
        
        # Remove existing directory if it exists
        if local_path.exists():
            shutil.rmtree(local_path)
        
        try:
            # Build git clone command
            cmd = ['git', 'clone']
            
            # Add shallow clone if requested
            if repo_info.shallow:
                cmd.extend(['--depth', str(self.shallow_depth)])
            
            # Add branch/tag specification
            if repo_info.branch:
                cmd.extend(['--branch', repo_info.branch])
            elif repo_info.tag:
                cmd.extend(['--branch', repo_info.tag])
            
            # Add URL and destination
            cmd.extend([repo_info.url, str(local_path)])
            
            # Execute clone command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.default_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception(f"Clone timeout after {self.default_timeout} seconds")
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown git error"
                raise Exception(f"Git clone failed: {error_msg}")
            
            # Get repository information
            branch = await self._get_current_branch(local_path)
            commit_hash = await self._get_current_commit(local_path)
            size_mb = self._calculate_directory_size(local_path)
            file_count = self._count_files(local_path)
            
            # Check size limits
            if size_mb > repo_info.max_size_mb:
                self.logger.warning(f"Repository {repo_info.name} exceeds size limit: {size_mb:.1f}MB")
                # Could implement partial clone here
            
            return CloneResult(
                repository_url=repo_info.url,
                local_path=str(local_path),
                status=CloneStatus.SUCCESS,
                branch=branch,
                commit_hash=commit_hash,
                size_mb=size_mb,
                file_count=file_count
            )
            
        except Exception as e:
            self.logger.error(f"Failed to clone {repo_info.name}: {e}")
            
            # Clean up failed clone
            if local_path.exists():
                shutil.rmtree(local_path, ignore_errors=True)
            
            return CloneResult(
                repository_url=repo_info.url,
                local_path="",
                status=CloneStatus.FAILED,
                branch=None,
                commit_hash=None,
                size_mb=0.0,
                file_count=0,
                error_message=str(e)
            )
    
    def _extract_repository_info(self, repository: Any) -> Optional[RepositoryInfo]:
        """Extract repository information from various repository object types."""
        
        # Handle different repository object types
        url = None
        name = None
        
        if hasattr(repository, 'repository_url') and repository.repository_url:
            url = repository.repository_url
        elif hasattr(repository, 'url') and repository.url:
            url = repository.url
        elif hasattr(repository, 'clone_url') and repository.clone_url:
            url = repository.clone_url
        
        if hasattr(repository, 'name') and repository.name:
            name = repository.name
        elif hasattr(repository, 'repository') and repository.repository:
            name = repository.repository
        elif hasattr(repository, 'full_name') and repository.full_name:
            name = repository.full_name.split('/')[-1]  # Get repo name from full_name
        
        if not url or not name:
            self.logger.warning(f"Could not extract repository info from {repository}")
            return None
        
        # Clean repository name for filesystem
        name = self._sanitize_repo_name(name)
        
        return RepositoryInfo(
            url=url,
            name=name,
            shallow=True,  # Default to shallow clone
            max_size_mb=self.max_repo_size_mb
        )
    
    def _sanitize_repo_name(self, name: str) -> str:
        """Sanitize repository name for filesystem use."""
        
        # Remove or replace invalid characters
        import re
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        sanitized = sanitized.strip('.')
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    async def _get_current_branch(self, repo_path: Path) -> Optional[str]:
        """Get current branch of cloned repository."""
        
        try:
            process = await asyncio.create_subprocess_exec(
                'git', 'branch', '--show-current',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode('utf-8').strip()
        except Exception as e:
            self.logger.debug(f"Could not get branch for {repo_path}: {e}")
        
        return None
    
    async def _get_current_commit(self, repo_path: Path) -> Optional[str]:
        """Get current commit hash of cloned repository."""
        
        try:
            process = await asyncio.create_subprocess_exec(
                'git', 'rev-parse', 'HEAD',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode('utf-8').strip()
        except Exception as e:
            self.logger.debug(f"Could not get commit for {repo_path}: {e}")
        
        return None
    
    def _calculate_directory_size(self, directory: Path) -> float:
        """Calculate directory size in MB."""
        
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            self.logger.debug(f"Could not calculate size for {directory}: {e}")
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def _count_files(self, directory: Path) -> int:
        """Count files in directory."""
        
        try:
            return len([f for f in directory.rglob('*') if f.is_file()])
        except Exception as e:
            self.logger.debug(f"Could not count files for {directory}: {e}")
            return 0
    
    async def cleanup_clones(self, clone_results: Dict[str, CloneResult]) -> None:
        """Clean up cloned repositories."""
        
        self.logger.info("Cleaning up cloned repositories...")
        
        for repo_name, result in clone_results.items():
            if result.status == CloneStatus.SUCCESS and result.local_path:
                try:
                    local_path = Path(result.local_path)
                    if local_path.exists():
                        shutil.rmtree(local_path)
                        self.logger.debug(f"Cleaned up {repo_name}")
                except Exception as e:
                    self.logger.warning(f"Could not clean up {repo_name}: {e}")
    
    def get_clone_summary(self, clone_results: Dict[str, CloneResult]) -> Dict[str, Any]:
        """Generate summary of clone operations."""
        
        successful = [r for r in clone_results.values() if r.status == CloneStatus.SUCCESS]
        failed = [r for r in clone_results.values() if r.status == CloneStatus.FAILED]
        
        total_size = sum(r.size_mb for r in successful)
        total_files = sum(r.file_count for r in successful)
        
        return {
            'total_repositories': len(clone_results),
            'successful_clones': len(successful),
            'failed_clones': len(failed),
            'total_size_mb': total_size,
            'total_files': total_files,
            'success_rate': len(successful) / len(clone_results) if clone_results else 0.0,
            'failed_repositories': [r.repository_url for r in failed]
        }


# Example usage
async def main():
    from ..search.tier1_packages import PackageResult
    from datetime import datetime
    
    cloner = RepositoryCloner()
    
    # Create test repositories
    test_repos = [
        PackageResult(
            name="requests",
            repository_url="https://github.com/psf/requests",
            description="HTTP library for Python",
            downloads=1000000,
            stars=50000,
            last_updated=datetime.now(),
            license="Apache-2.0",
            quality_score=0.9,
            language="python",
            package_manager="pypi",
            version="2.31.0",
            dependencies_count=5
        ),
        PackageResult(
            name="flask",
            repository_url="https://github.com/pallets/flask",
            description="Web framework for Python",
            downloads=2000000,
            stars=60000,
            last_updated=datetime.now(),
            license="BSD-3-Clause",
            quality_score=0.95,
            language="python",
            package_manager="pypi",
            version="2.3.0",
            dependencies_count=3
        )
    ]
    
    print("Testing repository cloning...")
    
    # Clone repositories
    clone_results = await cloner.clone_repositories(test_repos)
    
    # Print results
    print(f"\nClone Results:")
    for repo_name, result in clone_results.items():
        print(f"  {repo_name}: {result.status.value}")
        if result.status == CloneStatus.SUCCESS:
            print(f"    Path: {result.local_path}")
            print(f"    Branch: {result.branch}")
            print(f"    Size: {result.size_mb:.1f}MB")
            print(f"    Files: {result.file_count}")
        elif result.error_message:
            print(f"    Error: {result.error_message}")
    
    # Print summary
    summary = cloner.get_clone_summary(clone_results)
    print(f"\nSummary:")
    print(f"  Success rate: {summary['success_rate']:.1%}")
    print(f"  Total size: {summary['total_size_mb']:.1f}MB")
    print(f"  Total files: {summary['total_files']}")
    
    # Cleanup
    await cloner.cleanup_clones(clone_results)
    print("Cleanup completed")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())