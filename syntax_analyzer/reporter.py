from .errors import SyntacticError


def print_syntax_errors(errors: list[SyntacticError]) -> None:
  if not errors:
    print("\nNenhum erro sintático encontrado.")
    return

  print(f"\n--- Erros sintáticos ({len(errors)}) ---")

  for error in errors:
    print(f"  linha {error.line}, coluna {error.column}: {error.message}")
    print(f"    sugestão: {error.suggestion}")
