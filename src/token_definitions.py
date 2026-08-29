__all__ = ["token_definitions", "TokenEnum"]


class TokenEnum:
  CLASS_STEREOTYPES = "CLASS_STEREOTYPES"
  CLASS = "CLASS"
  RELATION = "RELATION"
  INSTANCE = "INSTANCE"
  INVALID_IDENTIFIER = "INVALID_IDENTIFIER"


reserved_words = {
  TokenEnum.CLASS_STEREOTYPES: {
    "event": "EVENT",
    "situation": "SITUATION",
    "process": "PROCESS",
    "category": "CATEGORY",
    "mixin": "MIXIN",
    "phaseMixin": "PHASEMIXIN",
    "roleMixin": "ROLEMIXIN",
    "historicalRoleMixin": "HISTORICALROLEMIXIN",
    "kind": "KIND",
    "collective": "COLLECTIVE",
    "quantity": "QUANTITY",
    "quality": "QUALITY",
    "mode": "MODE",
    "intrisicMode": "INTRISICMODE",
    "extrinsicMode": "EXTRINSICMODE",
    "subkind": "SUBKIND",
    "phase": "PHASE",
    "role": "ROLE",
    "historicalRole": "HISTORICALROLE",
  }
}

token_definitions = {
  TokenEnum.CLASS_STEREOTYPES: reserved_words[TokenEnum.CLASS_STEREOTYPES],
  TokenEnum.CLASS: r"^[A-Z][a-zA-Z_]*$",
  TokenEnum.RELATION: r"^[a-z][a-zA-Z_]*$",
  TokenEnum.INSTANCE: r"^[a-zA-Z][a-zA-Z_0-9]*[0-9]+$",
}
