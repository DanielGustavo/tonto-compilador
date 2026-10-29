"""Representação dos erros do Analisador Sintático/Semântico.

`SyntacticError` é emitido pela gramática (ver `error_handling.py::p_error`)
e `SemanticError` pelas ações semânticas (ver `semantic_actions.py`). Ambos
guardam o valor/lexema envolvido, linha, coluna, uma mensagem e uma sugestão
de correção.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntacticError:
  value: str
  line: int
  column: int
  message: str
  suggestion: str


@dataclass(frozen=True)
class SemanticError:
  value: str
  line: int
  column: int
  message: str
  suggestion: str
