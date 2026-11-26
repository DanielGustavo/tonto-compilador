"""Reconhecimento do padrão Role.

Valida roles que especializam um sortal, que dependem de um relator via
mediação e que respeitam a regra de genset quando há roles irmãos.
"""

from ..core.hierarchy import children, is_subtype
from ..core.index import OntologyIndex
from ..core.mediation import collect_mediation_edges
from ..core.model import (
  ClassInfo,
  GensetInfo,
  PatternDiagnostic,
  RelationInfo,
  RoleMatch,
  RoleReport,
)
from ..core.stereotypes import ROLE, ROLE_GENERALS
from ..core.utils import diagnostic, ref_of, unique_refs

PATTERN = "Role"

Mediation = tuple[ClassInfo, str, RelationInfo]


def analyze_role_patterns(index: OntologyIndex) -> RoleReport:
  """
  Analisa todas as classes `role` e monta o relatório do padrão Role

  Coleta as mediações, valida o general e o genset de cada role
  """

  coercions: list[PatternDiagnostic] = []
  deductions: list[PatternDiagnostic] = []
  errors: list[PatternDiagnostic] = []
  matches: list[RoleMatch] = []

  mediations = _collect_mediations(index, coercions)

  for info in index.classes.values():
    if info.coerced_stereotype != ROLE:
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

      if info.node.name == mediated:
        direct.append(mediation)
      elif is_subtype(info.node.name, mediated, index):
        inherited.append(mediation)

    # `relevant` reúne as mediações que sustentam a dependência do role
    # `direct` se o próprio role é mediado, `inherited` se a mediação vem de um
    # supertipo, ou vazio quando não tem dependência relacional
    if direct:
      relevant = direct
      deduced = False
    elif inherited:
      relevant = inherited
      deduced = True
      deductions.append(_inherited_dependency(info, inherited))
    else:
      relevant = []
      deduced = False

    structural_ok, genset = _check_genset(index, info, valid_generals)

    if not structural_ok:
      generals = ", ".join(general.node.name for general in valid_generals)
      deductions.append(
        diagnostic(
          PATTERN,
          "deduction",
          (
            f"role '{info.node.name}' possui irmãos role sob o mesmo general "
            f"({generals}) sem um genset que o inclua."
          ),
          info,
          (
            "declare um genset com esse general e inclua "
            f"'{info.node.name}' em 'specifics' (dedução pela sobrecarga do genset)."
          ),
        )
      )

    if not structural_ok:
      continue

    relators = unique_refs([relator for relator, _, _ in relevant])
    lines = {
      info.node.line,
      *(general.node.line for general in valid_generals),
      *(relator.line for relator in relators),
      *(relation.node.line for _, _, relation in relevant),
    }

    if genset is not None:
      lines.add(genset.node.line)

    matches.append(
      RoleMatch(
        role=ref_of(info),
        generals=tuple(ref_of(general) for general in valid_generals),
        relators=relators,
        genset=ref_of(genset) if genset is not None else None,
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

  for edge in collect_mediation_edges(
    index,
    both_ways=True,
    require_resolved=False,
  ):
    if edge.from_material:
      if edge.other is not None and edge.other.coerced_stereotype == ROLE:
        mediations.append((edge.relator, edge.other_name, edge.relation))
        coercions.append(
          _material_coercion(edge.relator, edge.other_name, edge.relation)
        )
    else:
      mediations.append((edge.relator, edge.other_name, edge.relation))

  return mediations


def _material_coercion(
  relator: ClassInfo,
  role_name: str,
  relation: RelationInfo,
) -> PatternDiagnostic:
  """Monta o diagnóstico de coerção de `@material` para `@mediation`."""

  return diagnostic(
    PATTERN,
    "coercion",
    (
      f"relação '@material' entre relator '{relator.node.name}' e role "
      f"'{role_name}' tratada como mediação "
      "(coerção @material -> @mediation)."
    ),
    relation,
    (
      f"declare a relação entre '{relator.node.name}' e '{role_name}' "
      "explicitamente como '@mediation'."
    ),
  )


def _general_error(
  info: ClassInfo,
  parent_infos: list[ClassInfo],
) -> PatternDiagnostic:
  """Gera o erro de role sem general ou com general fora dos aceitos."""

  if parent_infos:
    invalid = ", ".join(parent.node.name for parent in parent_infos)
    message = (
      f"role '{info.node.name}' especializa general inválido ({invalid}); "
      "o padrão Role exige um general kind, subkind, collective, phase, "
      "role ou roleMixin."
    )
  else:
    message = (
      f"role '{info.node.name}' não declara um general válido para o padrão Role."
    )

  return diagnostic(
    PATTERN,
    "error",
    message,
    info,
    (
      f"faça '{info.node.name}' especializar kind, subkind, collective, phase, "
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

  return diagnostic(
    PATTERN,
    "deduction",
    (
      f"role '{info.node.name}' não é mediado diretamente, mas herda a dependência "
      f"relacional do supertipo mediado '{', '.join(supertypes)}'."
    ),
    info,
    (
      f"declare explicitamente '@mediation' para '{info.node.name}' ou mantenha a "
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
    siblings = children(index, general.node.name, stereotype=ROLE)

    # `next` devolve o primeiro genset que satisfaz a condição
    genset = next(
      (
        candidate
        for candidate in index.gensets
        if candidate.node.general == general.node.name
        and info.node.name in candidate.node.specifics
      ),
      None,
    )

    if len(siblings) == 1 and siblings[0].node.name == info.node.name:
      return True, genset

    if genset is not None:
      return True, genset

  return False, None
