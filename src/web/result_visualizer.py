"""
Result Visualizer

Interactive visualization of AutoBot results and metrics.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    RADAR = "radar"
    HEATMAP = "heatmap"


@dataclass
class ChartData:
    """Chart data structure."""
    
    chart_type: ChartType
    title: str
    data: Dict[str, Any]
    options: Dict[str, Any]
    description: Optional[str] = None


class ResultVisualizer:
    """Creates interactive visualizations for AutoBot results."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Color schemes
        self.color_schemes = {
            'primary': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'],
            'success': ['#27ae60', '#2ecc71', '#58d68d', '#82e0aa', '#abebc6'],
            'warning': ['#f39c12', '#e67e22', '#d35400', '#dc7633', '#e8943a'],
            'error': ['#e74c3c', '#c0392b', '#a93226', '#cd6155', '#d98880'],
            'info': ['#3498db', '#2980b9', '#1f618d', '#5dade2', '#85c1e9']
        }
    
    def create_search_results_chart(self, search_results: Dict[str, Any]) -> ChartData:
        """Create chart for search results distribution."""
        
        data = {
            'labels': ['Tier 1 (Packages)', 'Tier 2 (Curated)', 'Tier 3 (Discovery)'],
            'datasets': [{
                'label': 'Components Found',
                'data': [
                    search_results.get('tier1_results', 0),
                    search_results.get('tier2_results', 0),
                    search_results.get('tier3_results', 0)
                ],
                'backgroundColor': self.color_schemes['primary'][:3],
                'borderColor': self.color_schemes['primary'][:3],
                'borderWidth': 2
            }]
        }
        
        options = {
            'responsive': True,
            'plugins': {
                'legend': {
                    'position': 'top'
                },
                'tooltip': {
                    'callbacks': {
                        'label': 'function(context) { return context.label + ": " + context.parsed + " components"; }'
                    }
                }
            }
        }
        
        return ChartData(
            chart_type=ChartType.BAR,
            title="Component Discovery Results",
            data=data,
            options=options,
            description="Distribution of components found across different search tiers"
        )
    
    def create_quality_metrics_chart(self, quality_metrics: Dict[str, Any]) -> ChartData:
        """Create radar chart for quality metrics."""
        
        metrics = [
            ('Complexity', quality_metrics.get('complexity_score', 0)),
            ('Maintainability', quality_metrics.get('maintainability_index', 0)),
            ('Security', quality_metrics.get('security_score', 0)),
            ('Performance', quality_metrics.get('performance_score', 0)),
            ('Documentation', quality_metrics.get('documentation_completeness', 0)),
            ('Technical Debt', 1.0 - quality_metrics.get('technical_debt_ratio', 0))  # Invert for display
        ]
        
        data = {
            'labels': [metric[0] for metric in metrics],
            'datasets': [{
                'label': 'Quality Scores',
                'data': [metric[1] for metric in metrics],
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 2,
                'pointBackgroundColor': 'rgba(54, 162, 235, 1)',
                'pointBorderColor': '#fff',
                'pointHoverBackgroundColor': '#fff',
                'pointHoverBorderColor': 'rgba(54, 162, 235, 1)'
            }]
        }
        
        options = {
            'responsive': True,
            'scales': {
                'r': {
                    'beginAtZero': True,
                    'max': 1.0,
                    'ticks': {
                        'callback': 'function(value) { return (value * 100).toFixed(0) + "%"; }'
                    }
                }
            },
            'plugins': {
                'legend': {
                    'position': 'top'
                }
            }
        }
        
        return ChartData(
            chart_type=ChartType.RADAR,
            title="Quality Assessment",
            data=data,
            options=options,
            description="Comprehensive quality metrics for the generated project"
        )
    
    def create_test_results_chart(self, test_results: Dict[str, Any]) -> ChartData:
        """Create pie chart for test results."""
        
        passed = test_results.get('passed_tests', 0)
        failed = test_results.get('failed_tests', 0)
        skipped = test_results.get('skipped_tests', 0)
        
        data = {
            'labels': ['Passed', 'Failed', 'Skipped'],
            'datasets': [{
                'data': [passed, failed, skipped],
                'backgroundColor': [
                    self.color_schemes['success'][0],
                    self.color_schemes['error'][0],
                    self.color_schemes['warning'][0]
                ],
                'borderColor': [
                    self.color_schemes['success'][0],
                    self.color_schemes['error'][0],
                    self.color_schemes['warning'][0]
                ],
                'borderWidth': 2
            }]
        }
        
        options = {
            'responsive': True,
            'plugins': {
                'legend': {
                    'position': 'right'
                },
                'tooltip': {
                    'callbacks': {
                        'label': 'function(context) { return context.label + ": " + context.parsed + " tests"; }'
                    }
                }
            }
        }
        
        return ChartData(
            chart_type=ChartType.PIE,
            title="Test Results",
            data=data,
            options=options,
            description="Distribution of test results from quality assurance"
        )
    
    def create_component_languages_chart(self, components: List[Dict[str, Any]]) -> ChartData:
        """Create chart showing programming languages of components."""
        
        # Count languages
        language_counts = {}
        for component in components:
            language = component.get('language', 'Unknown')
            language_counts[language] = language_counts.get(language, 0) + 1
        
        # Sort by count
        sorted_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
        
        data = {
            'labels': [lang[0] for lang in sorted_languages],
            'datasets': [{
                'label': 'Components by Language',
                'data': [lang[1] for lang in sorted_languages],
                'backgroundColor': self.color_schemes['primary'][:len(sorted_languages)],
                'borderColor': self.color_schemes['primary'][:len(sorted_languages)],
                'borderWidth': 2
            }]
        }
        
        options = {
            'responsive': True,
            'plugins': {
                'legend': {
                    'display': False
                }
            },
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'ticks': {
                        'stepSize': 1
                    }
                }
            }
        }
        
        return ChartData(
            chart_type=ChartType.BAR,
            title="Components by Programming Language",
            data=data,
            options=options,
            description="Distribution of programming languages in discovered components"
        )
    
    def create_timeline_chart(self, stages: List[Dict[str, Any]]) -> ChartData:
        """Create timeline chart for processing stages."""
        
        stage_names = []
        durations = []
        colors = []
        
        for stage in stages:
            stage_names.append(stage.get('name', 'Unknown'))
            durations.append(stage.get('duration', 0))
            
            # Color based on duration
            duration = stage.get('duration', 0)
            if duration < 5:
                colors.append(self.color_schemes['success'][0])
            elif duration < 15:
                colors.append(self.color_schemes['warning'][0])
            else:
                colors.append(self.color_schemes['error'][0])
        
        data = {
            'labels': stage_names,
            'datasets': [{
                'label': 'Duration (seconds)',
                'data': durations,
                'backgroundColor': colors,
                'borderColor': colors,
                'borderWidth': 2
            }]
        }
        
        options = {
            'responsive': True,
            'plugins': {
                'legend': {
                    'display': False
                }
            },
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'title': {
                        'display': True,
                        'text': 'Duration (seconds)'
                    }
                }
            }
        }
        
        return ChartData(
            chart_type=ChartType.BAR,
            title="Processing Timeline",
            data=data,
            options=options,
            description="Time taken for each processing stage"
        )
    
    def create_dependency_network_data(self, dependencies: List[str]) -> Dict[str, Any]:
        """Create network data for dependency visualization."""
        
        # Create nodes and edges for dependency network
        nodes = []
        edges = []
        
        # Main project node
        nodes.append({
            'id': 'main',
            'label': 'Your Project',
            'color': self.color_schemes['primary'][0],
            'size': 30,
            'font': {'color': 'white'}
        })
        
        # Dependency nodes
        for i, dep in enumerate(dependencies[:20]):  # Limit to 20 for readability
            nodes.append({
                'id': f'dep_{i}',
                'label': dep,
                'color': self.color_schemes['info'][i % len(self.color_schemes['info'])],
                'size': 20
            })
            
            # Edge from main to dependency
            edges.append({
                'from': 'main',
                'to': f'dep_{i}',
                'arrows': 'to'
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'options': {
                'physics': {
                    'enabled': True,
                    'stabilization': {'iterations': 100}
                },
                'interaction': {
                    'hover': True,
                    'tooltipDelay': 200
                }
            }
        }
    
    def create_summary_dashboard(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive dashboard data."""
        
        dashboard = {
            'overview': {
                'project_name': results.get('generated_project', {}).get('project_name', 'Unknown'),
                'project_type': results.get('generated_project', {}).get('project_type', 'Unknown'),
                'language': results.get('generated_project', {}).get('language', 'Unknown'),
                'total_components': results.get('search_results', {}).get('total_results', 0),
                'quality_score': results.get('quality_metrics', {}).get('overall_score', 0),
                'completion_time': results.get('completion_time', 0)
            },
            'charts': []
        }
        
        # Add search results chart
        if 'search_results' in results:
            dashboard['charts'].append(
                self.create_search_results_chart(results['search_results'])
            )
        
        # Add quality metrics chart
        if 'quality_metrics' in results:
            dashboard['charts'].append(
                self.create_quality_metrics_chart(results['quality_metrics'])
            )
        
        # Add test results chart
        if 'test_results' in results.get('quality_metrics', {}):
            dashboard['charts'].append(
                self.create_test_results_chart(results['quality_metrics']['test_results'])
            )
        
        return dashboard
    
    def export_chart_config(self, chart_data: ChartData) -> str:
        """Export chart configuration as JSON."""
        
        config = {
            'type': chart_data.chart_type.value,
            'data': chart_data.data,
            'options': chart_data.options
        }
        
        return json.dumps(config, indent=2)
    
    def generate_html_chart(self, chart_data: ChartData, chart_id: str = "chart") -> str:
        """Generate HTML for a chart using Chart.js."""
        
        html = f'''
<div class="chart-container" style="position: relative; height: 400px; width: 100%;">
    <canvas id="{chart_id}"></canvas>
</div>

<script>
const ctx_{chart_id} = document.getElementById('{chart_id}').getContext('2d');
const chart_{chart_id} = new Chart(ctx_{chart_id}, {self.export_chart_config(chart_data)});
</script>
'''
        
        return html
    
    def generate_dashboard_html(self, dashboard_data: Dict[str, Any]) -> str:
        """Generate complete HTML dashboard."""
        
        html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoBot Results Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .dashboard { max-width: 1200px; margin: 0 auto; }
        .overview { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; }
        .chart-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .chart-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #333; }
        .chart-description { font-size: 14px; color: #666; margin-bottom: 15px; }
        .overview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .overview-item { text-align: center; }
        .overview-value { font-size: 24px; font-weight: bold; color: #3498db; }
        .overview-label { font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>AutoBot Assembly Results</h1>
        
        <div class="overview">
            <h2>Project Overview</h2>
            <div class="overview-grid">
'''
        
        # Add overview items
        overview = dashboard_data.get('overview', {})
        overview_items = [
            ('Project Name', overview.get('project_name', 'N/A')),
            ('Project Type', overview.get('project_type', 'N/A')),
            ('Language', overview.get('language', 'N/A')),
            ('Components', overview.get('total_components', 0)),
            ('Quality Score', f"{overview.get('quality_score', 0):.2f}"),
            ('Completion Time', f"{overview.get('completion_time', 0):.1f}s")
        ]
        
        for label, value in overview_items:
            html += f'''
                <div class="overview-item">
                    <div class="overview-value">{value}</div>
                    <div class="overview-label">{label}</div>
                </div>
'''
        
        html += '''
            </div>
        </div>
        
        <div class="charts-grid">
'''
        
        # Add charts
        for i, chart in enumerate(dashboard_data.get('charts', [])):
            chart_id = f"chart_{i}"
            html += f'''
            <div class="chart-card">
                <div class="chart-title">{chart.title}</div>
                <div class="chart-description">{chart.description or ''}</div>
                {self.generate_html_chart(chart, chart_id)}
            </div>
'''
        
        html += '''
        </div>
    </div>
</body>
</html>
'''
        
        return html


# Example usage
def main():
    """Test the result visualizer."""
    
    visualizer = ResultVisualizer()
    
    # Mock results data
    mock_results = {
        'generated_project': {
            'project_name': 'test_project',
            'project_type': 'application',
            'language': 'python'
        },
        'search_results': {
            'total_results': 25,
            'tier1_results': 10,
            'tier2_results': 8,
            'tier3_results': 7
        },
        'quality_metrics': {
            'overall_score': 0.85,
            'complexity_score': 0.9,
            'maintainability_index': 0.8,
            'security_score': 0.85,
            'performance_score': 0.75,
            'documentation_completeness': 0.9,
            'technical_debt_ratio': 0.1,
            'test_results': {
                'passed_tests': 7,
                'failed_tests': 0,
                'skipped_tests': 1
            }
        },
        'completion_time': 45.2
    }
    
    # Create dashboard
    dashboard = visualizer.create_summary_dashboard(mock_results)
    
    print("Dashboard created with:")
    print(f"  Overview items: {len(dashboard['overview'])}")
    print(f"  Charts: {len(dashboard['charts'])}")
    
    # Generate HTML
    html = visualizer.generate_dashboard_html(dashboard)
    
    # Save to file
    with open('test_dashboard.html', 'w') as f:
        f.write(html)
    
    print("Dashboard HTML saved to test_dashboard.html")


if __name__ == "__main__":
    main()