from table_printer import print_table

from .model import PatternDiagnostic, PatternReport, SubkindMatch


def _origins(match: SubkindMatch) -> str:
  origins: list[str] = []

  for ref in (*match.generals, *match.specifics):
    if ref.origin and ref.origin not in origins:
      origins.append(ref.origin)

  if match.genset is not None and match.genset.origin not in origins:
    origins.append(match.genset.origin)

  return ", ".join(origins) if origins else "-"


def _format_genset(match: SubkindMatch) -> str:
  if match.genset is None:
    return "-"

  modifiers = [
    modifier for modifier in (match.disjointness, match.completeness) if modifier
  ]
  suffix = f" [{', '.join(modifiers)}]" if modifiers else ""
  return f"{match.genset.name}{suffix}"


def _print_diagnostic(diagnostic: PatternDiagnostic) -> None:
  print(
    f"  linha {diagnostic.line}, coluna {diagnostic.column} "
    f"[{diagnostic.origin}]: {diagnostic.message}"
  )

  if diagnostic.suggestion:
    print(f"    sugestão: {diagnostic.suggestion}")


def print_pattern_report(report: PatternReport) -> None:
  subkind = report.subkind

  print("\n============ PADRÕES DE PROJETO ============")

  print("\n(1) PADRÕES ENCONTRADOS POR LINHAS DE CÓDIGO")

  if subkind.matches:
    ordered = sorted(subkind.matches, key=lambda match: (match.lines, match.variant))
    print_table(
      "Padrões Subkind",
      ("Variante", "Pacote", "General", "Específicos", "Genset", "Linhas"),
      [
        (
          str(match.variant),
          _origins(match),
          ", ".join(ref.name for ref in match.generals),
          ", ".join(ref.name for ref in match.specifics),
          _format_genset(match),
          ", ".join(str(line) for line in match.lines),
        )
        for match in ordered
      ],
      indent="  ",
    )
  else:
    print("  Nenhum padrão Subkind encontrado.")

  print("\n(2) ERROS A SEREM CORRIGIDOS POR COERÇÃO")

  if subkind.coercions:
    for coercion in subkind.coercions:
      _print_diagnostic(coercion)
  else:
    print("  Nenhuma coerção de Subkind encontrada.")

  print("\n  Erros de padrão não coercíveis:")

  if subkind.errors:
    for error in subkind.errors:
      _print_diagnostic(error)
  else:
    print("  Nenhum erro de padrão Subkind encontrado.")

  print("\n(3) PADRÕES INCOMPLETOS DEDUZIDOS POR SOBRECARGA")

  if subkind.deductions:
    for deduction in subkind.deductions:
      _print_diagnostic(deduction)
  else:
    print("  Nenhum padrão Subkind incompleto deduzido.")
