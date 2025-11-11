"""Recipe loader for loading and validating recipes"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from opus.recipes.markdown_parser import MarkdownRecipeParser

logger = logging.getLogger(__name__)


class RecipeLoader:
    """
    Loads and manages recipes from Markdown files.

    Handles:
    - Loading recipes from ~/.opus/recipes/
    - Include resolution (merging included recipes)
    - Parameter interpolation
    """

    DEFAULT_RECIPES_DIR = Path.home() / ".opus" / "recipes"

    def __init__(self, recipes_dir: Optional[Path] = None):
        """
        Initialize recipe loader.

        Args:
            recipes_dir: Directory containing recipe files (default: ~/.opus/recipes)
        """
        self.recipes_dir = recipes_dir or self.DEFAULT_RECIPES_DIR
        self.recipes_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_recipes = {}  # Cache loaded recipes
        self.parser = MarkdownRecipeParser()

    def list_recipes(self) -> List[str]:
        """
        List available recipe names.

        Returns:
            List of recipe names (without .md extension)
        """
        if not self.recipes_dir.exists():
            return []

        recipes = []
        for file_path in self.recipes_dir.glob("*.md"):
            recipes.append(file_path.stem)

        return sorted(recipes)

    def load_recipe(self, recipe_name: str) -> Dict[str, Any]:
        """
        Load a recipe by name.

        Args:
            recipe_name: Recipe name (without .md extension)

        Returns:
            Loaded recipe dict

        Raises:
            FileNotFoundError: If recipe file doesn't exist
        """
        # Check cache
        if recipe_name in self.loaded_recipes:
            return self.loaded_recipes[recipe_name]

        # Find recipe file
        recipe_path = self.recipes_dir / f"{recipe_name}.md"
        if not recipe_path.exists():
            raise FileNotFoundError(f"Recipe not found: {recipe_name}")

        # Load
        recipe = self._load_recipe_file(recipe_path)

        # Cache and return
        self.loaded_recipes[recipe_name] = recipe
        return recipe

    def _load_recipe_file(self, recipe_path: Path) -> Dict[str, Any]:
        """
        Load a recipe file and handle includes.

        Args:
            recipe_path: Path to recipe Markdown file

        Returns:
            Loaded recipe dict
        """
        logger.info(f"Loading recipe from {recipe_path}")

        # Parse Markdown
        recipe_data = self.parser.parse_file(recipe_path)

        # Handle includes
        if recipe_data.get("includes"):
            recipe_data = self._resolve_includes(recipe_data)

        logger.info(f"Successfully loaded recipe '{recipe_data['name']}' with {len(recipe_data['steps'])} steps")

        return recipe_data

    def _resolve_includes(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve recipe includes by merging included recipes.

        Args:
            recipe_data: Recipe with includes

        Returns:
            Recipe with includes merged
        """
        included_steps = []

        for include_name in recipe_data["includes"]:
            logger.info(f"Including recipe: {include_name}")

            try:
                included_recipe = self.load_recipe(include_name)

                # Add included steps
                included_steps.extend(included_recipe["steps"])

                # Merge parameters (included recipe params are optional in parent)
                if "parameters" in included_recipe:
                    for param_name, param_def in included_recipe["parameters"].items():
                        if param_name not in recipe_data["parameters"]:
                            # Make included params optional unless they're required
                            included_param = param_def.copy()
                            if "required" in included_param and included_param["required"]:
                                logger.warning(f"Required parameter '{param_name}' from included recipe '{include_name}'")
                            recipe_data["parameters"][param_name] = included_param

            except FileNotFoundError:
                logger.warning(f"Included recipe not found: {include_name}")
            except Exception as e:
                logger.error(f"Failed to include recipe '{include_name}': {e}")

        # Prepend included steps before recipe's own steps
        recipe_data["steps"] = included_steps + recipe_data["steps"]

        return recipe_data

    def interpolate_variables(self, recipe: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpolate parameter variables in recipe.

        Replaces $param_name and ${param_name} with param values.

        Args:
            recipe: Recipe definition
            params: Parameter values

        Returns:
            Recipe with variables interpolated
        """
        return self.parser.interpolate_variables(recipe, params)

    def validate_params(self, recipe: Dict[str, Any], params: Dict[str, Any]) -> List[str]:
        """
        Validate provided parameters against recipe requirements.

        Args:
            recipe: Recipe definition
            params: Provided parameter values

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        recipe_params = recipe.get("parameters", {})

        # Check required parameters
        for param_name, param_def in recipe_params.items():
            if param_def.get("required", False):
                if param_name not in params:
                    errors.append(f"Missing required parameter: {param_name}")

        # Check parameter types
        for param_name, param_value in params.items():
            if param_name in recipe_params:
                param_def = recipe_params[param_name]
                expected_type = param_def.get("type", "string")

                # Type validation
                if expected_type == "string" and not isinstance(param_value, str):
                    errors.append(f"Parameter '{param_name}' must be a string")
                elif expected_type == "number" and not isinstance(param_value, (int, float)):
                    errors.append(f"Parameter '{param_name}' must be a number")
                elif expected_type == "boolean" and not isinstance(param_value, bool):
                    errors.append(f"Parameter '{param_name}' must be a boolean")

        return errors

    def get_recipe_info(self, recipe_name: str) -> Dict[str, Any]:
        """
        Get recipe metadata without loading full recipe.

        Args:
            recipe_name: Recipe name

        Returns:
            Dict with name, description, version, parameters

        Raises:
            FileNotFoundError: If recipe doesn't exist
        """
        recipe_path = self.recipes_dir / f"{recipe_name}.md"
        if not recipe_path.exists():
            raise FileNotFoundError(f"Recipe not found: {recipe_name}")

        recipe_data = self.parser.parse_file(recipe_path)

        return {
            "name": recipe_data.get("name", recipe_name),
            "description": recipe_data.get("description", ""),
            "version": recipe_data.get("version", "1.0.0"),
            "author": recipe_data.get("author", "Unknown"),
            "parameters": recipe_data.get("parameters", {}),
            "step_count": len(recipe_data.get("steps", [])),
        }
