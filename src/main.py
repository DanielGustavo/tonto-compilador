import re

from ply import lex

from token_definitions import TokenEnum, token_definitions

reserved = {}
tokens = []

for token, rule in token_definitions.items():
  if type(rule) is dict:
    reserved.update(rule)
    tokens += rule.values()
  else:
    tokens.append(token)


def t_ID(t):
  r"[a-zA-Z0-9_]+"
  reserved_word = reserved.get(t.value)

  if reserved_word is not None:
    t.type = reserved_word
  elif re.match(token_definitions[TokenEnum.CLASS], t.value):
    t.type = TokenEnum.CLASS
  elif re.match(token_definitions[TokenEnum.RELATION], t.value):
    t.type = TokenEnum.RELATION
  elif re.match(token_definitions[TokenEnum.INSTANCE], t.value):
    t.type = TokenEnum.INSTANCE
  else:
    # add diagnostic method
    return None

  return t


t_ignore = " \t"


def t_newline(t):
  r"\n+"
  t.lexer.lineno += len(t.value)


def t_error(t):
  source = t.lexer.lexdata
  bad = source[t.lexpos]

  if len(bad) == 1:
    message = f"unexpected character {bad!r}"
  else:
    message = f"unexpected characters {bad!r}"

  print(message)
  t.lexer.skip(len(bad))


lexer = lex.lex()
lexer.input("""
kind Cobertura_Da_Pizza8_
""")

for token in lexer:
  print(token)
