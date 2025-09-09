# Interactive Mode Documentation

## Overview

Interactive Mode is a command-line interface for the AutoBot Assembly System that allows users to create projects through natural language commands. It's designed for users who prefer typing commands over using a graphical interface or guided wizard.

## Starting Interactive Mode

To start Interactive Mode, use the following command:

```bash
source venv/bin/activate && python -m src.cli.autobot_cli interactive
```

## Interactive Mode Interface

When you start Interactive Mode, you'll see:

```
🚀 AutoBot Assembly System - Interactive Mode
Type 'help' for commands, 'quit' to exit
📁 Projects will be saved to: ./completed_downloads

AutoBot>
```

## Available Commands

### help
Shows available commands and their usage.

```
AutoBot> help
Available commands:
  generate <description>  - Generate a project from description
  help                   - Show this help message
  quit/exit/q           - Exit the program

Examples:
  generate Create a web scraper for news sites
  generate Build a REST API with FastAPI
  generate Make a CLI tool for file processing

Note: All projects are saved to the completed_downloads directory
```

### generate <description>
Generates a new project based on your description.

```
AutoBot> generate Create a web scraper that extracts news headlines from multiple websites
```

The system will then:
1. Analyze your requirements
2. Search for relevant components
3. Generate the project structure
4. Create necessary files
5. Generate a report

### quit/exit/q
Exits Interactive Mode.

```
AutoBot> quit
Goodbye!
```

## Project Generation Process

When you use the `generate` command, here's what happens:

### 1. Requirement Analysis
The system analyzes your project description to understand:
- Project type (application, library, web service, CLI tool)
- Programming language preference
- Required components and features
- Dependencies and packages needed

### 2. Component Search
The system searches through multiple tiers:
- Tier 1: Package ecosystems (PyPI, npm, etc.)
- Tier 2: Curated collections and frameworks
- Tier 3: GitHub repositories and examples

### 3. Project Assembly
Based on the found components, the system:
- Creates project structure
- Generates necessary files
- Implements core functionality
- Adds documentation and tests

### 4. Quality Assurance
The system performs:
- Code quality checks
- Integration tests
- Documentation review
- Compatibility analysis

### 5. Output
Once complete, you'll see:
```
🎉 Project Generation Complete!
📁 Project Location: ./completed_downloads/news_scraper
📊 Components Used: 25
📄 Files Generated: 5
📋 Report: ./completed_downloads/news_scraper/analysis_report.json
🗂️  Organized in: completed_downloads directory

📄 Key Files Generated:
  • main.py
  • requirements.txt
  • README.md
  • test_main.py
  • analysis_report.json
```

## Tips for Effective Project Descriptions

### Be Specific
Instead of "make a website," try:
```
AutoBot> generate Create a e-commerce website with product catalog, shopping cart, and user authentication using React and Node.js
```

### Include Technology Preferences
```
AutoBot> generate Build a data analysis dashboard using Python, Pandas, and Plotly with SQLite database backend
```

### Specify Requirements
```
AutoBot> generate Create a CLI tool for image processing with batch conversion, resizing, and watermarking features
```

### Mention Integration Points
```
AutoBot> generate Develop a REST API for a blog system with CRUD operations for posts and comments, integrating with PostgreSQL
```

## Command Line Options

Interactive Mode supports several command line options when starting:

```bash
# Custom output directory
source venv/bin/activate && python -m src.cli.autobot_cli interactive --output /path/to/output

# Set default language
source venv/bin/activate && python -m src.cli.autobot_cli interactive --language javascript

# Set project type
source venv/bin/activate && python -m src.cli.autobot_cli interactive --type web_service

# Enable verbose output
source venv/bin/activate && python -m src.cli.autobot_cli interactive --verbose

# Skip test generation
source venv/bin/activate && python -m src.cli.autobot_cli interactive --skip-tests

# Skip documentation generation
source venv/bin/activate && python -m src.cli.autobot_cli interactive --skip-docs

# Maximum repositories to analyze
source venv/bin/activate && python -m src.cli.autobot_cli interactive --max-repos 20

# Set timeout
source venv/bin/activate && python -m src.cli.autobot_cli interactive --timeout 600
```

## Advanced Features

### Command History
Interactive Mode maintains a history of your commands. You can:
- View previous commands with the `history` command
- Repeat previous commands with `!<command_number>`
- Clear history with `clear_history`

### Configuration Management
You can modify system behavior through configuration:
```bash
# View current configuration
AutoBot> config show

# Update configuration
AutoBot> config set default_language python

# Set API keys
AutoBot> config set openai_api_key sk-...
```

### Session Management
For complex projects, you can manage sessions:
```bash
# Save current session
AutoBot> session save my_project

# Load previous session
AutoBot> session load my_project

# List all sessions
AutoBot> session list
```

## Error Handling

### Common Errors and Solutions

#### Invalid Command
```
AutoBot> unknown_command
Unknown command. Type 'help' for available commands.
```

#### Missing Project Description
```
AutoBot> generate
Please provide a project description
```

#### API Rate Limits
```
⚠️ API rate limit reached. Falling back to free tier.
```

#### Project Generation Errors
```
❌ Error: Failed to generate project
Please check your project description and try again.
```

## Integration with Other Tools

### Shell Integration
You can integrate Interactive Mode with your shell:

```bash
# Add to .bashrc or .zshrc
alias autobot="source venv/bin/activate && python -m src.cli.autobot_cli interactive"

# Create a shell function
autobot() {
    source venv/bin/activate && python -m src.cli.autobot_cli interactive "$@"
}
```

### Scripting
You can use Interactive Mode in scripts:

```bash
#!/bin/bash
# generate_project.sh
source venv/bin/activate && python -m src.cli.autobot_cli interactive <<EOF
generate Create a web scraper for news sites
quit
EOF
```

## Performance Considerations

### API Usage
- The system automatically falls back to free APIs when rate limits are reached
- Premium API keys provide faster generation and better results
- API usage is tracked and displayed in reports

### Resource Usage
- Memory usage depends on project complexity
- Disk space usage varies with project size and dependencies
- Network usage is primarily for API calls and package downloads

### Optimization Tips
- Use specific project descriptions to reduce search time
- Limit the number of repositories with `--max-repos`
- Enable caching for repeated searches with similar requirements

## Troubleshooting

### Virtual Environment Issues
```bash
# Always activate virtual environment first
source venv/bin/activate

# Then run interactive mode
python -m src.cli.autobot_cli interactive
```

### Import Errors
```bash
# Ensure you're in the project root directory
cd /path/to/AutoBot-Assembly

# Set PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Configuration Issues
```bash
# Reset to default configuration
AutoBot> config reset

# Validate current configuration
AutoBot> config validate
```

## See Also

- [Wizard Mode Documentation](wizard-mode.md) - For users who prefer guided setup
- [Web Interface Documentation](web-interface.md) - For users who prefer a graphical interface
- [Batch Mode Documentation](../README.md#usage) - For users who prefer command-line scripts