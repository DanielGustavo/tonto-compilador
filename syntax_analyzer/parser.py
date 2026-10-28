import re
from pathlib import Path

from ply import yacc

from lexico_analyzer import lexer_rules
from lexico_analyzer.analyzer import construir_lexer
from lexico_analyzer.errors import LexicalError

from . import ast_nodes, error_handling, grammar_rules, semantic_actions
from .ast_nodes import Node
from .errors import SemanticError, SyntacticError
from .symbol import SymbolCategory

lexer = construir_lexer()
error_handling.analyzer = lexer

parser = yacc.yacc(
  module=grammar_rules,
  tabmodule="syntax_analyzer.parsetab",
  debug=True,
  debugfile="parser.out",
  outputdir=str(Path(__file__).parent),
)

_PACKAGE_NAME_RE = re.compile(r"^\s*package\s+([A-Z][a-zA-Z_]*)", re.MULTILINE)


def _index_packages_by_name(base_dir: Path) -> dict[str, Path]:
  indice: dict[str, Path] = {}

  for arquivo in base_dir.glob("*.tonto"):
    match = _PACKAGE_NAME_RE.search(arquivo.read_text(encoding="utf-8"))

    if match is not None:
      indice[match.group(1)] = arquivo

  return indice


def _parse_file_isolated(caminho: Path) -> ast_nodes.Program | None:
  snap = semantic_actions.snapshot()
  semantic_actions.reset()

  try:
    codigo_fonte = caminho.read_text(encoding="utf-8")
    lexer.lineno = 1
    arvore = parser.parse(codigo_fonte, lexer=lexer)
    return arvore if isinstance(arvore, ast_nodes.Program) else None
  finally:
    semantic_actions.restore(snap)


def _resolve_imports(
  programa: ast_nodes.Program, base_dir: Path | None
) -> list[tuple[Node, str]]:
  importados: list[tuple[Node, str]] = []

  if base_dir is None or not programa.imports:
    return importados

  pacote_atual = programa.package.name if programa.package else None
  indice = _index_packages_by_name(base_dir)

  visitados: set[str] = {pacote_atual} if pacote_atual else set()
  fila: list[ast_nodes.Import] = list(programa.imports)

  while fila:
    importacao = fila.pop(0)

    if importacao.name in visitados:
      continue

    visitados.add(importacao.name)
    caminho = indice.get(importacao.name)

    if caminho is None:
      semantic_actions.report_unresolved_import(
        importacao.name, importacao.line, importacao.column
      )
      continue

    arvore_importada = _parse_file_isolated(caminho)

    if arvore_importada is None or arvore_importada.package is None:
      continue

    pacote_importado = arvore_importada.package

    for declaracao in pacote_importado.declarations:
      if isinstance(declaracao, ast_nodes.ClassDeclaration):
        categoria = SymbolCategory.CLASS
      elif isinstance(declaracao, ast_nodes.DataTypeDeclaration):
        categoria = SymbolCategory.DATATYPE
      elif isinstance(declaracao, ast_nodes.Enumeration):
        categoria = SymbolCategory.ENUM
      elif isinstance(declaracao, ast_nodes.GeneralizationSet):
        categoria = SymbolCategory.GENSET
      else:
        continue

      semantic_actions.declare_imported(
        declaracao.name,
        categoria,
        declaracao.line,
        declaracao.column,
        importacao.name,
      )
      importados.append((declaracao, importacao.name))

    fila.extend(arvore_importada.imports)

  return importados


def analisar_codigo(
  codigo_fonte: str,
  base_dir: Path | None = None,
) -> tuple[
  Node | None,
  list[LexicalError],
  list[SyntacticError],
  list[SemanticError],
  list[tuple[Node, str]],
]:
  lexer_rules.erros_lexicos.clear()
  error_handling.syntax_errors.clear()
  semantic_actions.reset()

  lexer.lineno = 1
  arvore = parser.parse(codigo_fonte, lexer=lexer)

  declaracoes_importadas: list[tuple[Node, str]] = []
  if isinstance(arvore, ast_nodes.Program):
    declaracoes_importadas = _resolve_imports(arvore, base_dir)

  erros_semanticos = semantic_actions.finalize()

  return (
    arvore,
    list(lexer_rules.erros_lexicos),
    list(error_handling.syntax_errors),
    erros_semanticos,
    declaracoes_importadas,
  )


def analisar_arquivo(
  caminho: Path,
) -> tuple[
  Node | None,
  list[LexicalError],
  list[SyntacticError],
  list[SemanticError],
  list[tuple[Node, str]],
  str,
]:
  caminho = Path(caminho)
  codigo_fonte = caminho.read_text(encoding="utf-8")
  arvore, erros_lexicos, erros_sintaticos, erros_semanticos, declaracoes_importadas = (
    analisar_codigo(codigo_fonte, base_dir=caminho.parent)
  )

  return (
    arvore,
    erros_lexicos,
    erros_sintaticos,
    erros_semanticos,
    declaracoes_importadas,
    codigo_fonte,
  )
