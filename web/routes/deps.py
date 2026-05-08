"""
Shared route dependencies.
"""

from generator.prompt_generator import PromptGenerator
from generator.constraints import ConstraintEngine

# Keep one catalog loader instance per app process.
gen = PromptGenerator()
constraints = ConstraintEngine()


def get_generator() -> PromptGenerator:
    """Return the current generator instance."""
    return gen


def get_constraints() -> ConstraintEngine:
    """Return the constraint engine."""
    return constraints


def reinitialize_generator(catalog_mode: str = "lightweight") -> PromptGenerator:
    """Reinitialize the generator with a new catalog mode."""
    global gen, constraints
    gen = PromptGenerator(catalog_mode=catalog_mode)
    constraints = ConstraintEngine()
    return gen
