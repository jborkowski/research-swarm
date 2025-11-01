from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json

class PlannerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0.1,
            model="gpt-4"
        )
        self.prompt = ChatPromptTemplate.from_template("""
        Analyze the following idea and create an initial plan.
        
        Idea: {idea}
        
        Provide a JSON response with:
        1. complexity: "simple", "medium", or "complex"
        2. needs_research: boolean
        3. research_areas: list of topics to research
        4. initial_plan: high-level implementation steps
        5. estimated_effort: in minutes
        6. feasibility_score: 0-1
        
        Be realistic about complexity and effort.
        """)
    
    async def analyze(self, idea: str) -> dict:
        chain = self.prompt | self.llm
        response = await chain.ainvoke({"idea": idea})
        
        # Parse JSON response
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if response is not valid JSON
            result = {
                "complexity": "medium",
                "needs_research": True,
                "research_areas": [],
                "initial_plan": {"steps": ["Implement basic functionality"]},
                "estimated_effort": 120,
                "feasibility_score": 0.7
            }
        
        # Validate and set defaults
        result["complexity"] = result.get("complexity", "medium")
        result["needs_research"] = result.get("needs_research", True)
        
        return result