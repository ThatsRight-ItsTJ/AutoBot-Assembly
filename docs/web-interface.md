# Web Interface Documentation

## Overview

The Web Interface provides a browser-based experience for the AutoBot Assembly System using Flask and WebSocket communication. It features real-time project generation with live updates and an intuitive interface for creating projects.

## Starting the Web Interface

To start the web server, use the following command:

```bash
source venv/bin/activate && python -m src.web.web_server
```

The server will start and be available at `http://localhost:5000` by default.

## Accessing the Web Interface

1. Open your web browser
2. Navigate to `http://localhost:5000`
3. You'll see the AutoBot Assembly System interface

## Interface Overview

### Main Page (`/`)
The main interface provides:
- Project creation form
- Real-time generation status
- Project download options

### Available Pages
- **Home** (`/`) - Main project creation interface
- **Dashboard** (`/dashboard`) - Active sessions monitoring
- **History** (`/history`) - Previous projects (placeholder)

## Creating a Project

### 1. Project Description
Enter your project description in the main text area:

```
Create a web scraper that extracts news headlines from multiple websites and saves them to JSON format with timestamps
```

### 2. Generate Project
Click the "Generate Project" button to start the process. The interface will show real-time updates as your project is being generated.

## Real-Time Updates

### Progress Tracking
As your project is being generated, you'll see real-time updates:

```
🔍 Analyzing requirements... (10%)
🔍 Searching for components... (25%)
🏗️ Assembling project... (50%)
✅ Running quality checks... (75%)
🎉 Project ready! (100%)
```

### Live Status Updates
The interface provides live status updates including:
- Current stage of generation
- Progress percentage
- Active component searches
- Quality check results

### WebSocket Communication
The web interface uses WebSockets for real-time communication:
- Instant progress updates
- Error notifications
- Completion alerts

## Available API Endpoints

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Get Active Sessions
```bash
curl http://localhost:5000/api/sessions
```

### Get Session Details
```bash
curl http://localhost:5000/api/session/{session_id}
```

### Generate Project
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a web scraper"}'
```

### Download Project
```bash
curl -o project.zip http://localhost:5000/api/download/{session_id}
```

## WebSocket Events

### Client Events
The interface sends these events to the server:
- `join_session` - Subscribe to session updates
- `leave_session` - Unsubscribe from session updates

### Server Events
The server sends these events to clients:
- `progress_update` - Generation progress
- `error` - Error notification
- `completion` - Project generation complete

## Configuration

### Server Configuration
You can configure the web server by modifying the `WebConfig` class in `src/web/web_server.py`:

```python
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
```

### Environment Variables
You can configure the web server using environment variables:

```bash
export AUTOBOT_WEB_HOST=0.0.0.0
export AUTOBOT_WEB_PORT=5000
export AUTOBOT_WEB_DEBUG=true
export AUTOBOT_WEB_SECRET_KEY=your-secret-key
```

## What Actually Exists

### Implemented Features
- **Flask Web Server**: Basic web interface with templates
- **Real-time Updates**: WebSocket communication for live progress updates
- **Project Generation**: Creates basic project structure with main files
- **API Endpoints**: REST API for health checks, session management, and project generation
- **File Downloads**: ZIP download functionality for generated projects
- **Session Management**: Tracks active generation sessions

### Limited/Placeholder Features
- **Dashboard**: Shows active sessions but limited functionality
- **History**: Placeholder page with no actual history implementation
- **Advanced Options**: No advanced configuration options in the web interface
- **Authentication**: No user authentication system
- **Caching**: No caching implementation
- **Performance Optimization**: Basic implementation without advanced optimizations

### What Doesn't Exist
- **Security Features**: No authentication, authorization, or rate limiting
- **Production Readiness**: Not configured for production deployment
- **Advanced UI**: No complex user interface components
- **File Management**: No file upload or management features
- **Database**: No persistent storage for projects or sessions
- **Mobile Optimization**: Basic responsive design but no mobile-specific features

## Generated Project Structure

The web interface creates a simplified project structure:

```
project_name/
├── main.py (or index.js)
├── requirements.txt (or package.json)
├── README.md
└── analysis_report.json
```

### Python Project Example
```python
#!/usr/bin/env python3
"""
AutoBot Generated Project

Generated by AutoBot Assembly System
"""

def main():
    """Main entry point."""
    print("Hello from AutoBot!")
    print("Project: AutoBot Project")
    print("Type: web_application")
    
    # TODO: Implement your project logic here
    pass

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Common Issues

#### Connection Problems
```
Failed to connect to WebSocket
```
Solutions:
- Check if the server is running
- Verify the WebSocket URL
- Check browser console for errors
- Try refreshing the page

#### Project Generation Fails
```
Error during project generation
```
Solutions:
- Check the project description
- Verify API keys are configured
- Review server logs
- Try a simpler project description

#### Download Issues
```
Failed to download project
```
Solutions:
- Check if the project generation completed
- Verify the session ID is correct
- Check browser download settings
- Try downloading individual files

### Debug Mode
Enable debug mode for detailed logging:

```bash
export AUTOBOT_WEB_DEBUG=true
source venv/bin/activate && python -m src.web.web_server
```

### Browser Console
Check the browser console for:
- JavaScript errors
- WebSocket connection issues
- Network request problems
- API response errors

## Browser Compatibility

The web interface supports:
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

For best performance, use the latest version of your preferred browser.

## Limitations

### Current Limitations
1. **Simplified Generation**: Creates basic project structure, not full-featured projects
2. **No Advanced Options**: Limited configuration options compared to CLI modes
3. **No Authentication**: Not suitable for production use without security features
4. **No Persistence**: Sessions and projects are not stored permanently
5. **Limited Error Handling**: Basic error handling without detailed recovery options

### Future Enhancements
The documentation mentions features that are not yet implemented:
- Advanced project configuration options
- User authentication and session persistence
- Project history and management
- More sophisticated project generation
- Production deployment features

## Comparison with Other Modes

| Feature | Web Interface | CLI Batch Mode | CLI Interactive Mode | CLI Wizard Mode |
|---------|---------------|----------------|---------------------|-----------------|
| **Input Method** | Browser GUI | Command-line | Command-line | Guided prompts |
| **Real-time Updates** | ✅ WebSocket | ❌ | ❌ | ❌ |
| **Project Preview** | ✅ Browser | ❌ | ❌ | ❌ |
| **File Downloads** | ✅ ZIP | ❌ | ❌ | ❌ |
| **Session Management** | ✅ Built-in | ❌ | ❌ | ❌ |
| **Advanced Options** | ❌ Limited | ✅ All | ✅ All | ✅ Basic |
| **Best For** | Visual users | Automation | Regular use | Beginners |
| **Flexibility** | Medium | High | High | Low |

## Tips for Using Web Interface

1. **Be Specific**: More detailed descriptions generate better basic projects
2. **Use Simple Language**: The system works best with clear, straightforward descriptions
3. **Check Downloads**: Always verify downloaded projects before using them
4. **Monitor Progress**: Watch the real-time updates to understand generation stages
5. **Use Debug Mode**: Enable debug mode if you encounter issues

## Next Steps

After generating a project with the web interface:

1. **Review the Generated Code**: Check the basic structure and files created
2. **Customize**: The generated projects are starting points that need customization
3. **Add Functionality**: Implement the actual logic for your specific needs
4. **Test**: Add tests and verify the project works as expected
5. **Explore Other Modes**: Try CLI modes for more control and options

## See Also

- [Wizard Mode Documentation](wizard-mode.md) - For users who prefer guided setup
- [Interactive Mode Documentation](interactive-mode.md) - For users who prefer command-line control
- [Batch Mode Documentation](../README.md#usage) - For users who prefer command-line scripts