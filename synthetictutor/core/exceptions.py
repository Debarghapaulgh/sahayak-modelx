"""
Domain specific exceptions for SyntheticTutor.
"""

class SyntheticTutorError(Exception):
    """Base exception for all SyntheticTutor errors."""
    pass


class IngestionError(SyntheticTutorError):
    """Raised when parsing or reading curriculum files fails."""
    pass


class ExtractionError(SyntheticTutorError):
    """Raised when concept extraction fails or produces invalid schemas."""
    pass


class GraphValidationError(SyntheticTutorError):
    """Raised when a Concept Graph has cycles or missing prerequisite nodes."""
    pass


class SimulationError(SyntheticTutorError):
    """Raised when a multi-agent simulation fails or stalls."""
    pass


class EvaluationError(SyntheticTutorError):
    """Raised during multi-judge evaluation execution."""
    pass


class LLMProviderError(SyntheticTutorError):
    """Raised when LLM API calls fail or timeout."""
    pass
