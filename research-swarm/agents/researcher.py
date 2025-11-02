import asyncio
from typing import List, Dict
from langchain.tools import Tool
from langchain_community.utilities import SerpAPIWrapper, ArxivAPIWrapper

class ResearchAgent:
    def __init__(self, specialty: str):
        self.specialty = specialty
        self.tools = self._setup_tools()
    
    def _setup_tools(self):
        tools = []
        
        if self.specialty == "api":
            # API documentation search
            serp_api = SerpAPIWrapper()
            tools.append(
                Tool(
                    name="api_search",
                    func=serp_api.run,
                    description="Search for API documentation"
                )
            )
        elif self.specialty == "code":
            # Code example search
            serp_api = SerpAPIWrapper()
            tools.append(
                Tool(
                    name="code_search",
                    func=serp_api.run,
                    description="Search for code examples"
                )
            )
        elif self.specialty == "papers":
            # Academic paper search
            arxiv = ArxivAPIWrapper()
            tools.append(
                Tool(
                    name="arxiv_search",
                    func=arxiv.run,
                    description="Search academic papers"
                )
            )
        elif self.specialty == "tools":
            # Tool search
            serp_api = SerpAPIWrapper()
            tools.append(
                Tool(
                    name="tool_search",
                    func=serp_api.run,
                    description="Search for tools and frameworks"
                )
            )
        
        return tools
    
    async def research(self, query: str) -> Dict:
        results = []
        for tool in self.tools:
            try:
                # Run the synchronous tool function in a thread pool
                result = await asyncio.to_thread(tool.func, query)
                results.append({
                    "source": tool.name,
                    "content": result
                })
            except Exception as e:
                results.append({
                    "source": tool.name,
                    "error": str(e)
                })

        return {
            "agent": self.specialty,
            "query": query,
            "findings": results
        }

class ResearchSwarm:
    def __init__(self):
        self.agents = [
            ResearchAgent("api"),
            ResearchAgent("code"),
            ResearchAgent("papers"),
            ResearchAgent("tools")
        ]
    
    async def research(self, idea: str, areas: List[str]) -> List[Dict]:
        tasks = []
        for area in areas:
            for agent in self.agents:
                tasks.append(agent.research(f"{idea} {area}"))
        
        results = await asyncio.gather(*tasks)
        return results