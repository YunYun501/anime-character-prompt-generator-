"""
Shared route dependencies.
"""

from generator.prompt_generator import PromptGenerator

# Keep one catalog loader instance per app process.
gen = PromptGenerator()
