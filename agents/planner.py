from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import logging
from typing import Dict

from config.settings import settings

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Zero-shot planning agent that analyzes ideas and creates initial plans."""

    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=settings.temperature,
            model=settings.default_model,
            api_key=settings.openai_api_key
        )

        self.prompt = ChatPromptTemplate.from_template("""
You are an expert technical planning agent. Analyze the following idea and create a detailed initial plan.

Idea: {idea}
Context: {context}

Provide a JSON response with the following structure:
{{
  "complexity": "simple" | "medium" | "complex",
  "needs_research": boolean,
  "research_areas": ["list", "of", "topics"],
  "initial_plan": {{
    "overview": "Brief description",
    "requirements": {{
      "type": "web_app" | "api" | "mobile" | "extension" | "script" | "other",
      "key_features": ["feature1", "feature2"],
      "constraints": ["constraint1", "constraint2"]
    }},
    "dependencies": ["dependency1", "dependency2"],
    "estimated_effort_minutes": number
  }},
  "feasibility_score": 0.0-1.0,
  "feasible": boolean,
  "reasoning": "Explanation of complexity and feasibility assessment"
}}

Complexity Assessment:
- simple: < 3 dependencies, single API, < 30 min
- medium: 3-5 dependencies, 2-3 APIs, 30-90 min
- complex: > 5 dependencies, multiple complex APIs, > 90 min

Be realistic and conservative in your estimates.
""")

    async def analyze(self, idea: str, context: str = None) -> Dict:
        """Analyze an idea and create an initial plan."""
        try:
            logger.info(f"Planning idea: {idea[:100]}...")

            chain = self.prompt | self.llm
            response = await chain.ainvoke({
                "idea": idea,
                "context": context or "No additional context provided"
            })

            result = self._parse_response(response.content)

            logger.info(
                f"Plan created - Complexity: {result['complexity']}, "
                f"Feasible: {result['feasible']}, "
                f"Research needed: {result['needs_research']}"
            )

            return result

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return self._create_fallback_plan(idea)

    def _parse_response(self, content: str) -> Dict:
        """Parse LLM response and validate structure."""
        try:
            content_clean = content.strip()
            if content_clean.startswith("```json"):
                content_clean = content_clean[7:]
            if content_clean.endswith("```"):
                content_clean = content_clean[:-3]

            result = json.loads(content_clean.strip())

            result.setdefault("complexity", "medium")
            result.setdefault("needs_research", True)
            result.setdefault("research_areas", [])
            result.setdefault("feasibility_score", 0.5)
            result.setdefault("feasible", result["feasibility_score"] >= 0.3)

            if "initial_plan" not in result:
                result["initial_plan"] = {
                    "overview": "Analysis in progress",
                    "requirements": {"type": "other", "key_features": [], "constraints": []},
                    "dependencies": [],
                    "estimated_effort_minutes": 60
                }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {content[:500]}")
            raise

    def _create_fallback_plan(self, idea: str) -> Dict:
        """Create a basic fallback plan if analysis fails."""
        return {
            "complexity": "medium",
            "needs_research": True,
            "research_areas": ["general research"],
            "initial_plan": {
                "overview": f"Plan for: {idea}",
                "requirements": {
                    "type": "other",
                    "key_features": ["to be determined"],
                    "constraints": []
                },
                "dependencies": [],
                "estimated_effort_minutes": 60
            },
            "feasibility_score": 0.5,
            "feasible": True,
            "reasoning": "Fallback plan created due to analysis error"
        }
