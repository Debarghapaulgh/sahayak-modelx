"""
Interactive Student Persona Sandbox / Experimentation CLI.
Allows researchers and developers to customize student cognitive traits, misconceptions, and learning styles
to observe how Socratic Teacher Agents dynamically adapt.
"""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from synthetictutor.core.schemas import Concept, Misconception, StudentPersona, TeacherPersona
from synthetictutor.planning.lesson_planner import LessonPlanner
from synthetictutor.planning.persona_factory import PersonaFactory
from synthetictutor.knowledge.graph import KnowledgeGraph
from synthetictutor.simulation.engine import SimulationEngine
from synthetictutor.llm.router import MockLLMClient, get_llm_client

console = Console()

PRESET_PERSONAS = {
    "overconfident": {
        "description": "Confident student holding a stubborn misconception; resists quick correction until shown counter-examples.",
        "curiosity_level": 0.8,
        "prior_knowledge_score": 0.7,
        "communication_style": "over-confident with a hidden misconception"
    },
    "hesitant": {
        "description": "Timid learner who doubts their own answers and guesses frequently.",
        "curiosity_level": 0.4,
        "prior_knowledge_score": 0.3,
        "communication_style": "hesitant and prone to guessing"
    },
    "inquisitive": {
        "description": "Deeply curious student who asks 'why' at every step and demands physical analogies.",
        "curiosity_level": 0.95,
        "prior_knowledge_score": 0.5,
        "communication_style": "inquisitive and demanding deep explanations"
    },
    "literal_beginner": {
        "description": "Beginner needing step-by-step concrete analogies to grasp abstract concepts.",
        "curiosity_level": 0.6,
        "prior_knowledge_score": 0.2,
        "communication_style": "literal-minded beginner needing concrete analogies"
    },
    "taciturn": {
        "description": "Brief, quiet learner who gives minimal one-word responses.",
        "curiosity_level": 0.3,
        "prior_knowledge_score": 0.4,
        "communication_style": "brief and taciturn learner"
    }
}


@click.command()
@click.option("--type", "persona_type", default="overconfident", help="Student persona type: overconfident, hesitant, inquisitive, literal_beginner, taciturn.")
@click.option("--concept", default="Universal Gravitation", help="Target educational concept to teach.")
@click.option("--misconception", default="", help="Custom misconception text for the student.")
@click.option("--provider", default="mock", help="LLM provider: mock, gemini, vllm, omniroute.")
def main(persona_type: str, concept: str, misconception: str, provider: str):
    """Run an interactive Socratic dialogue simulation with a customized Student Persona."""
    console.print(Panel(f"[bold cyan]SyntheticTutor Persona Experimenter[/bold cyan]\nTesting Socratic Adaptation against Student Persona: [gold1]{persona_type.upper()}[/gold1]"))

    preset = PRESET_PERSONAS.get(persona_type.lower(), PRESET_PERSONAS["overconfident"])
    
    # Build concept and student misconception
    misc_obj = []
    if misconception:
        misc_obj = [Misconception(id="m_custom", description=misconception, typical_trigger="Explanation", correct_conception="Accurate concept")]
    
    target_concept = Concept(
        id="c_test",
        name=concept,
        description=f"Core principles of {concept}",
        domain="Physics",
        grade_level="Grade 9",
        prerequisite_ids=[],
        misconceptions=misc_obj
    )

    kg = KnowledgeGraph()
    kg.add_concept(target_concept)
    
    planner = LessonPlanner(kg)
    plan = planner.create_plan(target_concept)

    student = StudentPersona(
        id=f"student_{persona_type}",
        name=f"Student ({persona_type.capitalize()})",
        grade_level="Grade 9",
        prior_knowledge_score=preset["prior_knowledge_score"],
        active_misconceptions=misc_obj,
        curiosity_level=preset["curiosity_level"],
        communication_style=preset["communication_style"]
    )

    teacher = PersonaFactory.create_teacher_persona(
        persona_id="teacher_socratic",
        name="Socratic Tutor",
        teaching_style="Socratic Elicitation"
    )

    # Display Persona Profile Table
    table = Table(title="Student Persona Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="gold1")
    table.add_row("Persona Style", student.communication_style)
    table.add_row("Curiosity Level", str(student.curiosity_level))
    table.add_row("Prior Knowledge Score", str(student.prior_knowledge_score))
    table.add_row("Active Misconception", misconception if misconception else "None")
    table.add_row("Target Concept", concept)
    console.print(table)

    llm = get_llm_client(provider)
    engine = SimulationEngine(llm_client=llm)

    async def _run():
        console.print("\n[bold green]Simulating Socratic Dialogue...[/bold green]\n")
        session = await engine.run_simulation(plan, student, teacher)

        for turn in session.turns:
            if turn.role.value == "teacher":
                console.print(f"[bold cyan][Teacher - Socratic Tutor]:[/bold cyan] {turn.content}")
            else:
                console.print(f"[bold gold1][{student.name}]:[/bold gold1] {turn.content}\n")

    asyncio.run(_run())


if __name__ == "__main__":
    main()
