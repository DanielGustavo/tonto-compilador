"""Apresentação dos erros da Análise Semântica.

Paralelo a `lexico_analyzer/reporter.py` e `syntax_analyzer/reporter.py`:
imprime a lista de `SemanticError` produzida por `semantic_actions.py` e
`imports.py`. O relatório de padrões de projeto tem reporter próprio em
`semantic_analyzer/patterns/reporter.py`.
"""

from .errors import SemanticError


def print_semantic_errors(errors: list[SemanticError]) -> None:
  if not errors:
    print("\nNenhum erro semântico encontrado.")
    return

  print(f"\n--- Erros semânticos ({len(errors)}) ---")

  for error in errors:
    print(f"  linha {error.line}, coluna {error.column}: {error.message}")
    print(f"    sugestão: {error.suggestion}")
