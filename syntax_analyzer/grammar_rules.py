from lexico_analyzer import lexer_rules

from . import ast_nodes
from .error_handling import p_error

tokens = lexer_rules.tokens
start = "program"


def p_empty(p):
  "empty :"
  pass


# --------------------------------------------------------------------------- #
# 1. Programa e pacote
# --------------------------------------------------------------------------- #


def p_program(p):
  "program : imports_list package_declaration"
  package = p[2]
  first = p[1][0] if p[1] else package

  p[0] = ast_nodes.Program(
    line=first.line if first is not None else 1,
    column=first.column if first is not None else 1,
    imports=p[1],
    package=package,
  )


def p_imports_list(p):
  """
  imports_list : imports_list import
               | empty
  """
  p[0] = [*p[1], p[2]] if len(p) == 3 else []


def p_import(p):
  "import : IMPORT package_name"
  p[0] = ast_nodes.Import(line=p[1].line, column=p[1].column, name=p[2].value)


def p_package_name(p):
  "package_name : CLASS_ID"
  p[0] = p[1]


def p_package_declaration(p):
  """package_declaration : PACKAGE package_name package_body"""
  declarations = p[3]

  p[0] = ast_nodes.Package(
    line=p[1].line, column=p[1].column, name=p[2].value, declarations=declarations
  )


def p_package_body(p):
  """
  package_body : package_body declaration
               | empty
  """
  if len(p) == 2:
    p[0] = []
    return

  # `p[2]` é `None` quando a declaração foi descartada por `p_declaration_error`
  p[0] = [*p[1], p[2]] if p[2] is not None else list(p[1])


def p_declaration(p):
  "declaration : enum_declaration"
  #            | ..._declaration2
  #            | ..._declaration3
  #            | ..._declaration4
  p[0] = p[1]


def p_declaration_error(p):
  "declaration : error RBRACE"
  # Recuperação de erro: ao achar um token inesperado dentro de uma
  # declaração, descarta tudo até o próximo '}' e segue com a análise a
  # partir da próxima declaração, em vez de abortar o arquivo inteiro.
  p.parser.errok()


# --------------------------------------------------------------------------- #
# 2. Enums
# --------------------------------------------------------------------------- #


def p_enum_declaration(p):
  "enum_declaration : ENUM enum_name LBRACE instances_list RBRACE"
  p[0] = ast_nodes.Enumeration(
    line=p[1].line, column=p[1].column, name=p[2].value, literals=p[4]
  )


def p_enum_name(p):
  "enum_name : CLASS_ID"
  p[0] = p[1]


def p_instances_list(p):
  """
  instances_list : instance_name
                 | instances_list COMMA instance_name
  """
  token = p[1] if len(p) == 2 else p[3]
  literal = ast_nodes.Literal(line=token.line, column=token.column, name=token.value)

  p[0] = [literal] if len(p) == 2 else [*p[1], literal]


def p_instance_name(p):
  "instance_name : INSTANCE_ID"
  p[0] = p[1]
