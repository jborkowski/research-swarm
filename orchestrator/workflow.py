from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Literal
import asyncio
import json
from datetime import datetime

# Import settings
try:
    from config.settings import settings
except Exception as e:
    print(f"Warning: Could not load settings: {e}")
    settings = None

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
        # Simulate planning - in real implementation, this would use LLM
        print(f"Planning idea: {state['idea_text']}")
        
        # Simple heuristic for complexity
        word_count = len(state['idea_text'].split())
        if word_count < 10:
            complexity = "simple"
            needs_research = False
        elif word_count < 30:
            complexity = "medium"
            needs_research = True
        else:
            complexity = "complex"
            needs_research = True
        
        state["complexity"] = complexity
        state["needs_research"] = needs_research
        state["implementation_plan"] = {
            "complexity": complexity,
            "needs_research": needs_research,
            "research_areas": ["general research"] if needs_research else [],
            "initial_plan": f"Plan for {state['idea_text']}",
            "estimated_effort": 30,
            "feasibility_score": 0.8 if complexity != "complex" else 0.6
        }
        
        return state
    
    async def research_idea(self, state: IdeaState) -> IdeaState:
        # Simulate research - in real implementation, this would use research agents
        print(f"Researching idea: {state['idea_text']}")
        
        state["research_results"] = [
            {
                "agent": "api",
                "query": state["idea_text"],
                "findings": [f"Research findings for {state['idea_text']}"]
            }
        ]
        return state
    
    async def synthesize_research(self, state: IdeaState) -> IdeaState:
        # Synthesize research findings
        print("Synthesizing research")
        synthesis = {
            "overview": "Research synthesis",
            "findings": state["research_results"],
            "technical_analysis": "Technical analysis based on research",
            "recommendations": "Implementation recommendations",
            "next_steps": "Next steps for implementation"
        }
        state["implementation_plan"]["synthesis"] = synthesis
        return state
    
    async def decompose_tasks(self, state: IdeaState) -> IdeaState:
        # Decompose into atomic tasks
        print("Decomposing tasks")
        tasks = [
            {"id": "task_1", "description": "Set up project structure", "priority": 1, "dependencies": []},
            {"id": "task_2", "description": "Implement core functionality", "priority": 2, "dependencies": ["task_1"]},
            {"id": "task_3", "description": "Add tests", "priority": 3, "dependencies": ["task_2"]}
        ]
        state["implementation_plan"]["tasks"] = tasks
        state["implementation_plan"]["feasible"] = True
        return state
    
    async def build_implementation(self, state: IdeaState) -> IdeaState:
        # Simulate building implementation
        print(f"Building implementation (iteration {state['iteration_count'] + 1})")
        
        state["iteration_count"] += 1
        
        # Simple code generation
        code_artifacts = [
            {"name": "main.py", "content": f"# Generated code for: {state['idea_text']}\nprint('Hello from Research Swarm!')"},
            {"name": "test_main.py", "content": f"# Test for: {state['idea_text']}\nimport unittest\n\nclass TestMain(unittest.TestCase):\n    def test_example(self):\n        self.assertTrue(True)"}
        ]
        
        state["code_artifacts"] = code_artifacts
        
        return state
    
    async def test_implementation(self, state: IdeaState) -> IdeaState:
        # Simulate testing
        print("Testing implementation")
        
        test_results = {
            "unit_tests": {"status": "completed", "passed": True, "output": "All tests passed"},
            "coverage": {"percentage": 85, "meets_threshold": True},
            "e2e_tests": {"passed": True, "output": "E2E tests passed"},
            "passed": True
        }
        
        state["test_results"] = test_results
        return state
    
    async def generate_report(self, state: IdeaState) -> IdeaState:
        # Generate final report
        print("Generating report")
        
        report = {
            "idea_id": state["idea_id"],
            "idea_text": state["idea_text"],
            "complexity": state["complexity"],
            "status": "completed",
            "completion_time": datetime.utcnow().isoformat(),
            "artifacts": state.get("code_artifacts", []),
            "test_results": state.get("test_results", {}),
            "summary": f"Successfully processed idea: {state['idea_text']}"
        }
        
        state["final_output"] = report
        return state
    
    def should_research(self, state: IdeaState) -> bool:
        return state["needs_research"]
    
    def is_feasible(self, state: IdeaState) -> bool:
        return state["implementation_plan"].get("feasible", False)
    
    def check_build_status(self, state: IdeaState) -> str:
        if state["code_artifacts"]:
            return "success"
        elif state["iteration_count"] < (settings.max_iterations if settings else 10):
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