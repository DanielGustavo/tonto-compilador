KIND = "kind"
SUBKIND = "subkind"
PHASE = "phase"
ROLE = "role"
ROLE_MIXIN = "roleMixin"
RELATOR = "relator"

# possíveis pais imediatos de um subkind.
RIGID_SORTALS = {KIND, SUBKIND, "collective"}
# onde a cadeia de identidade termina.
IDENTITY_PROVIDERS = {KIND, "collective"}

# Universais que podem ser mediados por um relator.
SUBSTANTIALS = {
  KIND,
  SUBKIND,
  PHASE,
  ROLE,
  ROLE_MIXIN,
  "collective",
  "category",
  "mixin",
}

# Endurantes aceitos como portadores de um mode.
ENDURANTS = {
  KIND,
  SUBKIND,
  PHASE,
  ROLE,
  ROLE_MIXIN,
  "historicalRole",
  "historicalRoleMixin",
  "phaseMixin",
  "category",
  "mixin",
  "collective",
  "quantity",
  "quality",
  RELATOR,
  "mode",
  "intrisicMode",
  "extrinsicMode",
}

# General aceitável para uma partição de phases.
PHASE_GENERALS = {KIND, SUBKIND, "collective", PHASE}
# General aceitável para um role.
ROLE_GENERALS = {KIND, SUBKIND, "collective", PHASE, ROLE, ROLE_MIXIN}

MIXIN_STEREOTYPES = {"category", "mixin"}
MODE_STEREOTYPES = {"mode", "intrisicMode", "extrinsicMode"}
INHERENCE_STEREOTYPES = {"characterization", "inherence"}
EXTERNAL_DEPENDENCE_STEREOTYPES = {"externalDependence"}

# Relações que podem ser lidas como uma mediação
MEDIATION_STEREOTYPES = {"mediation", "material"}
