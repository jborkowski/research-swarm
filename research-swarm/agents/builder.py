import os
import subprocess
from typing import Dict, List
from pathlib import Path
import black
import autopep8

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class BuilderAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.2, model="gpt-4")
        self.supported_languages = ["python", "javascript", "typescript", "swift"]
    
    async def build(self, plan: Dict, iteration: int) -> Dict:
        try:
            # Select optimal tool/framework
            tool = self._select_tool(plan)
            
            # Generate code following TDD
            code_files = await self._generate_code(plan, tool, iteration)
            
            # Format code
            formatted_files = self._format_code(code_files)
            
            # Basic validation
            if self._validate_code(formatted_files):
                return {
                    "status": "success",
                    "artifacts": formatted_files,
                    "tool": tool
                }
            else:
                return {
                    "status": "retry",
                    "error": "Code validation failed"
                }
        except Exception as e:
            return {
                "status": "fail" if iteration >= 10 else "retry",
                "error": str(e)
            }
    
    def _select_tool(self, plan: Dict) -> str:
        """Select easiest tool for the job"""
        requirements = plan.get("requirements", {})
        
        if requirements.get("type") == "web_app":
            return "streamlit"  # Easiest for quick prototypes
        elif requirements.get("type") == "api":
            return "fastapi"
        elif requirements.get("type") == "mobile":
            return "pwa"  # Progressive Web App
        elif requirements.get("type") == "extension":
            return "manifest_v3"
        else:
            return "python"  # Default
    
    async def _generate_code(self, plan: Dict, tool: str, iteration: int) -> List[Dict]:
        # First, generate test
        test_prompt = f"""
        Generate a test file for the following plan:
        {plan}
        
        Use {tool} and follow TDD principles.
        This is iteration {iteration}, so focus on core functionality.
        """
        
        test_chain = ChatPromptTemplate.from_template(test_prompt) | self.llm
        test_response = await test_chain.ainvoke({})
        
        # Then, generate implementation
        impl_prompt = f"""
        Generate implementation to pass this test:
        {test_response.content}
        
        Use {tool} and keep it simple.
        """
        
        impl_chain = ChatPromptTemplate.from_template(impl_prompt) | self.llm
        impl_response = await impl_chain.ainvoke({})
        
        return [
            {"name": "test_main.py", "content": test_response.content},
            {"name": "main.py", "content": impl_response.content}
        ]
    
    def _format_code(self, files: List[Dict]) -> List[Dict]:
        """Format code based on language"""
        formatted = []
        for file in files:
            content = file["content"]
            if file["name"].endswith(".py"):
                try:
                    content = black.format_str(content, mode=black.Mode())
                except Exception:
                    try:
                        content = autopep8.fix_code(content)
                    except Exception:
                        pass  # If both fail, keep original content
            
            formatted.append({
                "name": file["name"],
                "content": content
            })
        
        return formatted
    
    def _validate_code(self, files: List[Dict]) -> bool:
        """Basic syntax validation"""
        for file in files:
            if file["name"].endswith(".py"):
                try:
                    compile(file["content"], file["name"], "exec")
                except SyntaxError:
                    return False
        return True