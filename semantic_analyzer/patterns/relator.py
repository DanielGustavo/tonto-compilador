"""Reconhecimento do padrão Relator.

Valida relatores que tem mediation com pelo menos dois universais substanciais.
A variante 1 tem apenas as mediações, a variante 2 acrescenta uma relação
material entre os mediados. O matcher também aplica as coerções
`kind -> relator` e `@material -> @mediation` e deduz mediações faltantes a
partir das materiais.
"""

from .index import OntologyIndex
from .model import (
  ClassInfo,
  ElementRef,
  PatternDiagnostic,
  RelationInfo,
  RelatorMatch,
  RelatorReport,
)

PATTERN = "Relator"

RELATOR = "relator"
SUBSTANTIALS = {
  "kind",
  "subkind",
  "phase",
  "role",
  "roleMixin",
  "collective",
  "category",
  "mixin",
}
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

    mediated = _valid_mediations(info, mediations.get(info.name, []), errors)

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

    mediated_refs = tuple(_ref(index.classes[name]) for name in mediated)
    material_refs = tuple(_ref(relation) for relation in materials)

    lines = {
      info.line,
      *(ref.line for ref in mediated_refs),
      *(
        entry.line
        for entries in mediated.values()
        for _, entry in entries
        if entry is not None
      ),
      *(relation.line for relation in materials),
    }

    matches.append(
      RelatorMatch(
        variant=2 if materials else 1,
        relator=_ref(info),
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


def _ref(info) -> ElementRef:
  """Converte uma classe ou relação em uma referência de relatório"""

  name = info.name

  if name is None:
    name = "anônima"

  return ElementRef(
    name=name,
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
  """Cria um diagnóstico do Relator usando linha, coluna e origem do nó"""

  return PatternDiagnostic(
    category=category,
    pattern=PATTERN,
    message=message,
    line=info.line,
    column=info.column,
    origin=info.origin,
    suggestion=suggestion,
  )


def _endpoint_source(relation: RelationInfo) -> str | None:
  """Devolve o lado de origem: `source` explícito ou `owner` da relação interna"""

  return relation.source if relation.source is not None else relation.owner


def _coerce_kinds_to_relator(
  index: OntologyIndex,
  coercions: list[PatternDiagnostic],
) -> None:
  """
  Coerção `kind -> relator` para kinds que medeiam dois ou mais universais substanciais
  """

  count: dict[str, set[str]] = {}

  for relation in index.relations:
    if relation.stereotype != "mediation":
      continue

    source = _endpoint_source(relation)
    source_info = index.classes.get(source) if source is not None else None
    target_info = index.classes.get(relation.target)

    if source_info is None or target_info is None:
      continue

    if target_info.coerced_stereotype not in SUBSTANTIALS:
      continue

    if source_info.name == target_info.name:
      continue

    count.setdefault(source_info.name, set()).add(target_info.name)

  for info in index.classes.values():
    if info.coerced_stereotype != "kind":
      continue

    endpoints = count.get(info.name, set())

    if len(endpoints) < MIN_MEDIATED:
      continue

    info.coerced_stereotype = RELATOR
    coercions.append(
      _diagnostic(
        "coercion",
        (
          f"classe '{info.name}' declarada kind medeia {len(endpoints)} "
          "universais substanciais, estereótipo coercido de 'kind' para "
          "'relator'."
        ),
        info,
        (
          f"declare '{info.name}' explicitamente como 'relator "
          f"{info.name}' (coerção kind -> relator)."
        ),
      )
    )


def _collect_mediations(
  index: OntologyIndex,
  coercions: list[PatternDiagnostic],
) -> dict[str, list[Mediation]]:
  """Agrupa as mediações por relator"""

  mediations: dict[str, list[Mediation]] = {}

  for relation in index.relations:
    source = _endpoint_source(relation)
    source_info = index.classes.get(source) if source is not None else None
    target_info = index.classes.get(relation.target)

    if relation.stereotype == "mediation":
      if (
        source_info is not None
        and source_info.coerced_stereotype == RELATOR
        and target_info is not None
      ):
        mediations.setdefault(source_info.name, []).append((target_info, relation))
      elif (
        target_info is not None
        and target_info.coerced_stereotype == RELATOR
        and source_info is not None
      ):
        mediations.setdefault(target_info.name, []).append((source_info, relation))

    elif relation.stereotype == "material":
      if source_info is not None and source_info.coerced_stereotype == RELATOR:
        if target_info is not None:
          mediations.setdefault(source_info.name, []).append((target_info, relation))
          _coerce_material(source_info, target_info, relation, coercions)

      elif target_info is not None and target_info.coerced_stereotype == RELATOR:
        if source_info is not None:
          mediations.setdefault(target_info.name, []).append((source_info, relation))
          _coerce_material(target_info, source_info, relation, coercions)

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
    _diagnostic(
      "coercion",
      (
        f"relação '@material' entre relator '{relator.name}' e universal "
        f"substancial '{other.name}' tratada como mediação "
        "(coerção @material -> @mediation)."
      ),
      relation,
      (
        f"declare a relação entre '{relator.name}' e '{other.name}' "
        "explicitamente como '@mediation'."
      ),
    )
  )


def _derived_materials(index: OntologyIndex) -> list[DerivedMaterial]:
  """Lista os materials entre universais substanciais"""

  materials: list[DerivedMaterial] = []

  for relation in index.relations:
    if relation.stereotype != "material":
      continue

    source = _endpoint_source(relation)
    source_info = index.classes.get(source) if source is not None else None
    target_info = index.classes.get(relation.target)

    if source_info is None or target_info is None:
      continue

    if source_info.coerced_stereotype == RELATOR:
      continue

    if target_info.coerced_stereotype == RELATOR:
      continue

    if source_info.name == target_info.name:
      continue

    materials.append((source_info.name, target_info.name, relation))

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
    if mediated.name == info.name:
      errors.append(
        _diagnostic(
          "error",
          f"relator '{info.name}' medeia a si mesmo.",
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
        _diagnostic(
          "error",
          (
            f"relator '{info.name}' medeia '{mediated.name}', que é "
            f"'{mediated.coerced_stereotype}' e não um universal substancial "
            "válido para mediação."
          ),
          relation if relation is not None else mediated,
          (
            f"faça '{info.name}' mediar kind, subkind, phase, role, roleMixin, "
            "collective, category ou mixin."
          ),
        )
      )
      continue

    valid.setdefault(mediated.name, []).append((mediated, relation))

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
        _diagnostic(
          "deduction",
          (
            f"relator '{info.name}' não declara mediação para "
            f"'{missing_info.name}', mas a relação '@material' entre "
            f"'{source}' e '{target}' deriva desse relator."
          ),
          relation,
          (
            f"adicione '{{ @mediation {missing_info.name} }}' ao relator "
            f"'{info.name}' (dedução pela sobrecarga da material derivada)."
          ),
        )
      )
      changed = True

  return deduced


def _incomplete(info: ClassInfo, count: int) -> PatternDiagnostic:
  """Gera a dedução de relator que não medeia substanciais suficientes"""

  return _diagnostic(
    "deduction",
    (
      f"relator '{info.name}' medeia {count} universal(is) substancial(is) "
      "distinto(s); "
      f"o padrão Relator exige pelo menos {MIN_MEDIATED}."
    ),
    info,
    (
      f"acrescente pelo menos {MIN_MEDIATED - count} mediação(ões) '@mediation' "
      f"ao relator '{info.name}' para completar o padrão."
    ),
  )
