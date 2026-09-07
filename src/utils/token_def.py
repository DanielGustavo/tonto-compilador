from ply import lex

from custom_token import CustomToken
from token_definitions import reserved_words, token_definitions


# used to avoid code duplication
def token_def(token_type):
  @lex.Token(token_definitions.get(token_type))
  def t_token(t):
    reserved_word = reserved_words.get(t.value)

    t.value = CustomToken(
      value=t.value,
      token_type=token_type if reserved_word is None else reserved_word[1],
    )
    return t

  return t_token
