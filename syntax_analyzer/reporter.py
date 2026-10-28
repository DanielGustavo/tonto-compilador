from typing import TypeVar

from table_printer import print_table

from . import ast_nodes
from .errors import SemanticError, SyntacticError

_NodeT = TypeVar("_NodeT", bound=ast_nodes.Node)


def print_syntax_errors(errors: list[SyntacticError]) -> None:
  if not errors:
    print("\nNenhum erro sintático encontrado.")
    return

  print(f"\n--- Erros sintáticos ({len(errors)}) ---")

  for error in errors:
    print(f"  linha {error.line}, coluna {error.column}: {error.message}")
    print(f"    sugestão: {error.suggestion}")


def print_semantic_errors(errors: list[SemanticError]) -> None:
  if not errors:
    print("\nNenhum erro semântico encontrado.")
    return

  print(f"\n--- Erros semânticos ({len(errors)}) ---")

  for error in errors:
    print(f"  linha {error.line}, coluna {error.column}: {error.message}")
    print(f"    sugestão: {error.suggestion}")


def print_tabela_sintese(
  package: ast_nodes.Package,
  imported: list[tuple[ast_nodes.Node, str]] | None = None,
) -> None:
  imported = imported or []

  def own(declaration_type: type[_NodeT]) -> list[tuple[_NodeT, str]]:
    return [
      (d, "-") for d in package.declarations if isinstance(d, declaration_type)
    ]

  def merged(declaration_type: type[_NodeT]) -> list[tuple[_NodeT, str]]:
    return own(declaration_type) + [
      (d, origin) for d, origin in imported if isinstance(d, declaration_type)
    ]

  classes = merged(ast_nodes.ClassDeclaration)
  datatypes = merged(ast_nodes.DataTypeDeclaration)
  enums = merged(ast_nodes.Enumeration)
  gensets = merged(ast_nodes.GeneralizationSet)
  external_relations = [
    d for d in package.declarations if isinstance(d, ast_nodes.Relation)
  ]

  print("\n============ TABELA DE SÍNTESE ============")
  print(f"\nPacote: {package.name}")
  print(
    f"  Classes: {len(classes)}  |  Datatypes: {len(datatypes)}  |  "
    f"Enums: {len(enums)}  |  Gensets: {len(gensets)}  |  "
    f"Relações externas: {len(external_relations)}"
  )

  def count_members(node: ast_nodes.ClassDeclaration, member_type: type) -> int:
    return sum(1 for member in node.members if isinstance(member, member_type))

  print_table(
    "Classes",
    (
      "Nome",
      "Estereótipo",
      "Especializa",
      "Atributos",
      "Relações internas",
      "Pacote de origem",
    ),
    [
      (
        node.name,
        node.stereotype,
        node.specializes or "-",
        str(count_members(node, ast_nodes.Attribute)),
        str(count_members(node, ast_nodes.Relation)),
        origem,
      )
      for node, origem in classes
    ],
    indent="  ",
  )

  print_table(
    "Datatypes",
    ("Nome", "Atributos", "Pacote de origem"),
    [(node.name, str(len(node.attributes)), origem) for node, origem in datatypes],
    indent="  ",
  )

  print_table(
    "Enums",
    ("Nome", "Literais", "Pacote de origem"),
    [(node.name, str(len(node.literals)), origem) for node, origem in enums],
    indent="  ",
  )

  print_table(
    "Gensets",
    ("Nome", "Geral", "Específicas", "Disjunção", "Completude", "Pacote de origem"),
    [
      (
        node.name,
        node.general,
        ", ".join(node.specifics),
        node.disjointness or "-",
        node.completeness or "-",
        origem,
      )
      for node, origem in gensets
    ],
    indent="  ",
  )

  print_table(
    "Relações externas",
    ("Nome", "Estereótipo", "Origem", "Destino"),
    [
      (node.name or "(anônima)", node.stereotype, node.source or "-", node.target)
      for node in external_relations
    ],
    indent="  ",
  )
