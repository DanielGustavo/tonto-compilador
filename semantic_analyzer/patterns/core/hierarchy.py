from .index import OntologyIndex
from .model import ClassInfo
from .stereotypes import IDENTITY_PROVIDERS, RIGID_SORTALS


def parents(info: ClassInfo, index: OntologyIndex) -> list[ClassInfo]:
  """Devolve os pais de `info` que existem no índice"""

  result: list[ClassInfo] = []

  for name in info.specializes:
    parent = index.classes.get(name)

    if parent is not None:
      result.append(parent)

  return result


def children(
  index: OntologyIndex,
  name: str,
  stereotype: str | None = None,
) -> list[ClassInfo]:
  """Devolve as classes que especializam `name` diretamente"""

  result = [info for info in index.classes.values() if name in info.specializes]

  if stereotype is None:
    return result

  return [info for info in result if info.coerced_stereotype == stereotype]


def rigid_children(index: OntologyIndex, name: str) -> list[ClassInfo]:
  """Devolve os filhos rígidos de `name`"""

  return [
    info for info in children(index, name) if info.coerced_stereotype in RIGID_SORTALS
  ]


def is_subtype(
  name: str,
  ancestor: str,
  index: OntologyIndex,
  seen: set[str] | None = None,
) -> bool:
  """Indica se `name` é subtipo direto ou indireto de `ancestor`"""

  seen = set() if seen is None else seen

  if name in seen:
    return False

  seen.add(name)
  info = index.classes.get(name)

  if info is None:
    return False

  for parent_name in info.specializes:
    if parent_name == ancestor:
      return True

    if is_subtype(parent_name, ancestor, index, seen):
      return True

  return False


def has_inheritance_cycle(
  name: str,
  index: OntologyIndex,
  path: set[str] | None = None,
) -> bool:
  """Verifica se `name` participa de um ciclo de especialização"""

  path = set() if path is None else path

  if name in path:
    return True

  info = index.classes.get(name)

  if info is None:
    return False

  next_path = path | {name}
  return any(
    has_inheritance_cycle(parent, index, next_path) for parent in info.specializes
  )


def has_identity_provider(
  info: ClassInfo,
  index: OntologyIndex,
  seen: set[str] | None = None,
) -> bool:
  """Verifica se `info` alcança direta ou indiretamente um kind/collective"""

  if info.coerced_stereotype in IDENTITY_PROVIDERS:
    return True

  seen = set() if seen is None else seen

  if info.node.name in seen:
    return False

  seen.add(info.node.name)

  for parent_name in info.specializes:
    parent = index.classes.get(parent_name)

    if parent is None:
      return False

    if has_identity_provider(parent, index, seen):
      return True

  return False
