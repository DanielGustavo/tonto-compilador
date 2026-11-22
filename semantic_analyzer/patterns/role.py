"""Reconhecimento do padrão Role.

Valida roles que especializam um sortal, que dependem de um relator via
mediação e que respeitam a regra de genset quando há roles irmãos.
"""

from .index import OntologyIndex
from .model import (
  ClassInfo,
  ElementRef,
  GensetInfo,
  PatternDiagnostic,
  RelationInfo,
  RoleMatch,
  RoleReport,
)

PATTERN = "Role"
ROLE_GENERALS = {"kind", "subkind", "collective", "phase", "role", "roleMixin"}
RELATOR = "relator"

Mediation = tuple[ClassInfo, str, RelationInfo]


def analyze_role_patterns(index: OntologyIndex) -> RoleReport:
  """
  Analisa todas as classes `role` e monta o relatório do padrão Role

  Coleta as mediações, valida o general, a dependência relacional e o genset
  de cada role
  """

  coercions: list[PatternDiagnostic] = []
  deductions: list[PatternDiagnostic] = []
  errors: list[PatternDiagnostic] = []
  matches: list[RoleMatch] = []

  mediations = _collect_mediations(index, coercions)

  for info in index.classes.values():
    if info.coerced_stereotype != "role":
      continue

    parent_infos = [
      index.classes[name] for name in info.specializes if name in index.classes
    ]
    valid_generals = [
      parent for parent in parent_infos if parent.coerced_stereotype in ROLE_GENERALS
    ]

    if not valid_generals:
      errors.append(_general_error(info, parent_infos))
      continue

    # Separa as mediações do próprio role das herdadas de um supertipo
    direct = []
    inherited = []

    for mediation in mediations:
      _, mediated, _ = mediation

      if info.name == mediated:
        direct.append(mediation)
      elif _is_subtype(info.name, mediated, index, set()):
        inherited.append(mediation)

    # `relevant` reúne as mediações que sustentam a dependência do role
    # `direct` se o próprio role é mediado, `inherited` se a mediação vem de um
    # supertipo, ou vazio quando não tem dependência relacional
    if direct:
      relevant = direct
      dependency_ok = True
      deduced = False
    elif inherited:
      relevant = inherited
      dependency_ok = True
      deduced = True
      deductions.append(_inherited_dependency(info, inherited))
    else:
      relevant = []
      dependency_ok = False
      deduced = False
      deductions.append(
        _diagnostic(
          "deduction",
          (
            f"role '{info.name}' não possui relator/mediação que sustente a "
            "dependência relacional."
          ),
          info,
          (
            f"adicione um relator com '@mediation' para '{info.name}' "
            "(dedução do padrão Role incompleto)."
          ),
        )
      )

    structural_ok, genset = _check_genset(index, info, valid_generals)

    if not structural_ok:
      generals = ", ".join(general.name for general in valid_generals)
      deductions.append(
        _diagnostic(
          "deduction",
          (
            f"role '{info.name}' possui irmãos role sob o mesmo general "
            f"({generals}) sem um genset que o inclua."
          ),
          info,
          (
            "declare um genset com esse general e inclua "
            f"'{info.name}' em 'specifics' (dedução pela sobrecarga do genset)."
          ),
        )
      )

    if not (dependency_ok and structural_ok):
      continue

    relators = _relator_refs(relevant)
    lines = {
      info.line,
      *(general.line for general in valid_generals),
      *(relator.line for relator in relators),
      *(relation.line for _, _, relation in relevant),
    }

    if genset is not None:
      lines.add(genset.line)

    matches.append(
      RoleMatch(
        role=_ref(info),
        generals=tuple(_ref(general) for general in valid_generals),
        relators=relators,
        genset=_ref(genset) if genset is not None else None,
        lines=tuple(sorted(lines)),
        deduced=deduced,
      )
    )

  return RoleReport(
    matches=matches,
    coercions=coercions,
    deductions=deductions,
    errors=errors,
  )


def _ref(info) -> ElementRef:
  """Converte uma classe, genset ou relação em uma referência de relatório"""
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
  """Cria um diagnóstico do Role usando linha, coluna e origem do nó"""
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


def _is_subtype(
  name: str,
  ancestor: str,
  index: OntologyIndex,
  seen: set[str],
) -> bool:
  """
  Indica se `name` é subtipo direto ou indireto de `ancestor`

  `seen` evita recursão infinita em hierarquias com ciclo
  """
  if name in seen:
    return False

  seen.add(name)
  info = index.classes.get(name)

  if info is None:
    return False

  for parent_name in info.specializes:
    if parent_name == ancestor:
      return True

    if _is_subtype(parent_name, ancestor, index, seen):
      return True

  return False


def _collect_mediations(
  index: OntologyIndex,
  coercions: list[PatternDiagnostic],
) -> list[Mediation]:
  """
  Normaliza as relações do índice em mediações (relator, mediado, relação)

  Aceita `@mediation` diretamente e trata `@material` entre relator e role,
  registrando o diagnóstico de coerção.
  """
  mediations: list[Mediation] = []

  for relation in index.relations:
    source = _endpoint_source(relation)
    target = relation.target
    source_info = index.classes.get(source) if source is not None else None
    target_info = index.classes.get(target)

    if relation.stereotype == "mediation":
      if source_info is not None and source_info.coerced_stereotype == RELATOR:
        mediations.append((source_info, target, relation))

      if target_info is not None and target_info.coerced_stereotype == RELATOR:
        if source is not None:
          mediations.append((target_info, source, relation))

    elif relation.stereotype == "material":
      if (
        source_info is not None
        and source_info.coerced_stereotype == RELATOR
        and target_info is not None
        and target_info.coerced_stereotype == "role"
      ):
        mediations.append((source_info, target, relation))
        coercions.append(_material_coercion(source_info, target, relation))

      elif (
        target_info is not None
        and target_info.coerced_stereotype == RELATOR
        and source_info is not None
        and source_info.coerced_stereotype == "role"
      ):
        mediations.append((target_info, source, relation))
        coercions.append(_material_coercion(target_info, source, relation))

  return mediations


def _material_coercion(
  relator: ClassInfo,
  role_name: str,
  relation: RelationInfo,
) -> PatternDiagnostic:
  """Monta o diagnóstico de coerção de `@material` para `@mediation`."""

  return _diagnostic(
    "coercion",
    (
      f"relação '@material' entre relator '{relator.name}' e role "
      f"'{role_name}' tratada como mediação "
      "(coerção @material -> @mediation)."
    ),
    relation,
    (
      f"declare a relação entre '{relator.name}' e '{role_name}' "
      "explicitamente como '@mediation'."
    ),
  )


def _general_error(
  info: ClassInfo,
  parent_infos: list[ClassInfo],
) -> PatternDiagnostic:
  """Gera o erro de role sem general ou com general fora dos aceitos."""

  if parent_infos:
    invalid = ", ".join(parent.name for parent in parent_infos)
    message = (
      f"role '{info.name}' especializa general inválido ({invalid}); "
      "o padrão Role exige um general kind, subkind, collective, phase, "
      "role ou roleMixin."
    )
  else:
    message = f"role '{info.name}' não declara um general válido para o padrão Role."

  return _diagnostic(
    "error",
    message,
    info,
    (
      f"faça '{info.name}' especializar kind, subkind, collective, phase, "
      "role ou roleMixin."
    ),
  )


def _inherited_dependency(
  info: ClassInfo,
  inherited: list[Mediation],
) -> PatternDiagnostic:
  """Gera a dedução de dependência relacional herdada de um supertipo mediado"""

  supertypes: list[str] = []

  for _, mediated, _ in inherited:
    if mediated not in supertypes:
      supertypes.append(mediated)

  return _diagnostic(
    "deduction",
    (
      f"role '{info.name}' não é mediado diretamente, mas herda a dependência "
      f"relacional do supertipo mediado '{', '.join(supertypes)}'."
    ),
    info,
    (
      f"declare explicitamente '@mediation' para '{info.name}' ou mantenha a "
      "dependência relacional via supertipo."
    ),
  )


def _check_genset(
  index: OntologyIndex,
  info: ClassInfo,
  valid_generals: list[ClassInfo],
) -> tuple[bool, GensetInfo | None]:
  """
  Verifica a regra de genset para os roles irmãos

  Um role sozinho sob o general não precisa genset, mas se houver irmãos é preciso um
  genset que tenha o general e inclua o role. Devolve `(ok, genset)`
  """
  for general in valid_generals:
    siblings = [
      other
      for other in index.classes.values()
      if other.coerced_stereotype == "role" and general.name in other.specializes
    ]

    # `next` devolve o primeiro genset que satisfaz a condição
    genset = next(
      (
        candidate
        for candidate in index.gensets
        if candidate.general == general.name and info.name in candidate.specifics
      ),
      None,
    )

    if len(siblings) == 1 and siblings[0].name == info.name:
      return True, genset

    if genset is not None:
      return True, genset

  return False, None


def _relator_refs(relevant: list[Mediation]) -> tuple[ElementRef, ...]:
  """Devolve as referências dos relatores sem repetir o mesmo relator"""

  refs: list[ElementRef] = []
  seen: set[tuple[str, int]] = set()

  for relator, _, _ in relevant:
    key = (relator.name, relator.line)

    if key in seen:
      continue

    seen.add(key)
    refs.append(_ref(relator))

  return tuple(refs)
