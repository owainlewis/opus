"""Markdown parser for recipe files"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class MarkdownRecipeParser:
    """
    Parses Markdown recipes with conventions:
    - # Title = recipe name
    - **Parameters:** section = recipe parameters
    - ## Step N: Name = step headers
    - ```language code blocks = executable commands
    - Other text = manual instructions/context
    """

    def __init__(self):
        self.step_pattern = re.compile(r'^## Step (\d+): (.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
        self.param_pattern = re.compile(r'\*\*Parameters:\*\*\s*\n((?:- .+\n?)+)', re.MULTILINE)
        self.param_line_pattern = re.compile(r'- (\w+)\s*(?:\(([^)]+)\))?: (.+)')

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a Markdown recipe file.

        Args:
            file_path: Path to .md file

        Returns:
            Recipe definition dict
        """
        with open(file_path, 'r') as f:
            content = f.read()

        return self.parse_content(content, file_path.stem)

    def parse_content(self, content: str, default_name: str = "recipe") -> Dict[str, Any]:
        """
        Parse Markdown content into recipe structure.

        Args:
            content: Markdown text
            default_name: Default recipe name if not found

        Returns:
            Recipe definition dict with structure:
            {
                'name': str,
                'description': str,
                'parameters': dict,
                'steps': list
            }
        """
        # Extract recipe name from first # header
        name = self._extract_name(content) or default_name

        # Extract description (text between title and first step/parameters)
        description = self._extract_description(content)

        # Extract parameters
        parameters = self._extract_parameters(content)

        # Extract steps
        steps = self._extract_steps(content)

        return {
            'name': name,
            'description': description or f"Recipe: {name}",
            'parameters': parameters,
            'steps': steps,
            'version': '1.0.0',
            'format': 'markdown'
        }

    def _extract_name(self, content: str) -> Optional[str]:
        """Extract recipe name from first # header"""
        match = re.search(r'^# (.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description (text between title and first step)"""
        # Find text after first # header, before ## Step or **Parameters:**
        match = re.search(
            r'^# .+$\s*\n+(.+?)(?=\n\*\*Parameters:\*\*|\n## Step|\Z)',
            content,
            re.MULTILINE | re.DOTALL
        )
        if match:
            desc = match.group(1).strip()
            # Remove extra whitespace and newlines
            desc = re.sub(r'\n\s*\n', '\n', desc)
            return desc
        return None

    def _extract_parameters(self, content: str) -> Dict[str, Any]:
        """
        Extract parameters from **Parameters:** section.

        Format:
        **Parameters:**
        - param_name (required): Description
        - param_name (default: value): Description
        """
        match = self.param_pattern.search(content)
        if not match:
            return {}

        params_section = match.group(1)
        parameters = {}

        for line in params_section.strip().split('\n'):
            param_match = self.param_line_pattern.match(line.strip())
            if param_match:
                name = param_match.group(1)
                options = param_match.group(2) or ''
                description = param_match.group(3)

                param_def = {
                    'type': 'string',  # Default type
                    'description': description
                }

                # Parse options (required, default: value)
                if 'required' in options.lower():
                    param_def['required'] = True

                # Extract default value
                default_match = re.search(r'default:\s*(.+?)(?:,|$)', options)
                if default_match:
                    param_def['default'] = default_match.group(1).strip()

                parameters[name] = param_def

        return parameters

    def _extract_steps(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract steps from ## Step N: headers.

        Each step includes:
        - name: From header
        - description: Text before code blocks
        - tool/manual: Determined by presence of code blocks
        - args: Extracted from code blocks
        """
        steps = []

        # Find all step headers
        step_matches = list(self.step_pattern.finditer(content))

        for i, match in enumerate(step_matches):
            step_num = int(match.group(1))
            step_name = match.group(2).strip()

            # Extract content between this step and next step (or end)
            start_pos = match.end()
            if i + 1 < len(step_matches):
                end_pos = step_matches[i + 1].start()
            else:
                end_pos = len(content)

            step_content = content[start_pos:end_pos].strip()

            # Parse step content
            step = self._parse_step_content(step_name, step_content)
            steps.append(step)

        return steps

    def _parse_step_content(self, name: str, content: str) -> Dict[str, Any]:
        """
        Parse individual step content.

        If code blocks present: tool step
        Otherwise: manual step
        """
        # Find code blocks
        code_blocks = list(self.code_block_pattern.finditer(content))

        # Extract text (everything except code blocks)
        text_parts = []
        last_end = 0
        for block in code_blocks:
            text_parts.append(content[last_end:block.start()].strip())
            last_end = block.end()
        text_parts.append(content[last_end:].strip())

        description = '\n'.join(p for p in text_parts if p).strip()

        if code_blocks:
            # Tool step - use first code block as command
            first_block = code_blocks[0]
            language = first_block.group(1) or 'bash'
            command = first_block.group(2).strip()

            # Determine tool based on language
            tool = self._language_to_tool(language)

            return {
                'name': name,
                'description': description or name,
                'tool': tool,
                'args': {
                    'command': command
                },
                'approval': 'optional'
            }
        else:
            # Manual step
            return {
                'name': name,
                'description': description or name,
                'manual': True,
                'instructions': content.strip()
            }

    def _language_to_tool(self, language: str) -> str:
        """Map code block language to tool name"""
        language_map = {
            'bash': 'bash',
            'sh': 'bash',
            'shell': 'bash',
            'python': 'bash',  # Execute via bash for now
            'javascript': 'bash',
            'js': 'bash',
        }
        return language_map.get(language.lower(), 'bash')

    def interpolate_variables(self, recipe: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace $variable references with parameter values.

        Supports: $var and ${var} syntax
        """
        import json
        recipe_json = json.dumps(recipe)

        # Replace variables
        for param_name, param_value in params.items():
            # Replace ${var} and $var patterns
            recipe_json = re.sub(
                rf'\${{{param_name}}}|\${param_name}\b',
                str(param_value),
                recipe_json
            )

        return json.loads(recipe_json)
