"""Reconhecimento do padrão Relator.

Valida relatores que tem mediation com pelo menos dois universais substanciais.
A variante 1 tem apenas as mediações, a variante 2 acrescenta uma relação
material entre os mediados. O matcher também aplica as coerções
`kind -> relator` e `@material -> @mediation` e deduz mediações faltantes a
partir das materiais.
"""

from ..core.index import OntologyIndex
from ..core.mediation import collect_mediation_edges, relation_endpoints
from ..core.model import (
  ClassInfo,
  PatternDiagnostic,
  RelationInfo,
  RelatorMatch,
  RelatorReport,
)
from ..core.stereotypes import RELATOR, SUBSTANTIALS
from ..core.utils import diagnostic, ref_of

PATTERN = "Relator"

MIN_MEDIATED = 2

# (universal substancial mediado, relação que sustenta a mediação ou None)
Mediation = tuple[ClassInfo, RelationInfo | None]
# (origem, destino, relação material)
DerivedMaterial = tuple[str, str, RelationInfo]


def analyze_relator_patterns(index: OntologyIndex) -> RelatorReport:
  """
  Analisa os relatores do índice e monta o relatório do padrão Relator

  coleta as mediações, valida os universais substanciais mediados, completa as mediações
  faltantes com os materials e classifica cada relator em variante 1 ou 2
  """

  coercions: list[PatternDiagnostic] = []
  deductions: list[PatternDiagnostic] = []
  errors: list[PatternDiagnostic] = []
  matches: list[RelatorMatch] = []

  _coerce_kinds_to_relator(index, coercions)

  mediations = _collect_mediations(index, coercions)
  derived = _derived_materials(index)

  for info in index.classes.values():
    if info.coerced_stereotype != RELATOR:
      continue

    mediated = _valid_mediations(info, mediations.get(info.node.name, []), errors)

    # só tenta completar quando falta mediação: em um relator já completo a
    # material pode pertencer a outro relator
    deduced_names: set[str] = set()

    if len(mediated) < MIN_MEDIATED:
      deduced_names = _deduce_missing_mediations(
        info, mediated, derived, index, deductions
      )

    if len(mediated) < MIN_MEDIATED:
      deductions.append(_incomplete(info, len(mediated)))
      continue

    materials = [
      relation
      for source, target, relation in derived
      if source in mediated and target in mediated
    ]

    mediated_refs = tuple(ref_of(index.classes[name]) for name in mediated)
    material_refs = tuple(ref_of(relation) for relation in materials)

    lines = {
      info.node.line,
      *(ref.line for ref in mediated_refs),
      *(
        entry.node.line
        for entries in mediated.values()
        for _, entry in entries
        if entry is not None
      ),
      *(relation.node.line for relation in materials),
    }

    matches.append(
      RelatorMatch(
        variant=2 if materials else 1,
        relator=ref_of(info),
        mediated=mediated_refs,
        materials=material_refs,
        lines=tuple(sorted(lines)),
        deduced=bool(deduced_names),
      )
    )

  return RelatorReport(
    matches=matches,
    coercions=coercions,
    deductions=deductions,
    errors=errors,
  )


def _coerce_kinds_to_relator(
  index: OntologyIndex,
  coercions: list[PatternDiagnostic],
) -> None:
  """
  Coerção `kind -> relator` para kinds que medeiam dois ou mais universais substanciais
  """

  count: dict[str, set[str]] = {}

  for relation in index.relations:
    if relation.node.stereotype != "mediation":
      continue

    source_info, target_info = relation_endpoints(relation, index)

    if source_info is None or target_info is None:
      continue

    if target_info.coerced_stereotype not in SUBSTANTIALS:
      continue

    if source_info.node.name == target_info.node.name:
      continue

    count.setdefault(source_info.node.name, set()).add(target_info.node.name)

  for info in index.classes.values():
    if info.coerced_stereotype != "kind":
      continue

    endpoints = count.get(info.node.name, set())

    if len(endpoints) < MIN_MEDIATED:
      continue

    info.coerced_stereotype = RELATOR
    coercions.append(
      diagnostic(
        PATTERN,
        "coercion",
        (
          f"classe '{info.node.name}' declarada kind medeia {len(endpoints)} "
          "universais substanciais, estereótipo coercido de 'kind' para "
          "'relator'."
        ),
        info,
        (
          f"declare '{info.node.name}' explicitamente como 'relator "
          f"{info.node.name}' (coerção kind -> relator)."
        ),
      )
    )


def _collect_mediations(
  index: OntologyIndex,
  coercions: list[PatternDiagnostic],
) -> dict[str, list[Mediation]]:
  """Agrupa as mediações por relator"""

  mediations: dict[str, list[Mediation]] = {}

  for edge in collect_mediation_edges(index):
    other = edge.other

    if other is None:
      continue

    mediations.setdefault(edge.relator.node.name, []).append((other, edge.relation))

    if edge.from_material:
      _coerce_material(edge.relator, other, edge.relation, coercions)

  return mediations


def _coerce_material(
  relator: ClassInfo,
  other: ClassInfo,
  relation: RelationInfo,
  coercions: list[PatternDiagnostic],
) -> None:
  """Registra `@material -> @mediation`"""

  if other.coerced_stereotype not in SUBSTANTIALS:
    return

  if other.coerced_stereotype == "role":
    return

  coercions.append(
    diagnostic(
      PATTERN,
      "coercion",
      (
        f"relação '@material' entre relator '{relator.node.name}' e universal "
        f"substancial '{other.node.name}' tratada como mediação "
        "(coerção @material -> @mediation)."
      ),
      relation,
      (
        f"declare a relação entre '{relator.node.name}' e '{other.node.name}' "
        "explicitamente como '@mediation'."
      ),
    )
  )


def _derived_materials(index: OntologyIndex) -> list[DerivedMaterial]:
  """Lista os materials entre universais substanciais"""

  materials: list[DerivedMaterial] = []

  for relation in index.relations:
    if relation.node.stereotype != "material":
      continue

    source_info, target_info = relation_endpoints(relation, index)

    if source_info is None or target_info is None:
      continue

    if source_info.coerced_stereotype == RELATOR:
      continue

    if target_info.coerced_stereotype == RELATOR:
      continue

    if source_info.node.name == target_info.node.name:
      continue

    materials.append((source_info.node.name, target_info.node.name, relation))

  return materials


def _valid_mediations(
  info: ClassInfo,
  entries: list[Mediation],
  errors: list[PatternDiagnostic],
) -> dict[str, list[tuple[ClassInfo, RelationInfo | None]]]:
  """
  Filtra as mediações válidas do relator e reporta os erros não coercíveis
  """

  valid: dict[str, list[tuple[ClassInfo, RelationInfo | None]]] = {}

  for mediated, relation in entries:
    if mediated.node.name == info.node.name:
      errors.append(
        diagnostic(
          PATTERN,
          "error",
          f"relator '{info.node.name}' medeia a si mesmo.",
          relation if relation is not None else info,
          (
            "substitua a auto mediação por um universal substancial distinto "
            "do próprio relator."
          ),
        )
      )
      continue

    if mediated.coerced_stereotype not in SUBSTANTIALS:
      errors.append(
        diagnostic(
          PATTERN,
          "error",
          (
            f"relator '{info.node.name}' medeia '{mediated.node.name}', que é "
            f"'{mediated.coerced_stereotype}' e não um universal substancial "
            "válido para mediação."
          ),
          relation if relation is not None else mediated,
          (
            f"faça '{info.node.name}' mediar kind, subkind, phase, role, roleMixin, "
            "collective, category ou mixin."
          ),
        )
      )
      continue

    valid.setdefault(mediated.node.name, []).append((mediated, relation))

  return valid


def _deduce_missing_mediations(
  info: ClassInfo,
  mediated: dict[str, list[tuple[ClassInfo, RelationInfo | None]]],
  derived: list[DerivedMaterial],
  index: OntologyIndex,
  deductions: list[PatternDiagnostic],
) -> set[str]:
  """
  Deduz a mediação faltante a partir de um material

  Se um material tem um extremo mediado e o outro não, o extremo ausente
  também precisa ser mediado pelo relator
  """

  deduced: set[str] = set()
  changed = True

  while changed:
    changed = False

    for source, target, relation in derived:
      endpoints = {source, target}
      # interseção entre os nomes dos extremos da material que já estão em `mediated`.
      present = endpoints & set(mediated)

      if len(present) != 1:
        continue

      # só um extremo está mediado: o outro é o que falta.
      missing = source

      if source in present:
        missing = target

      missing_info = index.classes.get(missing)

      if missing_info is None:
        continue

      if missing_info.coerced_stereotype not in SUBSTANTIALS:
        continue

      mediated.setdefault(missing, []).append((missing_info, relation))
      deduced.add(missing)
      deductions.append(
        diagnostic(
          PATTERN,
          "deduction",
          (
            f"relator '{info.node.name}' não declara mediação para "
            f"'{missing_info.node.name}', mas a relação '@material' entre "
            f"'{source}' e '{target}' deriva desse relator."
          ),
          relation,
          (
            f"adicione '{{ @mediation {missing_info.node.name} }}' ao relator "
            f"'{info.node.name}' (dedução pela sobrecarga da material derivada)."
          ),
        )
      )
      changed = True

  return deduced


def _incomplete(info: ClassInfo, count: int) -> PatternDiagnostic:
  """Gera a dedução de relator que não medeia substanciais suficientes"""

  return diagnostic(
    PATTERN,
    "deduction",
    (
      f"relator '{info.node.name}' medeia {count} universal(is) substancial(is) "
      "distinto(s); "
      f"o padrão Relator exige pelo menos {MIN_MEDIATED}."
    ),
    info,
    (
      f"acrescente pelo menos {MIN_MEDIATED - count} mediação(ões) '@mediation' "
      f"ao relator '{info.node.name}' para completar o padrão."
    ),
  )
