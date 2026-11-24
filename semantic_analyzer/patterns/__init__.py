"""Padrões de projeto reconhecidos a partir da AST sintática.

Este pacote roda depois de `semantic_actions.finalize()`, `analyze_patterns` é
a fachada usada pelo `main.py`.
"""

from syntax_analyzer import ast_nodes

from .index import OntologyIndex, build_index
from .mode import analyze_mode_patterns
from .model import (
  ClassInfo,
  ElementRef,
  GensetInfo,
  ModeMatch,
  ModeReport,
  PatternDiagnostic,
  PatternReport,
  PhaseMatch,
  PhaseReport,
  RelationInfo,
  RelatorMatch,
  RelatorReport,
  RoleMatch,
  RoleMixinMatch,
  RoleMixinReport,
  RoleReport,
  SubkindMatch,
  SubkindReport,
)
from .phase import analyze_phase_patterns
from .relator import analyze_relator_patterns
from .reporter import print_pattern_report
from .role import analyze_role_patterns
from .role_mixin import analyze_role_mixin_patterns
from .subkind import analyze_subkind_patterns

__all__ = [
  "ClassInfo",
  "ElementRef",
  "GensetInfo",
  "ModeMatch",
  "ModeReport",
  "OntologyIndex",
  "PatternDiagnostic",
  "PatternReport",
  "PhaseMatch",
  "PhaseReport",
  "RelationInfo",
  "RelatorMatch",
  "RelatorReport",
  "RoleMatch",
  "RoleMixinMatch",
  "RoleMixinReport",
  "RoleReport",
  "SubkindMatch",
  "SubkindReport",
  "analyze_mode_patterns",
  "analyze_patterns",
  "analyze_phase_patterns",
  "analyze_relator_patterns",
  "analyze_role_mixin_patterns",
  "analyze_role_patterns",
  "analyze_subkind_patterns",
  "build_index",
  "print_pattern_report",
]


def analyze_patterns(
  program: ast_nodes.Program,
  imported: list[tuple[ast_nodes.Node, str]],
) -> PatternReport:
  index = build_index(program, imported)

  # O phase roda antes do subkind para que a coerção subkind -> phase seja
  # aplicada antes de o Subkind tratar o subkind como erro de general.
  phase = analyze_phase_patterns(index)

  # O subkind roda antes do relator para que a coerção kind -> subkind de
  # classes com general não seja sobrescrita pela coerção kind -> relator.
  subkind = analyze_subkind_patterns(index)

  # O mode roda antes do relator para que um kind coercido para mode deixe de
  # ser aceito como universal substancial
  mode = analyze_mode_patterns(index)

  # O relator roda antes do role para que a coerção kind -> relator já esteja
  # aplicada quando o Role procurar as mediações.
  relator = analyze_relator_patterns(index)

  # O roleMixin roda depois do relator e antes do role
  role_mixin = analyze_role_mixin_patterns(index)

  return PatternReport(
    subkind=subkind,
    phase=phase,
    relator=relator,
    role=analyze_role_patterns(index),
    mode=mode,
    role_mixin=role_mixin,
  )
