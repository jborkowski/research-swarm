from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Literal
import asyncio
import logging
from datetime import datetime

from agents.planner import PlannerAgent
from agents.researcher import ResearchSwarm
from agents.builder import BuilderAgent
from agents.tester import TesterAgent
from utils.repository import RepositoryManager
from config.settings import settings

logger = logging.getLogger(__name__)


class IdeaState(TypedDict):
    """State object that flows through the workflow."""
    idea_id: str
    idea_text: str
    context: Optional[str]
    complexity: Literal["simple", "medium", "complex"]
    needs_research: bool
    research_results: Optional[List[dict]]
    synthesis: Optional[dict]
    implementation_plan: Optional[dict]
    code_artifacts: Optional[List[dict]]
    test_results: Optional[dict]
    iteration_count: int
    final_output: Optional[dict]
    errors: List[str]
    phase: str
    started_at: str


class ResearchWorkflow:
    """Main orchestrator for the research automation workflow."""

    def __init__(self, repo_manager: RepositoryManager):
        self.repo_manager = repo_manager
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()

    def _build_workflow(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(IdeaState)

        workflow.add_node("plan", self.plan_idea)
        workflow.add_node("research", self.research_idea)
        workflow.add_node("synthesize", self.synthesize_research)
        workflow.add_node("decompose", self.decompose_tasks)
        workflow.add_node("build", self.build_implementation)
        workflow.add_node("test", self.test_implementation)
        workflow.add_node("report", self.generate_report)

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

        workflow.set_entry_point("plan")

        return workflow

    async def plan_idea(self, state: IdeaState) -> IdeaState:
        """Phase 1: Zero-shot planning."""
        logger.info(f"[{state['idea_id']}] Starting planning phase")
        state["phase"] = "planning"

        try:
            planner = PlannerAgent()
            result = await planner.analyze(state["idea_text"], state.get("context"))

            state["complexity"] = result["complexity"]
            state["needs_research"] = result["needs_research"]
            state["implementation_plan"] = result["initial_plan"]

            logger.info(
                f"[{state['idea_id']}] Planning complete - "
                f"Complexity: {result['complexity']}, "
                f"Research needed: {result['needs_research']}"
            )

            idea_path = self.repo_manager.create_idea_folder(
                state["idea_id"],
                state["idea_text"]
            )
            self.repo_manager.save_plan(idea_path, result)

        except Exception as e:
            logger.error(f"[{state['idea_id']}] Planning failed: {e}")
            state["errors"].append(f"Planning error: {str(e)}")
            state["needs_research"] = True
            state["complexity"] = "medium"

        return state

    async def research_idea(self, state: IdeaState) -> IdeaState:
        """Phase 2: Research swarm."""
        logger.info(f"[{state['idea_id']}] Starting research phase")
        state["phase"] = "researching"

        try:
            swarm = ResearchSwarm()
            research_areas = state["implementation_plan"].get("research_areas", [])

            results = await swarm.research(
                idea=state["idea_text"],
                areas=research_areas
            )

            state["research_results"] = results

            logger.info(f"[{state['idea_id']}] Research complete - {len(results)} results")

        except Exception as e:
            logger.error(f"[{state['idea_id']}] Research failed: {e}")
            state["errors"].append(f"Research error: {str(e)}")
            state["research_results"] = []

        return state

    async def synthesize_research(self, state: IdeaState) -> IdeaState:
        """Phase 3: Knowledge synthesis."""
        logger.info(f"[{state['idea_id']}] Synthesizing research findings")
        state["phase"] = "synthesizing"

        try:
            swarm = ResearchSwarm()
            synthesis = await swarm.synthesize_findings(state["research_results"])

            state["synthesis"] = synthesis

            idea_path = self._get_idea_path(state["idea_id"])
            if idea_path:
                self.repo_manager.save_research(idea_path, {
                    "results": state["research_results"],
                    "synthesis": synthesis
                })

            logger.info(
                f"[{state['idea_id']}] Synthesis complete - "
                f"Feasible: {synthesis.get('feasible')}, "
                f"Confidence: {synthesis.get('confidence', 0):.2f}"
            )

        except Exception as e:
            logger.error(f"[{state['idea_id']}] Synthesis failed: {e}")
            state["errors"].append(f"Synthesis error: {str(e)}")
            state["synthesis"] = {
                "feasible": True,
                "confidence": 0.5,
                "blockers": [],
                "recommendations": []
            }

        return state

    async def decompose_tasks(self, state: IdeaState) -> IdeaState:
        """Phase 3.5: Task decomposition."""
        logger.info(f"[{state['idea_id']}] Decomposing into tasks")
        state["phase"] = "decomposing"

        try:
            plan = state["implementation_plan"]
            synthesis = state.get("synthesis", {})

            plan["feasible"] = synthesis.get("feasible", True)
            plan["synthesis"] = synthesis

            state["implementation_plan"] = plan

            logger.info(
                f"[{state['idea_id']}] Task decomposition complete - "
                f"Feasible: {plan.get('feasible')}"
            )

        except Exception as e:
            logger.error(f"[{state['idea_id']}] Decomposition failed: {e}")
            state["errors"].append(f"Decomposition error: {str(e)}")

        return state

    async def build_implementation(self, state: IdeaState) -> IdeaState:
        """Phase 4: TDD implementation."""
        state["iteration_count"] += 1
        logger.info(
            f"[{state['idea_id']}] Building implementation "
            f"(iteration {state['iteration_count']})"
        )
        state["phase"] = f"building (iteration {state['iteration_count']})"

        try:
            builder = BuilderAgent()

            result = await builder.build(
                plan=state["implementation_plan"],
                iteration=state["iteration_count"]
            )

            if result["status"] == "success":
                state["code_artifacts"] = result["artifacts"]

                idea_path = self._get_idea_path(state["idea_id"])
                if idea_path:
                    self.repo_manager.save_implementation(
                        idea_path,
                        result["artifacts"]
                    )

                logger.info(f"[{state['idea_id']}] Build successful")
            else:
                state["errors"].append(result.get("error", "Build failed"))
                logger.warning(
                    f"[{state['idea_id']}] Build failed: {result.get('error')}"
                )

        except Exception as e:
            logger.error(f"[{state['idea_id']}] Build exception: {e}")
            state["errors"].append(f"Build error: {str(e)}")

        return state

    async def test_implementation(self, state: IdeaState) -> IdeaState:
        """Phase 5: Testing & validation."""
        logger.info(f"[{state['idea_id']}] Testing implementation")
        state["phase"] = "testing"

        try:
            tester = TesterAgent()

            test_results = await tester.test(
                artifacts=state["code_artifacts"],
                requirements=state["implementation_plan"].get("requirements", {})
            )

            state["test_results"] = test_results

            idea_path = self._get_idea_path(state["idea_id"])
            if idea_path:
                self.repo_manager.save_test_results(idea_path, test_results)

            logger.info(
                f"[{state['idea_id']}] Testing complete - "
                f"Passed: {test_results.get('passed')}"
            )

        except Exception as e:
            logger.error(f"[{state['idea_id']}] Testing failed: {e}")
            state["errors"].append(f"Testing error: {str(e)}")
            state["test_results"] = {
                "passed": False,
                "error": str(e)
            }

        return state

    async def generate_report(self, state: IdeaState) -> IdeaState:
        """Phase 6: Generate final report."""
        logger.info(f"[{state['idea_id']}] Generating final report")
        state["phase"] = "reporting"

        try:
            completed_at = datetime.utcnow().isoformat()

            summary = {
                "idea_id": state["idea_id"],
                "idea_text": state["idea_text"],
                "started_at": state["started_at"],
                "completed_at": completed_at,
                "status": "completed" if not state["errors"] else "completed_with_errors",
                "complexity": state["complexity"],
                "research_conducted": state["needs_research"],
                "implementation_generated": state["code_artifacts"] is not None,
                "tests_passed": state.get("test_results", {}).get("passed", False),
                "errors": state["errors"],
                "outcomes": {
                    "feasibility": state.get("synthesis", {}).get("feasible", "Unknown"),
                    "confidence": state.get("synthesis", {}).get("confidence", 0),
                    "test_coverage": state.get("test_results", {}).get("coverage", {}).get("percentage", 0)
                },
                "message": self._generate_summary_message(state)
            }

            state["final_output"] = summary

            idea_path = self._get_idea_path(state["idea_id"])
            if idea_path:
                self.repo_manager.finalize_idea(idea_path, summary)

            logger.info(f"[{state['idea_id']}] Report generated - Status: {summary['status']}")

        except Exception as e:
            logger.error(f"[{state['idea_id']}] Report generation failed: {e}")
            state["errors"].append(f"Report error: {str(e)}")

        return state

    def should_research(self, state: IdeaState) -> bool:
        """Determine if research is needed."""
        return state.get("needs_research", True)

    def is_feasible(self, state: IdeaState) -> bool:
        """Determine if implementation should proceed."""
        return state.get("implementation_plan", {}).get("feasible", False)

    def check_build_status(self, state: IdeaState) -> str:
        """Check build status and determine next step."""
        if state.get("code_artifacts"):
            return "success"
        elif state["iteration_count"] < settings.max_iterations:
            return "retry"
        else:
            return "fail"

    async def process_idea(self, idea_text: str, idea_id: str, context: str = None) -> dict:
        """Process an idea through the complete workflow."""
        logger.info(f"Starting workflow for idea {idea_id}")

        initial_state = {
            "idea_id": idea_id,
            "idea_text": idea_text,
            "context": context,
            "complexity": "unknown",
            "needs_research": False,
            "research_results": None,
            "synthesis": None,
            "implementation_plan": None,
            "code_artifacts": None,
            "test_results": None,
            "iteration_count": 0,
            "final_output": None,
            "errors": [],
            "phase": "initializing",
            "started_at": datetime.utcnow().isoformat()
        }

        try:
            final_state = await self.app.ainvoke(initial_state)
            logger.info(f"Workflow completed for idea {idea_id}")
            return final_state.get("final_output", {})
        except Exception as e:
            logger.error(f"Workflow failed for idea {idea_id}: {e}")
            return {
                "idea_id": idea_id,
                "status": "failed",
                "error": str(e),
                "message": f"Workflow execution failed: {str(e)}"
            }

    def _get_idea_path(self, idea_id: str):
        """Get the path to an idea's folder."""
        ideas_dir = self.repo_manager.repo_path / "ideas"
        if not ideas_dir.exists():
            return None

        for folder in ideas_dir.iterdir():
            if folder.is_dir():
                metadata_file = folder / "metadata.json"
                if metadata_file.exists():
                    import json
                    metadata = json.loads(metadata_file.read_text())
                    if metadata.get("idea_id") == idea_id:
                        return folder

        return None

    def _generate_summary_message(self, state: IdeaState) -> str:
        """Generate a human-readable summary message."""
        messages = []

        if state.get("code_artifacts"):
            messages.append(f"✓ Implementation generated with {len(state['code_artifacts'])} files")

        if state.get("test_results", {}).get("passed"):
            coverage = state["test_results"].get("coverage", {}).get("percentage", 0)
            messages.append(f"✓ Tests passed with {coverage}% coverage")
        elif state.get("test_results"):
            messages.append("✗ Tests failed")

        if state.get("errors"):
            messages.append(f"⚠ {len(state['errors'])} errors encountered")

        if not messages:
            messages.append("Research and analysis completed")

        return " | ".join(messages)
