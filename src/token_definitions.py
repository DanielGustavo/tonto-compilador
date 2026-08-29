__all__ = ["token_definitions"]

reserved_words = {
  "CLASS_STEREOTYPES": {
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
  "CLASS_STEREOTYPES": reserved_words["CLASS_STEREOTYPES"],
  "CLASS": r"[A-Z][a-zA-Z_]*",
}
