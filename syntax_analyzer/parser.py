"""Monta o parser PLY e resolve imports entre arquivos `.tonto`.

Constrói o parser a partir de `grammar_rules` (`yacc.yacc`), liga
`error_handling` a ele, e implementa o parse isolado de um arquivo
importado (`_parse_file_isolated`), usado por
`semantic_analyzer.imports.resolve_imports` para decidir quais `import
<Nome>` casam com o cabeçalho `package <Nome>` de um arquivo vizinho. Expõe
`analisar_codigo` e `analisar_arquivo` como pontos de entrada públicos.
"""

from pathlib import Path

from ply import yacc

from lexico_analyzer import lexer_rules
from lexico_analyzer.analyzer import construir_lexer
from lexico_analyzer.errors import LexicalError
from semantic_analyzer import semantic_actions
from semantic_analyzer.errors import SemanticError
from semantic_analyzer.imports import resolve_imports

from . import ast_nodes, error_handling, grammar_rules
from .ast_nodes import Node
from .errors import SyntacticError

lexer = construir_lexer()
error_handling.analyzer = lexer

parser = yacc.yacc(
  module=grammar_rules,
  tabmodule="syntax_analyzer.parsetab",
  debug=True,
  debugfile="parser.out",
  outputdir=str(Path(__file__).parent),
)

error_handling.parser_ref = parser


def _parse_file_isolated(caminho: Path) -> ast_nodes.Program | None:
  # Faz o parse do arquivo importado com tabelas de símbolo e listas de erro
  # próprias (zeradas por `reset()`/`clear()`), e sempre restaura o estado do
  # arquivo principal no `finally`, assim a análise do import não contamina
  # a tabela de símbolos nem os erros do arquivo que está sendo analisado.
  snap = semantic_actions.snapshot()
  semantic_actions.reset()

  erros_lexicos_originais = list(lexer_rules.erros_lexicos)
  erros_sintaticos_originais = list(error_handling.syntax_errors)
  lexer_rules.erros_lexicos.clear()
  error_handling.syntax_errors.clear()

  try:
    codigo_fonte = caminho.read_text(encoding="utf-8")
    lexer.lineno = 1
    arvore = parser.parse(codigo_fonte, lexer=lexer)
    return arvore if isinstance(arvore, ast_nodes.Program) else None
  finally:
    semantic_actions.restore(snap)
    lexer_rules.erros_lexicos.clear()
    lexer_rules.erros_lexicos.extend(erros_lexicos_originais)
    error_handling.syntax_errors.clear()
    error_handling.syntax_errors.extend(erros_sintaticos_originais)


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
    declaracoes_importadas = resolve_imports(arvore, base_dir, _parse_file_isolated)

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
