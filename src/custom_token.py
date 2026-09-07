from enum import Enum


class TokenEnum(Enum):
  CLASS_STEREOTYPES = "CLASS_STEREOTYPES"
  RELATION_STEREOTYPES = "RELATION_STEREOTYPES"
  NATIVE_TYPES = "NATIVE_TYPES"
  META_ATTRIBUTES = "META_ATTRIBUTES"
  KEYWORDS = "KEYWORDS"
  CLASS_ID = "CLASS_ID"
  RELATION_ID = "RELATION_ID"
  INSTANCE_ID = "INSTANCE_ID"
  NEW_TYPE = "NEW_TYPE"
  FUNCTIONAL_COMPLEXES = "FUNCTIONAL_COMPLEXES"
  INTRINSIC_MODES = "INTRINSIC_MODES"
  COMPOSITION_L = "COMPOSITION_L"
  COMPOSITION_R = "COMPOSITION_R"
  COMPOSITION_LO = "COMPOSITION_LO"
  COMPOSITION_RO = "COMPOSITION_RO"
  ASSOCIATION = "ASSOCIATION"
  CARDINALITY = "CARDINALITY"
  # literals
  LPAREN = "LPAREN"
  RPAREN = "RPAREN"
  LBRACE = "LBRACE"
  RBRACE = "RBRACE"
  DOT = "DOT"
  COMMA = "COMMA"
  PLUS = "PLUS"
  LT = "LT"
  GT = "GT"
  AT = "AT"
  MINUS = "MINUS"
  STAR = "STAR"
  COLON = "COLON"


class CustomToken:
  def __init__(self, value: str, token_type: TokenEnum, line: int, column: int):
    self.value = value
    self.token_type = token_type
    self.line = line
    self.column = column

  def __str__(self):
    return f"CUSTOM_TOKEN({self.token_type}, {self.value}, line={self.line}, column={self.column})"
