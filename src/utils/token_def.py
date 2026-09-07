from ply import lex

from custom_token import CustomToken, TokenEnum
from token_definitions import reserved_words, token_definitions


# used to avoid code duplication
def token_def(token_type: TokenEnum):
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

  return t_token
