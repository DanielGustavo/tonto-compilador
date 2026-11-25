"""Reconhecimento do padrão RoleMixin.

O RoleMixin agrupa roles de kinds diferentes e depende de um relator. Aqui o
matcher confere os roles, o genset opcional e a dependência relacional, e
também converte category/mixin em roleMixin quando só há roles.
"""

from .index import OntologyIndex
from .model import (
  ClassInfo,
  ElementRef,
  GensetInfo,
  PatternDiagnostic,
  RelationInfo,
  RoleMixinMatch,
  RoleMixinReport,
)
from .subkind import has_identity_provider

PATTERN = "RoleMixin"
ROLE_MIXIN = "roleMixin"
ROLE = "role"
RIGID_SORTALS = {"kind", "subkind", "collective"}
MIXIN_STEREOTYPES = {"category", "mixin"}
MIN_ROLES = 2

Mediation = tuple[ClassInfo, RelationInfo]


def analyze_role_mixin_patterns(index: OntologyIndex) -> RoleMixinReport:
  """
  Analisa os roleMixins do índice e monta o relatório do padrão RoleMixin

  Aplica a coerção category/mixin -> roleMixin, valida a partição de roles,
  checa a identidade dos roles e a dependência relacional do roleMixin
  """

  coercions: list[PatternDiagnostic] = []
  deductions: list[PatternDiagnostic] = []
  errors: list[PatternDiagnostic] = []
  matches: list[RoleMixinMatch] = []

  # A coerção precisa vir antes da coleta para que a classe já seja tratada
  # como roleMixin na validação do padrão.
  _coerce_mixins_to_role_mixin(index, coercions)

  mediations = _collect_mediations(index)

  for info in index.classes.values():
    if info.coerced_stereotype != ROLE_MIXIN:
      continue

    # roleMixin é anti-rígido: não pode ser supertipo de um universal rígido
    rigid_children = _rigid_children(index, info.node.name)

    if rigid_children:
      for child in rigid_children:
        errors.append(_rigid_child_error(info, child))

      continue

    parent_mixins = _parent_role_mixins(index, info)
    roles, genset, pending, genset_ok = _validate_genset(
      index, info, _role_children(index, info.node.name), errors
    )

    if not genset_ok:
      continue

    # sem roles e sem ancestral roleMixin, o padrão está incompleto
    if not roles and not parent_mixins:
      deductions.append(_no_roles(info))
      continue

    identity_errors = _identity_errors(index, info, roles)

    if identity_errors:
      errors.extend(identity_errors)
      continue

    relevant, ancestor = _find_dependence(info, index, mediations)

    # roleMixin sem relator/mediação está incompleto
    if not relevant:
      deductions.append(_no_dependence(info))
      continue

    if ancestor != info.node.name:
      deductions.append(_inherited_dependence(info, ancestor))

    for role in pending:
      deductions.append(_deduced_edge(role, info, genset))

    relators = _relator_refs(relevant)
    lines = {
      info.node.line,
      *(role.node.line for role in roles),
      *(relator.node.line for relator, _ in relevant),
      *(relation.node.line for _, relation in relevant),
    }

    if genset is not None:
      lines.add(genset.node.line)

    matches.append(
      RoleMixinMatch(
        variant=1 if parent_mixins else 2,
        role_mixin=_ref(info),
        roles=tuple(_ref(role) for role in roles),
        relators=relators,
        genset=_ref(genset) if genset is not None else None,
        lines=tuple(sorted(lines)),
        deduced=bool(pending) or ancestor != info.node.name,
      )
    )

  return RoleMixinReport(
    matches=matches,
    coercions=coercions,
    deductions=deductions,
    errors=errors,
  )


def _ref(info) -> ElementRef:
  """Converte uma classe ou genset em uma referência de relatório"""
  return ElementRef(
    name=info.node.name,
    line=info.node.line,
    column=info.node.column,
    origin=info.origin,
  )


def _diagnostic(
  category: str,
  message: str,
  info,
  suggestion: str | None = None,
) -> PatternDiagnostic:
  """Cria um diagnóstico do RoleMixin usando linha, coluna e origem do nó"""
  return PatternDiagnostic(
    category=category,
    pattern=PATTERN,
    message=message,
    line=info.node.line,
    column=info.node.column,
    origin=info.origin,
    suggestion=suggestion,
  )


def _endpoint_source(relation: RelationInfo) -> str | None:
  """Devolve o lado de origem: `source` explícito ou `owner` da relação interna"""
  return relation.node.source if relation.node.source is not None else relation.owner


def _children(index: OntologyIndex, name: str) -> list[ClassInfo]:
  """Devolve as classes que especializam `name` diretamente"""
  return [info for info in index.classes.values() if name in info.specializes]


def _role_children(index: OntologyIndex, name: str) -> list[ClassInfo]:
  """Devolve os roles que especializam `name` diretamente"""
  return [child for child in _children(index, name) if child.coerced_stereotype == ROLE]


def _rigid_children(index: OntologyIndex, name: str) -> list[ClassInfo]:
  """Devolve os filhos rígidos de `name`, que são inválidos sob um roleMixin"""
  return [
    child
    for child in _children(index, name)
    if child.coerced_stereotype in RIGID_SORTALS
  ]


def _parent_role_mixins(index: OntologyIndex, info: ClassInfo) -> list[ClassInfo]:
  """Devolve os ancestrais diretos de `info` que são roleMixin"""
  parents: list[ClassInfo] = []

  for parent_name in info.specializes:
    parent = index.classes.get(parent_name)

    if parent is None or parent.node.name == info.node.name:
      continue

    if parent.coerced_stereotype == ROLE_MIXIN:
      parents.append(parent)

  return parents


def _coerce_mixins_to_role_mixin(
  index: OntologyIndex,
  coercions: list[PatternDiagnostic],
) -> None:
  """
  Coerção `category`/`mixin -> roleMixin` para mixins que só agregam roles
  """

  for info in index.classes.values():
    if info.coerced_stereotype not in MIXIN_STEREOTYPES:
      continue

    children = _children(index, info.node.name)

    if not children:
      continue

    if not all(child.coerced_stereotype == ROLE for child in children):
      continue

    declared = info.coerced_stereotype
    info.coerced_stereotype = ROLE_MIXIN
    names = ", ".join(child.node.name for child in children)
    coercions.append(
      _diagnostic(
        "coercion",
        (
          f"classe '{info.node.name}' declarada '{declared}' agrega apenas roles "
          f"({names}), estereótipo coercido de '{declared}' para 'roleMixin'."
        ),
        info,
        (
          f"declare '{info.node.name}' explicitamente como 'roleMixin {info.node.name}' "
          f"(coerção {declared} -> roleMixin)."
        ),
      )
    )


def _collect_mediations(index: OntologyIndex) -> dict[str, list[Mediation]]:
  """
  Agrupa as mediações por roleMixin

  Aceita `@mediation` diretamente e `@material` entre relator e roleMixin como
  dependência. A coerção `@material -> @mediation` é reportada pelo padrão
  Relator, então aqui ela não é duplicada.
  """
  mediations: dict[str, list[Mediation]] = {}

  for relation in index.relations:
    if relation.node.stereotype not in {"mediation", "material"}:
      continue

    source = _endpoint_source(relation)
    source_info = index.classes.get(source) if source is not None else None
    target_info = index.classes.get(relation.node.target)

    if source_info is None or target_info is None:
      continue

    if (
      source_info.coerced_stereotype == "relator"
      and target_info.coerced_stereotype == ROLE_MIXIN
    ):
      mediations.setdefault(target_info.node.name, []).append((source_info, relation))

    elif (
      target_info.coerced_stereotype == "relator"
      and source_info.coerced_stereotype == ROLE_MIXIN
    ):
      mediations.setdefault(source_info.node.name, []).append((target_info, relation))

  return mediations


def _find_dependence(
  info: ClassInfo,
  index: OntologyIndex,
  mediations: dict[str, list[Mediation]],
  seen: set[str] | None = None,
) -> tuple[list[Mediation], str | None]:
  """
  Procura a dependência relacional direta ou herdada de um roleMixin

  Devolve as mediações relevantes e o nome do roleMixin onde a dependência
  foi encontrada
  """

  seen = set() if seen is None else seen

  if info.node.name in seen:
    return [], None

  seen = seen | {info.node.name}
  direct = mediations.get(info.node.name, [])

  if direct:
    return direct, info.node.name

  for parent in _parent_role_mixins(index, info):
    inherited, ancestor = _find_dependence(parent, index, mediations, seen)

    if inherited:
      return inherited, ancestor

  return [], None


def _relator_refs(relevant: list[Mediation]) -> tuple[ElementRef, ...]:
  """Devolve as referências dos relatores sem repetir o mesmo relator"""
  refs: list[ElementRef] = []
  seen: set[tuple[str, int]] = set()

  for relator, _ in relevant:
    key = (relator.node.name, relator.node.line)

    if key in seen:
      continue

    seen.add(key)
    refs.append(_ref(relator))

  return tuple(refs)


def _validate_genset(
  index: OntologyIndex,
  info: ClassInfo,
  direct_roles: list[ClassInfo],
  errors: list[PatternDiagnostic],
) -> tuple[list[ClassInfo], GensetInfo | None, list[ClassInfo], bool]:
  """
  Valida o genset opcional de roles de um roleMixin

  Devolve `(roles, genset, arestas_pendentes, válido)`. Um role sem
  `specializes` tem a aresta deduzida apenas quando o genset é válido.
  """

  candidates = [genset for genset in index.gensets if genset.node.general == info.node.name]

  if not candidates:
    return list(direct_roles), None, [], True

  for genset in candidates:
    specific_infos: list[ClassInfo] = []
    valid = True

    for name in genset.node.specifics:
      specific = index.classes.get(name)

      if specific is None:
        valid = False
        errors.append(
          _diagnostic(
            "error",
            (
              f"genset de roles '{genset.node.name}' referencia a classe "
              f"inexistente '{name}'."
            ),
            genset,
            f"declare '{name}' ou remova-o do genset '{genset.node.name}'.",
          )
        )
        continue

      if specific.coerced_stereotype != ROLE:
        valid = False
        errors.append(
          _diagnostic(
            "error",
            (
              f"genset de roles '{genset.node.name}' do roleMixin '{info.node.name}' "
              f"mistura roles com '{specific.node.name}' "
              f"('{specific.coerced_stereotype}')."
            ),
            genset,
            "inclua no genset apenas classes declaradas como 'role'.",
          )
        )
        continue

      specific_infos.append(specific)

    if valid and len(specific_infos) < MIN_ROLES:
      valid = False
      errors.append(
        _diagnostic(
          "error",
          (
            f"genset de roles '{genset.node.name}' possui {len(specific_infos)} "
            f"role(s). Uma partição exige pelo menos {MIN_ROLES}."
          ),
          genset,
          "acrescente outro role ao genset para completar a partição.",
        )
      )

    if genset.node.disjointness != "disjoint":
      valid = False
      errors.append(
        _diagnostic(
          "error",
          f"genset de roles '{genset.node.name}' deve ser disjoint.",
          genset,
          f"declare '{genset.node.name}' como 'disjoint'.",
        )
      )

    pending: list[ClassInfo] = []

    if valid:
      for specific in specific_infos:
        if info.node.name in specific.specializes:
          continue

        # O genset agrupa roles que podem já ter outros pais (o kind que
        # fornece identidade). A aresta que falta para o roleMixin é deduzida.
        pending.append(specific)

    if not valid:
      continue

    roles: dict[str, ClassInfo] = {role.node.name: role for role in direct_roles}

    for specific in specific_infos:
      roles.setdefault(specific.node.name, specific)

    return list(roles.values()), genset, pending, True

  return list(direct_roles), None, [], False


def _identity_errors(
  index: OntologyIndex,
  info: ClassInfo,
  roles: list[ClassInfo],
) -> list[PatternDiagnostic]:
  """Reporta roles que não alcançam um kind/collective provedor de identidade"""

  errors: list[PatternDiagnostic] = []

  for role in roles:
    if has_identity_provider(role, index):
      continue

    errors.append(
      _diagnostic(
        "error",
        (
          f"role '{role.node.name}' do roleMixin '{info.node.name}' não alcança um "
          "kind/collective provedor de identidade, roleMixin não fornece "
          "identidade."
        ),
        role,
        (f"faça '{role.node.name}' especializar também um kind/collective"),
      )
    )

  return errors


def _rigid_child_error(info: ClassInfo, child: ClassInfo) -> PatternDiagnostic:
  """Gera o erro de roleMixin que é supertipo de um universal rígido"""

  return _diagnostic(
    "error",
    (
      f"roleMixin '{info.node.name}' é anti-rígido e não pode ser supertipo do "
      f"universal rígido '{child.node.name}' ('{child.coerced_stereotype}')."
    ),
    child,
    (
      f"remova '{child.node.name}' da hierarquia de '{info.node.name}' ou declare "
      f"'{info.node.name}' como 'category'/'mixin', se a agregação for de sortais "
      "rígidos."
    ),
  )


def _no_roles(info: ClassInfo) -> PatternDiagnostic:
  """Gera a dedução de roleMixin sem roles especializando"""

  return _diagnostic(
    "deduction",
    (
      f"roleMixin '{info.node.name}' não possui roles que o especializem nem "
      "especializa outro roleMixin."
    ),
    info,
    (
      f"declare roles especializando '{info.node.name}' ou faça '{info.node.name}' "
      "especializar outro roleMixin (dedução do padrão RoleMixin incompleto)."
    ),
  )


def _no_dependence(info: ClassInfo) -> PatternDiagnostic:
  """Gera a dedução de roleMixin sem relator/mediação"""

  return _diagnostic(
    "deduction",
    (
      f"roleMixin '{info.node.name}' não participa de uma dependência relacional "
      "(nenhum relator/mediação)."
    ),
    info,
    (
      f"adicione um relator com '@mediation' para '{info.node.name}' ou faça "
      f"'{info.node.name}' herdar a dependência de outro roleMixin (dedução do "
      "padrão RoleMixin incompleto)."
    ),
  )


def _inherited_dependence(info: ClassInfo, ancestor: str | None) -> PatternDiagnostic:
  """Gera a dedução de dependência relacional herdada de um roleMixin"""

  return _diagnostic(
    "deduction",
    (
      f"roleMixin '{info.node.name}' herda a dependência relacional do roleMixin "
      f"'{ancestor}'."
    ),
    info,
    (
      f"declare explicitamente '@mediation' para '{info.node.name}' ou mantenha a "
      f"dependência relacional via '{ancestor}'."
    ),
  )


def _deduced_edge(
  role: ClassInfo,
  info: ClassInfo,
  genset: GensetInfo | None,
) -> PatternDiagnostic:
  """Gera a dedução da aresta specializes de um role a partir do genset"""

  genset_name = genset.node.name if genset is not None else "-"

  return _diagnostic(
    "deduction",
    (
      f"'{role.node.name}' não declara 'specializes {info.node.name}', mas o genset "
      f"'{genset_name}' o agrupa sob '{info.node.name}'."
    ),
    role,
    (
      f"declare explicitamente 'role {role.node.name} specializes {info.node.name}' "
      "(dedução pela sobrecarga do genset)."
    ),
  )
