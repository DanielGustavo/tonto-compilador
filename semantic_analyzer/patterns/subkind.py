"""Reconhecimento do padrão Subkind.

O Subkind é um sortal rígido que especializa outro sortal rígido. Aqui o matcher
cobre as duas variantes do padrão, coerce `kind -> subkind` quando o kind
especializa um sortal rígido e valida a identidade herdada dos subkinds.
"""

from .index import OntologyIndex
from .model import (
  ElementRef,
  PatternDiagnostic,
  SubkindMatch,
  SubkindReport,
)

PATTERN = "Subkind"

RIGID_SORTALS = {"kind", "subkind", "collective"}
IDENTITY_PROVIDERS = {"kind", "collective"}


def analyze_subkind_patterns(index: OntologyIndex) -> SubkindReport:
  """
  Analisa os subkinds do índice e monta o relatório do padrão Subkind

  Aplica a coerção kind -> subkind e reconhece as duas variantes do padrão,
  validando a identidade herdada e evitando duplicar específicos cobertos
  por um genset.
  """

  coercions: list[PatternDiagnostic] = []
  deductions: list[PatternDiagnostic] = []
  errors: list[PatternDiagnostic] = []
  matches: list[SubkindMatch] = []
  covered: set[str] = set()

  _coerce_declared_kinds(index, coercions, errors)

  # Analisa primeiro a variante 2 (genset de subkinds), que também marca os
  # específicos cobertos para não duplicar na variante 1.
  _variant_two(index, matches, deductions, errors, covered)

  # Depois analisa a variante 1 (subkind especializando um sortal rígido),
  # ignorando os específicos já cobertos por um genset válido.
  _variant_one(index, matches, errors, covered)

  return SubkindReport(
    matches=matches,
    coercions=coercions,
    deductions=deductions,
    errors=errors,
  )


def _ref(info) -> ElementRef:
  """Converte uma classe ou genset em uma referência de relatório"""
  return ElementRef(
    name=info.name,
    line=info.line,
    column=info.column,
    origin=info.origin,
  )


def _diagnostic(
  category: str,
  message: str,
  info,
  suggestion: str | None = None,
) -> PatternDiagnostic:
  """Cria um diagnóstico do Subkind usando linha, coluna e origem do nó"""
  return PatternDiagnostic(
    category=category,
    pattern=PATTERN,
    message=message,
    line=info.line,
    column=info.column,
    origin=info.origin,
    suggestion=suggestion,
  )


def _has_inheritance_cycle(name: str, index: OntologyIndex, path: set[str]) -> bool:
  """Verifica se `name` participa de um ciclo de especialização"""
  if name in path:
    return True

  info = index.classes.get(name)

  if info is None:
    return False

  next_path = path | {name}
  return any(
    _has_inheritance_cycle(parent, index, next_path) for parent in info.specializes
  )


def _coerce_declared_kinds(
  index: OntologyIndex,
  coercions: list[PatternDiagnostic],
  errors: list[PatternDiagnostic],
) -> None:
  """
  Coerção `kind -> subkind` para kinds que especializam um sortal rígido

  Um kind que especializa outro kind, subkind ou collective deixa de ser
  sortal e passa a ser subkind. Ciclos e pais não-sortais são reportados como
  erro.
  """

  resolved: set[str] = set()
  visiting: set[str] = set()
  reported_cycles: set[str] = set()

  def resolve(info) -> None:
    """Resolve recursivamente o estereótipo coercido de `info` e dos seus pais"""
    if info.name in resolved or info.name in visiting:
      return

    if info.declared_stereotype != "kind" or not info.specializes:
      resolved.add(info.name)
      return

    if _has_inheritance_cycle(info.name, index, set()):
      if info.name not in reported_cycles:
        reported_cycles.add(info.name)
        errors.append(
          _diagnostic(
            "error",
            (
              f"kind '{info.name}' participa de um ciclo de especialização. "
              "Não foi possível coercer kind -> subkind."
            ),
            info,
            "remova o ciclo em 'specializes' antes de analisar o Subkind.",
          )
        )
      resolved.add(info.name)
      return

    visiting.add(info.name)

    existing = []
    for parent_name in info.specializes:
      parent = index.classes.get(parent_name)

      if parent is None:
        continue

      resolve(parent)
      existing.append(parent)

    visiting.discard(info.name)

    invalid = [
      parent for parent in existing if parent.coerced_stereotype not in RIGID_SORTALS
    ]

    if invalid:
      for parent in invalid:
        errors.append(
          _diagnostic(
            "error",
            (
              f"kind '{info.name}' especializa '{parent.name}', que é "
              "não-sortal. Não foi possível coercer kind -> subkind."
            ),
            info,
            (
              f"faça '{info.name}' especializar um kind, subkind ou "
              "collective, ou remova o 'specializes'."
            ),
          )
        )
    elif existing:
      info.coerced_stereotype = "subkind"
      coercions.append(
        _diagnostic(
          "coercion",
          (
            f"kind '{info.name}' especializa sortal rígido, estereótipo "
            "coercido de 'kind' para 'subkind'."
          ),
          info,
          (
            f"declare '{info.name}' explicitamente como 'subkind "
            f"{info.name} specializes {', '.join(info.specializes)}' "
            "(coerção kind -> subkind)."
          ),
        )
      )

    resolved.add(info.name)

  for info in index.classes.values():
    resolve(info)


def has_identity_provider(
  info, index: OntologyIndex, seen: set[str] | None = None
) -> bool:
  """
  Verifica se `info` alcança direta ou indiretamente um kind/collective

  Percorre a cadeia de `specializes`. Esses estereótipos são os provedores de
  identidade usados para validar subkinds e roles.
  """

  if info.coerced_stereotype in IDENTITY_PROVIDERS:
    return True

  seen = set() if seen is None else seen

  if info.name in seen:
    return False

  seen.add(info.name)

  for parent_name in info.specializes:
    parent = index.classes.get(parent_name)

    if parent is None:
      return False

    if has_identity_provider(parent, index, seen):
      return True

  return False


# Variante 2 do Subkind pattern: um genset disjoint (opcionalmente complete)
# cujos específicos são subkinds que especializam o mesmo sortal rígido.
def _variant_two(
  index: OntologyIndex,
  matches: list[SubkindMatch],
  deductions: list[PatternDiagnostic],
  errors: list[PatternDiagnostic],
  covered: set[str],
) -> None:
  """
  Reconhece a variante 2: um genset disjoint de subkinds

  O general do genset precisa ser um sortal rígido e os específicos precisam
  ser subkinds que o especializam. Específicos sem `specializes` tem a aresta
  deduzida, e os nomes cobertos são registrados para não repetir na variante 1.
  """

  for genset in index.gensets:
    general = index.classes.get(genset.general)

    # Gensets de Phase/Role (ou cujo general ainda não é sortal rígido) não
    # pertencem ao padrão Subkind.
    if general is None or general.coerced_stereotype not in RIGID_SORTALS:
      continue

    specific_infos = []
    valid = True

    for name in genset.specifics:
      info = index.classes.get(name)

      if info is None or info.coerced_stereotype != "subkind":
        valid = False
        break

      specific_infos.append(info)

    if not valid:
      continue

    pending_deductions = []
    valid = True

    for info in specific_infos:
      if general.name in info.specializes:
        continue

      if not info.specializes:
        pending_deductions.append(info)
        continue

      valid = False
      errors.append(
        _diagnostic(
          "error",
          (
            f"'{info.name}' não especializa o general "
            f"'{general.name}' do genset '{genset.name}'."
          ),
          info,
          (
            f"faça '{info.name}' especializar '{general.name}' ou remova-o "
            f"do genset '{genset.name}'."
          ),
        )
      )

    if genset.disjointness != "disjoint":
      valid = False
      errors.append(
        _diagnostic(
          "error",
          f"genset de subkinds '{genset.name}' deve ser disjoint.",
          genset,
          (f"declare '{genset.name}' como 'disjoint' (opcionalmente 'complete')."),
        )
      )

    if not valid:
      continue

    # As deduções entram temporariamente no índice para que a
    # checagem de identidade dos específicos considere o general. Se o genset
    # não passar na checagem, elas são removidas e nenhuma dedução é reportada.
    for info in pending_deductions:
      info.specializes.append(general.name)

    if not has_identity_provider(general, index):
      valid = False
      errors.append(
        _diagnostic(
          "error",
          (
            f"o general '{general.name}' do genset '{genset.name}' não "
            "alcança um kind/collective provedor de identidade."
          ),
          general,
          (
            f"faça '{general.name}' especializar direta ou indiretamente um "
            "kind ou collective."
          ),
        )
      )

    for info in specific_infos:
      if has_identity_provider(info, index):
        continue

      valid = False
      errors.append(
        _diagnostic(
          "error",
          (
            f"o específico '{info.name}' do genset '{genset.name}' não "
            "alcança um kind/collective provedor de identidade."
          ),
          info,
          (
            f"faça '{info.name}' especializar direta ou indiretamente um "
            "kind ou collective."
          ),
        )
      )

    if not valid:
      for info in pending_deductions:
        info.specializes.remove(general.name)
      continue

    for info in pending_deductions:
      deductions.append(
        _diagnostic(
          "deduction",
          (
            f"'{info.name}' não declara 'specializes "
            f"{general.name}', mas o genset '{genset.name}' o agrupa sob "
            f"'{general.name}'."
          ),
          info,
          (
            f"declare explicitamente 'subkind {info.name} specializes "
            f"{general.name}' (dedução pela sobrecarga do genset)."
          ),
        )
      )

    deduced = bool(pending_deductions)
    lines = sorted(
      {
        genset.line,
        general.line,
        *(info.line for info in specific_infos),
      }
    )

    matches.append(
      SubkindMatch(
        variant=2,
        generals=(_ref(general),),
        specifics=tuple(_ref(info) for info in specific_infos),
        genset=_ref(genset),
        lines=tuple(lines),
        disjointness=genset.disjointness,
        completeness=genset.completeness,
        deduced=deduced,
      )
    )

    covered.update(info.name for info in specific_infos)


# Variante 1 do Subkind pattern: um subkind especializando diretamente um
# sortal rígido (kind, subkind ou collective), sem depender de um genset.
def _variant_one(
  index: OntologyIndex,
  matches: list[SubkindMatch],
  errors: list[PatternDiagnostic],
  covered: set[str],
) -> None:
  """
  Reconhece a variante 1: subkinds que especializam um sortal rígido

  Cada subkind não coberto por um genset precisa especializar diretamente um
  kind, subkind ou collective e alcançar um provedor de identidade.
  """

  for info in index.classes.values():
    if info.coerced_stereotype != "subkind" or info.name in covered:
      continue

    if not info.specializes:
      errors.append(
        _diagnostic(
          "error",
          f"subkind '{info.name}' não declara nenhum general.",
          info,
          f"adicione 'specializes <General>' à declaração de '{info.name}'.",
        )
      )
      continue

    parents = []
    missing = False

    for parent_name in info.specializes:
      parent = index.classes.get(parent_name)

      if parent is None:
        missing = True
        break

      parents.append(parent)

    # Um pai inexistente já é reportado como erro semântico.
    if missing:
      continue

    invalid = [
      parent for parent in parents if parent.coerced_stereotype not in RIGID_SORTALS
    ]

    if invalid:
      for parent in invalid:
        errors.append(
          _diagnostic(
            "error",
            (
              f"subkind '{info.name}' especializa '{parent.name}', mas "
              "subkind só pode especializar sortal rígido "
              "(kind, subkind ou collective)."
            ),
            info,
            (f"faça '{info.name}' especializar um kind, subkind ou collective."),
          )
        )
      continue

    if not has_identity_provider(info, index):
      errors.append(
        _diagnostic(
          "error",
          (
            f"subkind '{info.name}' não alcança um kind/collective "
            "provedor de identidade."
          ),
          info,
          (
            f"faça '{info.name}' especializar direta ou indiretamente um "
            "kind ou collective."
          ),
        )
      )
      continue

    lines = sorted({info.line, *(parent.line for parent in parents)})

    matches.append(
      SubkindMatch(
        variant=1,
        generals=tuple(_ref(parent) for parent in parents),
        specifics=(_ref(info),),
        genset=None,
        lines=tuple(lines),
      )
    )
