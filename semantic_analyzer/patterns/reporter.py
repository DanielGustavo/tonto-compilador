from table_printer import print_table

from .core.model import (
  ElementRef,
  PatternDiagnostic,
  PatternReport,
)


def _origins(*groups: tuple[ElementRef, ...], genset: ElementRef | None = None) -> str:
  """Lista os pacotes de origem das referências"""

  origins: list[str] = []

  for group in groups:
    for ref in group:
      if ref.origin and ref.origin not in origins:
        origins.append(ref.origin)

  if genset is not None and genset.origin not in origins:
    origins.append(genset.origin)

  return ", ".join(origins) if origins else "-"


def _format_genset(match) -> str:
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


def _print_diagnostics(
  groups: list[list[PatternDiagnostic]],
  empty_message: str,
) -> None:
  printed = False

  for group in groups:
    for diagnostic in group:
      printed = True
      _print_diagnostic(diagnostic)

  if not printed:
    print(empty_message)


def print_pattern_report(report: PatternReport) -> None:
  subkind = report.subkind
  phase = report.phase
  role = report.role
  relator = report.relator
  mode = report.mode
  role_mixin = report.role_mixin

  results = [subkind, phase, role, relator, mode, role_mixin]

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
          _origins(match.generals, match.specifics, genset=match.genset),
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

  if phase.matches:
    ordered_phases = sorted(phase.matches, key=lambda match: match.lines)
    print_table(
      "Padrões Phase",
      ("General", "Fases", "Genset", "Pacote", "Linhas"),
      [
        (
          match.general.name,
          ", ".join(ref.name for ref in match.specifics),
          _format_genset(match),
          _origins(
            (match.general,),
            match.specifics,
            genset=match.genset,
          ),
          ", ".join(str(line) for line in match.lines),
        )
        for match in ordered_phases
      ],
      indent="  ",
    )
  else:
    print("  Nenhum padrão Phase encontrado.")

  if role.matches:
    ordered_roles = sorted(role.matches, key=lambda match: match.lines)
    print_table(
      "Padrões Role",
      ("Papel", "General", "Relator(es)", "Genset", "Pacote", "Linhas"),
      [
        (
          match.role.name,
          ", ".join(ref.name for ref in match.generals),
          ", ".join(ref.name for ref in match.relators) or "-",
          match.genset.name if match.genset is not None else "-",
          _origins(
            (match.role,),
            match.generals,
            match.relators,
            genset=match.genset,
          ),
          ", ".join(str(line) for line in match.lines),
        )
        for match in ordered_roles
      ],
      indent="  ",
    )
  else:
    print("  Nenhum padrão Role encontrado.")

  if relator.matches:
    ordered_relators = sorted(relator.matches, key=lambda match: match.lines)
    print_table(
      "Padrões Relator",
      ("Variante", "Relator", "Mediados", "Material(is)", "Pacote", "Linhas"),
      [
        (
          str(match.variant),
          match.relator.name,
          ", ".join(ref.name for ref in match.mediated),
          ", ".join(ref.name for ref in match.materials) or "-",
          _origins((match.relator,), match.mediated, match.materials),
          ", ".join(str(line) for line in match.lines),
        )
        for match in ordered_relators
      ],
      indent="  ",
    )
  else:
    print("  Nenhum padrão Relator encontrado.")

  if mode.matches:
    ordered_modes = sorted(mode.matches, key=lambda match: match.lines)
    print_table(
      "Padrões Mode",
      ("Mode", "Portador(es)", "Dependências externas", "Pacote", "Linhas"),
      [
        (
          match.mode.name,
          ", ".join(ref.name for ref in match.hosts),
          ", ".join(ref.name for ref in match.external_dependencies) or "-",
          _origins((match.mode,), match.hosts, match.external_dependencies),
          ", ".join(str(line) for line in match.lines),
        )
        for match in ordered_modes
      ],
      indent="  ",
    )
  else:
    print("  Nenhum padrão Mode encontrado.")

  if role_mixin.matches:
    ordered_role_mixins = sorted(role_mixin.matches, key=lambda match: match.lines)
    print_table(
      "Padrões RoleMixin",
      (
        "Variante",
        "RoleMixin",
        "Papéis",
        "Relator(es)",
        "Genset",
        "Pacote",
        "Linhas",
      ),
      [
        (
          str(match.variant),
          match.role_mixin.name,
          ", ".join(ref.name for ref in match.roles) or "-",
          ", ".join(ref.name for ref in match.relators) or "-",
          match.genset.name if match.genset is not None else "-",
          _origins(
            (match.role_mixin,),
            match.roles,
            match.relators,
            genset=match.genset,
          ),
          ", ".join(str(line) for line in match.lines),
        )
        for match in ordered_role_mixins
      ],
      indent="  ",
    )
  else:
    print("  Nenhum padrão RoleMixin encontrado.")

  print("\n(2) ERROS A SEREM CORRIGIDOS POR COERÇÃO")

  _print_diagnostics(
    [result.coercions for result in results],
    "  Nenhuma coerção encontrada.",
  )

  print("\n  Erros de padrão não coercíveis:")

  _print_diagnostics(
    [result.errors for result in results],
    "  Nenhum erro de padrão encontrado.",
  )

  print("\n(3) PADRÕES INCOMPLETOS DEDUZIDOS POR SOBRECARGA")

  _print_diagnostics(
    [result.deductions for result in results],
    "  Nenhum padrão incompleto deduzido.",
  )
