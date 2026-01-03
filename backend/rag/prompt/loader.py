"""Prompt template loader - loads system prompts from external files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from loguru import logger


class PromptLoader:
    """Loads and caches prompt templates from files."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize the prompt loader.
        
        Parameters
        ----------
        templates_dir : Path, optional
            Directory containing prompt templates. Defaults to 
            backend/rag/prompt/templates/ relative to this file.
        """
        if templates_dir is None:
            # Resolve path relative to this file's location
            self.templates_dir = Path(__file__).parent / "templates"
        else:
            self.templates_dir = Path(templates_dir)
        
        self._cache: Dict[str, str] = {}
        
        if not self.templates_dir.exists():
            logger.warning(
                f"Prompt templates directory not found: {self.templates_dir}. "
                "Prompts will need to be loaded from code fallbacks."
            )
    
    def load(self, template_name: str, **kwargs) -> str:
        """Load a prompt template, optionally with variable substitution.
        
        Parameters
        ----------
        template_name : str
            Name of the template file (without .txt extension)
        **kwargs
            Variables to substitute in the template using {variable_name} syntax
            
        Returns
        -------
        str
            The loaded prompt template with variables substituted
            
        Raises
        ------
        FileNotFoundError
            If the template file doesn't exist
        """
        # Check cache first
        if template_name in self._cache and not kwargs:
            return self._cache[template_name]
        
        # Load from file
        template_path = self.templates_dir / f"{template_name}.txt"
        
        if not template_path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {template_path}. "
                f"Available templates: {list(self._get_available_templates())}"
            )
        
        try:
            content = template_path.read_text(encoding="utf-8")
            
            # Strip leading/trailing whitespace but preserve internal formatting
            content = content.strip()
            
            # Perform variable substitution if kwargs provided
            if kwargs:
                try:
                    content = content.format(**kwargs)
                except KeyError as e:
                    logger.error(
                        f"Missing template variable: {e}. "
                        f"Available variables in template: {self._extract_variables(content)}"
                    )
                    raise ValueError(f"Missing template variable: {e}") from e
            
            # Cache if no variables were substituted
            if not kwargs:
                self._cache[template_name] = content
            
            logger.debug(f"Loaded prompt template: {template_name} ({len(content)} chars)")
            return content
            
        except Exception as e:
            logger.error(f"Error loading prompt template {template_name}: {e}")
            raise
    
    def _get_available_templates(self) -> list[str]:
        """Get list of available template files."""
        if not self.templates_dir.exists():
            return []
        return [
            f.stem for f in self.templates_dir.glob("*.txt")
        ]
    
    @staticmethod
    def _extract_variables(template: str) -> set[str]:
        """Extract variable names from a template string."""
        import re
        pattern = r'\{(\w+)\}'
        return set(re.findall(pattern, template))


# Global loader instance
_default_loader: Optional[PromptLoader] = None


def get_loader() -> PromptLoader:
    """Get the global prompt loader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader


def load_prompt(template_name: str, **kwargs) -> str:
    """Convenience function to load a prompt template.
    
    Parameters
    ----------
    template_name : str
        Name of the template file (without .txt extension)
    **kwargs
        Variables to substitute in the template
        
    Returns
    -------
    str
        The loaded prompt template
    """
    return get_loader().load(template_name, **kwargs)
