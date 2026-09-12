"""Apresentação dos resultados da análise léxica.

Separado do `analyzer` de propósito: a análise produz dados, o reporter decide
como esses dados aparecem na tela. Trocar/adicionar uma visualização (tabela,
JSON, CSV) mexe só neste arquivo.
"""

import json
from pathlib import Path

from .token_types import CustomToken, TokenEnum

# Agrupamento didático dos tipos (`TokenEnum`) em classificações, usado só na
# apresentação da visão analítica — não afeta o tipo real atribuído pelo lexer.
_groups: dict[str, tuple[TokenEnum, ...]] = {
  "Palavra reservada": (
    TokenEnum.KEYWORDS,
    TokenEnum.META_ATTRIBUTES,
    TokenEnum.FUNCTIONAL_COMPLEXES,
    TokenEnum.INTRINSIC_MODES,
  ),
  "Classe": (TokenEnum.CLASS_ID,),
  "Relação": (TokenEnum.RELATION_ID,),
  "Instância": (TokenEnum.INSTANCE_ID,),
  "Estereótipo de classe": (TokenEnum.CLASS_STEREOTYPES,),
  "Estereótipo de relação": (TokenEnum.RELATION_STEREOTYPES,),
  "Tipo nativo": (TokenEnum.NATIVE_TYPES,),
  "Novo tipo": (TokenEnum.NEW_TYPE,),
}

group_by_token_type: dict[TokenEnum, str] = {
  token_type: group
  for group, token_types in _groups.items()
  for token_type in token_types
}


def imprimir_visao_analitica(tokens: list[CustomToken], codigo_fonte: str) -> None:
  """Visão analítica: cada linha do fonte seguida de uma tabela com os tokens que ela gerou."""
  lines = codigo_fonte.splitlines()
  tokens_by_line: dict[int, list[CustomToken]] = {}

  for token in tokens:
    tokens_by_line.setdefault(token.line, []).append(token)

  is_first_line = True

  for line_number, line_tokens in tokens_by_line.items():
    if not is_first_line:
      print()

    is_first_line = False

    print(f'linha {line_number}: "{lines[line_number - 1].strip()}"')
    _print_token_table(line_tokens)


def _print_token_table(tokens: list[CustomToken]) -> None:
  """Tabela com bordas mostrando valor, coluna, tipo e classificação de cada token."""
  header = ("Valor", "Coluna", "Tipo", "Classificação")
  table_rows = [
    (
      token.value,
      str(token.column),
      token.token_type.value,
      group_by_token_type.get(token.token_type, ""),
    )
    for token in tokens
  ]

  column_widths = [
    max(len(header[i]), *(len(row[i]) for row in table_rows)) for i in range(4)
  ]

  def format_border(left: str, middle: str, right: str) -> str:
    return left + middle.join("─" * (width + 2) for width in column_widths) + right

  def format_row(row: tuple[str, ...]) -> str:
    cells = (f" {value.ljust(width)} " for value, width in zip(row, column_widths))
    return "│" + "│".join(cells) + "│"

  print(format_border("┌", "┬", "┐"))
  print(format_row(header))
  print(format_border("├", "┼", "┤"))

  for row in table_rows:
    print(format_row(row))

  print(format_border("└", "┴", "┘"))


def imprimir_erros(erros: list[dict]) -> None:
  """Resumo dos erros léxicos encontrados, agrupados por linha."""
  if not erros:
    print("\nNenhum erro léxico encontrado.")
    return

  print(f"\n--- Erros léxicos ({len(erros)}) ---")

  for erro in erros:
    print(f"  linha {erro['line']}, coluna {erro['column']}: {erro['message']}")


def count_tokens_by_category(tokens: list[CustomToken]) -> dict[TokenEnum, int]:
  """Quantos tokens de cada tipo (`TokenEnum`) foram reconhecidos.

  A ordem do resultado segue a ordem de declaração de `TokenEnum`, não a
  ordem de aparição no código-fonte — mesma preocupação de saída
  determinística que já existe em `lexer_rules.py`.
  """
  count = {category: 0 for category in TokenEnum}

  for token in tokens:
    count[token.token_type] += 1

  return {category: quantity for category, quantity in count.items() if quantity > 0}


def count_tokens_by_group(count: dict[TokenEnum, int]) -> dict[str, int]:
  """Agrega a contagem por tipo na contagem por classificação (`group_by_token_type`).

  A ordem do resultado segue a ordem de declaração de `_groups`.
  """
  group_count = {group: 0 for group in _groups}

  for token_type, quantity in count.items():
    group = group_by_token_type.get(token_type)

    if group is not None:
      group_count[group] += quantity

  return {group: quantity for group, quantity in group_count.items()}


def print_token_count(count: dict[TokenEnum, int]) -> None:
  """Resumo de quantos tokens foram reconhecidos por classificação (tipos sem
  classificação, como símbolos, não entram nesse resumo)."""
  group_count = count_tokens_by_group(count)

  print("\n--- Contagem de tokens por classificação ---")

  for group, quantity in group_count.items():
    print(f"  {group}: {quantity}")

  print(f"\nTotal: {sum(count.values())} tokens")


def export_tokens_json(
  source_path: Path, tokens: list[CustomToken], count: dict[TokenEnum, int]
) -> None:
  """Exporta os tokens e a contagem por tipo para `lexico_analyzer/exports/<nome>.json`."""
  exports_dir = Path(__file__).parent / "exports"
  exports_dir.mkdir(exist_ok=True)

  output_path = exports_dir / f"{source_path.stem}.json"
  data = {
    "tokens": [
      {
        "type": token.token_type.value,
        "value": token.value,
        "line": token.line,
        "column": token.column,
      }
      for token in tokens
    ],
    "token_count": {category.value: quantity for category, quantity in count.items()},
    "total": sum(count.values()),
  }

  output_path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
  )
  print(f"\nTokens e contagem exportados para: {output_path}")
