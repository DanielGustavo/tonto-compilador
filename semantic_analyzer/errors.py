"""Representação do erro do Analisador Semântico.

`SemanticError` é emitido pelas ações semânticas (ver `semantic_actions.py`)
e pela resolução de imports (ver `imports.py`). Guarda o valor/lexema
envolvido, linha, coluna, uma mensagem e uma sugestão de correção. O
equivalente sintático, `SyntacticError`, vive em `syntax_analyzer/errors.py`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticError:
  value: str
  line: int
  column: int
  message: str
  suggestion: str
