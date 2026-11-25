from dataclasses import dataclass

from .index import OntologyIndex
from .model import ClassInfo, RelationInfo
from .stereotypes import MEDIATION_STEREOTYPES, RELATOR


@dataclass(frozen=True)
class MediationEdge:
  """Relação orientada do relator para o outro extremo"""

  relator: ClassInfo
  other_name: str
  other: ClassInfo | None
  relation: RelationInfo
  from_material: bool


def relation_endpoints(
  relation: RelationInfo,
  index: OntologyIndex,
) -> tuple[ClassInfo | None, ClassInfo | None]:
  """Devolve as classes das duas pontas da relação, quando existirem"""

  source_name = relation.endpoint_source()
  source = index.classes.get(source_name) if source_name is not None else None
  target = index.classes.get(relation.node.target)

  return source, target


def collect_mediation_edges(
  index: OntologyIndex,
  *,
  both_ways: bool = False,
  require_resolved: bool = True,
) -> list[MediationEdge]:
  """
  Coleta as relações de mediação/material orientadas pelo relator

  `both_ways` replica o comportamento do padrão Role, que considera as duas
  orientações quando os dois extremos são relatores. `require_resolved` exige
  que as duas pontas existam no índice; o Role também aceita o nome de um
  mediado que não foi resolvido.
  """

  edges: list[MediationEdge] = []

  for relation in index.relations:
    if relation.node.stereotype not in MEDIATION_STEREOTYPES:
      continue

    source, target = relation_endpoints(relation, index)

    if require_resolved and (source is None or target is None):
      continue

    source_name = relation.endpoint_source()
    target_name = relation.node.target
    from_material = relation.node.stereotype == "material"

    if source is not None and source.coerced_stereotype == RELATOR:
      if target_name is not None:
        edges.append(
          MediationEdge(source, target_name, target, relation, from_material)
        )

      if (
        both_ways
        and target is not None
        and target.coerced_stereotype == RELATOR
        and source_name is not None
      ):
        edges.append(
          MediationEdge(target, source_name, source, relation, from_material)
        )

    elif target is not None and target.coerced_stereotype == RELATOR:
      if source_name is not None:
        edges.append(
          MediationEdge(target, source_name, source, relation, from_material)
        )

  return edges
