"""YAML recipe parser for simple, prompt-centric recipes"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class YamlRecipeParser:
    """
    Parse YAML recipes in Goose-style format.

    Simple structure:
    - title: Recipe name
    - description: What the recipe does
    - instructions: Optional system-level role/persona (e.g., "You are a senior Python developer...")
    - parameters: Input parameters with type, description, required, default
    - prompt: The actual task instructions/context for the agent
    """

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a YAML recipe file.

        Args:
            file_path: Path to YAML file

        Returns:
            Recipe dict with: title, description, parameters, prompt
        """
        logger.info(f"Parsing YAML recipe: {file_path}")

        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        return self.parse_content(data)

    def parse_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse YAML recipe data.

        Args:
            data: Parsed YAML dict

        Returns:
            Normalized recipe dict
        """
        recipe = {
            'title': data.get('title', 'Untitled Recipe'),
            'description': data.get('description', ''),
            'instructions': data.get('instructions', ''),  # Optional system-level instructions
            'parameters': self._parse_parameters(data.get('parameters', {})),
            'prompt': data.get('prompt', ''),
            'version': data.get('version', '2.0.0'),  # New version for new format
            'format': 'yaml'
        }

        return recipe

    def _parse_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and normalize parameter definitions.

        Args:
            params: Raw parameter dict from YAML

        Returns:
            Normalized parameter dict
        """
        normalized = {}

        for name, definition in params.items():
            if isinstance(definition, dict):
                normalized[name] = {
                    'type': definition.get('type', 'string'),
                    'description': definition.get('description', ''),
                    'required': definition.get('required', False),
                }

                if 'default' in definition:
                    normalized[name]['default'] = definition['default']
            else:
                # Simple format: just a description string
                normalized[name] = {
                    'type': 'string',
                    'description': str(definition),
                    'required': False
                }

        return normalized

    def interpolate_variables(self, recipe: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpolate parameter values into the prompt.

        Supports {{ variable }} and {{ variable }} syntax (Jinja2-like).

        Args:
            recipe: Recipe dict
            params: Parameter values

        Returns:
            Recipe with interpolated prompt
        """
        import re

        prompt = recipe.get('prompt', '')

        # Replace {{ variable }} patterns
        def replace_var(match):
            var_name = match.group(1).strip()
            return str(params.get(var_name, f'{{{{ {var_name} }}}}'))

        # Handle {{ variable }} syntax
        prompt = re.sub(r'\{\{\s*(\w+)\s*\}\}', replace_var, prompt)

        # Create new recipe with interpolated prompt
        interpolated = recipe.copy()
        interpolated['prompt'] = prompt

        return interpolated
