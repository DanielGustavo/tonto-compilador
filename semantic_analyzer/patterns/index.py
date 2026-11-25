"""Índice das classes e gensets vistos na AST.

Constrói a partir do pacote principal e das declarações trazidas por imports.
"""

from dataclasses import dataclass, field

from syntax_analyzer import ast_nodes

from .model import ClassInfo, GensetInfo, RelationInfo


# `field` é necessário para criar objetos novos a cada instância do dataclass
@dataclass
class OntologyIndex:
  package_name: str
  classes: dict[str, ClassInfo] = field(default_factory=dict)
  gensets: list[GensetInfo] = field(default_factory=list)
  relations: list[RelationInfo] = field(default_factory=list)


def build_index(
  program: ast_nodes.Program,
  imported: list[tuple[ast_nodes.Node, str]],
) -> OntologyIndex:
  package_name = program.package.name if program.package is not None else ""
  index = OntologyIndex(package_name=package_name)

  def add_relation(node: ast_nodes.Relation, origin: str, owner: str | None) -> None:
    index.relations.append(RelationInfo.from_node(node, owner, origin))

  def add_class(node: ast_nodes.ClassDeclaration, origin: str) -> None:
    if not node.name or node.name in index.classes:
      return

    index.classes[node.name] = ClassInfo.from_node(node, origin)

    for member in node.members:
      if isinstance(member, ast_nodes.Relation):
        add_relation(member, origin, node.name)

  def add_genset(node: ast_nodes.GeneralizationSet, origin: str) -> None:
    if not node.name:
      return

    index.gensets.append(GensetInfo.from_node(node, origin))

  def add_declaration(node: ast_nodes.Node | None, origin: str) -> None:
    if isinstance(node, ast_nodes.ClassDeclaration):
      add_class(node, origin)
    elif isinstance(node, ast_nodes.GeneralizationSet):
      add_genset(node, origin)
    elif isinstance(node, ast_nodes.Relation):
      add_relation(node, origin, None)

  if program.package is not None:
    for declaration in program.package.declarations:
      add_declaration(declaration, package_name)

  for declaration, origin in imported:
    add_declaration(declaration, origin)

  return index
