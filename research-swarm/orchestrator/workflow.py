from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Literal, Dict
import asyncio
from agents.planner import PlannerAgent
from agents.researcher import ResearchSwarm
from agents.builder import BuilderAgent
from agents.tester import TesterAgent
from config.settings import settings
from utils.notifications import notification_manager

class IdeaState(TypedDict):
    idea_id: str
    idea_text: str
    complexity: Literal["simple", "medium", "complex"]
    needs_research: bool
    research_results: Optional[List[dict]]
    implementation_plan: Optional[dict]
    code_artifacts: Optional[List[Dict]]
    test_results: Optional[dict]
    iteration_count: int
    final_output: Optional[dict]
    errors: List[str]

class ResearchWorkflow:
    def __init__(self):
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self):
        workflow = StateGraph(IdeaState)
        
        # Add nodes
        workflow.add_node("plan", self.plan_idea)
        workflow.add_node("research", self.research_idea)
        workflow.add_node("synthesize", self.synthesize_research)
        workflow.add_node("decompose", self.decompose_tasks)
        workflow.add_node("build", self.build_implementation)
        workflow.add_node("test", self.test_implementation)
        workflow.add_node("report", self.generate_report)
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "plan",
            self.should_research,
            {
                True: "research",
                False: "synthesize"
            }
        )

        workflow.add_edge("research", "synthesize")
        workflow.add_edge("synthesize", "decompose")
        
        workflow.add_conditional_edges(
            "decompose",
            self.is_feasible,
            {
                True: "build",
                False: "report"
            }
        )
        
        workflow.add_conditional_edges(
            "build",
            self.check_build_status,
            {
                "success": "test",
                "retry": "build",
                "fail": "report"
            }
        )
        
        workflow.add_edge("test", "report")
        workflow.add_edge("report", END)
        
        # Set entry point
        workflow.set_entry_point("plan")
        
        return workflow
    
    async def plan_idea(self, state: IdeaState) -> IdeaState:
        planner = PlannerAgent()
        result = await planner.analyze(state["idea_text"])
        
        state["complexity"] = result["complexity"]
        state["needs_research"] = result["needs_research"]
        state["implementation_plan"] = result["initial_plan"]
        
        return state
    
    async def research_idea(self, state: IdeaState) -> IdeaState:
        swarm = ResearchSwarm()
        research_results = await swarm.research(
            idea=state["idea_text"],
            areas=state["implementation_plan"].get("research_areas", [])
        )

        state["research_results"] = research_results
        return state
    
    async def synthesize_research(self, state: IdeaState) -> IdeaState:
        # Synthesize research findings
        if state["research_results"] is None:
            state["research_results"] = []

        # If no research was conducted, assume feasibility based on complexity
        if not state["research_results"]:
            complexity = state.get("complexity", "medium")
            if complexity == "simple":
                synthesis = {
                    "feasible": True,
                    "confidence": 0.9,
                    "blockers": [],
                    "recommendations": ["Simple implementation should be feasible"],
                    "estimated_effort": "1-2 hours",
                    "api_available": False,
                    "code_examples": True,
                    "research_available": False,
                    "tools_available": True
                }
            else:
                synthesis = await self._synthesize_findings(state["research_results"])
        else:
            synthesis = await self._synthesize_findings(state["research_results"])

        if state["implementation_plan"] is None:
            state["implementation_plan"] = {}
        state["implementation_plan"]["synthesis"] = synthesis
        return state
    
    async def decompose_tasks(self, state: IdeaState) -> IdeaState:
        # Decompose into atomic tasks
        if state["implementation_plan"] is None:
            state["implementation_plan"] = {}
        tasks = await self._decompose_plan(state["implementation_plan"])
        state["implementation_plan"]["tasks"] = tasks
        return state
    
    async def build_implementation(self, state: IdeaState) -> IdeaState:
        builder = BuilderAgent()

        state["iteration_count"] += 1

        plan = state["implementation_plan"] or {}
        result = await builder.build(
            plan=plan,
            iteration=state["iteration_count"]
        )

        if result["status"] == "success":
            state["code_artifacts"] = result["artifacts"]
        else:
            state["errors"].append(result["error"])

        return state
    
    async def test_implementation(self, state: IdeaState) -> IdeaState:
        tester = TesterAgent()

        plan = state["implementation_plan"] or {}
        requirements = plan.get("requirements", {})
        artifacts = state["code_artifacts"] or []

        test_results = await tester.test(
            artifacts=artifacts,
            requirements=requirements
        )

        state["test_results"] = test_results
        return state
    
    async def generate_report(self, state: IdeaState) -> IdeaState:
        # Generate final report
        report = await self._create_report(state)
        state["final_output"] = report

        # Send completion notification
        try:
            await notification_manager.send_completion_notification(state["idea_id"], report)
        except Exception as e:
            # Don't fail the workflow if notification fails
            print(f"Failed to send notification: {e}")

        return state
    
    async def _synthesize_findings(self, research_results: Optional[List[dict]]) -> dict:
        """Synthesize research findings into actionable insights"""
        if not research_results:
            return {
                "feasible": False,
                "confidence": 0.0,
                "blockers": ["No research results available"],
                "recommendations": ["Conduct additional research"],
                "estimated_effort": "Unknown"
            }

        # Analyze findings across all agents
        api_findings = []
        code_findings = []
        paper_findings = []
        tool_findings = []

        for result in research_results or []:
            agent_type = result.get("agent", "")
            findings = result.get("findings", [])

            if agent_type == "api":
                api_findings.extend(findings)
            elif agent_type == "code":
                code_findings.extend(findings)
            elif agent_type == "papers":
                paper_findings.extend(findings)
            elif agent_type == "tools":
                tool_findings.extend(findings)

        # Determine feasibility based on findings
        blockers = []
        recommendations = []

        # Check API availability
        api_available = any("API" in str(f.get("content", "")) for f in api_findings)
        if not api_available:
            blockers.append("No suitable APIs found")
        else:
            recommendations.append("APIs available for integration")

        # Check code examples
        code_available = any("code" in str(f.get("content", "")).lower() for f in code_findings)
        if code_available:
            recommendations.append("Similar implementations found")

        # Check academic research
        research_available = len(paper_findings) > 0
        if research_available:
            recommendations.append("Academic research available")

        # Check tools/frameworks
        tools_available = len(tool_findings) > 0
        if not tools_available:
            blockers.append("No suitable tools/frameworks identified")

        # Calculate feasibility score
        feasibility_score = 0.0
        if api_available: feasibility_score += 0.3
        if code_available: feasibility_score += 0.2
        if research_available: feasibility_score += 0.2
        if tools_available: feasibility_score += 0.3

        # Determine overall feasibility
        feasible = feasibility_score >= 0.5 and len(blockers) == 0

        return {
            "feasible": feasible,
            "confidence": feasibility_score,
            "blockers": blockers,
            "recommendations": recommendations,
            "estimated_effort": self._estimate_effort(feasibility_score),
            "api_available": api_available,
            "code_examples": code_available,
            "research_available": research_available,
            "tools_available": tools_available
        }

    def _estimate_effort(self, feasibility_score: float) -> str:
        """Estimate development effort based on feasibility score"""
        if feasibility_score >= 0.8:
            return "1-2 hours"
        elif feasibility_score >= 0.6:
            return "2-4 hours"
        elif feasibility_score >= 0.4:
            return "4-8 hours"
        else:
            return "8+ hours or not feasible"
    
    async def _decompose_plan(self, implementation_plan: Optional[dict]) -> List[dict]:
        """Decompose implementation plan into atomic tasks"""
        if not implementation_plan:
            return [{"id": "task_1", "description": "Implement basic functionality", "priority": 1}]

        tasks = []
        synthesis = implementation_plan.get("synthesis", {})

        # Create tasks based on synthesis findings
        if synthesis.get("api_available"):
            tasks.append({
                "id": "api_integration",
                "description": "Integrate with identified APIs",
                "priority": 2,
                "estimated_time": "30min"
            })

        if synthesis.get("code_examples"):
            tasks.append({
                "id": "code_implementation",
                "description": "Implement core functionality using reference examples",
                "priority": 1,
                "estimated_time": "45min"
            })

        if synthesis.get("tools_available"):
            tasks.append({
                "id": "tool_setup",
                "description": "Set up development tools and frameworks",
                "priority": 1,
                "estimated_time": "15min"
            })

        # Always include testing task
        tasks.append({
            "id": "testing",
            "description": "Write and run tests",
            "priority": 3,
            "estimated_time": "20min"
        })

        return tasks
    
    async def _create_report(self, state: IdeaState) -> dict:
        """Create final report from completed workflow"""
        success = (
            state["code_artifacts"] is not None and
            state["test_results"] is not None and
            state["test_results"].get("passed", False)
        )

        return {
            "idea_id": state["idea_id"],
            "status": "completed" if success else "failed",
            "summary": "Research and implementation completed successfully" if success else "Implementation failed or incomplete",
            "research_results": state["research_results"],
            "implementation": state["code_artifacts"],
            "test_results": state["test_results"],
            "errors": state["errors"],
            "iterations_used": state["iteration_count"]
        }
    
    def should_research(self, state: IdeaState) -> bool:
        return state["needs_research"]
    
    def is_feasible(self, state: IdeaState) -> bool:
        synthesis = state["implementation_plan"].get("synthesis", {})
        return synthesis.get("feasible", False)
    
    def check_build_status(self, state: IdeaState) -> str:
        if state["code_artifacts"]:
            return "success"
        elif state["iteration_count"] < settings.max_iterations:
            return "retry"
        else:
            return "fail"
    
    async def process_idea(self, idea_text: str, idea_id: str) -> dict:
        initial_state = {
            "idea_id": idea_id,
            "idea_text": idea_text,
            "complexity": "unknown",
            "needs_research": False,
            "research_results": None,
            "implementation_plan": None,
            "code_artifacts": None,
            "test_results": None,
            "iteration_count": 0,
            "final_output": None,
            "errors": []
        }

        try:
            final_state = await self.app.ainvoke(initial_state)
            return final_state["final_output"]
        except Exception as e:
            error_msg = f"Workflow failed for idea {idea_id}: {str(e)}"
            print(error_msg)

            # Send error notification
            try:
                await notification_manager.send_error_notification(idea_id, error_msg)
            except Exception as notify_error:
                print(f"Failed to send error notification: {notify_error}")

            # Return error report
            return {
                "idea_id": idea_id,
                "status": "error",
                "summary": "Workflow execution failed",
                "errors": [error_msg],
                "iterations_used": initial_state["iteration_count"]
            }