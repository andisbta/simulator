"""YAML pattern parser – converts pattern definitions into condition objects."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

import yaml


@dataclass
class Condition:
    """A single condition within a pattern rule."""

    column: str
    operator: str
    value: Any
    value_type: str = "absolute"  # "absolute" or "percentile"


@dataclass
class EvaluationTarget:
    """What forward return to evaluate when the pattern triggers."""

    target: str  # e.g. "return_15m"
    direction: str = "long"  # "long" or "short"


@dataclass
class Pattern:
    """A complete pattern definition with conditions and evaluation target."""

    name: str
    description: str
    conditions: List[Condition]
    evaluate: EvaluationTarget
    source_file: Optional[str] = None


class PatternParser:
    """Parses pattern YAML files into Pattern objects."""

    VALID_OPERATORS = {"<", "<=", ">", ">=", "==", "!="}

    def parse_file(self, filepath: str) -> Pattern:
        """Parse a single pattern YAML file."""
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
        return self._parse_dict(data, source_file=str(filepath))

    def parse_directory(self, dirpath: str) -> List[Pattern]:
        """Parse all YAML files in a directory."""
        patterns = []
        pattern_dir = Path(dirpath)

        if not pattern_dir.exists():
            return patterns

        for yaml_file in sorted(pattern_dir.glob("*.yaml")):
            try:
                pattern = self.parse_file(str(yaml_file))
                patterns.append(pattern)
            except Exception as e:
                print(f"  [WARN] Failed to parse {yaml_file.name}: {e}")

        return patterns

    def _parse_dict(self, data: dict, source_file: str = None) -> Pattern:
        """Convert a raw YAML dict into a Pattern object."""
        conditions = []
        for cond in data.get("conditions", []):
            if cond["operator"] not in self.VALID_OPERATORS:
                raise ValueError(
                    f"Invalid operator '{cond['operator']}' in pattern "
                    f"'{data.get('name', 'unknown')}'"
                )
            conditions.append(
                Condition(
                    column=cond["column"],
                    operator=cond["operator"],
                    value=cond["value"],
                    value_type=cond.get("value_type", "absolute"),
                )
            )

        eval_cfg = data.get("evaluate", {})
        evaluate = EvaluationTarget(
            target=eval_cfg.get("target", "return_15m"),
            direction=eval_cfg.get("direction", "long"),
        )

        return Pattern(
            name=data.get("name", "Unnamed Pattern"),
            description=data.get("description", ""),
            conditions=conditions,
            evaluate=evaluate,
            source_file=source_file,
        )
