"""Base agent class for Triathlon Coach AI"""
import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for CrewAI agents"""
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str
    ):
        """
        Initialize base agent
        
        Args:
            role: Agent role/title
            goal: Agent goal
            backstory: Agent backstory/context
        """
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.memory: List[dict] = []
    
    @abstractmethod
    def execute(self, input_data: Any) -> str:
        """
        Execute agent task
        
        Args:
            input_data: Input data for processing
        
        Returns:
            Agent response/result
        """
        pass
    
    def add_to_memory(self, interaction: dict):
        """Add interaction to agent memory"""
        self.memory.append(interaction)
    
    def get_memory(self) -> List[dict]:
        """Get agent memory"""
        return self.memory
    
    def clear_memory(self):
        """Clear agent memory"""
        self.memory = []
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.role}>"
