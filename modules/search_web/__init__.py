from core.modules.base import BaseModule
from core.modules.registry import registry
from typing import Dict, Any
from duckduckgo_search import DDGS

class WebSearchModule(BaseModule):
    @property
    def name(self) -> str:
        return "WebSearch"

    @property
    def description(self) -> str:
        return "Search the internet for real-time information and news using DuckDuckGo."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        if not query:
            return {"error": "No query provided"}
            
        try:
            with DDGS() as ddgs:
                # Increase results to 8 for more comprehensive context (Perplexity style)
                results = [r for m, r in enumerate(ddgs.text(query, max_results=8))]
                
            return {
                "source": "DuckDuckGo Search (Real-time)",
                "results": results,
                "summary": "\n".join([f"- {r['title']} ({r['href']}): {r['body']}" for r in results])
            }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

# Register the module
registry.register(WebSearchModule())
