import sys
from pathlib import Path

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
t_NEW_TYPE = token_def(TokenEnum.NEW_TYPE)
t_FUNCTIONAL_COMPLEXES = token_def(TokenEnum.FUNCTIONAL_COMPLEXES)
t_INTRINSIC_MODES = token_def(TokenEnum.INTRINSIC_MODES)
t_COMPOSITION_L = token_def(TokenEnum.COMPOSITION_L)
t_COMPOSITION_R = token_def(TokenEnum.COMPOSITION_R)
t_COMPOSITION_LO = token_def(TokenEnum.COMPOSITION_LO)
t_COMPOSITION_RO = token_def(TokenEnum.COMPOSITION_RO)
t_ASSOCIATION = token_def(TokenEnum.ASSOCIATION)
t_CARDINALITY = token_def(TokenEnum.CARDINALITY)
t_INSTANCE_ID = token_def(TokenEnum.INSTANCE_ID)
t_CLASS_ID = token_def(TokenEnum.CLASS_ID)
t_RELATION_ID = token_def(TokenEnum.RELATION_ID)
# literals
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
###

t_ignore = " \t"
t_ignore_COMMENT = r"\#.*"
t_ignore_CPP_COMMENT = r"//.*"


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


def main():
  if len(sys.argv) != 2:
    print(f"uso: python {Path(__file__).name} <caminho_do_arquivo.tonto>")
    sys.exit(1)

  file_path = Path(sys.argv[1])

  if not file_path.is_file():
    print(f"arquivo não encontrado: {file_path}")
    sys.exit(1)

  source_code = file_path.read_text(encoding="utf-8")
  source_lines = source_code.splitlines()

  lexer.input(source_code)

  current_line = None

  for plyToken in lexer:
    # use our custom token instead
    token: CustomToken = plyToken.value

    if token.line != current_line:
      if current_line is not None:
        print()

      current_line = token.line
      print(f"{current_line}: {source_lines[current_line - 1]}")

    print(f"  {token}")


if __name__ == "__main__":
  main()
