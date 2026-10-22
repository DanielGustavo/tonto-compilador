"""Representação de um erro léxico (ver `lexer_rules.py::t_error`)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LexicalError:
  value: str
  line: int
  column: int
  message: str
