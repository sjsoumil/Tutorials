import asyncio
import json
import requests
from typing import Dict, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import os

from openai import OpenAI

# ========== SETUP ==========
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise EnvironmentError("Please set your OPENROUTER_API_KEY in your .env file.")

# Initialize OpenAI client with OpenRouter configuration
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

def kimi_k2_chat(messages, model="moonshotai/kimi-k2", temperature=0.3, max_tokens=1000):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content

# ========== TOOLS ==========
class SerperSearchTool:
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

# ========== STATE SCHEMA ==========
class AgentState(TypedDict):
    topic: str
    academic: Optional[str]
    news: Optional[str]
    report: Optional[str]
    output: Optional[str]

# ========== AGENT FUNCTIONS ==========

def academic_agent(state: AgentState) -> AgentState:
    topic = state["topic"]
    
    # First, search the web for latest information
    search_tool = SerperSearchTool()
    search_results = search_tool._run(f"latest academic research and papers about {topic}")
    
    # Extract relevant information from search results
    search_context = ""
    if "organic" in search_results:
        search_context = "Recent search results:\n"
        for i, result in enumerate(search_results["organic"][:3], 1):
            search_context += f"{i}. {result.get('title', 'No title')}: {result.get('snippet', 'No snippet')}\n"
    
    messages = [
        {"role": "system", "content": "You are an expert at finding and summarizing academic research. Use the provided search results to enhance your knowledge with up-to-date information."},
        {"role": "user", "content": (
            f"Summarize the latest academic research, key papers, and leading experts for the topic: '{topic}'.\n\n"
            f"{search_context}\n"
            "Mention at least two papers, breakthroughs, and trends. "
            "If search results are available, incorporate them into your response. "
            "Otherwise, rely on your training knowledge."
        )}
    ]
    content = kimi_k2_chat(messages)
    return {"academic": content}

def news_agent(state: AgentState) -> AgentState:
    topic = state["topic"]
    
    # Search for recent news
    search_tool = SerperSearchTool()
    search_results = search_tool._run(f"latest news about {topic}")
    
    # Format search results
    news_items = []
    if "news" in search_results:
        for item in search_results["news"][:5]:  # Get top 5 news items
            news_items.append({
                "title": item.get("title", "No title"),
                "source": item.get("source", "Unknown source"),
                "date": item.get("date", "Unknown date"),
                "snippet": item.get("snippet", "No details available")
            })
    
    messages = [
        {"role": "system", "content": "You are a news analyst that provides concise, factual summaries of current events."},
        {"role": "user", "content": (
            f"Provide a summary of the latest news about '{topic}'. "
            f"Here are some recent search results (use them if relevant):\n{json.dumps(news_items, indent=2)}\n\n"
            "Focus on the most important developments and their implications. "
            "Include dates and sources where available. "
            "If no recent news is found, state that clearly and provide general information."
        )}
    ]
    content = kimi_k2_chat(messages)
    return {"news": content}

def merge_and_summarize_agent(state: AgentState) -> AgentState:
    academic = state.get("academic", "No academic research found.")
    news = state.get("news", "No news found.")
    topic = state["topic"]
    
    messages = [
        {"role": "system", "content": "You are an expert analyst that synthesizes information from multiple sources into a comprehensive report."},
        {"role": "user", "content": (
            f"Create a comprehensive report about '{topic}' by combining the following information. "
            "Focus on key insights, trends, and important details. Make sure to maintain academic rigor while being accessible.\n\n"
            f"ACADEMIC RESEARCH:\n{academic}\n\n"
            f"LATEST NEWS:\n{news}\n\n"
            "Provide a well-structured report with clear sections and key takeaways. "
            "Include references to sources where available."
        )}
    ]
    
    report = kimi_k2_chat(messages)
    return {"report": report}

def output_node(state: AgentState) -> AgentState:
    print("\n\n======= 360° TOPIC REPORT =======\n")
    print(state["report"])
    return {"output": state["report"]}

# ========== LANGGRAPH STRUCTURE ==========

def build_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("academic_agent", academic_agent)
    workflow.add_node("news_agent", news_agent)
    workflow.add_node("merge_and_summarize_agent", merge_and_summarize_agent)
    workflow.add_node("output_node", output_node)
    
    # Define edges
    workflow.add_edge("academic_agent", "news_agent")
    workflow.add_edge("news_agent", "merge_and_summarize_agent")
    workflow.add_edge("merge_and_summarize_agent", "output_node")
    
    # Set entry and end points
    workflow.set_entry_point("academic_agent")
    workflow.set_finish_point("output_node")
    
    return workflow.compile()

# ========== MAIN RUN FUNCTION ==========

def run_topic_analyzer(topic: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(arun_topic_analyzer(topic))
    finally:
        loop.close()

async def arun_topic_analyzer(topic: str):
    initial_state = AgentState(
        topic=topic,
        academic=None,
        report=None,
        output=None
    )
    graph = build_graph()
    final_state = await graph.ainvoke(initial_state)
    return final_state


# ========== ENTRY POINT ==========
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("Enter a topic to analyze (e.g., 'AI in education'): ")

    run_topic_analyzer(topic)
