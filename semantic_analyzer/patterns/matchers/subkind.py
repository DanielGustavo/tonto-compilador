"""Reconhecimento do padrão Subkind.

O Subkind é um sortal rígido que especializa outro sortal rígido. Aqui o matcher
cobre as duas variantes do padrão, coerce `kind -> subkind` quando o kind
especializa um sortal rígido e valida a identidade herdada dos subkinds.
"""

from ..core.genset import apply_missing_edges, collect_missing_edges
from ..core.hierarchy import has_identity_provider, has_inheritance_cycle
from ..core.index import OntologyIndex
from ..core.model import PatternDiagnostic, SubkindMatch, SubkindReport
from ..core.stereotypes import RIGID_SORTALS, SUBKIND
from ..core.utils import diagnostic, ref_of

PATTERN = "Subkind"


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
    if info.node.name in resolved or info.node.name in visiting:
      return

    if info.node.stereotype != "kind" or not info.specializes:
      resolved.add(info.node.name)
      return

    if has_inheritance_cycle(info.node.name, index):
      if info.node.name not in reported_cycles:
        reported_cycles.add(info.node.name)
        errors.append(
          diagnostic(
            PATTERN,
            "error",
            (
              f"kind '{info.node.name}' participa de um ciclo de especialização. "
              "Não foi possível coercer kind -> subkind."
            ),
            info,
            "remova o ciclo em 'specializes' antes de analisar o Subkind.",
          )
        )
      resolved.add(info.node.name)
      return

    visiting.add(info.node.name)

    existing = []
    for parent_name in info.specializes:
      parent = index.classes.get(parent_name)

      if parent is None:
        continue

      resolve(parent)
      existing.append(parent)

    visiting.discard(info.node.name)

    invalid = [
      parent for parent in existing if parent.coerced_stereotype not in RIGID_SORTALS
    ]

    if invalid:
      for parent in invalid:
        errors.append(
          diagnostic(
            PATTERN,
            "error",
            (
              f"kind '{info.node.name}' especializa '{parent.node.name}', que é "
              "não-sortal. Não foi possível coercer kind -> subkind."
            ),
            info,
            (
              f"faça '{info.node.name}' especializar um kind, subkind ou "
              "collective, ou remova o 'specializes'."
            ),
          )
        )
    elif existing:
      info.coerced_stereotype = "subkind"
      coercions.append(
        diagnostic(
          PATTERN,
          "coercion",
          (
            f"kind '{info.node.name}' especializa sortal rígido, estereótipo "
            "coercido de 'kind' para 'subkind'."
          ),
          info,
          (
            f"declare '{info.node.name}' explicitamente como 'subkind "
            f"{info.node.name} specializes {', '.join(info.specializes)}' "
            "(coerção kind -> subkind)."
          ),
        )
      )

    resolved.add(info.node.name)

  for info in index.classes.values():
    resolve(info)


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
    general = index.classes.get(genset.node.general)

    # Gensets de Phase/Role (ou cujo general ainda não é sortal rígido) não
    # pertencem ao padrão Subkind.
    if general is None or general.coerced_stereotype not in RIGID_SORTALS:
      continue

    specific_infos = []
    valid = True

    for name in genset.node.specifics:
      info = index.classes.get(name)

      if info is None or info.coerced_stereotype != SUBKIND:
        valid = False
        break

      specific_infos.append(info)

    if not valid:
      continue

    edges_ok, pending = collect_missing_edges(
      genset,
      general,
      specific_infos,
      pattern=PATTERN,
      removal_phrase="remova-o",
      errors=errors,
    )

    disjoint_ok = genset.node.disjointness == "disjoint"

    if not disjoint_ok:
      errors.append(
        diagnostic(
          PATTERN,
          "error",
          f"genset de subkinds '{genset.node.name}' deve ser disjoint.",
          genset,
          (f"declare '{genset.node.name}' como 'disjoint' (opcionalmente 'complete')."),
        )
      )

    if not (edges_ok and disjoint_ok):
      continue

    partition_ok = apply_missing_edges(
      index,
      genset,
      general,
      specific_infos,
      pending,
      pattern=PATTERN,
      specific_subject="o específico",
      stereotype_keyword=SUBKIND,
      deductions=deductions,
      errors=errors,
    )

    if not partition_ok:
      continue

    lines = sorted(
      {
        genset.node.line,
        general.node.line,
        *(info.node.line for info in specific_infos),
      }
    )

    matches.append(
      SubkindMatch(
        variant=2,
        generals=(ref_of(general),),
        specifics=tuple(ref_of(info) for info in specific_infos),
        genset=ref_of(genset),
        lines=tuple(lines),
        disjointness=genset.node.disjointness,
        completeness=genset.node.completeness,
        deduced=bool(pending),
      )
    )

    covered.update(info.node.name for info in specific_infos)


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
    if info.coerced_stereotype != SUBKIND or info.node.name in covered:
      continue

    if not info.specializes:
      errors.append(
        diagnostic(
          PATTERN,
          "error",
          f"subkind '{info.node.name}' não declara nenhum general.",
          info,
          f"adicione 'specializes <General>' à declaração de '{info.node.name}'.",
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
          diagnostic(
            PATTERN,
            "error",
            (
              f"subkind '{info.node.name}' especializa '{parent.node.name}', mas "
              "subkind só pode especializar sortal rígido "
              "(kind, subkind ou collective)."
            ),
            info,
            (f"faça '{info.node.name}' especializar um kind, subkind ou collective."),
          )
        )
      continue

    if not has_identity_provider(info, index):
      errors.append(
        diagnostic(
          PATTERN,
          "error",
          (
            f"subkind '{info.node.name}' não alcança um kind/collective "
            "provedor de identidade."
          ),
          info,
          (
            f"faça '{info.node.name}' especializar direta ou indiretamente um "
            "kind ou collective."
          ),
        )
      )
      continue

    lines = sorted({info.node.line, *(parent.node.line for parent in parents)})

    matches.append(
      SubkindMatch(
        variant=1,
        generals=tuple(ref_of(parent) for parent in parents),
        specifics=(ref_of(info),),
        genset=None,
        lines=tuple(lines),
      )
    )
