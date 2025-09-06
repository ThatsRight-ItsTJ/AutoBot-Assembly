"""
Semgrep Integration

Security and pattern-based analysis using Semgrep Community Edition.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class SeverityLevel(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class SemgrepFinding:
    rule_id: str
    severity: SeverityLevel
    message: str
    file_path: str
    line_number: int
    column_number: int
    code_snippet: str
    fix_suggestion: Optional[str] = None


@dataclass
class SecurityScore:
    overall_score: float
    vulnerability_count: int
    warning_count: int
    info_count: int
    critical_issues: List[SemgrepFinding]
    security_categories: Dict[str, int]


@dataclass
class SemgrepResults:
    findings: List[SemgrepFinding]
    files_analyzed: int
    rules_applied: int
    execution_time: float
    security_score: SecurityScore
    summary: Dict[str, Any]


class SemgrepAnalyzer:
    """Security and pattern analysis using Semgrep."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Rule sets for different types of analysis
        self.rule_sets = {
            'security': 'auto',  # Semgrep's curated security rules
            'performance': 'auto',
            'correctness': 'auto',
            'owasp-top-10': 'owasp-top-10',
            'cwe-top-25': 'cwe-top-25'
        }
        
        # Severity weights for scoring
        self.severity_weights = {
            SeverityLevel.ERROR: 1.0,
            SeverityLevel.WARNING: 0.6,
            SeverityLevel.INFO: 0.2
        }
    
    async def analyze_repository(self, repo_path: str, language_hint: Optional[str] = None) -> SemgrepResults:
        """
        Run Semgrep analysis on repository.
        
        Args:
            repo_path: Path to repository to analyze
            language_hint: Optional language hint for rule optimization
            
        Returns:
            SemgrepResults with security analysis
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Run Semgrep scans
            all_findings = []
            rules_applied = 0
            
            for rule_set_name, rule_set in self.rule_sets.items():
                try:
                    findings = await self._run_semgrep_scan(repo_path, rule_set, language_hint)
                    all_findings.extend(findings)
                    rules_applied += 1
                except Exception as e:
                    self.logger.error(f"Error running {rule_set_name} rules: {e}")
                    continue
            
            # Calculate security score
            security_score = self._calculate_security_score(all_findings)
            
            # Count analyzed files
            files_analyzed = len(set(finding.file_path for finding in all_findings))
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return SemgrepResults(
                findings=all_findings,
                files_analyzed=files_analyzed,
                rules_applied=rules_applied,
                execution_time=execution_time,
                security_score=security_score,
                summary=self._generate_summary(all_findings, security_score)
            )
            
        except Exception as e:
            self.logger.error(f"Semgrep analysis failed: {e}")
            return self._create_empty_results()
    
    async def analyze_files(self, file_paths: List[str], base_path: str) -> Dict[str, SecurityScore]:
        """
        Analyze specific files for security issues.
        
        Args:
            file_paths: List of file paths to analyze
            base_path: Base repository path
            
        Returns:
            Dict mapping file paths to security scores
        """
        file_scores = {}
        
        for file_path in file_paths:
            full_path = Path(base_path) / file_path
            if full_path.exists():
                try:
                    # Run analysis on single file
                    findings = []
                    for rule_set_name, rule_set in self.rule_sets.items():
                        file_findings = await self._run_semgrep_scan(str(full_path), rule_set)
                        findings.extend(file_findings)
                    
                    # Calculate score for this file
                    file_findings = [f for f in findings if f.file_path == file_path]
                    security_score = self._calculate_security_score(file_findings)
                    file_scores[file_path] = security_score
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing file {file_path}: {e}")
                    continue
        
        return file_scores
    
    async def _run_semgrep_scan(self, target_path: str, rule_set: str, 
                              language_hint: Optional[str] = None) -> List[SemgrepFinding]:
        """Run a single Semgrep scan with specified rules."""
        
        # Build Semgrep command
        cmd = [
            'semgrep',
            '--config', rule_set,
            '--json',
            '--quiet',
            '--no-git-ignore',
            '--timeout', '60'
        ]
        
        # Add language filter if provided
        if language_hint:
            lang_extensions = self._get_language_extensions(language_hint)
            if lang_extensions:
                for ext in lang_extensions:
                    cmd.extend(['--include', f'*.{ext}'])
        
        cmd.append(target_path)
        
        try:
            # Run Semgrep
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 or process.returncode == 1:  # 1 means findings found
                # Parse JSON output
                output = stdout.decode('utf-8')
                if output.strip():
                    data = json.loads(output)
                    return self._parse_semgrep_output(data)
            else:
                self.logger.error(f"Semgrep failed with code {process.returncode}: {stderr.decode()}")
                
        except Exception as e:
            self.logger.error(f"Error running Semgrep: {e}")
        
        return []
    
    def _parse_semgrep_output(self, data: dict) -> List[SemgrepFinding]:
        """Parse Semgrep JSON output into findings."""
        findings = []
        
        results = data.get('results', [])
        for result in results:
            try:
                finding = SemgrepFinding(
                    rule_id=result.get('check_id', 'unknown'),
                    severity=SeverityLevel(result.get('extra', {}).get('severity', 'INFO')),
                    message=result.get('extra', {}).get('message', 'No message'),
                    file_path=result.get('path', ''),
                    line_number=result.get('start', {}).get('line', 0),
                    column_number=result.get('start', {}).get('col', 0),
                    code_snippet=result.get('extra', {}).get('lines', ''),
                    fix_suggestion=result.get('extra', {}).get('fix', None)
                )
                findings.append(finding)
            except Exception as e:
                self.logger.error(f"Error parsing Semgrep result: {e}")
                continue
        
        return findings
    
    def _calculate_security_score(self, findings: List[SemgrepFinding]) -> SecurityScore:
        """Calculate security score from findings."""
        
        if not findings:
            return SecurityScore(
                overall_score=1.0,
                vulnerability_count=0,
                warning_count=0,
                info_count=0,
                critical_issues=[],
                security_categories={}
            )
        
        # Count findings by severity
        severity_counts = {
            SeverityLevel.ERROR: 0,
            SeverityLevel.WARNING: 0,
            SeverityLevel.INFO: 0
        }
        
        for finding in findings:
            severity_counts[finding.severity] += 1
        
        # Calculate base score (starts at 1.0, decreases with findings)
        total_score = 1.0
        
        for severity, count in severity_counts.items():
            weight = self.severity_weights[severity]
            # Each finding reduces score by weight * 0.1, capped at 0.8 reduction per severity
            reduction = min(0.8, count * weight * 0.1)
            total_score -= reduction
        
        overall_score = max(0.0, total_score)
        
        # Identify critical issues (ERROR severity)
        critical_issues = [f for f in findings if f.severity == SeverityLevel.ERROR]
        
        # Categorize security issues
        security_categories = self._categorize_security_issues(findings)
        
        return SecurityScore(
            overall_score=overall_score,
            vulnerability_count=severity_counts[SeverityLevel.ERROR],
            warning_count=severity_counts[SeverityLevel.WARNING],
            info_count=severity_counts[SeverityLevel.INFO],
            critical_issues=critical_issues,
            security_categories=security_categories
        )
    
    def _categorize_security_issues(self, findings: List[SemgrepFinding]) -> Dict[str, int]:
        """Categorize security issues by type."""
        categories = {}
        
        for finding in findings:
            rule_id = finding.rule_id.lower()
            
            # Map rule IDs to categories
            if any(keyword in rule_id for keyword in ['sql', 'injection', 'sqli']):
                category = 'SQL Injection'
            elif any(keyword in rule_id for keyword in ['xss', 'cross-site']):
                category = 'Cross-Site Scripting'
            elif any(keyword in rule_id for keyword in ['auth', 'authentication']):
                category = 'Authentication'
            elif any(keyword in rule_id for keyword in ['crypto', 'encryption', 'hash']):
                category = 'Cryptography'
            elif any(keyword in rule_id for keyword in ['path', 'traversal', 'directory']):
                category = 'Path Traversal'
            elif any(keyword in rule_id for keyword in ['deserial', 'pickle', 'yaml']):
                category = 'Deserialization'
            elif any(keyword in rule_id for keyword in ['command', 'exec', 'shell']):
                category = 'Command Injection'
            elif any(keyword in rule_id for keyword in ['hardcode', 'secret', 'password']):
                category = 'Hardcoded Secrets'
            else:
                category = 'Other'
            
            categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def _get_language_extensions(self, language: str) -> List[str]:
        """Get file extensions for language filtering."""
        extensions = {
            'python': ['py', 'pyw'],
            'javascript': ['js', 'jsx', 'ts', 'tsx'],
            'java': ['java'],
            'go': ['go'],
            'rust': ['rs'],
            'php': ['php'],
            'ruby': ['rb'],
            'c': ['c', 'h'],
            'cpp': ['cpp', 'cxx', 'cc', 'hpp'],
            'csharp': ['cs'],
            'kotlin': ['kt', 'kts']
        }
        
        return extensions.get(language.lower(), [])
    
    def _generate_summary(self, findings: List[SemgrepFinding], security_score: SecurityScore) -> Dict[str, Any]:
        """Generate analysis summary."""
        return {
            'total_findings': len(findings),
            'security_score': security_score.overall_score,
            'vulnerability_count': security_score.vulnerability_count,
            'warning_count': security_score.warning_count,
            'info_count': security_score.info_count,
            'top_categories': dict(sorted(security_score.security_categories.items(), 
                                        key=lambda x: x[1], reverse=True)[:5]),
            'critical_rules': list(set(f.rule_id for f in security_score.critical_issues))
        }
    
    def _create_empty_results(self) -> SemgrepResults:
        """Create empty results for failed analysis."""
        empty_score = SecurityScore(
            overall_score=0.5,  # Neutral score when analysis fails
            vulnerability_count=0,
            warning_count=0,
            info_count=0,
            critical_issues=[],
            security_categories={}
        )
        
        return SemgrepResults(
            findings=[],
            files_analyzed=0,
            rules_applied=0,
            execution_time=0,
            security_score=empty_score,
            summary={'status': 'failed'}
        )


# Example usage
async def main():
    analyzer = SemgrepAnalyzer()
    
    # Test with current repository
    repo_path = "."
    print("Running Semgrep security analysis...")
    
    results = await analyzer.analyze_repository(repo_path, language_hint="python")
    
    print(f"\nSemgrep Results:")
    print(f"  Files analyzed: {results.files_analyzed}")
    print(f"  Total findings: {len(results.findings)}")
    print(f"  Security score: {results.security_score.overall_score:.2f}")
    print(f"  Vulnerabilities: {results.security_score.vulnerability_count}")
    print(f"  Warnings: {results.security_score.warning_count}")
    print(f"  Execution time: {results.execution_time:.2f}s")
    
    if results.security_score.security_categories:
        print(f"\nTop security categories:")
        for category, count in list(results.security_score.security_categories.items())[:5]:
            print(f"  {category}: {count}")
    
    if results.security_score.critical_issues:
        print(f"\nCritical issues:")
        for issue in results.security_score.critical_issues[:3]:
            print(f"  {issue.rule_id}: {issue.message}")
            print(f"    File: {issue.file_path}:{issue.line_number}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())