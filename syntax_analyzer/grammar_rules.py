from lexico_analyzer import lexer_rules
from lexico_analyzer.token_types import TokenEnum

from . import ast_nodes, semantic_actions
from .error_handling import p_error
from .symbol import SymbolCategory

tokens = lexer_rules.tokens
start = "program"

_CLASS_ONLY = set({SymbolCategory.CLASS})
_TYPE_LIKE = set({SymbolCategory.CLASS, SymbolCategory.DATATYPE, SymbolCategory.ENUM})


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
  """
  declaration : enum_declaration
              | class_declaration
              | datatype_declaration
              | genset_declaration
              | relation_declaration
  """
  p[0] = p[1]


def p_declaration_error(p):
  "declaration : error"
  # Recuperação de erro de nível de pacote
  p.parser.errok()
  semantic_actions.recover_to_package_scope()


# --------------------------------------------------------------------------- #
# 2. Enums
# --------------------------------------------------------------------------- #


def p_enum_declaration(p):
  "enum_declaration : ENUM enum_name enter_enum_scope LBRACE instances_list RBRACE"
  name = p[2]

  node = ast_nodes.Enumeration(
    line=p[1].line, column=p[1].column, name=name.value, literals=p[5]
  )

  semantic_actions.exit_scope()

  p[0] = node


def p_enter_enum_scope(p):
  "enter_enum_scope :"
  name = p[-1]  # enum_name
  semantic_actions.declare(name, SymbolCategory.ENUM)
  p[0] = semantic_actions.enter_scope(f"enum {name.value}")


def p_enum_name(p):
  "enum_name : CLASS_ID"
  p[0] = p[1]


def p_instances_list(p):
  """
  instances_list : instance_name
                 | instances_list COMMA instance_name
                 | empty
  """
  if len(p) == 2:
    if p[1] is None:
      p[0] = []
      return
    token = p[1]
  else:
    token = p[3]

  literal = ast_nodes.Literal(line=token.line, column=token.column, name=token.value)
  p[0] = [literal] if len(p) == 2 else [*p[1], literal]


def p_instances_list_error(p):
  "instances_list : instances_list error"
  p.parser.errok()
  p[0] = p[1]


def p_instance_name(p):
  "instance_name : INSTANCE_ID"
  semantic_actions.declare(p[1], SymbolCategory.LITERAL)
  p[0] = p[1]


# --------------------------------------------------------------------------- #
# 3. Classes
# --------------------------------------------------------------------------- #


def p_class_declaration(p):
  "class_declaration : class_stereotype CLASS_ID opt_specializes enter_class_scope opt_class_body"
  stereotype = p[1]
  name = p[2]

  node = ast_nodes.ClassDeclaration(
    line=stereotype.line,
    column=stereotype.column,
    stereotype=stereotype.value,
    name=name.value,
    specializes=p[3],
    members=p[5],
  )

  semantic_actions.exit_scope()

  p[0] = node


def p_enter_class_scope(p):
  "enter_class_scope :"
  name = p[-2]  # CLASS_ID
  semantic_actions.declare(name, SymbolCategory.CLASS)
  p[0] = semantic_actions.enter_scope(f"classe {name.value}")


def p_class_stereotype(p):
  """
  class_stereotype : KIND
                    | SUBKIND
                    | ROLE
                    | PHASE
                    | CATEGORY
                    | MIXIN
                    | PHASEMIXIN
                    | ROLEMIXIN
                    | HISTORICALROLEMIXIN
                    | COLLECTIVE
                    | QUANTITY
                    | QUALITY
                    | MODE
                    | INTRISICMODE
                    | EXTRINSICMODE
                    | HISTORICALROLE
                    | RELATOR
                    | EVENT
                    | SITUATION
                    | PROCESS
  """
  p[0] = p[1]


def p_opt_specializes(p):
  """
  opt_specializes : SPECIALIZES CLASS_ID
                   | empty
  """
  if len(p) == 3:
    semantic_actions.resolve_later(p[2], _CLASS_ONLY, "uma classe")
    p[0] = p[2].value
  else:
    p[0] = None


def p_opt_class_body(p):
  """
  opt_class_body : LBRACE class_members_list RBRACE
                  | empty
  """
  p[0] = p[2] if len(p) == 4 else []


def p_class_members_list(p):
  """
  class_members_list : class_members_list class_member
                      | empty
  """
  p[0] = [*p[1], p[2]] if len(p) == 3 else []


def p_class_members_list_error(p):
  "class_members_list : class_members_list error"
  # Recuperação de erro local ao corpo da classe
  p.parser.errok()
  p[0] = p[1]


def p_class_member(p):
  """
  class_member : attribute_declaration
               | relation_end_declaration
  """
  p[0] = p[1]


def p_attributes_list(p):
  """
  attributes_list : attributes_list attribute_declaration
                   | empty
  """
  p[0] = [*p[1], p[2]] if len(p) == 3 else []


def p_attributes_list_error(p):
  "attributes_list : attributes_list error"
  # Mesma ideia de class_members_list_error, para o corpo de um datatype.
  p.parser.errok()
  p[0] = p[1]


def p_attribute_declaration(p):
  "attribute_declaration : RELATION_ID COLON type_name opt_cardinality opt_modifiers"
  name = p[1]

  node = ast_nodes.Attribute(
    line=name.line,
    column=name.column,
    name=name.value,
    type_name=p[3],
    cardinality=p[4],
    modifiers=p[5],
  )

  semantic_actions.declare(name, SymbolCategory.ATTRIBUTE)

  p[0] = node


def p_type_name(p):
  """
  type_name : NUMBER
            | STRING
            | BOOLEAN
            | DATE
            | TIME
            | DATETIME
            | CLASS_ID
  """
  token = p[1]

  if token.token_type == TokenEnum.CLASS_ID:
    semantic_actions.resolve_later(
      token, _TYPE_LIKE, "um tipo (classe, datatype ou enum)"
    )

  p[0] = token.value


def p_opt_cardinality(p):
  """
  opt_cardinality : CARDINALITY
                   | empty
  """
  p[0] = p[1].value if p[1] is not None else None


def p_opt_modifiers(p):
  """
  opt_modifiers : LBRACE modifiers_list RBRACE
                 | empty
  """
  p[0] = p[2] if len(p) == 4 else []


def p_modifiers_list(p):
  """
  modifiers_list : modifiers_list COMMA modifier
                 | modifier
  """
  p[0] = [*p[1], p[3]] if len(p) == 4 else [p[1]]


def p_modifier(p):
  """
  modifier : ORDERED
           | CONST
           | DERIVED
           | SUBSETS
           | REDEFINES
  """
  p[0] = p[1].value


# --------------------------------------------------------------------------- #
# 4. Tipos de dados (datatypes)
# --------------------------------------------------------------------------- #


def p_datatype_declaration(p):
  "datatype_declaration : DATATYPE CLASS_ID enter_datatype_scope LBRACE attributes_list RBRACE"
  name = p[2]

  node = ast_nodes.DataTypeDeclaration(
    line=p[1].line, column=p[1].column, name=name.value, attributes=p[5]
  )

  semantic_actions.exit_scope()

  p[0] = node


def p_enter_datatype_scope(p):
  "enter_datatype_scope :"
  name = p[-1]  # CLASS_ID
  semantic_actions.declare(name, SymbolCategory.DATATYPE)
  p[0] = semantic_actions.enter_scope(f"datatype {name.value}")


# --------------------------------------------------------------------------- #
# 5. Generalizações (genset)
# --------------------------------------------------------------------------- #


def p_genset_declaration_where(p):
  """
  genset_declaration : opt_disjointness opt_completeness GENSET genset_name \
                        WHERE class_id_list SPECIALIZES CLASS_ID
  """
  genset_token = p[3]
  name = p[4]
  general = p[8]

  node = ast_nodes.GeneralizationSet(
    line=genset_token.line,
    column=genset_token.column,
    name=name.value,
    general=general.value,
    specifics=p[6],
    disjointness=p[1],
    completeness=p[2],
  )

  semantic_actions.declare(name, SymbolCategory.GENSET)
  semantic_actions.resolve_later(general, _CLASS_ONLY, "uma classe")

  p[0] = node


def p_genset_declaration_block(p):
  """
  genset_declaration : opt_disjointness opt_completeness GENSET genset_name \
                        LBRACE GENERAL CLASS_ID SPECIFICS class_id_list RBRACE
  """
  genset_token = p[3]
  name = p[4]
  general = p[7]

  node = ast_nodes.GeneralizationSet(
    line=genset_token.line,
    column=genset_token.column,
    name=name.value,
    general=general.value,
    specifics=p[9],
    disjointness=p[1],
    completeness=p[2],
  )

  semantic_actions.declare(name, SymbolCategory.GENSET)
  semantic_actions.resolve_later(general, _CLASS_ONLY, "uma classe")

  p[0] = node


def p_genset_name(p):
  "genset_name : CLASS_ID"
  p[0] = p[1]


def p_opt_disjointness(p):
  """
  opt_disjointness : DISJOINT
                    | OVERLAPPING
                    | empty
  """
  p[0] = p[1].value if p[1] is not None else None


def p_opt_completeness(p):
  """
  opt_completeness : COMPLETE
                    | INCOMPLETE
                    | empty
  """
  p[0] = p[1].value if p[1] is not None else None


def p_class_id_list(p):
  """
  class_id_list : CLASS_ID
                 | class_id_list COMMA CLASS_ID
  """
  token = p[1] if len(p) == 2 else p[3]
  semantic_actions.resolve_later(token, _CLASS_ONLY, "uma classe")

  p[0] = [token.value] if len(p) == 2 else [*p[1], token.value]


# --------------------------------------------------------------------------- #
# 6. Relações
# --------------------------------------------------------------------------- #


def p_relation_stereotype(p):
  """
  relation_stereotype : MATERIAL
                       | DERIVATION
                       | COMPARATIVE
                       | MEDIATION
                       | CHARACTERIZATION
                       | EXTERNALDEPENDENCE
                       | COMPONENTOF
                       | MEMBEROF
                       | SUBCOLLECTIONOF
                       | SUBQUALITYOF
                       | INSTANTIATION
                       | TERMINATION
                       | PARTICIPATIONAL
                       | PARTICIPATION
                       | HISTORICALDEPENDENCE
                       | CREATION
                       | MANIFESTATION
                       | BRINGSABOUT
                       | TRIGGERS
                       | COMPOSITION
                       | AGGREGATION
                       | INHERENCE
                       | VALUE
                       | FORMAL
                       | CONSTITUTION
  """
  p[0] = p[1]


def p_relation_symbol(p):
  """
  relation_symbol : ASSOCIATION
                   | COMPOSITION_L
                   | COMPOSITION_R
                   | COMPOSITION_LO
                   | COMPOSITION_RO
  """
  p[0] = p[1].value


def p_relation_declaration_named(p):
  """
  relation_declaration : AT relation_stereotype RELATION CLASS_ID opt_cardinality \
                          relation_symbol RELATION_ID relation_symbol opt_cardinality CLASS_ID
  """
  at_token = p[1]
  source = p[4]
  name = p[7]
  target = p[10]

  node = ast_nodes.Relation(
    line=at_token.line,
    column=at_token.column,
    stereotype=p[2].value,
    source=source.value,
    source_cardinality=p[5],
    symbol=p[6],
    name=name.value,
    target_cardinality=p[9],
    target=target.value,
  )

  semantic_actions.declare(name, SymbolCategory.RELATION)
  semantic_actions.resolve_later(source, _CLASS_ONLY, "uma classe")
  semantic_actions.resolve_later(target, _CLASS_ONLY, "uma classe")

  p[0] = node


def p_relation_declaration_anonymous(p):
  """
  relation_declaration : AT relation_stereotype RELATION CLASS_ID opt_cardinality \
                          relation_symbol opt_cardinality CLASS_ID
  """
  at_token = p[1]
  source = p[4]
  target = p[8]

  node = ast_nodes.Relation(
    line=at_token.line,
    column=at_token.column,
    stereotype=p[2].value,
    source=source.value,
    source_cardinality=p[5],
    symbol=p[6],
    name=None,
    target_cardinality=p[7],
    target=target.value,
  )

  semantic_actions.resolve_later(source, _CLASS_ONLY, "uma classe")
  semantic_actions.resolve_later(target, _CLASS_ONLY, "uma classe")

  p[0] = node


def p_relation_end_declaration_named(p):
  """
  relation_end_declaration : AT relation_stereotype opt_cardinality relation_symbol \
                              RELATION_ID relation_symbol opt_cardinality CLASS_ID
  """
  at_token = p[1]
  name = p[5]
  target = p[8]

  node = ast_nodes.Relation(
    line=at_token.line,
    column=at_token.column,
    stereotype=p[2].value,
    source=None,
    source_cardinality=p[3],
    symbol=p[4],
    name=name.value,
    target_cardinality=p[7],
    target=target.value,
  )

  semantic_actions.declare(name, SymbolCategory.RELATION)
  semantic_actions.resolve_later(target, _CLASS_ONLY, "uma classe")

  p[0] = node


def p_relation_end_declaration_anonymous(p):
  """
  relation_end_declaration : AT relation_stereotype opt_cardinality relation_symbol \
                              opt_cardinality CLASS_ID
  """
  at_token = p[1]
  target = p[6]

  node = ast_nodes.Relation(
    line=at_token.line,
    column=at_token.column,
    stereotype=p[2].value,
    source=None,
    source_cardinality=p[3],
    symbol=p[4],
    name=None,
    target_cardinality=p[5],
    target=target.value,
  )

  semantic_actions.resolve_later(target, _CLASS_ONLY, "uma classe")

  p[0] = node
