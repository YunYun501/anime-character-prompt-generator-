"""
ComfyUI Custom Node: Random Character Prompt Generator
Auto-generates anime character prompts for Stable Diffusion.

Installation:
1. Copy entire 'auto_prompt' folder to ComfyUI/custom_nodes/
2. Restart ComfyUI
3. Find nodes in the node menu under "prompt":
   - "Random Character Prompt" - Lightweight curated prompts
   - "Expanded Auto Prompter" - 20,000+ auto-generated tags
"""

from .nodes import RandomCharacterPromptNode, ExpandedAutoPrompterNode, AutoPromptExpandedNode

NODE_CLASS_MAPPINGS = {
    "RandomCharacterPrompt": RandomCharacterPromptNode,
    "ExpandedAutoPrompter": ExpandedAutoPrompterNode,
    "AutoPromptExpanded": AutoPromptExpandedNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RandomCharacterPrompt": "Random Character Prompt",
    "ExpandedAutoPrompter": "Expanded Auto Prompter",
    "AutoPromptExpanded": "Auto Prompt Expanded (Constrained)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
