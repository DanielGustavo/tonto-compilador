from custom_token import TokenEnum

reserved_words = {
  # class stereotypes
  "event": ("EVENT", TokenEnum.CLASS_STEREOTYPES),
  "situation": ("SITUATION", TokenEnum.CLASS_STEREOTYPES),
  "process": ("PROCESS", TokenEnum.CLASS_STEREOTYPES),
  "category": ("CATEGORY", TokenEnum.CLASS_STEREOTYPES),
  "mixin": ("MIXIN", TokenEnum.CLASS_STEREOTYPES),
  "phaseMixin": ("PHASEMIXIN", TokenEnum.CLASS_STEREOTYPES),
  "roleMixin": ("ROLEMIXIN", TokenEnum.CLASS_STEREOTYPES),
  "historicalRoleMixin": ("HISTORICALROLEMIXIN", TokenEnum.CLASS_STEREOTYPES),
  "kind": ("KIND", TokenEnum.CLASS_STEREOTYPES),
  "collective": ("COLLECTIVE", TokenEnum.CLASS_STEREOTYPES),
  "quantity": ("QUANTITY", TokenEnum.CLASS_STEREOTYPES),
  "quality": ("QUALITY", TokenEnum.CLASS_STEREOTYPES),
  "mode": ("MODE", TokenEnum.CLASS_STEREOTYPES),
  "intrisicMode": ("INTRISICMODE", TokenEnum.CLASS_STEREOTYPES),
  "extrinsicMode": ("EXTRINSICMODE", TokenEnum.CLASS_STEREOTYPES),
  "subkind": ("SUBKIND", TokenEnum.CLASS_STEREOTYPES),
  "phase": ("PHASE", TokenEnum.CLASS_STEREOTYPES),
  "role": ("ROLE", TokenEnum.CLASS_STEREOTYPES),
  "historicalRole": ("HISTORICALROLE", TokenEnum.CLASS_STEREOTYPES),
  # ...
}

token_definitions = {
  TokenEnum.INSTANCE_ID: r"[a-zA-Z_][a-zA-Z0-9_]*[0-9]",
  TokenEnum.CLASS_ID: r"[A-Z_][a-zA-Z_]*",
  TokenEnum.RELATION_ID: r"[a-z_][a-zA-Z_]*",
}
