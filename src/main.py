from ply import lex

from custom_token import CustomToken, TokenEnum
from token_definitions import reserved_words, token_definitions
from utils.token_def import token_def

# add reserved words
tokens = [token for token, _ in reserved_words.values()]

# add token types
for token_definition, _ in token_definitions.items():
  tokens.append(token_definition.value)

# define tokens handlers (the order matters)
t_INSTANCE_ID = token_def(TokenEnum.INSTANCE_ID)
t_CLASS_ID = token_def(TokenEnum.CLASS_ID)
t_RELATION_ID = token_def(TokenEnum.RELATION_ID)
###

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
kind CoberturaDaPizza09
""")

for plyToken in lexer:
  # use our custom token instead
  token: CustomToken = plyToken.value

  print(token)
