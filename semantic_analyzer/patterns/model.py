"""Modelo de dados da análise de padrões de projeto"""

from dataclasses import dataclass


@dataclass
class ClassInfo:
  name: str
  declared_stereotype: str
  coerced_stereotype: str
  specializes: list[str]
  line: int
  column: int
  origin: str


@dataclass(frozen=True)
class GensetInfo:
  name: str
  general: str
  specifics: tuple[str, ...]
  disjointness: str | None
  completeness: str | None
  line: int
  column: int
  origin: str


@dataclass(frozen=True)
class ElementRef:
  name: str
  line: int
  column: int
  origin: str


@dataclass(frozen=True)
class RelationInfo:
  name: str | None
  stereotype: str
  source: str | None
  target: str
  source_cardinality: str | None
  target_cardinality: str | None
  owner: str | None
  symbol: str
  line: int
  column: int
  origin: str


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
class PatternReport:
  subkind: SubkindReport
  phase: PhaseReport
  role: RoleReport
  relator: RelatorReport
  mode: ModeReport
