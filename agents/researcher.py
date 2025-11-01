import asyncio
from typing import List, Dict, Optional
import logging
import aiohttp
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Individual research agent specialized in a specific domain."""

    def __init__(self, specialty: str):
        self.specialty = specialty
        self.llm = ChatOpenAI(
            temperature=0.3,
            model=settings.default_model,
            api_key=settings.openai_api_key
        )

    async def research(self, query: str, idea: str) -> Dict:
        """Conduct research on a specific query."""
        try:
            logger.info(f"[{self.specialty}] Researching: {query[:100]}")

            if self.specialty == "api":
                result = await self._research_apis(query, idea)
            elif self.specialty == "code":
                result = await self._research_code_examples(query, idea)
            elif self.specialty == "tools":
                result = await self._research_tools(query, idea)
            elif self.specialty == "compliance":
                result = await self._research_compliance(query, idea)
            else:
                result = await self._general_research(query, idea)

            logger.info(f"[{self.specialty}] Research completed")
            return result

        except Exception as e:
            logger.error(f"[{self.specialty}] Research failed: {e}")
            return {
                "agent": self.specialty,
                "query": query,
                "status": "error",
                "error": str(e),
                "findings": []
            }

    async def _research_apis(self, query: str, idea: str) -> Dict:
        """Research available APIs for the idea."""
        prompt = ChatPromptTemplate.from_template("""
You are an API research specialist. Given an idea, identify the best APIs and services to use.

Idea: {idea}
Research Focus: {query}

Provide a JSON response with:
{{
  "recommended_apis": [
    {{
      "name": "API name",
      "purpose": "What it does",
      "documentation": "URL or description",
      "complexity": "simple" | "medium" | "complex",
      "authentication": "type of auth",
      "rate_limits": "limits if known",
      "cost": "free/paid/freemium"
    }}
  ],
  "alternatives": ["alternative options"],
  "recommendations": "Overall recommendation"
}}
""")

        chain = prompt | self.llm
        response = await chain.ainvoke({"idea": idea, "query": query})

        return {
            "agent": self.specialty,
            "query": query,
            "status": "success",
            "findings": [response.content],
            "summary": "API research completed"
        }

    async def _research_code_examples(self, query: str, idea: str) -> Dict:
        """Research code examples and implementations."""
        prompt = ChatPromptTemplate.from_template("""
You are a code research specialist. Find similar implementations and patterns.

Idea: {idea}
Research Focus: {query}

Provide a JSON response with:
{{
  "similar_projects": [
    {{
      "name": "Project name",
      "description": "What it does",
      "tech_stack": ["technologies used"],
      "repository": "URL if available",
      "relevance": "How it relates to this idea"
    }}
  ],
  "code_patterns": ["relevant design patterns"],
  "best_practices": ["applicable best practices"],
  "recommendations": "Implementation recommendations"
}}
""")

        chain = prompt | self.llm
        response = await chain.ainvoke({"idea": idea, "query": query})

        return {
            "agent": self.specialty,
            "query": query,
            "status": "success",
            "findings": [response.content],
            "summary": "Code research completed"
        }

    async def _research_tools(self, query: str, idea: str) -> Dict:
        """Research tools, frameworks, and libraries."""
        prompt = ChatPromptTemplate.from_template("""
You are a tools and frameworks specialist. Recommend the best tools for implementation.

Idea: {idea}
Research Focus: {query}

Provide a JSON response with:
{{
  "frameworks": [
    {{
      "name": "Framework name",
      "purpose": "What it's good for",
      "pros": ["advantages"],
      "cons": ["disadvantages"],
      "learning_curve": "easy" | "medium" | "hard",
      "maturity": "stable" | "beta" | "experimental"
    }}
  ],
  "libraries": ["recommended libraries"],
  "development_tools": ["useful dev tools"],
  "deployment_options": ["hosting/deployment options"],
  "recommendation": "Best choice and why"
}}
""")

        chain = prompt | self.llm
        response = await chain.ainvoke({"idea": idea, "query": query})

        return {
            "agent": self.specialty,
            "query": query,
            "status": "success",
            "findings": [response.content],
            "summary": "Tools research completed"
        }

    async def _research_compliance(self, query: str, idea: str) -> Dict:
        """Research compliance, legal, and privacy requirements."""
        prompt = ChatPromptTemplate.from_template("""
You are a compliance and legal specialist. Identify potential legal and privacy concerns.

Idea: {idea}
Research Focus: {query}

Provide a JSON response with:
{{
  "privacy_concerns": ["data privacy issues"],
  "legal_requirements": ["applicable laws/regulations"],
  "compliance_standards": ["GDPR, HIPAA, etc."],
  "data_handling": ["best practices for data"],
  "risks": ["potential legal risks"],
  "mitigations": ["how to address concerns"],
  "assessment": "Overall risk level: low/medium/high"
}}
""")

        chain = prompt | self.llm
        response = await chain.ainvoke({"idea": idea, "query": query})

        return {
            "agent": self.specialty,
            "query": query,
            "status": "success",
            "findings": [response.content],
            "summary": "Compliance research completed"
        }

    async def _general_research(self, query: str, idea: str) -> Dict:
        """Conduct general research."""
        prompt = ChatPromptTemplate.from_template("""
Research the following topic in depth:

Idea: {idea}
Research Focus: {query}

Provide comprehensive information including:
- Key concepts and technologies
- Current state of the art
- Common approaches and solutions
- Potential challenges
- Recommendations

Format as detailed text.
""")

        chain = prompt | self.llm
        response = await chain.ainvoke({"idea": idea, "query": query})

        return {
            "agent": self.specialty,
            "query": query,
            "status": "success",
            "findings": [response.content],
            "summary": "General research completed"
        }


class ResearchSwarm:
    """Orchestrates multiple research agents in parallel."""

    def __init__(self):
        self.agents = {
            "api": ResearchAgent("api"),
            "code": ResearchAgent("code"),
            "tools": ResearchAgent("tools"),
            "compliance": ResearchAgent("compliance")
        }

    async def research(self, idea: str, areas: List[str]) -> List[Dict]:
        """Conduct parallel research across multiple domains."""
        if not areas:
            areas = ["general research"]

        logger.info(f"Starting research swarm for {len(areas)} areas")

        tasks = []
        for area in areas:
            for agent_name, agent in self.agents.items():
                tasks.append(agent.research(area, idea))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Research task failed: {result}")
                processed_results.append({
                    "status": "error",
                    "error": str(result)
                })
            else:
                processed_results.append(result)

        logger.info(f"Research swarm completed: {len(processed_results)} results")
        return processed_results

    async def synthesize_findings(self, research_results: List[Dict]) -> Dict:
        """Synthesize research findings into actionable insights."""
        llm = ChatOpenAI(
            temperature=0.2,
            model=settings.default_model,
            api_key=settings.openai_api_key
        )

        successful_results = [r for r in research_results if r.get("status") == "success"]

        if not successful_results:
            return {
                "synthesis": "No successful research results to synthesize",
                "feasible": False,
                "confidence": 0.0,
                "blockers": ["Research failed"],
                "recommendations": []
            }

        findings_text = "\n\n".join([
            f"### {r['agent'].upper()} Agent\n{r.get('summary', '')}\n{r.get('findings', [''])[0]}"
            for r in successful_results
        ])

        prompt = ChatPromptTemplate.from_template("""
Synthesize the following research findings into actionable implementation guidance.

Research Findings:
{findings}

Provide a JSON response with:
{{
  "synthesis": "Overall summary of findings",
  "feasible": boolean,
  "confidence": 0.0-1.0,
  "blockers": ["identified blockers"],
  "recommendations": [
    "specific actionable recommendations"
  ],
  "technical_approach": "Recommended technical approach",
  "estimated_complexity": "simple" | "medium" | "complex",
  "key_decisions": [
    {{
      "decision": "What to decide",
      "options": ["option1", "option2"],
      "recommendation": "Recommended option"
    }}
  ]
}}
""")

        try:
            chain = prompt | llm
            response = await chain.ainvoke({"findings": findings_text})

            import json
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            synthesis = json.loads(content.strip())
            logger.info("Research synthesis completed")
            return synthesis

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {
                "synthesis": "Synthesis failed, but research data is available",
                "feasible": True,
                "confidence": 0.5,
                "blockers": [],
                "recommendations": ["Review research findings manually"]
            }
