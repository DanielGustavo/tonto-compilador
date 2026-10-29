"""Tratamento de erro sintático do parser PLY.

Expõe o hook `p_error(p)` chamado pelo PLY sempre que a gramática não
consegue reduzir o token atual, além de um conjunto de regras
que inspecionam a pilha de símbolos do parser (`symstack`) para sugerir a
causa mais provável do erro, registrando o resultado em `syntax_errors`,
consumido por `syntax_analyzer/reporter.py`.
"""

from lexico_analyzer.token_definitions import reserved_words, token_names_by_category
from lexico_analyzer.token_types import TokenEnum

from . import semantic_actions
from .errors import SyntacticError

syntax_errors: list[SyntacticError] = []

# Preenchido por `parser.py` logo após `lexer = construir_lexer()`.
analyzer = None
parser_ref = None

_RESERVED_TOKEN_NAMES = {token_name for token_name, _ in reserved_words.values()}

_SUPPORTED_CATEGORIES = (
  TokenEnum.CLASS_STEREOTYPES,
  TokenEnum.RELATION_STEREOTYPES,
  TokenEnum.NATIVE_TYPES,
  TokenEnum.META_ATTRIBUTES,
)

_SUPPORTED_KEYWORDS = {
  "IMPORT",
  "PACKAGE",
  "ENUM",
  "DATATYPE",
  "SPECIALIZES",
  "GENSET",
  "DISJOINT",
  "OVERLAPPING",
  "COMPLETE",
  "INCOMPLETE",
  "GENERAL",
  "SPECIFICS",
  "WHERE",
  "RELATION",
}

_SUPPORTED_TOKEN_NAMES = {
  name
  for category in _SUPPORTED_CATEGORIES
  for name in token_names_by_category(category)
} | _SUPPORTED_KEYWORDS

_RELATION_SYMBOL_TOKENS = {
  "ASSOCIATION",
  "COMPOSITION_L",
  "COMPOSITION_R",
  "COMPOSITION_LO",
  "COMPOSITION_RO",
}

_SUGGESTIONS_BY_TOKEN = {
  "LBRACE": "verifique se o bloco anterior foi fechado corretamente antes de abrir um novo '{'.",
  "RBRACE": "verifique se sobra um '}' sem bloco correspondente, ou se falta abrir um bloco antes dele.",
  "COMMA": "verifique se há uma ',' sobrando ou faltando entre os itens.",
  "COLON": "verifique se o atributo está no formato 'nome : tipo'.",
  "CLASS_ID": "verifique se o identificador de classe está no lugar certo (ex.: nome de classe, tipo de atributo ou alvo de 'specializes').",
  "RELATION_ID": "verifique se o identificador está no lugar certo (ex.: nome de atributo, que deve começar com letra minúscula).",
  "AT": "verifique se o estereótipo da relação (ex.: '@mediation') foi escrito logo após o '@', sem espaços.",
  "RELATION": "falta o '@' + estereótipo da relação (ex.: '@mediation', '@material', '@componentOf') antes de 'relation'.",
}


def _eof_suggestion() -> str:
  return (
    "o arquivo terminou antes do esperado; verifique se todas as chaves "
    "'{' abertas foram fechadas com '}' e se a declaração atual (pacote ou "
    "enum) está completa."
  )


def _instance_id_suggestion() -> str:
  scope_name = semantic_actions.current_table.scope_name

  if scope_name.startswith("enum "):
    return "verifique se falta uma ',' separando as instâncias do enum."

  return (
    "esse identificador foi interpretado como nome de instância (não de "
    "classe) porque termina em dígito, conforme a convenção de nomes do "
    "léxico; se a intenção era um nome de classe, remova o dígito final, "
    "ou, se é mesmo uma instância, verifique se ela está dentro de um "
    "bloco 'enum { ... }'."
  )


def _missing_genset_name(symstack: list) -> bool:
  # "genset { ... }" sem nome: ao chegar o '{', o topo da pilha ainda é o
  # próprio terminal GENSET, pois `genset_name` nunca foi reduzido.
  return bool(symstack) and symstack[-1].type == "GENSET"


def _missing_relation_target(symstack: list) -> bool:
  # "@estereotipo ... <simbolo>" sem a classe de destino: ao chegar o token
  # inesperado, o topo da pilha é o terminal do `relation_symbol` (ex.:
  # COMPOSITION_L) ou, se uma cardinalidade foi informada antes do alvo
  # faltante, o `opt_cardinality` já reduzido logo após esse terminal.
  if not symstack:
    return False

  if symstack[-1].type in _RELATION_SYMBOL_TOKENS:
    return True

  return (
    symstack[-1].type == "opt_cardinality"
    and len(symstack) >= 2
    and symstack[-2].type in _RELATION_SYMBOL_TOKENS
  )


def _missing_class_id_list_comma(symstack: list) -> bool:
  # "specifics Child Adult" / "where Child Adult specializes ..." / "role X
  # specializes Child Adult": como o lookahead do segundo CLASS_ID não está
  # no conjunto de lookaheads válido para reduzir "CLASS_ID -> class_id_list",
  # o erro ocorre antes dessa redução
  if len(symstack) < 2 or symstack[-1].type != "CLASS_ID":
    return False

  if symstack[-2].type in ("SPECIFICS", "WHERE", "SPECIALIZES"):
    return True

  return (
    symstack[-2].type == "COMMA"
    and len(symstack) >= 3
    and symstack[-3].type == "class_id_list"
  )


def _suggestion_for_token(token_type: str, lexeme: str, symstack: list) -> str:
  if token_type == "INSTANCE_ID":
    return _instance_id_suggestion()

  if token_type == "LBRACE" and _missing_genset_name(symstack):
    return "falta o nome do genset entre 'genset' e '{' (ex.: 'genset NomeDoGenset { ... }')."

  if token_type == "RBRACE" and _missing_relation_target(symstack):
    return (
      "falta a classe de destino da relação depois do símbolo (ex.: '--', "
      "'<>--'); verifique se o nome da classe-alvo foi escrito antes do '}'."
    )

  if token_type == "CLASS_ID" and _missing_class_id_list_comma(symstack):
    return (
      "verifique se falta uma ',' separando os nomes de classe na lista "
      "(ex.: 'specifics A, B', 'where A, B specializes C' ou "
      "'role X specializes A, B')."
    )

  if token_type in _SUGGESTIONS_BY_TOKEN:
    return _SUGGESTIONS_BY_TOKEN[token_type]

  if token_type in _RESERVED_TOKEN_NAMES and token_type not in _SUPPORTED_TOKEN_NAMES:
    return (
      "o analisador sintático atual só reconhece declarações 'enum', "
      "declarações de classe (estereótipo + nome, com especialização e "
      "atributos/relações opcionais), declarações de 'datatype' (nome + "
      "atributos), declarações de 'genset' (generalization sets) e "
      "declarações de relação (internas a uma classe ou externas, com "
      "'relation') dentro de um pacote."
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
  symstack = parser_ref.symstack if parser_ref is not None else []

  syntax_errors.append(
    SyntacticError(
      value=token.value,
      line=token.line,
      column=token.column,
      message=f"token inesperado '{token.value}' ({p.type})",
      suggestion=_suggestion_for_token(p.type, token.value, symstack),
    )
  )
