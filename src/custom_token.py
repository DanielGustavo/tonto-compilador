from enum import Enum


class TokenEnum(Enum):
  CLASS_STEREOTYPES = "CLASS_STEREOTYPES"
  CLASS_ID = "CLASS_ID"
  RELATION_ID = "RELATION_ID"
  INSTANCE_ID = "INSTANCE_ID"


class CustomToken:
  def __init__(self, value: str, token_type: TokenEnum):
    self.value = value
    self.token_type = token_type
    # add line, column, ...

  def __str__(self):
    return f"CUSTOM_TOKEN({self.token_type}, {self.value})"
