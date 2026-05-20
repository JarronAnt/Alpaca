# src/alpaca/agents/builder.py
"""GROG - Builder based on working version."""

from alpaca.config import Config
from alpaca.core.llm import call_llm
from alpaca.core.parser import ToolParser
from alpaca.models import AgentRole, AgentStatus, TaskResult, ToolCall
from alpaca.agents.base import BaseAgent
from alpaca.tools.registry import run_tool


class BuilderAgent(BaseAgent):
    """GROG - The building caveman."""
    
    role = AgentRole.BUILDER
    model = Config.builder_model
    
    system_prompt = """You are Grog, a caveman coding builder agent.

RULES:
- Use RELATIVE paths only (like "myproject/main.py")
- ALWAYS use tools for file operations
- NEVER assume full system paths
- ALWAYS create directory before writing files
- You may output multiple tools per response
- Do not explain actions

Available tools:
- create_directory: {"path": "dir_name"}
- write_file: {"path": "file_name", "content": "file contents"}
- read_file: {"path": "file_name"}
- list_files: {"path": "."}
- run_shell: {"command": "shell command"}

Tool format:
<tool name="write_file">
{"path":"hello_app/main.py","content":"print('hi')"}
</tool>"""
    
    PLACEHOLDERS = ["/path/to", "path/to", "/example/", "example/path", "/path/to/your"]
    
    def __init__(self):
        super().__init__()
        # Use raw list like original, not fancy memory
        self.raw_memory = [{"role": "system", "content": self.system_prompt}]
    
    def _normalize_tool_calls(self, tool_calls: list) -> list:
        """Convert shell builtins to run_shell."""
        normalized = []
        for tool in tool_calls:
            if tool.name in ("cd", "ls", "cat", "mkdir", "rm", "touch", "echo", "pwd", "chmod"):
                if tool.name == "cd":
                    path = tool.args.get("path", tool.args.get("dir", "."))
                    cmd = f"cd {path}"
                elif tool.name == "ls":
                    path = tool.args.get("path", ".")
                    cmd = f"ls {path}"
                elif tool.name == "cat":
                    path = tool.args.get("path", "")
                    cmd = f"cat {path}"
                elif tool.name == "mkdir":
                    path = tool.args.get("path", "")
                    cmd = f"mkdir -p {path}"
                elif tool.name == "chmod":
                    path = tool.args.get("path", "")
                    mode = tool.args.get("mode", "+x")
                    cmd = f"chmod {mode} {path}"
                else:
                    cmd = tool.name
                
                normalized.append(ToolCall(name="run_shell", args={"command": cmd}))
            else:
                normalized.append(tool)
        return normalized
    
    def _check_placeholders(self, text: str) -> tuple[bool, str]:
        """Check for placeholder paths."""
        for ph in self.PLACEHOLDERS:
            if ph in text:
                return False, f"Use actual paths, not '{ph}'"
        return True, ""
    
    def _execute_tool(self, tool: ToolCall):
        """Execute a tool with auto-directory creation."""
        name = tool.name
        args = tool.args
        
        # Auto-create directory before writing files
        if name == "write_file":
            file_path = args.get("path", "")
            if file_path and "/" in file_path:
                dir_path = "/".join(file_path.split("/")[:-1])
                if dir_path:
                    run_tool("create_directory", {"path": dir_path})
        
        return run_tool(name, args)
    
    def _trim_memory(self):
        """Keep memory size manageable."""
        # Keep system + last 15 messages
        if len(self.raw_memory) > 16:
            system = self.raw_memory[0]
            recent = self.raw_memory[-14:]
            self.raw_memory = [system] + recent
    
    def run(self, user_input: str, plan: dict | None = None) -> TaskResult:
        """Build according to plan."""
        self.update_state(AgentStatus.BUILDING, task="building project")
        
        # Clear memory
        self.raw_memory = [{"role": "system", "content": self.system_prompt}]
        
        # Build context like original
        plan_steps = plan.get("steps", []) if plan else []
        project = plan.get("project", "project") if plan else "project"
        steps_list = [s.get("description", str(s)) if isinstance(s, dict) else str(s) for s in plan_steps]
        
        self.raw_memory.append({
            "role": "user",
            "content": f"""PROJECT: {project}
TASK: {user_input}
PLAN: {steps_list}"""
        })
        
        completed_steps = []
        step_index = 0
        max_steps = min(len(plan_steps) if plan_steps else 10, Config.max_tool_steps)
        
        while step_index < max_steps:
            step = plan_steps[step_index].get("description", str(plan_steps[step_index])) if plan_steps else "continue"
            
            self.raw_memory.append({
                "role": "user",
                "content": f"""CURRENT STEP:
{step}

COMPLETED STEPS:
{completed_steps}

RULE: Use tools only."""
            })
            
            tool_attempts = 0
            
            while True:
                # Call LLM with raw memory (like original)
                try:
                    response = call_llm(self.model, self.raw_memory, temperature=0.7)
                except Exception as e:
                    return TaskResult(success=False, error=f"LLM failed: {e}")
                
                print("\n--- GROG OUTPUT ---\n")
                print(response)
                print("\n-------------------\n")
                
                tool_calls = ToolParser.parse(response)
                tool_calls = self._normalize_tool_calls(tool_calls)
                
                # No tools - retry
                if not tool_calls:
                    tool_attempts += 1
                    self.raw_memory.append({"role": "assistant", "content": response})
                    self.raw_memory.append({
                        "role": "user",
                        "content": """You MUST use tools only.

Example:
<tool name="write_file">
{"path":"hello_app/main.py","content":"print('hi')"}
</tool>"""
                    })
                    if tool_attempts > 3:
                        return TaskResult(success=False, error="Tool loop stuck")
                    continue
                
                # Check for placeholders
                has_placeholders = False
                for tool in tool_calls:
                    path = tool.args.get("path", tool.args.get("command", ""))
                    valid, error = self._check_placeholders(path)
                    if not valid:
                        has_placeholders = True
                        self.raw_memory.append({"role": "assistant", "content": response})
                        self.raw_memory.append({"role": "user", "content": f"Error: {error}"})
                        break
                
                if has_placeholders:
                    continue
                
                # Execute tools
                self.raw_memory.append({"role": "assistant", "content": response})
                step_failed = False
                last_error = None
                
                for tool in tool_calls:
                    result = self._execute_tool(tool)
                    
                    # Add result like original format
                    result_content = result.output
                    if result.error:
                        result_content += f"\n{result.error}"
                    
                    self.raw_memory.append({
                        "role": "tool",
                        "name": tool.name,
                        "content": result_content
                    })
                    
                    if not result.success or result.error:
                        step_failed = True
                        last_error = result.error or "Unknown error"
                
                # Self-heal
                if step_failed:
                    self.raw_memory.append({
                        "role": "user",
                        "content": f"""STEP FAILED:
{step}

ERROR:
{last_error}

FIX USING TOOLS ONLY."""
                    })
                    continue
                
                # Step complete
                completed_steps.append(step)
                step_index += 1
                break
            
            # Trim memory
            self._trim_memory()
        
        self.update_state(AgentStatus.SUCCESS)
        return TaskResult(
            success=True,
            output=f"BUILD COMPLETE - {len(completed_steps)} steps",
            data={"completed_steps": completed_steps}
        )
    
    def fix(self, error_report: str) -> TaskResult:
        """Fix code based on error report."""
        self.raw_memory.append({
            "role": "user",
            "content": f"""SELF HEAL MODE

ERROR:
{error_report}

FIX USING TOOLS ONLY."""
        })
        
        max_attempts = 3
        for _ in range(max_attempts):
            try:
                response = call_llm(self.model, self.raw_memory, temperature=0.7)
            except Exception as e:
                return TaskResult(success=False, error=f"Fix failed: {e}")
            
            tool_calls = ToolParser.parse(response)
            tool_calls = self._normalize_tool_calls(tool_calls)
            
            if not tool_calls:
                self.raw_memory.append({"role": "assistant", "content": response})
                self.raw_memory.append({"role": "user", "content": "Use tools only."})
                continue
            
            self.raw_memory.append({"role": "assistant", "content": response})
            
            for tool in tool_calls:
                result = self._execute_tool(tool)
                self.raw_memory.append({
                    "role": "tool",
                    "name": tool.name,
                    "content": result.output
                })
                
                if result.success and not result.error:
                    return TaskResult(success=True, output="FIX COMPLETE")
        
        return TaskResult(success=False, error="Failed to fix")
