from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Literal
import asyncio
from agents.planner import PlannerAgent
from agents.researcher import ResearchSwarm
from agents.builder import BuilderAgent
from agents.tester import TesterAgent
from config.settings import settings

class IdeaState(TypedDict):
    idea_id: str
    idea_text: str
    complexity: Literal["simple", "medium", "complex"]
    needs_research: bool
    research_results: Optional[List[dict]]
    implementation_plan: Optional[dict]
    code_artifacts: Optional[List[str]]
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
                False: "decompose"
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
        synthesis = await self._synthesize_findings(state["research_results"])
        state["implementation_plan"]["synthesis"] = synthesis
        return state
    
    async def decompose_tasks(self, state: IdeaState) -> IdeaState:
        # Decompose into atomic tasks
        tasks = await self._decompose_plan(state["implementation_plan"])
        state["implementation_plan"]["tasks"] = tasks
        return state
    
    async def build_implementation(self, state: IdeaState) -> IdeaState:
        builder = BuilderAgent()
        
        state["iteration_count"] += 1
        
        result = await builder.build(
            plan=state["implementation_plan"],
            iteration=state["iteration_count"]
        )
        
        if result["status"] == "success":
            state["code_artifacts"] = result["artifacts"]
        else:
            state["errors"].append(result["error"])
        
        return state
    
    async def test_implementation(self, state: IdeaState) -> IdeaState:
        tester = TesterAgent()
        
        requirements = state["implementation_plan"].get("requirements", {})
        test_results = await tester.test(
            artifacts=state["code_artifacts"],
            requirements=requirements
        )
        
        state["test_results"] = test_results
        return state
    
    async def generate_report(self, state: IdeaState) -> IdeaState:
        # Generate final report
        report = await self._create_report(state)
        state["final_output"] = report
        return state
    
    async def _synthesize_findings(self, research_results: List[dict]) -> dict:
        # Placeholder for synthesis logic
        return {"summary": "Synthesized findings from research", "results": research_results}
    
    async def _decompose_plan(self, implementation_plan: dict) -> List[dict]:
        # Placeholder for decomposition logic
        return [{"id": "task_1", "description": "Implement basic functionality", "priority": 1}]
    
    async def _create_report(self, state: IdeaState) -> dict:
        # Create final report
        return {
            "idea_id": state["idea_id"],
            "summary": "Research and implementation completed",
            "research_results": state["research_results"],
            "implementation": state["code_artifacts"],
            "test_results": state["test_results"],
            "errors": state["errors"]
        }
    
    def should_research(self, state: IdeaState) -> bool:
        return state["needs_research"]
    
    def is_feasible(self, state: IdeaState) -> bool:
        return state["implementation_plan"].get("feasible", False)
    
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
        
        final_state = await self.app.ainvoke(initial_state)
        return final_state["final_output"]