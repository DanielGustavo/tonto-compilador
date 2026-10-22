from pathlib import Path

from ply import yacc

from lexico_analyzer import lexer_rules
from lexico_analyzer.analyzer import construir_lexer
from lexico_analyzer.errors import LexicalError

from . import error_handling, grammar_rules
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


def analisar_codigo(
  codigo_fonte: str,
) -> tuple[Node | None, list[LexicalError], list[SyntacticError]]:
  lexer_rules.erros_lexicos.clear()
  error_handling.syntax_errors.clear()

  lexer.lineno = 1
  arvore = parser.parse(codigo_fonte, lexer=lexer)

  return (
    arvore,
    list(lexer_rules.erros_lexicos),
    list(error_handling.syntax_errors),
  )


def analisar_arquivo(
  caminho: Path,
) -> tuple[Node | None, list[LexicalError], list[SyntacticError], str]:
  codigo_fonte = Path(caminho).read_text(encoding="utf-8")
  arvore, erros_lexicos, erros_sintaticos = analisar_codigo(codigo_fonte)

  return arvore, erros_lexicos, erros_sintaticos, codigo_fonte
