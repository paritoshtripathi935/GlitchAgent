# GlitchAgent - AI-Powered Browser Automation

GlitchAgent is an AI-powered agent that automates browser workflows using natural language commands. It translates natural language instructions into browser actions using Cloudflare's LLM service and executes them using Playwright.

## Features

- **Natural Language Commands**: Control your browser with simple English instructions
- **Browser Automation**: Automatically navigate, click, fill forms, and more
- **Error Handling**: Robust error handling for browser automation
- **Screenshot Capture**: Capture screenshots of the browser state
- **Execution History**: Track and review past automation tasks

## Requirements

- Python 3.8+
- Playwright
- FastAPI
- Cloudflare API credentials

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/GlitchAgent.git
   cd GlitchAgent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   playwright install
   ```

4. Set up environment variables:
   Create a `.env` file in the `backend` directory with the following:
   ```
   CLOUDFLARE_API_KEY=your_cloudflare_api_key
   CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
   ```

## Running the Application

1. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```

2. The API will be available at `http://localhost:8000`

## API Endpoints

- `POST /v1/glitch-agent/command`: Process a natural language command
- `GET /v1/glitch-agent/execution/{request_id}`: Get the result of a command execution
- `GET /v1/glitch-agent/history`: Get history of command executions
- `POST /v1/glitch-agent/stop-browser`: Stop all browser instances

## Example Usage

You can use the included test script to see GlitchAgent in action:

```bash
cd backend
python test_glitch_agent.py
```

This will demonstrate a workflow of:
1. Logging into GitHub
2. Searching for "playwright python"
3. Clicking on the first search result

## Sample Commands

GlitchAgent can understand commands like:

- "Log into GitHub using my credentials"
- "Search for 'playwright python' on GitHub"
- "Click on the first search result"
- "Fill out the contact form on example.com"
- "Navigate to amazon.com and search for headphones"

## Project Structure

```
GlitchAgent/
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── requirements.txt         # Python dependencies
│   ├── src/
│   │   ├── models/              # Pydantic models
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── utils/               # Utility functions
│   │   └── settings/            # Application settings
│   └── test_glitch_agent.py     # Test script
└── README.md                    # This file
```

## Level 1 Implementation

This implementation satisfies the Level 1 requirements of the Crustdata Build Challenge:
- Implements the Interact API to execute commands
- Handles errors (timeouts, invalid selectors)
- Demonstrates the Login → Search → Interact workflow

## Future Enhancements (Level 2+)

- Extract API for data scraping
- Support for proxies and extensions
- Scheduled tasks
- Conversational memory
- Cross-platform support

## License

MIT
