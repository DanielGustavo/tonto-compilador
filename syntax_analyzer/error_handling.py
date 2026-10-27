from lexico_analyzer.token_definitions import reserved_words

from .errors import SyntacticError

syntax_errors: list[SyntacticError] = []

# Preenchido por `parser.py` logo após `lexer = construir_lexer()`.
analyzer = None

# Nomes de token do PLY (ex.: "KIND", "RELATION") correspondentes a palavras
# reservadas válidas do Tonto, usado para distinguir "token conhecido pela
# linguagem mas ainda não suportado por esta gramática" de um token qualquer.
_RESERVED_TOKEN_NAMES = {token_name for token_name, _ in reserved_words.values()}

# Palavras reservadas que a gramática atual já sabe tratar; qualquer outra
# reservada cai na sugestão de "ainda não suportado" em `_suggestion_for_token`.
_SUPPORTED_TOKEN_NAMES = {
  "IMPORT",
  "PACKAGE",
  "ENUM",
  "DATATYPE",
  # estereótipos de classe
  "KIND",
  "SUBKIND",
  "ROLE",
  "PHASE",
  "CATEGORY",
  "MIXIN",
  "PHASEMIXIN",
  "ROLEMIXIN",
  "HISTORICALROLEMIXIN",
  "COLLECTIVE",
  "QUANTITY",
  "QUALITY",
  "MODE",
  "INTRISICMODE",
  "EXTRINSICMODE",
  "HISTORICALROLE",
  "RELATOR",
  "EVENT",
  "SITUATION",
  "PROCESS",
  # cláusula de especialização e tipos de atributo
  "SPECIALIZES",
  "NUMBER",
  "STRING",
  "BOOLEAN",
  "DATE",
  "TIME",
  "DATETIME",
  # meta-atributos
  "ORDERED",
  "CONST",
  "DERIVED",
  "SUBSETS",
  "REDEFINES",
  # genset (generalization sets)
  "GENSET",
  "DISJOINT",
  "OVERLAPPING",
  "COMPLETE",
  "INCOMPLETE",
  "GENERAL",
  "SPECIFICS",
  "WHERE",
}

_SUGGESTIONS_BY_TOKEN = {
  "LBRACE": "verifique se o bloco anterior foi fechado corretamente antes de abrir um novo '{'.",
  "RBRACE": "verifique se sobra um '}' sem bloco correspondente, ou se falta abrir um bloco antes dele.",
  "COMMA": "verifique se há uma ',' sobrando ou faltando entre os itens.",
  "INSTANCE_ID": "verifique se falta uma ',' separando as instâncias do enum.",
  "COLON": "verifique se o atributo está no formato 'nome : tipo'.",
  "CLASS_ID": "verifique se o identificador de classe está no lugar certo (ex.: nome de classe, tipo de atributo ou alvo de 'specializes').",
  "RELATION_ID": "verifique se o identificador está no lugar certo (ex.: nome de atributo, que deve começar com letra minúscula).",
}


def _eof_suggestion() -> str:
  return (
    "o arquivo terminou antes do esperado; verifique se todas as chaves "
    "'{' abertas foram fechadas com '}' e se a declaração atual (pacote ou "
    "enum) está completa."
  )


def _suggestion_for_token(token_type: str, lexeme: str) -> str:
  if token_type in _SUGGESTIONS_BY_TOKEN:
    return _SUGGESTIONS_BY_TOKEN[token_type]

  if token_type in _RESERVED_TOKEN_NAMES and token_type not in _SUPPORTED_TOKEN_NAMES:
    return (
      "o analisador sintático atual só reconhece declarações 'enum', "
      "declarações de classe (estereótipo + nome, com especialização e "
      "atributos opcionais), declarações de 'datatype' (nome + atributos) e "
      "declarações de 'genset' (generalization sets) dentro de um pacote; "
      "relações ainda não são suportadas por esta gramática."
    )

  return f"verifique a sintaxe perto de '{lexeme}' (token {token_type})."


def p_error(p):
  """Registra o erro sintático em `syntax_errors` em vez de abortar com print."""
  if p is None:
    line = analyzer.lineno if analyzer is not None else 0

    syntax_errors.append(
      SyntacticError(
        value="",
        line=line,
        column=0,
        message="fim de arquivo inesperado",
        suggestion=_eof_suggestion(),
      )
    )
    return

  token = p.value

  syntax_errors.append(
    SyntacticError(
      value=token.value,
      line=token.line,
      column=token.column,
      message=f"token inesperado '{token.value}' ({p.type})",
      suggestion=_suggestion_for_token(p.type, token.value),
    )
  )
