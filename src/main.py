from ply import lex

from token_definitions import token_definitions

reserved = {}
tokens = []

for token, rule in token_definitions.items():
  if type(rule) is dict:
    reserved.update(rule)
    tokens += rule.values()
  else:
    tokens.append(token)

t_CLASS = token_definitions["CLASS"]

t_ignore = " \t"


@lex.TOKEN(r"" + "|".join(key for key in reserved.keys()))
def t_RESERVED(t):
  t.type = reserved.get(t.value)
  return t


def t_newline(t):
  r"\n+"
  t.lexer.lineno += len(t.value)


def t_error(t):
  print("Invalid symbol '%s'" % t.value[0])
  t.lexer.skip(1)


lexer = lex.lex()
lexer.input("kind Cobertura_Da_Pizza")

for token in lexer:
  print(token)
