"""Padrões de projeto reconhecidos a partir da AST sintática.

Este pacote roda depois de `semantic_actions.finalize()`, `analyze_patterns` é
a fachada usada pelo `main.py`.
"""

from syntax_analyzer import ast_nodes

from .index import OntologyIndex, build_index
from .model import (
  ClassInfo,
  ElementRef,
  GensetInfo,
  PatternDiagnostic,
  PatternReport,
  RelationInfo,
  RoleMatch,
  RoleReport,
  SubkindMatch,
  SubkindReport,
)
from .reporter import print_pattern_report
from .role import analyze_role_patterns
from .subkind import analyze_subkind_patterns

__all__ = [
  "ClassInfo",
  "ElementRef",
  "GensetInfo",
  "OntologyIndex",
  "PatternDiagnostic",
  "PatternReport",
  "RelationInfo",
  "RoleMatch",
  "RoleReport",
  "SubkindMatch",
  "SubkindReport",
  "analyze_patterns",
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

  return PatternReport(
    subkind=analyze_subkind_patterns(index),
    role=analyze_role_patterns(index),
  )
