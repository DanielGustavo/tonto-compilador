"""Representação do erro do Analisador Sintático.

`SyntacticError` é emitido pela gramática (ver `error_handling.py::p_error`).
Guarda o valor/lexema envolvido, linha, coluna, uma mensagem e uma sugestão
de correção. O equivalente semântico, `SemanticError`, vive em
`semantic_analyzer/errors.py`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntacticError:
  value: str
  line: int
  column: int
  message: str
  suggestion: str
