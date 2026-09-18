"""
Command Line Interface (CLI) for SyntheticTutor.
"""

import asyncio
import click
import logging
from rich.console import Console
from synthetictutor.llm.router import get_llm_client
from synthetictutor.ingestion.json_parser import TextbookParser
from synthetictutor.knowledge.extractor import ConceptExtractor
from synthetictutor.pipeline.runner import BatchPipelineRunner

console = Console()
logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    """SyntheticTutor: Scalable Synthetic Data Generation Pipeline for Educational Socratic Dialogues."""
    pass


@cli.command()
@click.option("--source", required=True, help="Path to input JSON or text textbook chapter.")
@click.option("--provider", default="mock", help="LLM provider (gemini, openai, vllm, omniroute, mock).")
@click.option("--lang", default="en,hi,hinglish", help="Comma-separated target languages (e.g. en,hi,hinglish).")
@click.option("--output", default="output/synthetic_sharegpt.jsonl", help="Output SFT dataset path.")
def run(source: str, provider: str, lang: str, output: str):
    """Run full synthetic data generation pipeline from textbook source to SFT dataset."""
    console.print(f"[bold green]SyntheticTutor Pipeline Initiated[/bold green] (Provider: {provider})")
    
    llm = get_llm_client(provider)
    parser = TextbookParser()
    chapter = parser.parse_file(source)

    extractor = ConceptExtractor(llm)
    
    async def _execute():
        console.print("[cyan]Extracting concept graph from curriculum source...[/cyan]")
        kg = await extractor.extract_from_text(chapter["content"], chapter["domain"], chapter["grade_level"])
        
        target_langs = [l.strip() for l in lang.split(",") if l.strip()]
        console.print(f"[cyan]Simulating Socratic dialogues & running quality guardrails ({len(target_langs)} languages)...[/cyan]")
        
        runner = BatchPipelineRunner(llm_client=llm)
        stats = await runner.run_pipeline(kg, target_languages=target_langs, sharegpt_output=output)
        
        console.print(f"[bold gold1]Success![/bold gold1] Generated {stats['total_generated']} dialogues.")
        console.print(f"Dataset exported to: [link={stats['sharegpt_path']}]{stats['sharegpt_path']}[/link]")

    asyncio.run(_execute())


@cli.command("generate-paper")
@click.option("--board", default="WBBSE", help="Examination Board (WBBSE / WBCHSE)")
@click.option("--class-level", default="Class 10", help="Class Level (e.g. Class 10, Class 12)")
@click.option("--subject", default="Life Science", help="Subject name (e.g. Life Science, Physical Science, Mathematics, History, Geography, Chemistry, Physics, Biology)")
@click.option("--medium", default="Bengali", help="Medium of instruction")
@click.option("--total-marks", default=90.0, type=float, help="Total examination marks (e.g. 25, 50, 70, 80, 90)")
@click.option("--duration", default=180, type=int, help="Examination duration in minutes")
@click.option("--mode", default="NEW_QUESTIONS", type=click.Choice(["PAST_PAPER", "NEW_QUESTIONS", "HYBRID", "CUSTOM"]), help="Generation mode")
@click.option("--difficulty", default="BOARD_STYLE", type=click.Choice(["EASY", "MODERATE", "BOARD_STYLE", "CHALLENGING"]), help="Difficulty level")
@click.option("--output-dir", default="datasets/generated_question_papers", help="Base directory for generated papers")
def generate_paper(board, class_level, subject, medium, total_marks, duration, mode, difficulty, output_dir):
    """Generate an authentic Board-Style Question Paper with Answer Key and Marking Scheme."""
    from synthetictutor.question_papers.generator.models import QuestionPaperConfig, GenerationMode, DifficultyLevel
    from synthetictutor.question_papers.generator.pipeline import BoardQuestionPaperPipeline
    
    mode_map = {
        "PAST_PAPER": GenerationMode.PAST_PAPER,
        "NEW_QUESTIONS": GenerationMode.NEW_QUESTIONS,
        "HYBRID": GenerationMode.HYBRID,
        "CUSTOM": GenerationMode.CUSTOM
    }
    diff_map = {
        "EASY": DifficultyLevel.EASY,
        "MODERATE": DifficultyLevel.MODERATE,
        "BOARD_STYLE": DifficultyLevel.BOARD_STYLE,
        "CHALLENGING": DifficultyLevel.CHALLENGING
    }
    
    config = QuestionPaperConfig(
        board=board,
        class_level=class_level,
        subject=subject,
        medium=medium,
        total_marks=total_marks,
        duration_minutes=duration,
        mode=mode_map[mode],
        difficulty=diff_map[difficulty],
        include_answer_key=True,
        include_marking_scheme=True
    )
    
    console.print(f"[bold green]Generating {board} {class_level} {subject} Question Paper ({total_marks} Marks | Mode: {mode})...[/bold green]")
    pipeline = BoardQuestionPaperPipeline(output_base_dir=output_dir)
    result = pipeline.generate_and_export(config, export_to_disk=True)
    
    console.print(f"[bold gold1]Success![/bold gold1] Generated Question Paper: [cyan]{result['title']}[/cyan]")
    console.print(f"Export directory: [link={result.get('export_directory')}]{result.get('export_directory')}[/link]")


@cli.command("wbbse-paper")
@click.option("--grade", default="Class 10", help="Grade level (Class 1 ... Class 10)")
@click.option("--subject", default="Mathematics", help="Subject name (e.g. Mathematics, Science, Bengali, History, Geography)")
@click.option("--chapter", "-c", "chapters", multiple=True, help="Specific chapter(s) to include (repeatable). Omit for full syllabus.")
@click.option("--difficulty", default="Mixed", type=click.Choice(["Easy", "Moderate", "Challenging", "Mixed"]), help="Difficulty distribution")
@click.option("--no-answer-key", is_flag=True, default=False, help="Exclude answer key")
@click.option("--no-marking-scheme", is_flag=True, default=False, help="Exclude marking scheme")
@click.option("--total-marks", default=None, type=float, help="Optional override for total marks")
@click.option("--output-dir", default="datasets/generated_question_papers", help="Output base directory")
def wbbse_paper(grade, subject, chapters, difficulty, no_answer_key, no_marking_scheme, total_marks, output_dir):
    """Generate a WBBSE question paper with product-comparison configuration."""
    from synthetictutor.question_papers.wbbse_generator.config import WBBSEPaperConfig
    from synthetictutor.question_papers.wbbse_generator.pipeline_wbbse import WBBSEQuestionPaperPipeline

    config = WBBSEPaperConfig(
        grade=grade,
        subject=subject,
        chapters=list(chapters),
        difficulty=difficulty,
        include_answer_key=not no_answer_key,
        include_marking_scheme=not no_marking_scheme,
        total_marks_override=total_marks
    )

    console.print(f"[bold green]Generating WBBSE {grade} {subject} Paper ({config.chapter_mode} | Difficulty: {difficulty})...[/bold green]")
    pipeline = WBBSEQuestionPaperPipeline(output_base_dir=output_dir)
    result = pipeline.generate_and_export(config, export_to_disk=True)

    console.print(f"[bold gold1]Success![/bold gold1] Generated: [cyan]{result['title']}[/cyan]")
    console.print(f"Validation: {'[green]PASSED[/green]' if result['is_valid'] else '[red]FAILED[/red]'}")
    console.print(f"Export directory: [link={result.get('export_directory')}]{result.get('export_directory')}[/link]")


if __name__ == "__main__":
    cli()


