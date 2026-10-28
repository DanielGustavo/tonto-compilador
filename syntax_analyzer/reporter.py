from table_printer import print_table

from . import ast_nodes
from .errors import SemanticError, SyntacticError


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


def print_tabela_sintese(package: ast_nodes.Package) -> None:
  classes = [
    d for d in package.declarations if isinstance(d, ast_nodes.ClassDeclaration)
  ]
  datatypes = [
    d for d in package.declarations if isinstance(d, ast_nodes.DataTypeDeclaration)
  ]
  enums = [d for d in package.declarations if isinstance(d, ast_nodes.Enumeration)]
  gensets = [
    d for d in package.declarations if isinstance(d, ast_nodes.GeneralizationSet)
  ]
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
    ("Nome", "Estereótipo", "Especializa", "Atributos", "Relações internas"),
    [
      (
        node.name,
        node.stereotype,
        node.specializes or "-",
        str(count_members(node, ast_nodes.Attribute)),
        str(count_members(node, ast_nodes.Relation)),
      )
      for node in classes
    ],
    indent="  ",
  )

  print_table(
    "Datatypes",
    ("Nome", "Atributos"),
    [(node.name, str(len(node.attributes))) for node in datatypes],
    indent="  ",
  )

  print_table(
    "Enums",
    ("Nome", "Literais"),
    [(node.name, str(len(node.literals))) for node in enums],
    indent="  ",
  )

  print_table(
    "Gensets",
    ("Nome", "Geral", "Específicas", "Disjunção", "Completude"),
    [
      (
        node.name,
        node.general,
        ", ".join(node.specifics),
        node.disjointness or "-",
        node.completeness or "-",
      )
      for node in gensets
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
