from mcp.server.fastmcp import FastMCP
from finance_crew import run_financial_analysis
import json

# create FastMCP instance
mcp = FastMCP("financial-analyst")

@mcp.tool()
def analyze_stock(query: str) -> dict:
    """
    Analyzes stock market data based on the query and generates executable Python code for analysis and visualization.
    Returns a formatted Python script ready for execution.
    
    The query is a string that must contain the stock symbol (e.g., TSLA, AAPL, NVDA, etc.), 
    timeframe (e.g., 1d, 1mo, 1y), and action to perform (e.g., plot, analyze, compare).

    Example queries:
    - "Show me Tesla's stock performance over the last 3 months"
    - "Compare Apple and Microsoft stocks for the past year"
    - "Analyze the trading volume of Amazon stock for the last month"

    Args:
        query (str): The query to analyze the stock market data.
    
    Returns:
        dict: A dictionary containing the result or error message.
    """
    try:
        result = run_financial_analysis(query)
        print("DEBUG MCP OUTPUT:", result)  # Debug output
        # Clean the output to ensure valid JSON
        if isinstance(result, dict):
            cleaned = json.dumps(result)
        else:
            lines = str(result).splitlines()
            # Remove ASCII tables and code blocks
            cleaned = '\n'.join(
                line for line in lines
                if not line.strip().startswith(('+', '|', '-', '`'))
            ).replace('```', '').strip()
        return {"result": cleaned}
    except Exception as e:
        return {"result": f"Error: {e}"}
    

@mcp.tool()
def save_code(code: str) -> dict:
    """
    Expects a nicely formatted, working and executable python code as input in form of a string. 
    Save the given code to a file stock_analysis.py, make sure the code is a valid python file, nicely formatted and ready to execute.

    Args:
        code (str): The nicely formatted, working and executable python code as string.
    
    Returns:
        dict: A dictionary containing the success message or error.
    """
    try:
        with open('stock_analysis.py', 'w') as f:
            f.write(code)
        return {"result": "Code saved successfully"}
    except Exception as e:
        return {"result": f"Error: {e}"}

@mcp.tool()
def run_code_and_show_plot() -> dict:
    """
    Run the code in stock_analysis.py and generate the plot
    """
    try:
        with open('stock_analysis.py', 'r') as f:
            exec(f.read())
        return {"result": "Plot generated successfully"}
    except Exception as e:
        return {"result": f"Error: {e}"}

# Run the server locally
if __name__ == "__main__":
    mcp.run(transport='stdio')