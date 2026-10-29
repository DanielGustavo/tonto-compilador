"""Fachada do analisador léxico.

Constrói o lexer do PLY a partir de `lexer_rules` e devolve a lista de
`CustomToken` encontrados, junto com os erros léxicos do caminho. É o módulo
que roda a tokenização; a apresentação do resultado (tabelas, contagem,
exportação JSON) é responsabilidade separada de `reporter.py`, importado
diretamente pelo `main.py` quando precisa dessas funções.
"""

from pathlib import Path

from ply import lex

from . import lexer_rules
from .errors import LexicalError
from .token_types import CustomToken


def construir_lexer():
  return lex.lex(module=lexer_rules)


lexer = construir_lexer()


def analisar_codigo(codigo_fonte: str) -> tuple[list[CustomToken], list[LexicalError]]:
  """Roda a análise léxica sobre uma string e devolve (tokens, erros)."""
  lexer_rules.erros_lexicos.clear()

  lexer.lineno = 1
  lexer.input(codigo_fonte)

  # `ply_token.value` já é o nosso CustomToken (ver `lexer_rules.token_def`).
  tokens = [ply_token.value for ply_token in lexer]

  return tokens, list(lexer_rules.erros_lexicos)


def analisar_arquivo(caminho: Path) -> tuple[list[CustomToken], list[LexicalError], str]:
  """Lê um arquivo `.tonto` e devolve (tokens, erros, código-fonte)."""
  codigo_fonte = Path(caminho).read_text(encoding="utf-8")
  tokens, erros = analisar_codigo(codigo_fonte)

  return tokens, erros, codigo_fonte
