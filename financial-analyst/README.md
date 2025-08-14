# Financial Analyst for Claude Desktop

A powerful financial analysis tool that integrates with Claude Desktop using Model Context Protocol (MCP). This project helps you analyze stock market data and generate visualizations through natural language queries.

## Features

- 🤖 Natural Language Stock Analysis
- 📈 Real-time Stock Data Visualization
- 📊 Interactive Plotting
- 🔄 Multi-Agent Workflow using CrewAI
- 🧠 Local LLM Integration with Deepseek-R1

## Prerequisites

1. **Python 3.12** or later
2. **Conda** for environment management
3. **Claude Desktop** application

## Installation

1. **Create and activate conda environment:**
```bash
conda create -n financial-analyst python=3.12
conda activate financial-analyst
```

2. **Install dependencies:**
```bash
pip install crewai crewai-tools ollama mcp pydantic yfinance pandas matplotlib
```


## Configuration

1. **Claude Desktop Setup:**
- Open Claude Desktop Settings
- Navigate to MCP section
- Add new global MCP server with this configuration:

```json
{
    "mcpServers": {
        "financial-analyst": {
            "command": "<path-to-conda-env>/python.exe",
            "args": [
                "<path-to-project>/server.py"
            ],
            "env": {
                "PYTHONPATH": "<path-to-project>"
            }
        }
    }
}
```

Replace the placeholders:
- `<path-to-conda-env>`: Path to Python in your conda environment (e.g., `C:\\Users\\username\\miniconda3\\envs\\financial-analyst\\python.exe`)
- `<path-to-project>`: Path to this project folder

2. **Enable the Server:**
- In Claude Desktop MCP settings
- Toggle the button to connect to the financial-analyst server

## Usage

Simply chat with Claude and ask questions about stocks. Example queries:

1. **Single Stock Analysis:**
   - "Show me Tesla's stock performance over the last 3 months"
   - "Analyze Amazon's trading volume for the past month"

2. **Comparative Analysis:**
   - "Compare Apple and Microsoft stocks for the past year"
   - "Show me price trends of NVIDIA vs AMD this year"

3. **Volume Analysis:**
   - "Plot the trading volume of Google stock for Q1"
   - "Show me unusual volume patterns in Meta stock"

## How it Works

1. Your query is processed by a specialized CrewAI workflow
2. Multiple AI agents collaborate to:
   - Parse your request
   - Generate visualization code
   - Execute and validate the analysis
3. Results are displayed through Claude Desktop

## Project Structure

- `server.py`: MCP server implementation
- `finance_crew.py`: CrewAI workflow and agent definitions
- `building-financial-analyst.ipynb`: Development notebook

## Troubleshooting

1. **Connection Issues:**
   - Verify conda environment is active
   - Check paths in Claude Desktop config
   - Ensure Ollama is running

2. **Visualization Errors:**
   - Confirm matplotlib installation
   - Check if save_code permissions are correct

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

