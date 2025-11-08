"""
Code Agent with ReAct Pattern

Implements Reason → Act → Observe loop for complex task execution.
Uses tools: codebase search, code execution, web search.

Version: 1.0.0
"""

import json
import logging
import subprocess
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed, web_search will be disabled")


class CodeAgent:
    """
    ReAct agent for code-related tasks.
    
    Implements:
    - Reasoning about task
    - Action selection (tools)
    - Observation of results
    - Iterative refinement
    
    Tools:
    - search_codebase: Search in knowledge base via RAG
    - execute_code: Execute Python in sandbox
    - web_search: Search web for information (requires Tavily API)
    
    Example:
        >>> agent = CodeAgent(llm, rag)
        >>> result = agent.run("Create a Python script to fetch HackerNews top stories")
        >>> print(result)
    """
    
    def __init__(self, llm, rag, enable_sandbox: bool = False, tavily_api_key: Optional[str] = None):
        """
        Initialize CodeAgent.
        
        Args:
            llm: Language model (llama-cpp Llama instance)
            rag: RAG system (KnowledgeRAG instance)
            enable_sandbox: Enable code execution sandbox (requires firejail/docker)
            tavily_api_key: API key for Tavily web search
        """
        self.llm = llm
        self.rag = rag
        self.enable_sandbox = enable_sandbox
        self.tavily_api_key = tavily_api_key
        
        # Register tools
        self.tools: Dict[str, Callable] = {
            "search_codebase": self._search_codebase,
        }
        
        if enable_sandbox:
            self.tools["execute_code"] = self._execute_sandbox
            logger.info("Code execution sandbox enabled")
        
        if tavily_api_key and REQUESTS_AVAILABLE:
            self.tools["web_search"] = self._web_search
            logger.info("Web search enabled")
        
        logger.info(f"CodeAgent initialized with {len(self.tools)} tools: {list(self.tools.keys())}")
    
    def _search_codebase(self, query: str) -> Dict[str, Any]:
        """Search in codebase via RAG."""
        try:
            results = self.rag.retrieve(query, top_k=3)
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Codebase search error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_sandbox(self, code: str) -> Dict[str, Any]:
        """
        Execute Python code in sandbox.
        
        Uses firejail for isolation. Requires firejail installed:
        sudo apt install firejail
        
        Args:
            code: Python code to execute
        
        Returns:
            Dict with stdout, stderr, returncode
        """
        try:
            result = subprocess.run(
                ["firejail", "--quiet", "python3", "-c", code],
                capture_output=True,
                timeout=5,
                text=True
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except FileNotFoundError:
            logger.error("firejail not found, cannot execute code")
            return {
                "success": False,
                "error": "firejail not installed"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timeout"
            }
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _web_search(self, query: str) -> str:
        """
        Search web using Tavily API.
        
        Tavily is better for code/technical content than Google.
        Get API key: https://tavily.com/
        
        Args:
            query: Search query
        
        Returns:
            Search results or error message
        """
        if not REQUESTS_AVAILABLE:
            return "Error: requests library not installed"
        
        if not self.tavily_api_key:
            return "Error: Tavily API key not configured"
        
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "query": query,
                    "api_key": self.tavily_api_key,
                    "search_depth": "basic"
                },
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                if "results" in data and data["results"]:
                    return data["results"][0]["content"]
                return "No results found"
            else:
                return f"Error: API returned {response.status_code}"
        
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"Error: {str(e)}"
    
    def run(self, task: str, max_steps: int = 5) -> str:
        """
        Execute task using ReAct pattern.
        
        Loop:
        1. Generate thought about task
        2. Decide action (tool to use)
        3. Execute action
        4. Observe result
        5. Repeat or return final answer
        
        Args:
            task: Task description
            max_steps: Maximum reasoning steps
        
        Returns:
            Final answer/result
        """
        logger.info(f"Starting ReAct loop for task: {task[:60]}...")
        
        # Build initial prompt
        prompt = self._build_initial_prompt(task)
        
        for step in range(max_steps):
            logger.debug(f"ReAct step {step + 1}/{max_steps}")
            
            # Generate thought + action
            try:
                response = self.llm(
                    prompt,
                    max_tokens=256,
                    temperature=0.3,
                    stop=["<|end|>", "\nObservation:"]
                )
                
                response_text = response["choices"][0]["text"]
                prompt += response_text
                
                # Parse action
                if "Action:" in response_text:
                    action_line = response_text.split("Action:")[1].split("\n")[0].strip()
                    tool_name, args = self._parse_action(action_line)
                    
                    if tool_name in self.tools:
                        # Execute tool
                        logger.debug(f"Executing tool: {tool_name}({args})")
                        result = self.tools[tool_name](args)
                        
                        # Add observation
                        observation = f"\nObservation: {json.dumps(result)[:500]}\n"
                        prompt += observation
                    else:
                        logger.warning(f"Unknown tool: {tool_name}")
                        break
                
                # Check for final answer
                if "Final Answer:" in response_text:
                    final = response_text.split("Final Answer:")[-1].strip()
                    logger.info(f"ReAct completed in {step + 1} steps")
                    return final
            
            except Exception as e:
                logger.error(f"ReAct step error: {e}")
                break
        
        # No final answer reached, return last response
        logger.warning(f"ReAct stopped after {max_steps} steps without final answer")
        return prompt.split("\n")[-1] if prompt else "No result"
    
    def _build_initial_prompt(self, task: str) -> str:
        """Build initial ReAct prompt."""
        return f"""<|user|>
Task: {task}

You have access to these tools:
{', '.join(self.tools.keys())}

Think step by step and use tools as needed.

Format:
Thought: (your reasoning)
Action: tool_name(argument)
Observation: (tool result)
... (repeat as needed)
Final Answer: (your final answer)
<|end|>
<|assistant|>
"""
    
    def _parse_action(self, action_line: str) -> tuple[str, str]:
        """
        Parse action line.
        
        Args:
            action_line: Line like "search_codebase(authentication)"
        
        Returns:
            Tuple of (tool_name, args)
        """
        if "(" in action_line and ")" in action_line:
            tool_name = action_line.split("(")[0].strip()
            args = action_line.split("(")[1].split(")")[0].strip()
            return tool_name, args
        else:
            return action_line.strip(), ""
    
    def __repr__(self) -> str:
        return f"CodeAgent(tools={list(self.tools.keys())})"


# USO EN PRODUCCIÓN
if __name__ == "__main__":
    # Demo (requiere LLM y RAG initialized)
    from llama_cpp import Llama
    from hlcs.memory.rag import KnowledgeRAG
    
    llm = Llama(model_path="./models/phi4_mini_q4.gguf", n_ctx=4096)
    rag = KnowledgeRAG("./data/codebase.py")
    
    agent = CodeAgent(llm, rag, enable_sandbox=False)
    result = agent.run("How do I implement JWT authentication in Python?")
    print(result)
