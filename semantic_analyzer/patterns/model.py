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


@dataclass
class SubkindReport:
  matches: list[SubkindMatch]
  coercions: list[PatternDiagnostic]
  deductions: list[PatternDiagnostic]
  errors: list[PatternDiagnostic]


@dataclass
class PatternReport:
  subkind: SubkindReport
