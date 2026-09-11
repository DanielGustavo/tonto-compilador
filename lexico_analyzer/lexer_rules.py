"""Regras do lexer PLY.

Este módulo é o "arquivo LEX" do projeto: ele expõe, no nível do módulo, tudo o
que a biblioteca PLY procura para montar o autômato — a lista `tokens`, as
regras `t_*`, os padrões ignorados e o tratamento de erro.

Nada aqui é executado diretamente: quem constrói o lexer é `analyzer.py`, com
`lex.lex(module=lexer_rules)`.
"""

import itertools

from ply import lex

from .token_definitions import reserved_words, token_definitions
from .token_types import CustomToken, TokenEnum

# Erros léxicos encontrados na análise atual (preenchido por `t_error`).
erros_lexicos: list[dict] = []


# --------------------------------------------------------------------------- #
# Lista de tokens exigida pelo PLY
# --------------------------------------------------------------------------- #

# 1) um token para cada palavra reservada (EVENT, KIND, PACKAGE, ...)
tokens = [token for token, _ in reserved_words.values()]

# 2) um token para cada categoria com expressão regular (CLASS_ID, LPAREN, ...)
for token_definition in token_definitions:
  tokens.append(token_definition.value)


# --------------------------------------------------------------------------- #
# Fábrica de regras (evita duplicar o mesmo corpo de função dezenas de vezes)
# --------------------------------------------------------------------------- #


# O PLY decide a ordem de teste das regras `t_*` pela linha em que a função foi
# definida (`__code__.co_firstlineno`). Como todas nascem de `def t_token(t):`
# dentro da fábrica abaixo, elas empatariam nessa linha; usamos este contador
# para atribuir a cada uma um "número de linha" artificial e crescente, na
# ordem em que `token_def(...)` é chamado em `lexer_rules.py` — é isso que
# garante, por exemplo, que `INSTANCE_ID` seja testado antes de `CLASS_ID`.
_rule_order = itertools.count(1)


def token_def(token_type: TokenEnum):
  """Cria a função `t_<TOKEN>` correspondente a `token_type`.

  A função gerada faz três coisas:
  - decide se o lexema é uma palavra reservada ou a categoria genérica;
  - calcula a coluna a partir da última quebra de linha;
  - troca o valor do token do PLY por um `CustomToken`.
  """

  @lex.Token(token_definitions.get(token_type))
  def t_token(t):
    reserved_word = reserved_words.get(t.value)

    t.type = token_type.value if reserved_word is None else reserved_word[0]

    last_newline = t.lexer.lexdata.rfind("\n", 0, t.lexpos)
    column = t.lexpos - last_newline

    t.value = CustomToken(
      value=t.value,
      token_type=token_type if reserved_word is None else reserved_word[1],
      line=t.lineno,
      column=column,
    )
    return t

  t_token.__code__ = t_token.__code__.replace(co_firstlineno=next(_rule_order))

  return t_token


# --------------------------------------------------------------------------- #
# A ordem abaixo importa: é ela quem decide, em caso de ambiguidade, qual regra
# o PLY testa primeiro (ver o contador `_rule_order` em `token_def`).
# --------------------------------------------------------------------------- #

# tipos e identificadores
t_NEW_TYPE = token_def(TokenEnum.NEW_TYPE)
t_FUNCTIONAL_COMPLEXES = token_def(TokenEnum.FUNCTIONAL_COMPLEXES)
t_INTRINSIC_MODES = token_def(TokenEnum.INTRINSIC_MODES)

# relações (composições e associações)
t_COMPOSITION_L = token_def(TokenEnum.COMPOSITION_L)
t_COMPOSITION_R = token_def(TokenEnum.COMPOSITION_R)
t_COMPOSITION_LO = token_def(TokenEnum.COMPOSITION_LO)
t_COMPOSITION_RO = token_def(TokenEnum.COMPOSITION_RO)
t_ASSOCIATION = token_def(TokenEnum.ASSOCIATION)
t_CARDINALITY = token_def(TokenEnum.CARDINALITY)

# convenções de nomes (instância antes de classe/relação: termina com dígito)
t_INSTANCE_ID = token_def(TokenEnum.INSTANCE_ID)
t_CLASS_ID = token_def(TokenEnum.CLASS_ID)
t_RELATION_ID = token_def(TokenEnum.RELATION_ID)

# símbolos especiais
t_LPAREN = token_def(TokenEnum.LPAREN)
t_RPAREN = token_def(TokenEnum.RPAREN)
t_LBRACE = token_def(TokenEnum.LBRACE)
t_RBRACE = token_def(TokenEnum.RBRACE)
t_DOT = token_def(TokenEnum.DOT)
t_COMMA = token_def(TokenEnum.COMMA)
t_PLUS = token_def(TokenEnum.PLUS)
t_LT = token_def(TokenEnum.LT)
t_GT = token_def(TokenEnum.GT)
t_AT = token_def(TokenEnum.AT)
t_MINUS = token_def(TokenEnum.MINUS)
t_STAR = token_def(TokenEnum.STAR)
t_COLON = token_def(TokenEnum.COLON)


# --------------------------------------------------------------------------- #
# O que é descartado e como erros são tratados
# --------------------------------------------------------------------------- #

t_ignore = " \t"
t_ignore_COMMENT = r"\#.*"
t_ignore_CPP_COMMENT = r"//.*"


def t_newline(t):
  r"\n+"
  t.lexer.lineno += len(t.value)


def t_error(t):
  """Registra o caractere inesperado, informa a linha e segue a análise."""
  bad = t.lexer.lexdata[t.lexpos]

  last_newline = t.lexer.lexdata.rfind("\n", 0, t.lexpos)
  column = t.lexpos - last_newline

  erros_lexicos.append(
    {
      "value": bad,
      "line": t.lineno,
      "column": column,
      "message": f"caractere inesperado {bad!r}",
    }
  )

  print(
    f"[ERRO LÉXICO] linha {t.lineno}, coluna {column}: caractere inesperado {bad!r}"
  )
  t.lexer.skip(1)
