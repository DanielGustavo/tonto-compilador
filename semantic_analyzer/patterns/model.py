"""Modelo de dados da análise de padrões de projeto

Cada `Info` guarda o nó da AST em `node` e acrescenta o estado que existe
apenas na análise (`coerced_stereotype`, `origin`, `owner`)
"""

from dataclasses import dataclass

from syntax_analyzer import ast_nodes


@dataclass
class ClassInfo:
  node: ast_nodes.ClassDeclaration
  origin: str
  coerced_stereotype: str
  # Especializações declaradas mais as deduzidas.
  # As deduções mudam esta lista, e não `node.specializes`, para não alterar a AST.
  specializes: list[str]

  @classmethod
  def from_node(
    cls,
    node: ast_nodes.ClassDeclaration,
    origin: str,
  ) -> "ClassInfo":
    return cls(
      node=node,
      origin=origin,
      coerced_stereotype=node.stereotype,
      specializes=list(node.specializes),
    )


@dataclass(frozen=True)
class GensetInfo:
  node: ast_nodes.GeneralizationSet
  origin: str

  @classmethod
  def from_node(
    cls,
    node: ast_nodes.GeneralizationSet,
    origin: str,
  ) -> "GensetInfo":
    return cls(node=node, origin=origin)


@dataclass(frozen=True)
class ElementRef:
  name: str
  line: int
  column: int
  origin: str


@dataclass(frozen=True)
class RelationInfo:
  node: ast_nodes.Relation
  owner: str | None
  origin: str

  @classmethod
  def from_node(
    cls,
    node: ast_nodes.Relation,
    owner: str | None,
    origin: str,
  ) -> "RelationInfo":
    return cls(node=node, owner=owner, origin=origin)


@dataclass(frozen=True)
class SubkindMatch:
  variant: int
  generals: tuple[ElementRef, ...]
  specifics: tuple[ElementRef, ...]
  genset: ElementRef | None
  lines: tuple[int, ...]
  disjointness: str | None = None
  completeness: str | None = None
  deduced: bool = False


@dataclass(frozen=True)
class PatternDiagnostic:
  category: str  # "coercion", "deduction" ou "error"
  pattern: str
  message: str
  line: int
  column: int
  origin: str
  suggestion: str | None = None


@dataclass(frozen=True)
class RoleMatch:
  role: ElementRef
  generals: tuple[ElementRef, ...]
  relators: tuple[ElementRef, ...]
  genset: ElementRef | None
  lines: tuple[int, ...]
  deduced: bool = False


@dataclass(frozen=True)
class PhaseMatch:
  general: ElementRef
  specifics: tuple[ElementRef, ...]
  genset: ElementRef | None
  lines: tuple[int, ...]
  disjointness: str | None = None
  completeness: str | None = None
  deduced: bool = False


@dataclass(frozen=True)
class RelatorMatch:
  variant: int
  relator: ElementRef
  mediated: tuple[ElementRef, ...]
  materials: tuple[ElementRef, ...]
  lines: tuple[int, ...]
  deduced: bool = False


@dataclass(frozen=True)
class ModeMatch:
  mode: ElementRef
  hosts: tuple[ElementRef, ...]
  external_dependencies: tuple[ElementRef, ...]
  lines: tuple[int, ...]
  deduced: bool = False


@dataclass(frozen=True)
class RoleMixinMatch:
  variant: int
  role_mixin: ElementRef
  roles: tuple[ElementRef, ...]
  relators: tuple[ElementRef, ...]
  genset: ElementRef | None
  lines: tuple[int, ...]
  deduced: bool = False


@dataclass
class SubkindReport:
  matches: list[SubkindMatch]
  coercions: list[PatternDiagnostic]
  deductions: list[PatternDiagnostic]
  errors: list[PatternDiagnostic]


@dataclass
class PhaseReport:
  matches: list[PhaseMatch]
  coercions: list[PatternDiagnostic]
  deductions: list[PatternDiagnostic]
  errors: list[PatternDiagnostic]


@dataclass
class RoleReport:
  matches: list[RoleMatch]
  coercions: list[PatternDiagnostic]
  deductions: list[PatternDiagnostic]
  errors: list[PatternDiagnostic]


@dataclass
class RelatorReport:
  matches: list[RelatorMatch]
  coercions: list[PatternDiagnostic]
  deductions: list[PatternDiagnostic]
  errors: list[PatternDiagnostic]


@dataclass
class ModeReport:
  matches: list[ModeMatch]
  coercions: list[PatternDiagnostic]
  deductions: list[PatternDiagnostic]
  errors: list[PatternDiagnostic]


@dataclass
class RoleMixinReport:
  matches: list[RoleMixinMatch]
  coercions: list[PatternDiagnostic]
  deductions: list[PatternDiagnostic]
  errors: list[PatternDiagnostic]


@dataclass
class PatternReport:
  subkind: SubkindReport
  phase: PhaseReport
  role: RoleReport
  relator: RelatorReport
  mode: ModeReport
  role_mixin: RoleMixinReport
