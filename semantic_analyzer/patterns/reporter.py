from table_printer import print_table

from .model import (
  ModeMatch,
  PatternDiagnostic,
  PatternReport,
  PhaseMatch,
  RelatorMatch,
  RoleMatch,
  RoleMixinMatch,
  SubkindMatch,
)


def _origins(match: SubkindMatch) -> str:
  origins: list[str] = []

  for ref in (*match.generals, *match.specifics):
    if ref.origin and ref.origin not in origins:
      origins.append(ref.origin)

  if match.genset is not None and match.genset.origin not in origins:
    origins.append(match.genset.origin)

  return ", ".join(origins) if origins else "-"


def _phase_origins(match: PhaseMatch) -> str:
  origins: list[str] = []

  for ref in (match.general, *match.specifics):
    if ref.origin and ref.origin not in origins:
      origins.append(ref.origin)

  if match.genset is not None and match.genset.origin not in origins:
    origins.append(match.genset.origin)

  return ", ".join(origins) if origins else "-"


def _role_origins(match: RoleMatch) -> str:
  origins: list[str] = []

  for ref in (match.role, *match.generals, *match.relators):
    if ref.origin and ref.origin not in origins:
      origins.append(ref.origin)

  if match.genset is not None and match.genset.origin not in origins:
    origins.append(match.genset.origin)

  return ", ".join(origins) if origins else "-"


def _relator_origins(match: RelatorMatch) -> str:
  origins: list[str] = []

  for ref in (match.relator, *match.mediated, *match.materials):
    if ref.origin and ref.origin not in origins:
      origins.append(ref.origin)

  return ", ".join(origins) if origins else "-"


def _mode_origins(match: ModeMatch) -> str:
  origins: list[str] = []

  for ref in (match.mode, *match.hosts, *match.external_dependencies):
    if ref.origin and ref.origin not in origins:
      origins.append(ref.origin)

  return ", ".join(origins) if origins else "-"


def _role_mixin_origins(match: RoleMixinMatch) -> str:
  origins: list[str] = []

  for ref in (match.role_mixin, *match.roles, *match.relators):
    if ref.origin and ref.origin not in origins:
      origins.append(ref.origin)

  if match.genset is not None and match.genset.origin not in origins:
    origins.append(match.genset.origin)

  return ", ".join(origins) if origins else "-"


def _format_genset(match: SubkindMatch | PhaseMatch) -> str:
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
  phase = report.phase
  role = report.role
  relator = report.relator
  mode = report.mode
  role_mixin = report.role_mixin

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
          _phase_origins(match),
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
          _role_origins(match),
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
          _relator_origins(match),
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
          _mode_origins(match),
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
          _role_mixin_origins(match),
          ", ".join(str(line) for line in match.lines),
        )
        for match in ordered_role_mixins
      ],
      indent="  ",
    )
  else:
    print("  Nenhum padrão RoleMixin encontrado.")

  print("\n(2) ERROS A SEREM CORRIGIDOS POR COERÇÃO")

  if subkind.coercions:
    for coercion in subkind.coercions:
      _print_diagnostic(coercion)

  if phase.coercions:
    for coercion in phase.coercions:
      _print_diagnostic(coercion)

  if role.coercions:
    for coercion in role.coercions:
      _print_diagnostic(coercion)

  if relator.coercions:
    for coercion in relator.coercions:
      _print_diagnostic(coercion)

  if mode.coercions:
    for coercion in mode.coercions:
      _print_diagnostic(coercion)

  if role_mixin.coercions:
    for coercion in role_mixin.coercions:
      _print_diagnostic(coercion)

  if (
    not subkind.coercions
    and not phase.coercions
    and not role.coercions
    and not relator.coercions
    and not mode.coercions
    and not role_mixin.coercions
  ):
    print("  Nenhuma coerção encontrada.")

  print("\n  Erros de padrão não coercíveis:")

  if subkind.errors:
    for error in subkind.errors:
      _print_diagnostic(error)

  if phase.errors:
    for error in phase.errors:
      _print_diagnostic(error)

  if role.errors:
    for error in role.errors:
      _print_diagnostic(error)

  if relator.errors:
    for error in relator.errors:
      _print_diagnostic(error)

  if mode.errors:
    for error in mode.errors:
      _print_diagnostic(error)

  if role_mixin.errors:
    for error in role_mixin.errors:
      _print_diagnostic(error)

  if (
    not subkind.errors
    and not phase.errors
    and not role.errors
    and not relator.errors
    and not mode.errors
    and not role_mixin.errors
  ):
    print("  Nenhum erro de padrão encontrado.")

  print("\n(3) PADRÕES INCOMPLETOS DEDUZIDOS POR SOBRECARGA")

  if subkind.deductions:
    for deduction in subkind.deductions:
      _print_diagnostic(deduction)

  if phase.deductions:
    for deduction in phase.deductions:
      _print_diagnostic(deduction)

  if role.deductions:
    for deduction in role.deductions:
      _print_diagnostic(deduction)

  if relator.deductions:
    for deduction in relator.deductions:
      _print_diagnostic(deduction)

  if mode.deductions:
    for deduction in mode.deductions:
      _print_diagnostic(deduction)

  if role_mixin.deductions:
    for deduction in role_mixin.deductions:
      _print_diagnostic(deduction)

  if (
    not subkind.deductions
    and not phase.deductions
    and not role.deductions
    and not relator.deductions
    and not mode.deductions
    and not role_mixin.deductions
  ):
    print("  Nenhum padrão incompleto deduzido.")
