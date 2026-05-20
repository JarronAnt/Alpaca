# src/alpaca/agents/router.py
"""THAG - Router agent that decides if task is coding-related."""

from alpaca.agents.base import BaseAgent
from alpaca.config import Config
from alpaca.models import AgentRole, AgentStatus, TaskResult


class RouterAgent(BaseAgent):
    """THAG - Chief caveman router."""
    
    role = AgentRole.ROUTER
    model = Config.router_model
    
    system_prompt = """You are Thag, the Chief Caveman Router.

Your job is to decide if a user request is a CODING TASK or NORMAL CONVERSATION.

CODING TASK indicators:
- Requests to write, create, or modify code
- Bug fixes or debugging
- Building apps, scripts, tools, or projects
- File operations, project structure
- Technical implementation requests

NORMAL CONVERSATION indicators:
- General questions
- Greetings
- Non-technical discussions
- Advice or explanations without code

Respond EXACTLY:
If CODING TASK: output only "CODE_TASK"
If NORMAL: respond in caveman style (brief, simple)

Rules:
- Be decisive
- No explanations for CODE_TASK
- Keep normal responses under 3 sentences
"""
    
    def is_coding_task(self, text: str) -> bool:
        """Check if text indicates a coding task."""
        text_lower = text.lower()
        
        # Check for explicit marker
        if "CODE_TASK" in text:
            return True
            
        # Check keywords
        return any(kw in text_lower for kw in Config.coding_keywords)
    
    def run(self, user_input: str) -> TaskResult:
        """Route the user input."""
        self.update_state(AgentStatus.RUNNING, task="routing")
        
        self.memory.add_user(user_input)
        response = self.call_llm()
        self.memory.add_assistant(response)
        
        is_code = self.is_coding_task(response)
        
        self.update_state(
            AgentStatus.SUCCESS if is_code else AgentStatus.IDLE
        )
        
        return TaskResult(
            success=True,
            output=response,
            data={"is_coding_task": is_code},
        )
