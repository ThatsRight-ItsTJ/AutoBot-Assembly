#!/usr/bin/env python3
"""
AI-Integrated Project Reporter

Generates comprehensive reports using existing AI analysis components including:
- Unified file scoring from analysis engine
- Repository discovery results from search tiers
- Security and compliance metrics
- AI-determined file purposes and relevance scores
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from ..analysis.unified_scorer import UnifiedFileScorer, CompositeFileScore
from ..analysis.megalinter_client import MegaLinterAnalyzer
from ..analysis.semgrep_client import SemgrepAnalyzer
from ..analysis.astgrep_client import ASTGrepAnalyzer
from ..search.tier1_packages import Tier1Search
from ..search.tier2_curated import Tier2Search
from ..search.tier3_discovery import Tier3Search, RepositoryInfo
from ..orchestration.search_orchestrator import SearchOrchestrator


@dataclass
class AIProjectReport:
    """Complete AI-integrated project assembly report."""
    project_name: str
    generated_at: str
    
    # AI Analysis Results
    file_analysis: Dict[str, CompositeFileScore]
    integration_summary: Dict[str, Any]
    
    # Repository Discovery Results
    source_repositories: List[RepositoryInfo]
    repository_mapping: Dict[str, Dict[str, Any]]
    
    # Search Results
    tier1_packages: List[Dict[str, Any]]
    tier2_collections: List[Dict[str, Any]]
    tier3_discoveries: List[RepositoryInfo]
    
    # Implementation Strategy
    implementation_phases: List[Dict[str, Any]]
    coverage_analysis: Dict[str, Any]
    development_priorities: List[Dict[str, Any]]


class AIIntegratedReporter:
    """Generates comprehensive reports using existing AI analysis systems."""
    
    def __init__(self):
        # Initialize AI analysis components
        self.unified_scorer = UnifiedFileScorer()
        self.megalinter = MegaLinterAnalyzer()
        self.semgrep = SemgrepAnalyzer()
        self.astgrep = ASTGrepAnalyzer()
        
        # Initialize search components
        self.tier1_search = Tier1Search()
        self.tier2_search = Tier2Search()
        self.tier3_search = Tier3Search()
        self.search_orchestrator = SearchOrchestrator()
    
    async def generate_ai_integrated_report(
        self,
        project_path: str,
        project_description: str,
        language: str = "python",
        repositories: List[Dict] = None
    ) -> AIProjectReport:
        """
        Generate comprehensive AI-integrated project report.
        
        Args:
            project_path: Path to the project directory
            project_description: Description of the project requirements
            language: Primary programming language
            repositories: List of source repository information
            
        Returns:
            AIProjectReport with complete AI analysis
        """
        project_path = Path(project_path)
        project_name = project_path.name
        
        print(f"🤖 Generating AI-integrated report for: {project_name}")
        
        # Step 1: Run comprehensive AI file analysis
        print("📊 Running AI file analysis...")
        file_analysis = await self._run_ai_file_analysis(str(project_path), language)
        
        # Step 2: Generate integration summary
        print("🔍 Generating integration summary...")
        integration_summary = self.unified_scorer.generate_integration_report(file_analysis)
        
        # Step 3: Run AI-driven repository discovery
        print("🔎 Running AI repository discovery...")
        search_results = await self.search_orchestrator.orchestrate_search(
            project_description, language
        )
        
        # Step 4: Process repository information
        print("📦 Processing repository mapping...")
        repository_mapping = self._create_repository_mapping(
            repositories or [], search_results.tier3_results
        )
        
        # Step 5: Generate implementation strategy
        print("🚀 Generating implementation strategy...")
        implementation_phases = self._generate_implementation_phases(
            file_analysis, search_results
        )
        
        # Step 6: Calculate coverage analysis
        print("📈 Calculating coverage analysis...")
        coverage_analysis = self._calculate_coverage_analysis(
            file_analysis, search_results
        )
        
        # Step 7: Determine development priorities
        print("⭐ Determining development priorities...")
        development_priorities = self._generate_development_priorities(
            file_analysis, search_results
        )
        
        return AIProjectReport(
            project_name=project_name,
            generated_at=datetime.now().isoformat(),
            file_analysis=file_analysis,
            integration_summary=integration_summary,
            source_repositories=search_results.tier3_results,
            repository_mapping=repository_mapping,
            tier1_packages=search_results.tier1_results,
            tier2_collections=search_results.tier2_results,
            tier3_discoveries=search_results.tier3_results,
            implementation_phases=implementation_phases,
            coverage_analysis=coverage_analysis,
            development_priorities=development_priorities
        )
    
    async def _run_ai_file_analysis(self, project_path: str, language: str) -> Dict[str, CompositeFileScore]:
        """Run comprehensive AI analysis on all project files."""
        
        # Run all analysis tools
        megalinter_results = await self.megalinter.analyze_repository(project_path, language)
        semgrep_results = await self.semgrep.analyze_repository(project_path, language)
        astgrep_analyses = await self.astgrep.analyze_repository_structure(project_path, language)
        
        # Calculate composite scores using AI analysis
        file_scores = self.unified_scorer.score_repository_files(
            megalinter_results, semgrep_results, astgrep_analyses
        )
        
        return file_scores
    
    def _create_repository_mapping(
        self, 
        provided_repos: List[Dict], 
        discovered_repos: List[RepositoryInfo]
    ) -> Dict[str, Dict[str, Any]]:
        """Create mapping between project components and source repositories."""
        
        mapping = {}
        
        # Process provided repositories
        for repo in provided_repos:
            repo_name = repo.get('name', 'unknown')
            mapping[repo_name] = {
                'source': 'provided',
                'url': repo.get('url', ''),
                'files_copied': repo.get('files_copied', []),
                'purpose': repo.get('purpose', ''),
                'license': repo.get('license'),
                'integration_score': 0.8,  # Default high score for provided repos
                'ai_analysis': {
                    'relevance_score': 0.9,
                    'quality_score': 0.8,
                    'recommendation': 'Provided repository - assumed high quality'
                }
            }
        
        # Process AI-discovered repositories
        for repo in discovered_repos:
            if repo.name not in mapping:
                mapping[repo.name] = {
                    'source': 'ai_discovered',
                    'url': repo.url,
                    'files_copied': [],  # Would be populated during actual integration
                    'purpose': self._determine_repo_purpose(repo),
                    'license': repo.license,
                    'integration_score': repo.quality_score * repo.relevance_score,
                    'ai_analysis': {
                        'relevance_score': repo.relevance_score,
                        'quality_score': repo.quality_score,
                        'recommendation': self._generate_repo_recommendation(repo),
                        'stars': repo.stars,
                        'forks': repo.forks,
                        'last_updated': repo.last_updated,
                        'topics': repo.topics
                    }
                }
        
        return mapping
    
    def _determine_repo_purpose(self, repo: RepositoryInfo) -> str:
        """Determine repository purpose using AI analysis."""
        
        # Analyze repository name and description
        name_lower = repo.name.lower()
        desc_lower = repo.description.lower() if repo.description else ""
        
        # Framework detection
        if any(fw in name_lower or fw in desc_lower for fw in ['flask', 'django', 'fastapi']):
            return "Web framework and API development"
        elif any(fw in name_lower or fw in desc_lower for fw in ['react', 'vue', 'angular']):
            return "Frontend framework and UI components"
        elif any(term in name_lower or term in desc_lower for term in ['scraper', 'crawler', 'scraping']):
            return "Web scraping and data extraction"
        elif any(term in name_lower or term in desc_lower for term in ['ml', 'machine learning', 'ai']):
            return "Machine learning and AI functionality"
        elif any(term in name_lower or term in desc_lower for term in ['cli', 'command', 'terminal']):
            return "Command-line interface and tools"
        elif any(term in name_lower or term in desc_lower for term in ['auth', 'authentication', 'security']):
            return "Authentication and security features"
        elif any(term in name_lower or term in desc_lower for term in ['database', 'db', 'storage']):
            return "Database and data storage"
        elif any(term in name_lower or term in desc_lower for term in ['test', 'testing', 'unittest']):
            return "Testing framework and utilities"
        else:
            return f"General {repo.language} development utilities"
    
    def _generate_repo_recommendation(self, repo: RepositoryInfo) -> str:
        """Generate AI-based recommendation for repository integration."""
        
        combined_score = repo.quality_score * repo.relevance_score
        
        if combined_score >= 0.8:
            return f"Excellent - High quality ({repo.quality_score:.2f}) and relevance ({repo.relevance_score:.2f})"
        elif combined_score >= 0.6:
            return f"Good - Solid choice with {repo.stars} stars and active maintenance"
        elif combined_score >= 0.4:
            return f"Acceptable - Consider for specific use cases"
        else:
            return f"Low priority - Limited relevance or quality concerns"
    
    def _generate_implementation_phases(
        self, 
        file_analysis: Dict[str, CompositeFileScore],
        search_results
    ) -> List[Dict[str, Any]]:
        """Generate implementation phases based on AI analysis."""
        
        phases = []
        
        # Phase 1: High-priority, high-quality files
        high_priority_files = [
            (path, score) for path, score in file_analysis.items()
            if score.integration_priority == "High" and score.overall_score >= 0.8
        ]
        
        if high_priority_files:
            phases.append({
                'phase': 1,
                'name': 'Core Foundation',
                'description': 'Integrate highest quality, most critical components',
                'duration_estimate': '1-2 weeks',
                'files': [
                    {
                        'path': path,
                        'score': score.overall_score,
                        'recommendation': score.recommendation,
                        'purpose': self._extract_ai_purpose(score)
                    }
                    for path, score in high_priority_files[:10]
                ],
                'repositories': [
                    repo.name for repo in search_results.tier3_results[:3]
                    if repo.quality_score >= 0.8
                ]
            })
        
        # Phase 2: Medium priority components
        medium_priority_files = [
            (path, score) for path, score in file_analysis.items()
            if score.integration_priority == "Medium"
        ]
        
        if medium_priority_files:
            phases.append({
                'phase': 2,
                'name': 'Feature Enhancement',
                'description': 'Add secondary features and optimizations',
                'duration_estimate': '2-3 weeks',
                'files': [
                    {
                        'path': path,
                        'score': score.overall_score,
                        'recommendation': score.recommendation,
                        'purpose': self._extract_ai_purpose(score)
                    }
                    for path, score in medium_priority_files[:15]
                ],
                'repositories': [
                    repo.name for repo in search_results.tier3_results[3:8]
                    if repo.quality_score >= 0.6
                ]
            })
        
        # Phase 3: Polish and optimization
        phases.append({
            'phase': 3,
            'name': 'Polish & Optimization',
            'description': 'Final optimizations, testing, and documentation',
            'duration_estimate': '1-2 weeks',
            'files': [
                {
                    'path': path,
                    'score': score.overall_score,
                    'recommendation': score.recommendation,
                    'purpose': self._extract_ai_purpose(score)
                }
                for path, score in file_analysis.items()
                if score.integration_priority == "Low" and score.overall_score >= 0.6
            ][:10],
            'repositories': [
                repo.name for repo in search_results.tier3_results[8:]
                if repo.quality_score >= 0.5
            ][:5]
        })
        
        return phases
    
    def _extract_ai_purpose(self, score: CompositeFileScore) -> str:
        """Extract AI-determined file purpose from detailed analysis."""
        
        if 'structure_analysis' in score.detailed_analysis:
            structure = score.detailed_analysis['structure_analysis']
            frameworks = structure.get('detected_frameworks', [])
            
            if frameworks:
                return f"Framework integration: {', '.join(frameworks[:2])}"
            elif structure.get('class_count', 0) > 0:
                return f"Core logic: {structure['class_count']} classes, {structure.get('method_count', 0)} methods"
        
        if 'quality_analysis' in score.detailed_analysis:
            quality = score.detailed_analysis['quality_analysis']
            if quality.get('maintainability', 0) > 0.8:
                return "High-quality maintainable code"
        
        if 'security_analysis' in score.detailed_analysis:
            security = score.detailed_analysis['security_analysis']
            if security.get('vulnerabilities', 0) == 0:
                return "Security-validated component"
        
        return "General utility component"
    
    def _calculate_coverage_analysis(
        self, 
        file_analysis: Dict[str, CompositeFileScore],
        search_results
    ) -> Dict[str, Any]:
        """Calculate coverage analysis using AI metrics."""
        
        total_files = len(file_analysis)
        high_quality_files = len([s for s in file_analysis.values() if s.overall_score >= 0.8])
        secure_files = len([
            s for s in file_analysis.values() 
            if 'security_analysis' in s.detailed_analysis and 
            s.detailed_analysis['security_analysis'].get('vulnerabilities', 0) == 0
        ])
        
        return {
            'total_files_analyzed': total_files,
            'high_quality_files': high_quality_files,
            'security_validated_files': secure_files,
            'quality_coverage_percentage': (high_quality_files / total_files * 100) if total_files > 0 else 0,
            'security_coverage_percentage': (secure_files / total_files * 100) if total_files > 0 else 0,
            'ai_analysis_tools_used': ['MegaLinter', 'Semgrep', 'AST-grep', 'Unified Scorer'],
            'repository_discovery_results': {
                'tier1_packages_found': len(search_results.tier1_results),
                'tier2_collections_found': len(search_results.tier2_results),
                'tier3_repositories_found': len(search_results.tier3_results),
                'high_quality_repos': len([r for r in search_results.tier3_results if r.quality_score >= 0.8])
            }
        }
    
    def _generate_development_priorities(
        self, 
        file_analysis: Dict[str, CompositeFileScore],
        search_results
    ) -> List[Dict[str, Any]]:
        """Generate development priorities based on AI analysis."""
        
        priorities = []
        
        # High priority: Security issues
        security_issues = [
            (path, score) for path, score in file_analysis.items()
            if 'security_analysis' in score.detailed_analysis and
            score.detailed_analysis['security_analysis'].get('vulnerabilities', 0) > 0
        ]
        
        if security_issues:
            priorities.append({
                'priority': 'Critical',
                'category': 'Security',
                'description': 'Address security vulnerabilities identified by AI analysis',
                'affected_files': len(security_issues),
                'action_required': 'Review and fix security issues before deployment',
                'ai_recommendation': 'Use Semgrep analysis results to prioritize fixes'
            })
        
        # High priority: Quality improvements
        low_quality_files = [
            (path, score) for path, score in file_analysis.items()
            if score.overall_score < 0.6
        ]
        
        if low_quality_files:
            priorities.append({
                'priority': 'High',
                'category': 'Code Quality',
                'description': 'Improve code quality for better maintainability',
                'affected_files': len(low_quality_files),
                'action_required': 'Refactor low-scoring files or find better alternatives',
                'ai_recommendation': 'Focus on files with maintainability scores below 0.6'
            })
        
        # Medium priority: Integration optimization
        priorities.append({
            'priority': 'Medium',
            'category': 'Integration',
            'description': 'Optimize repository integration based on AI scoring',
            'affected_files': len([r for r in search_results.tier3_results if r.quality_score < 0.7]),
            'action_required': 'Review lower-scored repositories for integration value',
            'ai_recommendation': 'Prioritize repositories with quality_score >= 0.7'
        })
        
        # Low priority: Documentation
        priorities.append({
            'priority': 'Low',
            'category': 'Documentation',
            'description': 'Enhance documentation based on AI analysis',
            'affected_files': len([
                s for s in file_analysis.values()
                if 'quality_analysis' in s.detailed_analysis and
                s.detailed_analysis['quality_analysis'].get('documentation', 0) < 0.7
            ]),
            'action_required': 'Add documentation for poorly documented components',
            'ai_recommendation': 'Use MegaLinter documentation scores to guide improvements'
        })
        
        return priorities
    
    def generate_markdown_report(self, report: AIProjectReport) -> str:
        """Generate comprehensive markdown report similar to AI API Liaison example."""
        
        md = []
        
        # Header
        md.append(f"# 🏗️ **{report.project_name.upper()} - AI-INTEGRATED PROJECT REPORT**")
        md.append("")
        md.append("## 📊 **AI-Powered Analysis & Integration Strategy**")
        md.append(f"Generated using AutoBot Assembly System's AI analysis engine on {report.generated_at}")
        md.append("")
        md.append("---")
        md.append("")
        
        # File Structure with AI Analysis
        md.append("## 🗂️ **AI-ANALYZED FILE STRUCTURE**")
        md.append("")
        md.append("```")
        md.append(f"{report.project_name}/")
        
        # Group files by AI-determined priority
        high_priority = [(path, score) for path, score in report.file_analysis.items() if score.integration_priority == "High"]
        medium_priority = [(path, score) for path, score in report.file_analysis.items() if score.integration_priority == "Medium"]
        low_priority = [(path, score) for path, score in report.file_analysis.items() if score.integration_priority == "Low"]
        
        for path, score in high_priority:
            md.append(f"├── 📄 {path}  # 🔥 HIGH PRIORITY (Score: {score.overall_score:.2f})")
        
        for path, score in medium_priority:
            md.append(f"├── 📄 {path}  # ⭐ MEDIUM PRIORITY (Score: {score.overall_score:.2f})")
        
        for path, score in low_priority:
            md.append(f"├── 📄 {path}  # 📋 LOW PRIORITY (Score: {score.overall_score:.2f})")
        
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")
        
        # Repository Integration Strategy
        md.append("## 🎯 **AI-DRIVEN REPOSITORY INTEGRATION STRATEGY**")
        md.append("")
        
        for repo_name, repo_data in report.repository_mapping.items():
            ai_analysis = repo_data['ai_analysis']
            md.append(f"### **{repo_name}**")
            md.append(f"- **URL:** {repo_data['url']}")
            md.append(f"- **Purpose:** {repo_data['purpose']}")
            md.append(f"- **Integration Score:** {repo_data['integration_score']:.2f}")
            md.append(f"- **AI Quality Score:** {ai_analysis['quality_score']:.2f}")
            md.append(f"- **AI Relevance Score:** {ai_analysis['relevance_score']:.2f}")
            md.append(f"- **AI Recommendation:** {ai_analysis['recommendation']}")
            
            if 'stars' in ai_analysis:
                md.append(f"- **GitHub Stats:** {ai_analysis['stars']} stars, {ai_analysis.get('forks', 0)} forks")
            
            if repo_data['files_copied']:
                md.append("- **Files Integrated:**")
                for file in repo_data['files_copied']:
                    md.append(f"  - {file}")
            
            md.append("")
        
        md.append("---")
        md.append("")
        
        # AI Analysis Results
        md.append("## 🤖 **COMPREHENSIVE AI ANALYSIS RESULTS**")
        md.append("")
        
        # Integration Summary
        summary = report.integration_summary['summary']
        md.append("### **📊 Analysis Summary**")
        md.append(f"- **Total Files Analyzed:** {summary['total_files']}")
        md.append(f"- **Average AI Quality Score:** {summary['average_score']:.2f}")
        md.append(f"- **Highest Quality Score:** {summary['max_score']:.2f}")
        md.append(f"- **Files Above Quality Threshold:** {summary['files_above_threshold']}")
        md.append("")
        
        # Top Files by AI Analysis
        md.append("### **🏆 Top Files by AI Analysis**")
        md.append("")
        md.append("| File | AI Score | Quality | Security | Structure | Recommendation |")
        md.append("|------|----------|---------|----------|-----------|----------------|")
        
        top_files = sorted(report.file_analysis.items(), key=lambda x: x[1].overall_score, reverse=True)[:10]
        for path, score in top_files:
            quality = score.component_scores.get('quality', 0)
            security = score.component_scores.get('security', 0)
            structure = score.component_scores.get('structure', 0)
            recommendation = score.recommendation.split(' - ')[0]
            
            md.append(f"| {path} | {score.overall_score:.2f} | {quality:.2f} | {security:.2f} | {structure:.2f} | {recommendation} |")
        
        md.append("")
        
        # Repository Discovery Results
        md.append("### **🔍 AI Repository Discovery Results**")
        md.append("")
        
        coverage = report.coverage_analysis['repository_discovery_results']
        md.append(f"- **Tier 1 Packages Found:** {coverage['tier1_packages_found']}")
        md.append(f"- **Tier 2 Collections Found:** {coverage['tier2_collections_found']}")
        md.append(f"- **Tier 3 Repositories Discovered:** {coverage['tier3_repositories_found']}")
        md.append(f"- **High-Quality Repositories:** {coverage['high_quality_repos']}")
        md.append("")
        
        # Implementation Phases
        md.append("## 🚀 **AI-OPTIMIZED IMPLEMENTATION PHASES**")
        md.append("")
        
        for phase in report.implementation_phases:
            md.append(f"### **Phase {phase['phase']}: {phase['name']}**")
            md.append(f"**Duration:** {phase['duration_estimate']}")
            md.append(f"**Description:** {phase['description']}")
            md.append("")
            
            if phase['files']:
                md.append("**Priority Files:**")
                for file_info in phase['files'][:5]:
                    md.append(f"- `{file_info['path']}` (Score: {file_info['score']:.2f}) - {file_info['purpose']}")
                md.append("")
            
            if phase['repositories']:
                md.append("**Key Repositories:**")
                for repo in phase['repositories'][:3]:
                    md.append(f"- {repo}")
                md.append("")
        
        md.append("---")
        md.append("")
        
        # Development Priorities
        md.append("## ⭐ **AI-DETERMINED DEVELOPMENT PRIORITIES**")
        md.append("")
        
        for priority in report.development_priorities:
            md.append(f"### **{priority['priority']} Priority: {priority['category']}**")
            md.append(f"**Description:** {priority['description']}")
            md.append(f"**Affected Files:** {priority['affected_files']}")
            md.append(f"**Action Required:** {priority['action_required']}")
            md.append(f"**AI Recommendation:** {priority['ai_recommendation']}")
            md.append("")
        
        # Coverage Analysis
        md.append("## 📈 **AI COVERAGE ANALYSIS**")
        md.append("")
        
        coverage = report.coverage_analysis
        md.append("| Metric | Value | Percentage |")
        md.append("|--------|-------|------------|")
        md.append(f"| Total Files Analyzed | {coverage['total_files_analyzed']} | 100% |")
        md.append(f"| High Quality Files | {coverage['high_quality_files']} | {coverage['quality_coverage_percentage']:.1f}% |")
        md.append(f"| Security Validated | {coverage['security_validated_files']} | {coverage['security_coverage_percentage']:.1f}% |")
        md.append("")
        
        md.append("**AI Analysis Tools Used:**")
        for tool in coverage['ai_analysis_tools_used']:
            md.append(f"- ✅ {tool}")
        md.append("")
        
        # Footer
        md.append("---")
        md.append("")
        md.append("## 🎯 **INTEGRATION BENEFITS**")
        md.append("")
        md.append("### **✅ AI-POWERED ADVANTAGES**")
        md.append("- **Intelligent Quality Assessment** using multi-tool analysis")
        md.append("- **Automated Security Validation** with Semgrep integration")
        md.append("- **Smart Repository Discovery** with relevance scoring")
        md.append("- **Data-Driven Integration Priorities** based on composite scores")
        md.append("")
        md.append("### **🚀 DEVELOPMENT ACCELERATION**")
        md.append("- **Reduced Risk** through AI-validated component selection")
        md.append("- **Optimized Integration Order** based on quality and priority scores")
        md.append("- **Automated Quality Assurance** with continuous AI monitoring")
        md.append("- **Intelligent Dependency Management** with framework coupling analysis")
        md.append("")
        md.append("---")
        md.append("")
        md.append("*Report generated by AutoBot Assembly System's AI-Integrated Analysis Engine*")
        
        return "\n".join(md)
    
    def save_report(self, report: AIProjectReport, output_path: str, filename: str = "README.md") -> str:
        """Save the AI-integrated report as README.md."""
        
        output_path = Path(output_path)
        report_file = output_path / filename
        
        # Generate markdown content
        markdown_content = self.generate_markdown_report(report)
        
        # Save to file
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(report_file)