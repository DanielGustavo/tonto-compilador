from pathlib import Path

from ply import yacc

from lexico_analyzer import lexer_rules
from lexico_analyzer.analyzer import construir_lexer
from lexico_analyzer.errors import LexicalError

from . import error_handling, grammar_rules, semantic_actions
from .ast_nodes import Node
from .errors import SemanticError, SyntacticError

lexer = construir_lexer()
error_handling.analyzer = lexer

parser = yacc.yacc(
  module=grammar_rules,
  tabmodule="syntax_analyzer.parsetab",
  debug=True,
  debugfile="parser.out",
  outputdir=str(Path(__file__).parent),
)


def analisar_codigo(
  codigo_fonte: str,
) -> tuple[Node | None, list[LexicalError], list[SyntacticError], list[SemanticError]]:
  lexer_rules.erros_lexicos.clear()
  error_handling.syntax_errors.clear()
  semantic_actions.reset()

  lexer.lineno = 1
  arvore = parser.parse(codigo_fonte, lexer=lexer)
  erros_semanticos = semantic_actions.finalize()

  return (
    arvore,
    list(lexer_rules.erros_lexicos),
    list(error_handling.syntax_errors),
    erros_semanticos,
  )


def analisar_arquivo(
  caminho: Path,
) -> tuple[
  Node | None, list[LexicalError], list[SyntacticError], list[SemanticError], str
]:
  codigo_fonte = Path(caminho).read_text(encoding="utf-8")
  arvore, erros_lexicos, erros_sintaticos, erros_semanticos = analisar_codigo(
    codigo_fonte
  )

  return arvore, erros_lexicos, erros_sintaticos, erros_semanticos, codigo_fonte
