"""Reconhecimento do padrão Mode

Valida modes que tem characterization/inherence com um endurante.
Também aplica a coerção `kind -> mode`, registra as dependências
externas opcionais e deduz modes sem portador.
"""

from .index import OntologyIndex
from .model import (
  ClassInfo,
  ElementRef,
  ModeMatch,
  ModeReport,
  PatternDiagnostic,
  RelationInfo,
)

PATTERN = "Mode"

MODE_STEREOTYPES = {"mode", "intrisicMode", "extrinsicMode"}
INHERENCE_STEREOTYPES = {"characterization", "inherence"}
EXTERNAL_DEPENDENCE_STEREOTYPES = {"externalDependence"}

# universais endurantes aceitos como portador de um mode
ENDURANTS = {
  "kind",
  "subkind",
  "phase",
  "role",
  "roleMixin",
  "historicalRole",
  "historicalRoleMixin",
  "phaseMixin",
  "category",
  "mixin",
  "collective",
  "quantity",
  "quality",
  "relator",
  "mode",
  "intrisicMode",
  "extrinsicMode",
}

# (portador, relação de inerência)
Host = tuple[ClassInfo, RelationInfo]


def analyze_mode_patterns(index: OntologyIndex) -> ModeReport:
  """
  Analisa os modes do índice e monta o relatório do padrão Mode

  coleta as relações de inerência, valida os endurantes, registra as
  dependências externas e deduz os modes que ficaram sem endurante
  """

  coercions: list[PatternDiagnostic] = []
  deductions: list[PatternDiagnostic] = []
  errors: list[PatternDiagnostic] = []
  matches: list[ModeMatch] = []

  # a coerção precisa vir antes da coleta para que um kind coercido já
  # seja tratado como mode na validação do padrão
  _coerce_kinds_to_mode(index, coercions)

  inherence = _collect_inherence(index)
  external = _collect_external_dependencies(index)

  for info in index.classes.values():
    if info.coerced_stereotype not in MODE_STEREOTYPES:
      continue

    entries = inherence.get(info.name, [])

    # sem nenhuma relação de inerência, o padrão está incompleto
    if not entries:
      deductions.append(_incomplete(info))
      continue

    hosts = _valid_hosts(info, entries, errors)

    if not hosts:
      continue

    dependencies = _unique_refs(external.get(info.name, []))
    lines = {
      info.line,
      *(host.line for host, _ in hosts),
      *(relation.line for _, relation in hosts),
      *(dependency.line for dependency in dependencies),
    }

    matches.append(
      ModeMatch(
        mode=_ref(info),
        hosts=tuple(_ref(host) for host, _ in hosts),
        external_dependencies=tuple(_ref(dependency) for dependency in dependencies),
        lines=tuple(sorted(lines)),
      )
    )

  return ModeReport(
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
  """Cria um diagnóstico do Mode usando linha, coluna e origem do nó"""

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


def _endpoints(
  relation: RelationInfo,
  index: OntologyIndex,
) -> tuple[ClassInfo | None, ClassInfo | None]:
  """Devolve as classes das duas pontas da relação"""

  source_name = _endpoint_source(relation)
  source = index.classes.get(source_name) if source_name is not None else None
  target = index.classes.get(relation.target)

  return source, target


def _can_coerce_to_mode(info: ClassInfo) -> bool:
  """Indica se a classe ainda pode ser coercida de kind para mode"""

  return info.declared_stereotype == "kind" and info.coerced_stereotype == "kind"


def _coerce_kinds_to_mode(
  index: OntologyIndex,
  coercions: list[PatternDiagnostic],
) -> None:
  """
  Coerção `kind -> mode` para kinds que participam de uma inerência

  Se um dos lados já é mode nada é coercido. Se ambos ainda são kind, o lado
  de origem da relação é tratado como o mode e o destino como portador.
  """

  for relation in index.relations:
    if relation.stereotype not in INHERENCE_STEREOTYPES:
      continue

    source, target = _endpoints(relation, index)

    if source is None or target is None:
      continue

    if (
      source.coerced_stereotype in MODE_STEREOTYPES
      or target.coerced_stereotype in MODE_STEREOTYPES
    ):
      continue

    candidates = [info for info in (source, target) if _can_coerce_to_mode(info)]

    if not candidates:
      continue

    # a origem da relação é a convenção para o lado do mode quando ambos ainda são kinds
    chosen = source if source in candidates else candidates[0]
    other = target if chosen is source else source

    chosen.coerced_stereotype = "mode"
    coercions.append(
      _diagnostic(
        "coercion",
        (
          f"classe '{chosen.name}' declarada kind participa de inerência com "
          f"'{other.name}', estereótipo coercido de 'kind' para 'mode'."
        ),
        chosen,
        (
          f"declare '{chosen.name}' explicitamente como 'mode {chosen.name}' "
          "(coerção kind -> mode)."
        ),
      )
    )


def _collect_inherence(index: OntologyIndex) -> dict[str, list[Host]]:
  """Agrupa as relações de inerência por mode"""

  inherence: dict[str, list[Host]] = {}

  for relation in index.relations:
    if relation.stereotype not in INHERENCE_STEREOTYPES:
      continue

    source, target = _endpoints(relation, index)

    if source is not None and source.coerced_stereotype in MODE_STEREOTYPES:
      if target is not None:
        inherence.setdefault(source.name, []).append((target, relation))
      continue

    if target is not None and target.coerced_stereotype in MODE_STEREOTYPES:
      if source is not None:
        inherence.setdefault(target.name, []).append((source, relation))

  return inherence


def _collect_external_dependencies(
  index: OntologyIndex,
) -> dict[str, list[ClassInfo]]:
  """Agrupa as dependências externas opcionais por mode"""

  dependencies: dict[str, list[ClassInfo]] = {}

  for relation in index.relations:
    if relation.stereotype not in EXTERNAL_DEPENDENCE_STEREOTYPES:
      continue

    source, target = _endpoints(relation, index)

    if source is not None and source.coerced_stereotype in MODE_STEREOTYPES:
      if target is not None:
        dependencies.setdefault(source.name, []).append(target)
      continue

    if target is not None and target.coerced_stereotype in MODE_STEREOTYPES:
      if source is not None:
        dependencies.setdefault(target.name, []).append(source)

  return dependencies


def _valid_hosts(
  info: ClassInfo,
  entries: list[Host],
  errors: list[PatternDiagnostic],
) -> list[Host]:
  """Filtra os portadores válidos do mode e reporta os erros não coercíveis"""

  valid: list[Host] = []
  seen: set[str] = set()

  for host, relation in entries:
    if host.name == info.name:
      errors.append(
        _diagnostic(
          "error",
          f"mode '{info.name}' inere ele mesmo.",
          relation,
          ("substitua a inerência por um endurante diferente do próprio mode."),
        )
      )
      continue

    if host.coerced_stereotype not in ENDURANTS:
      errors.append(
        _diagnostic(
          "error",
          (
            f"mode '{info.name}' inere em '{host.name}', que é "
            f"'{host.coerced_stereotype}' e não um endurante."
          ),
          relation,
          (
            f"faça '{info.name}' inerir um endurante, como kind, "
            "subkind, phase, role, collective ou relator."
          ),
        )
      )
      continue

    if host.name in seen:
      continue

    seen.add(host.name)
    valid.append((host, relation))

  return valid


def _unique_refs(infos: list[ClassInfo]) -> list[ClassInfo]:
  """Remove portadores externos repetidos preservando a ordem"""

  unique: list[ClassInfo] = []
  seen: set[tuple[str, int]] = set()

  for info in infos:
    key = (info.name, info.line)

    if key in seen:
      continue

    seen.add(key)
    unique.append(info)

  return unique


def _incomplete(info: ClassInfo) -> PatternDiagnostic:
  """Gera a dedução de mode sem relação de inerência"""

  return _diagnostic(
    "deduction",
    (
      f"mode '{info.name}' não possui relação de inerência "
      "('@characterization' ou '@inherence') com um portador."
    ),
    info,
    (
      f"adicione uma relação de inerência do mode '{info.name}' para um "
      "endurante (dedução do padrão Mode incompleto)."
    ),
  )
