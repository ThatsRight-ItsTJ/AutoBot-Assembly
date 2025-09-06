# AI-Powered GitHub Repository Assembly System

Transform natural language project descriptions into working codebases by intelligently discovering, analyzing, and assembling compatible GitHub repositories and files.

## 🎯 What This Does

Input: *"Create a Python FastAPI application with JWT authentication, PostgreSQL database, and Redis caching"*

Output: A complete project structure with production-ready code files selectively extracted from the best GitHub repositories, fully compatible and license-compliant.

## 🏗️ System Architecture

```
User Prompt → AI Analysis → Tiered Search → File Scoring → Compatibility Analysis → Selective Download
     ↓              ↓           ↓              ↓                ↓                    ↓
Pollinations AI → Project → GitHub API → MegaLinter+Semgrep → License Check → GitHub-File-Seek
                Structure   Libraries.io   ast-grep+linguist   Compatibility
```

## 🔧 Installation Requirements

### Prerequisites
- **Python 3.9+**
- **Docker** (for analysis tools)
- **Ruby 3.0+** (for github-linguist)
- **Rust** (for ast-grep)
- **Node.js 16+** (optional, for JavaScript analysis)
- **Git**

### System Resources
- **Memory**: 8GB+ recommended
- **Storage**: 50GB+ for repository caching
- **Network**: Stable internet for API calls

## 📦 Dependencies to Install

### Python Packages
```bash
pip install PyGithub semgrep radon pipdeptree requests aiohttp asyncio docker redis
```

### Ruby Gems
```bash
gem install github-linguist
```

### Rust Tools
```bash
cargo install ast-grep
```

### Docker Images
```bash
docker pull oxsecurity/megalinter:v7
docker pull redis:alpine
```

### Optional (for JavaScript support)
```bash
npm install -g eslint @eslint/js
```

## 🍴 Repositories to Fork/Clone

### Core Integration Repository
```bash
# REQUIRED - Your primary file extraction engine
git clone https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek.git
cd GitHub-File-Seek
# Follow their setup instructions
```

### Reference Repositories (for patterns and logic)
```bash
# Language detection patterns
git clone https://github.com/github/linguist.git

# License detection algorithms  
git clone https://github.com/licensee/licensee.git

# Curated repository lists
git clone https://github.com/sindresorhus/awesome.git
```

### Optional Reference Repositories
```bash
# GitHub API usage patterns (optional - just for reference)
git clone https://github.com/PyGithub/PyGithub.git

# Package ecosystem understanding (optional)
git clone https://github.com/librariesio/libraries.io.git
```

## 🔑 API Keys Required

### Required APIs
1. **GitHub Personal Access Token**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate token with `repo` and `user` scopes
   - 5,000 requests/hour (authenticated) vs 60/hour (unauthenticated)

2. **Pollinations AI** (Free tier available)
   - No API key required for basic usage
   - Endpoint: `https://text.pollinations.ai/openai`

### Optional APIs
1. **libraries.io API** (for package ecosystem data)
   - Free tier: 60 requests/minute
   - Register at libraries.io for API key

## 📁 Project Structure

```
github-assembly-system/
├── src/
│   ├── ai_integration/          # Pollinations AI client
│   ├── search/                  # Tiered search implementation
│   │   ├── tier1_packages.py    # Package ecosystem search
│   │   ├── tier2_curated.py     # Awesome lists + GitHub topics
│   │   └── tier3_discovery.py   # AI-driven GitHub search
│   ├── analysis/                # File scoring system
│   │   ├── megalinter_client.py # Code quality analysis
│   │   ├── semgrep_client.py    # Security analysis
│   │   ├── astgrep_client.py    # Structure analysis
│   │   └── unified_scorer.py    # Combined scoring
│   ├── compatibility/           # Compatibility analysis
│   │   ├── framework_checker.py # Framework compatibility
│   │   └── license_analyzer.py  # License compliance
│   └── orchestration/           # Main workflow
│       ├── project_analyzer.py  # AI prompt analysis
│       ├── search_orchestrator.py
│       └── batch_generator.py   # GitHub-File-Seek integration
├── config/
│   ├── compatibility_matrix.json
│   ├── project_templates.json
│   └── search_patterns.json
├── scripts/
│   ├── setup.sh                # Installation script
│   └── test_workflow.py        # End-to-end testing
└── requirements.txt
```

## 🚀 Quick Start

### 1. Clone This Repository
```bash
git clone https://github.com/your-username/github-assembly-system.git
cd github-assembly-system
```

### 2. Run Setup Script
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your GitHub token and other API keys
```

### 4. Test Installation
```bash
python scripts/test_workflow.py
```

### 5. Basic Usage
```python
from src.orchestration.project_analyzer import ProjectAnalyzer

analyzer = ProjectAnalyzer()
result = await analyzer.assemble_project(
    prompt="Create a Python web scraper with proxy rotation",
    language="python"
)
print(f"Generated batch config: {result.batch_config}")
```

## 🔍 What Gets Analyzed

### File-Level Scoring (80% Static Analysis)
- **Code Quality**: Complexity, maintainability, style compliance
- **Security**: Vulnerability detection, security patterns
- **Structure**: Dependencies, coupling, adaptability
- **Documentation**: Comments, README quality, examples

### Repository-Level Assessment (20% AI Enhancement)
- **Uniqueness**: Novel implementations vs. common patterns
- **Integration Potential**: How well components work together
- **Maintenance Status**: Activity, community engagement
- **License Compatibility**: Legal compliance checking

## 📊 Cost Breakdown

### Development Costs
- **Setup Time**: 4-8 hours
- **Customization**: 8-16 hours additional

### Operating Costs (Monthly)
- **Pollinations AI**: $0-50 (depending on usage)
- **GitHub API**: $0 (free tier sufficient for most use)
- **Infrastructure**: $20-100 (if using cloud hosting)
- **Total**: $20-150/month

### Performance Targets
- **Complete Workflow**: <5 minutes
- **Simple Projects**: <2 minutes  
- **Complex Projects**: <10 minutes

## 🤝 Integration with GitHub-File-Seek

This system generates optimized batch configurations for GitHub-File-Seek:

```json
{
  "repositories": [
    {
      "repository": "fastapi/fastapi",
      "profile": "api",
      "patterns": ["fastapi/security/*.py", "fastapi/middleware/*.py"],
      "purpose": "Authentication and middleware components",
      "compatibility_score": 0.92
    }
  ]
}
```

GitHub-File-Seek then downloads only the highest-quality, most compatible files.

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### End-to-End Test
```bash
python scripts/test_complete_workflow.py \
  --prompt "Create a React dashboard with authentication" \
  --language "javascript"
```

## 🐳 Docker Deployment

```bash
# Build the system
docker-compose build

# Run with all dependencies
docker-compose up -d

# Test the deployment
curl -X POST http://localhost:8000/api/assemble \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Python CLI tool with configuration management", "language": "python"}'
```

## 🔧 Configuration

### Main Configuration (`config/settings.py`)
```python
# AI Settings
POLLINATIONS_ENDPOINT = "https://text.pollinations.ai/openai"
AI_MODEL = "gpt-4"  # or "claude-3"

# GitHub Settings  
GITHUB_TOKEN = "your_github_token"
GITHUB_RATE_LIMIT = 5000  # requests per hour

# Quality Thresholds
MIN_FILE_SCORE = 0.7
MIN_COMPATIBILITY_SCORE = 0.8
MAX_REPOSITORIES = 50
```

### File Scoring Weights (`config/scoring.json`)
```json
{
  "quality_weight": 0.3,
  "security_weight": 0.25, 
  "structure_weight": 0.2,
  "standalone_weight": 0.15,
  "documentation_weight": 0.1
}
```

## 📚 Documentation

- [Detailed Setup Guide](docs/setup.md)
- [API Reference](docs/api.md)
- [Configuration Options](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🤖 AI Integration Details

### Pollinations AI Usage
- **Prompt Analysis**: Convert natural language to project structure
- **Gap Analysis**: Identify missing components from initial search
- **Query Generation**: Create targeted GitHub search queries
- **Uniqueness Assessment**: Evaluate code novelty and value

### Rate Limiting
- Built-in request throttling
- Intelligent caching to minimize API calls
- Fallback to cached results when limits exceeded

## 🔐 Security Considerations

- API keys stored in environment variables
- No sensitive data in repository cloning
- License compliance checking before download
- Security vulnerability scanning via Semgrep

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Issues**: GitHub Issues tracker
- **Discussions**: GitHub Discussions
- **Documentation**: [Wiki](wiki/Home)

## 🌟 Acknowledgments

Built on top of amazing open-source tools:
- [GitHub-File-Seek](https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek) - Selective file extraction
- [MegaLinter](https://github.com/oxsecurity/megalinter) - Multi-language analysis
- [Semgrep](https://github.com/semgrep/semgrep) - Security analysis  
- [github-linguist](https://github.com/github/linguist) - Language detection
- [Pollinations AI](https://pollinations.ai/) - AI-powered analysis
