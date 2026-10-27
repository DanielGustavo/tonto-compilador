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


# --------------------------------------------------------------------------- #
# 3. Classes
# --------------------------------------------------------------------------- #


def p_class_declaration(p):
  "class_declaration : class_stereotype CLASS_ID opt_specializes opt_class_body"
  stereotype = p[1]
  name = p[2]

  p[0] = ast_nodes.ClassDeclaration(
    line=stereotype.line,
    column=stereotype.column,
    stereotype=stereotype.value,
    name=name.value,
    specializes=p[3],
    members=p[4],
  )


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
  p[0] = p[2].value if len(p) == 3 else None


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

  p[0] = ast_nodes.Attribute(
    line=name.line,
    column=name.column,
    name=name.value,
    type_name=p[3],
    cardinality=p[4],
    modifiers=p[5],
  )


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
  p[0] = p[1].value


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
  "datatype_declaration : DATATYPE CLASS_ID LBRACE attributes_list RBRACE"
  p[0] = ast_nodes.DataTypeDeclaration(
    line=p[1].line, column=p[1].column, name=p[2].value, attributes=p[4]
  )


# --------------------------------------------------------------------------- #
# 5. Generalizações (genset)
# --------------------------------------------------------------------------- #


def p_genset_declaration_where(p):
  """
  genset_declaration : opt_disjointness opt_completeness GENSET genset_name \
                        WHERE class_id_list SPECIALIZES CLASS_ID
  """
  genset_token = p[3]

  p[0] = ast_nodes.GeneralizationSet(
    line=genset_token.line,
    column=genset_token.column,
    name=p[4].value,
    general=p[8].value,
    specifics=p[6],
    disjointness=p[1],
    completeness=p[2],
  )


def p_genset_declaration_block(p):
  """
  genset_declaration : opt_disjointness opt_completeness GENSET genset_name \
                        LBRACE GENERAL CLASS_ID SPECIFICS class_id_list RBRACE
  """
  genset_token = p[3]

  p[0] = ast_nodes.GeneralizationSet(
    line=genset_token.line,
    column=genset_token.column,
    name=p[4].value,
    general=p[7].value,
    specifics=p[9],
    disjointness=p[1],
    completeness=p[2],
  )


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

  p[0] = ast_nodes.Relation(
    line=at_token.line,
    column=at_token.column,
    stereotype=p[2].value,
    source=p[4].value,
    source_cardinality=p[5],
    symbol=p[6],
    name=p[7].value,
    target_cardinality=p[9],
    target=p[10].value,
  )


def p_relation_declaration_anonymous(p):
  """
  relation_declaration : AT relation_stereotype RELATION CLASS_ID opt_cardinality \
                          relation_symbol opt_cardinality CLASS_ID
  """
  at_token = p[1]

  p[0] = ast_nodes.Relation(
    line=at_token.line,
    column=at_token.column,
    stereotype=p[2].value,
    source=p[4].value,
    source_cardinality=p[5],
    symbol=p[6],
    name=None,
    target_cardinality=p[7],
    target=p[8].value,
  )


def p_relation_end_declaration_named(p):
  """
  relation_end_declaration : AT relation_stereotype opt_cardinality relation_symbol \
                              RELATION_ID relation_symbol opt_cardinality CLASS_ID
  """
  at_token = p[1]

  p[0] = ast_nodes.Relation(
    line=at_token.line,
    column=at_token.column,
    stereotype=p[2].value,
    source=None,
    source_cardinality=p[3],
    symbol=p[4],
    name=p[5].value,
    target_cardinality=p[7],
    target=p[8].value,
  )


def p_relation_end_declaration_anonymous(p):
  """
  relation_end_declaration : AT relation_stereotype opt_cardinality relation_symbol \
                              opt_cardinality CLASS_ID
  """
  at_token = p[1]

  p[0] = ast_nodes.Relation(
    line=at_token.line,
    column=at_token.column,
    stereotype=p[2].value,
    source=None,
    source_cardinality=p[3],
    symbol=p[4],
    name=None,
    target_cardinality=p[5],
    target=p[6].value,
  )
