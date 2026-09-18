"""
Simulation package for multi-agent educational dialogues.
"""

from synthetictutor.simulation.teacher_agent import TeacherAgent
from synthetictutor.simulation.student_agent import StudentAgent
from synthetictutor.simulation.engine import SimulationEngine, DialogueModerator

__all__ = ["TeacherAgent", "StudentAgent", "SimulationEngine", "DialogueModerator"]
