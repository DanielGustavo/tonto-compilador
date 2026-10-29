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
    return [(d, "-") for d in package.declarations if isinstance(d, declaration_type)]

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

  pacotes: dict[str, dict[str, int]] = {package.name: {}}

  def increment_declaration(nome: str, chave: str) -> None:
    pacotes.setdefault(nome, {})
    pacotes[nome][chave] = pacotes[nome].get(chave, 0) + 1

  for declaracao in package.declarations:
    if isinstance(declaracao, ast_nodes.ClassDeclaration):
      increment_declaration(package.name, "Classes")
    elif isinstance(declaracao, ast_nodes.DataTypeDeclaration):
      increment_declaration(package.name, "Datatypes")
    elif isinstance(declaracao, ast_nodes.Enumeration):
      increment_declaration(package.name, "Enums")
    elif isinstance(declaracao, ast_nodes.GeneralizationSet):
      increment_declaration(package.name, "Gensets")

  for declaracao, origem in imported:
    if isinstance(declaracao, ast_nodes.ClassDeclaration):
      increment_declaration(origem, "Classes")
    elif isinstance(declaracao, ast_nodes.DataTypeDeclaration):
      increment_declaration(origem, "Datatypes")
    elif isinstance(declaracao, ast_nodes.Enumeration):
      increment_declaration(origem, "Enums")
    elif isinstance(declaracao, ast_nodes.GeneralizationSet):
      increment_declaration(origem, "Gensets")

  colunas_pacote = ("Classes", "Datatypes", "Enums", "Gensets")

  print_table(
    "Pacotes",
    ("Nome", *colunas_pacote),
    [
      (nome, *(str(contagens.get(coluna, 0)) for coluna in colunas_pacote))
      for nome, contagens in pacotes.items()
    ],
    indent="  ",
  )

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
        ", ".join(node.specializes) if node.specializes else "-",
        str(count_members(node, ast_nodes.Attribute)),
        str(count_members(node, ast_nodes.Relation)),
        origem,
      )
      for node, origem in classes
    ],
    indent="  ",
  )

  internal_relations = [
    (node.name, member, origem)
    for node, origem in classes
    for member in node.members
    if isinstance(member, ast_nodes.Relation)
  ]

  print_table(
    "Relações internas",
    (
      "Classe",
      "Estereótipo",
      "Nome",
      "Destino",
      "Cardinalidade origem",
      "Cardinalidade destino",
      "Pacote de origem",
    ),
    [
      (
        classe,
        relacao.stereotype,
        relacao.name or "(anônima)",
        relacao.target,
        relacao.source_cardinality or "-",
        relacao.target_cardinality or "-",
        origem,
      )
      for classe, relacao, origem in internal_relations
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
