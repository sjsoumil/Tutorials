import asyncio
import json
import requests
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from dotenv import load_dotenv
import os

# ========== SETUP ==========
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4.1-nano",
    temperature=0.3
)

# ========== STATE SCHEMA ==========
class AgentState(TypedDict):
    topic: str
    academic: Optional[str]
    news: Optional[str]
    industry: Optional[str]
    report: Optional[str]
    output: Optional[str]

# ========== TOOLS ==========
class SerperSearchTool(BaseTool):
    name: str = "search_web"
    description: str = "Searches the web for real-time information and returns structured results"
    
    def _run(self, query: str) -> Dict[str, Any]:
        """Search the web using Serper API"""
        try:
            api_key = os.getenv("SERPER_API_KEY")
            if not api_key:
                return {"error": "SERPER_API_KEY not found in environment variables"}
                
            url = "https://google.serper.dev/search"
            payload = json.dumps({"q": query, "num": 5})
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Network issue: {str(e)}"}
        except Exception as e:
            return {"error": f"Search error: {str(e)}"}

# ========== AGENT FUNCTIONS ==========

def academic_agent(state: AgentState) -> Dict[str, Any]:
    topic = state["topic"]
    prompt = (
        f"Summarize the latest academic research, key papers, and leading experts for the topic: '{topic}'. "
        "Mention at least two papers, breakthroughs, and cite sources if possible."
    )
    response = llm.invoke(prompt)
    return {"academic": response.content}

def news_agent(state: AgentState) -> Dict[str, Any]:
    topic = state["topic"]
    print(f"Fetching news for: {topic}")
    
    try:
        search_tool = SerperSearchTool()
        
        # Search for news about the topic
        results = search_tool._run(f"{topic} news")
        
        if "error" in results:
            error_msg = f"Error fetching news: {results['error']}"
            print(error_msg)
            return {"news": error_msg}
            
        headlines = []
        # Check both 'news' and 'organic' sections for news items
        news_items = results.get("news", [])
        if not news_items:  # Fallback to organic results if no news results
            news_items = results.get("organic", [])[:5]
        
        for item in news_items[:5]:  # Limit to 5 news items
            title = item.get("title", "No Title")
            link = item.get("link", "")
            source = item.get("source", item.get("displayLink", ""))
            date = item.get("date", item.get("snippet", "")[:50] + "...")
            snippet = item.get("snippet", "")
            
            headlines.append(
                f"- **{title}**\n  *Source*: {source} | *Date*: {date}\n  {snippet}\n  [Read more]({link})\n"
            )
        
        news_summary = "\n".join(headlines) if headlines else "No recent news found for this topic."
        return {"news": news_summary}
        
    except Exception as e:
        error_msg = f"Error in news_agent: {str(e)}"
        print(error_msg)
        return {"news": error_msg}

def industry_agent(state: AgentState) -> Dict[str, Any]:
    topic = state["topic"]
    search_tool = SerperSearchTool()
    
    # Search for industry insights
    results = search_tool._run(f"{topic} startup funding OR product launch OR market trends")
    
    if "error" in results:
        return {"industry": f"Error fetching industry insights: {results['error']}"}
        
    organic = results.get("organic", [])
    industry_insights = []
    
    for item in organic[:5]:  # Limit to 5 items
        title = item.get("title", "No Title")
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        
        industry_insights.append(
            f"- **{title}**\n  {snippet}\n  [Read more]({link})"
        )
    
    summary = "\n".join(industry_insights) if industry_insights else "No industry info found."
    return {"industry": summary}

def merge_and_summarize_agent(state: AgentState) -> Dict[str, Any]:
    topic = state["topic"]
    academic = state.get("academic", "")
    news = state.get("news", "")
    industry = state.get("industry", "")
    
    prompt = f"""
You are an expert research summarizer. Given the following research, write a concise, well-structured '360° Topic Report' on '{topic}'.

Start with a 1-line TL;DR.

Academic highlights:
{academic}

News insights:
{news}

Industry snapshot:
{industry}

Format with sections, use clear bullet points, and end with: 'Generated by LangGraph-powered AI research assistant.'
"""
    response = llm.invoke(prompt)
    return {"report": response.content}

def output_node(state: AgentState) -> Dict[str, Any]:
    # Print for demo (replace with file write/export for prod)
    print("\n\n======= 360° TOPIC REPORT =======\n")
    print(state["report"])
    return {"output": state["report"]}

# ========== LANGGRAPH STRUCTURE ==========

def build_graph():
    # Create a new graph with the AgentState
    workflow = StateGraph(AgentState)
    
    # Add nodes for each agent
    workflow.add_node("academic_agent", academic_agent)
    workflow.add_node("news_agent", news_agent)
    workflow.add_node("industry_agent", industry_agent)
    workflow.add_node("merge_and_summarize_agent", merge_and_summarize_agent)
    workflow.add_node("output_node", output_node)
    
    # Define the graph structure
    workflow.set_entry_point("academic_agent")
    workflow.add_edge("academic_agent", "merge_and_summarize_agent")
    
    # Add parallel paths for news and industry agents
    workflow.add_edge("academic_agent", "news_agent")
    workflow.add_edge("news_agent", "industry_agent")
    workflow.add_edge("industry_agent", "merge_and_summarize_agent")
    
    # Connect to output
    workflow.add_edge("merge_and_summarize_agent", "output_node")
    workflow.add_edge("output_node", END)
    
    # Compile the workflow with parallel execution
    return workflow.compile()

# ========== MAIN RUN FUNCTION ==========

def run_topic_analyzer(topic: str):
    """Run the topic analyzer synchronously"""
    # Create a new event loop for synchronous execution
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(arun_topic_analyzer(topic))
    finally:
        loop.close()

async def arun_topic_analyzer(topic: str):
    """Run the topic analyzer asynchronously"""
    initial_state = AgentState(
        topic=topic,
        academic=None,
        news=None,
        industry=None,
        report=None,
        output=None
    )
    graph = build_graph()
    
    # Run the graph asynchronously
    final_state = await graph.ainvoke(initial_state)
    return final_state

if __name__ == "__main__":
    import sys
    # Ask the user for a topic if not provided as a command-line argument
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("Enter a topic to analyze (e.g., 'AI in healthcare'): ")
    
    # Run synchronously (recommended for most use cases)
    run_topic_analyzer(topic)
    
    # Alternative: Run asynchronously
    # asyncio.run(arun_topic_analyzer(topic))

# ---- without web search----

