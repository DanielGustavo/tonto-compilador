"""Representação de um erro sintático (ver `grammar_rules.py::p_error`)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntacticError:
  value: str
  line: int
  column: int
  message: str
  suggestion: str
