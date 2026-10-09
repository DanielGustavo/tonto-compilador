from pathlib import Path

from ply import yacc

from lexico_analyzer import lexer_rules
from lexico_analyzer.analyzer import construir_lexer

from . import grammar_rules
from .ast_nodes import Node

lexer = construir_lexer()

parser = yacc.yacc(
  module=grammar_rules,
  tabmodule="syntax_analyzer.parsetab",
  debug=True,
  debugfile="parser.out",
  outputdir=str(Path(__file__).parent),
)


def analisar_codigo(codigo_fonte: str) -> tuple[Node | None, list[dict]]:
  lexer_rules.erros_lexicos.clear()

  lexer.lineno = 1
  arvore = parser.parse(codigo_fonte, lexer=lexer)

  return (
    arvore,
    list(lexer_rules.erros_lexicos),
  )


def analisar_arquivo(caminho: Path) -> tuple[Node | None, list[dict], str]:
  codigo_fonte = Path(caminho).read_text(encoding="utf-8")
  arvore, erros_lexicos = analisar_codigo(codigo_fonte)

  return arvore, erros_lexicos, codigo_fonte
