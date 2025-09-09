# Wizard Mode

Wizard Mode provides a simple, guided interface for creating projects through a series of prompts. It's designed for users who prefer a step-by-step approach rather than typing commands directly.

## Overview

Wizard Mode walks you through basic project configuration options and then generates a project using the same underlying engine as Batch Mode. It's essentially a simplified frontend to the Batch Mode functionality.

## Usage

### Starting Wizard Mode

```bash
source venv/bin/activate && python -m src.cli.autobot_cli wizard
```

### Wizard Mode Workflow

1. **Welcome**: The wizard starts with a welcome message and shows where projects will be saved.

2. **Project Type**: 
   ```
   Project type [application]: 
   ```
   - Accepts the default or enter one of: `application`, `library`, `web_service`, `cli_tool`

3. **Programming Language**:
   ```
   Programming language [python]: 
   ```
   - Accepts the default or enter one of: `python`, `javascript`, `java`

4. **Project Description**:
   ```
   Describe your project:
   Project description: 
   ```
   - Enter a detailed description of what you want to build
   - This is required and will be passed directly to the generation engine

5. **Output Directory**:
   ```
   Output directory [./completed_downloads]: 
   ```
   - Accepts the default or specify a custom path

6. **Confirmation**:
   ```
   Project Configuration:
     Type: application
     Language: python
     Description: Your project description
     Output: ./completed_downloads
   
   Proceed with generation? [Y/n]: 
   ```
   - Review the settings and confirm to start generation
   - Type 'n' or anything other than 'y'/'yes' to cancel

## Features

### What Wizard Mode Does

- **Guided Prompts**: Walks through basic project configuration
- **Simple Confirmation**: Shows all settings before proceeding
- **Basic Validation**: Ensures project description is provided
- **Flexible Defaults**: Accepts default values for all options
- **Cancellation Option**: Allows easy cancellation before generation

### What Wizard Mode Doesn't Do

- **No AI Analysis**: Doesn't analyze requirements or suggest components
- **No Input Validation**: Only validates that description is not empty
- **No Progress Tracking**: Shows the same progress as Batch Mode
- **No Advanced Options**: Doesn't expose all CLI options like `--skip-tests`, `--max-repos`, etc.
- **No Error Handling**: Uses the same error handling as Batch Mode

## Command Line Options

Wizard Mode supports the same command line options as Batch Mode, which are applied to all projects generated in wizard mode:

```bash
source venv/bin/activate && python -m src.cli.autobot_cli wizard \
  --output ./my_projects \
  --skip-tests \
  --max-repos 15 \
  --timeout 600
```

### Common Options

- `--output, -o`: Output directory for generated projects
- `--skip-tests`: Skip test generation
- `--skip-docs`: Skip documentation generation
- `--max-repos`: Maximum repositories to analyze (default: 10)
- `--timeout`: Timeout in seconds (default: 300)
- `--verbose, -v`: Enable verbose output

## Examples

### Basic Usage

```bash
$ source venv/bin/activate && python -m src.cli.autobot_cli wizard
🧙 AutoBot Assembly System - Wizard Mode
Let's create your project step by step...

📁 Projects will be saved to: ./completed_downloads

Project type [application]: 
Programming language [python]: 

Describe your project:
Project description: Create a web scraper that extracts news headlines from multiple websites

Output directory [./completed_downloads]: 

📋 Project Configuration:
  Type: application
  Language: python
  Description: Create a web scraper that extracts news headlines from multiple websites
  Output: ./completed_downloads

Proceed with generation? [Y/n]: y
🚀 AutoBot Assembly System - Batch Mode
📝 Project: Create a web scraper that extracts news headlines from multiple websites
🔧 Language: python
📁 Output: ./completed_downloads
--------------------------------------------------
🔍 Searching for components...
✅ Found 25 components
🏗️ Generating project...
✅ Project generated: ./completed_downloads/web_scraper
📊 Generating analysis report...
✅ Report saved: ./completed_downloads/web_scraper/analysis_report.json

🎉 Project Generation Complete!
📁 Project Location: ./completed_downloads/web_scraper
📊 Components Used: 25
📄 Files Generated: 5
📋 Report: ./completed_downloads/web_scraper/analysis_report.json
🗂️  Organized in: completed_downloads directory

📄 Key Files Generated:
  • main.py
  • requirements.txt
  • README.md
  • test_main.py
  • analysis_report.json
```

### With Custom Options

```bash
$ source venv/bin/activate && python -m src.cli.autobot_cli wizard \
  --output ./my_apps \
  --skip-tests \
  --max-repos 20

🧙 AutoBot Assembly System - Wizard Mode
Let's create your project step by step...

📁 Projects will be saved to: ./my_apps

Project type [application]: web_service
Programming language [python]: 

Describe your project:
Project description: Build a REST API for user management with authentication

Output directory [./my_apps]: 

📋 Project Configuration:
  Type: web_service
  Language: python
  Description: Build a REST API for user management with authentication
  Output: ./my_apps

Proceed with generation? [Y/n]: y
🚀 AutoBot Assembly System - Batch Mode
📝 Project: Build a REST API for user management with authentication
🔧 Language: python
📁 Output: ./my_apps
--------------------------------------------------
🔍 Searching for components...
✅ Found 32 components
🏗️ Generating project...
✅ Project generated: ./my_apps/rest_api
...
```

## Comparison with Other Modes

| Feature | Wizard Mode | Interactive Mode | Batch Mode |
|---------|-------------|------------------|------------|
| **Input Method** | Guided prompts | Command-line commands | Single command |
| **Complexity** | Simple | Medium | Low |
| **Flexibility** | Low | Medium | High |
| **Options** | Basic via CLI args | All CLI options | All CLI options |
| **Best For** | Beginners | Regular users | Automation |
| **Project Analysis** | No | No | No |

## Tips

1. **Be Descriptive**: The more detailed your project description, the better the results
2. **Use Defaults**: The defaults are usually good choices for most projects
3. **Check Path**: Make sure the output directory exists or you have write permissions
4. **Be Patient**: Project generation can take 30 seconds to several minutes
5. **Review Output**: Always check the generated files and README for usage instructions

## Troubleshooting

### Common Issues

**1. Empty Project Description**
```
Project description: 
Project description is required!
```
- Solution: Make sure to enter a description before pressing Enter

**2. Permission Denied**
```
Error: [Errno 13] Permission denied: './completed_downloads'
```
- Solution: Check directory permissions or use a different output directory

**3. Generation Takes Too Long**
- Solution: Reduce `--max-repos` value or increase `--timeout` value
- Check your internet connection and API key status

**4. Poor Quality Results**
- Solution: Provide more detailed project descriptions
- Consider using premium API keys (OpenAI, Anthropic) for better results

### Getting Help

If you encounter issues with Wizard Mode:

1. Try the same command in Batch Mode to see if it's a mode-specific issue
2. Check the troubleshooting section in the main documentation
3. Enable verbose mode with `--verbose` for more detailed output
4. Verify your API keys are properly configured

## Next Steps

After generating a project with Wizard Mode:

1. **Review the Generated Code**: Check the generated files in your output directory
2. **Install Dependencies**: Run `pip install -r requirements.txt` for Python projects
3. **Test the Project**: Run tests if they were generated
4. **Customize**: Modify the generated code to fit your specific needs
5. **Try Other Modes**: Explore Interactive Mode for more control or Batch Mode for automation
