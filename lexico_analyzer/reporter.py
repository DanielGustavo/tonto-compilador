"""Apresentação dos resultados da análise léxica.

Separado do `analyzer` de propósito: a análise produz dados, o reporter decide
como esses dados aparecem na tela. Trocar/adicionar uma visualização (tabela,
JSON, CSV) mexe só neste arquivo.
"""

from .token_types import CustomToken


def imprimir_visao_analitica(tokens: list[CustomToken], codigo_fonte: str) -> None:
  """Visão analítica: cada linha do fonte seguida dos tokens que ela gerou."""
  linhas = codigo_fonte.splitlines()
  linha_atual = None

  for token in tokens:
    if token.line != linha_atual:
      if linha_atual is not None:
        print()

      linha_atual = token.line
      print(f"{linha_atual}: {linhas[linha_atual - 1]}")

    print(f"  {token}")


def imprimir_erros(erros: list[dict]) -> None:
  """Resumo dos erros léxicos encontrados, agrupados por linha."""
  if not erros:
    print("\nNenhum erro léxico encontrado.")
    return

  print(f"\n--- Erros léxicos ({len(erros)}) ---")

  for erro in erros:
    print(f"  linha {erro['line']}, coluna {erro['column']}: {erro['message']}")
