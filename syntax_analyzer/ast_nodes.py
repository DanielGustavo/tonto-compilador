"""Nós da AST produzida pelo Analisador Sintático.

Um `Node(line, column)` base e um dataclass por construção da linguagem
TONTO (classes, relações, datatypes, enums, gensets, pacotes e imports),
montados pelas regras de `grammar_rules.py` e consumidos pelas ações
semânticas e pelos reporters.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
  line: int
  column: int

  def label(self) -> str:
    raise NotImplementedError

  def children(self) -> list["Node"]:
    return []


@dataclass(frozen=True)
class Literal(Node):
  """Indivíduo de uma classe enumerada."""

  name: str

  def label(self) -> str:
    return f"literal {self.name}"


@dataclass(frozen=True)
class Enumeration(Node):
  """Enum: classe de enumeração."""

  name: str
  literals: list[Literal]

  def label(self) -> str:
    return f"enum {self.name}"

  def children(self) -> list[Node]:
    return list(self.literals)


@dataclass(frozen=True)
class Attribute(Node):
  """Atributo próprio de uma classe."""

  name: str
  type_name: str
  cardinality: str | None
  modifiers: list[str]

  def label(self) -> str:
    suffix = f" {self.cardinality}" if self.cardinality else ""
    if self.modifiers:
      suffix += " {" + ", ".join(self.modifiers) + "}"
    return f"attribute {self.name}: {self.type_name}{suffix}"


@dataclass(frozen=True)
class ClassDeclaration(Node):
  """Declaração de classe (estereótipo + nome + especialização + membros)."""

  stereotype: str
  name: str
  specializes: list[str]
  members: list[Node]

  def label(self) -> str:
    suffix = f" specializes {', '.join(self.specializes)}" if self.specializes else ""
    return f"<<{self.stereotype}>> {self.name}{suffix}"

  def children(self) -> list[Node]:
    return list(self.members)


@dataclass(frozen=True)
class Relation(Node):
  """Declaração de relação (interna a uma classe ou externa, a nível de pacote)."""

  stereotype: str
  source: str | None
  source_cardinality: str | None
  symbol: str
  name: str | None
  target_cardinality: str | None
  target: str

  def label(self) -> str:
    source = self.source if self.source is not None else "(implicit)"
    parts = [f"<<{self.stereotype}>>", source]
    if self.source_cardinality:
      parts.append(self.source_cardinality)
    parts.append(self.symbol)
    if self.name:
      parts.append(self.name)
      parts.append(self.symbol)
    if self.target_cardinality:
      parts.append(self.target_cardinality)
    parts.append(self.target)
    return " ".join(parts)


@dataclass(frozen=True)
class DataTypeDeclaration(Node):
  """Declaração de tipo de dado derivado (datatype)."""

  name: str
  attributes: list[Attribute]

  def label(self) -> str:
    return f"datatype {self.name}"

  def children(self) -> list[Node]:
    return list(self.attributes)


@dataclass(frozen=True)
class GeneralizationSet(Node):
  """Genset: agrupamento de generalização (classe geral + classes específicas)."""

  name: str
  general: str
  specifics: list[str]
  disjointness: str | None
  completeness: str | None

  def label(self) -> str:
    modifiers = " ".join(m for m in (self.disjointness, self.completeness) if m)
    prefix = f"{modifiers} " if modifiers else ""
    specifics = ", ".join(self.specifics)
    return f"{prefix}genset {self.name} where {specifics} specializes {self.general}"


@dataclass(frozen=True)
class Import(Node):
  """Importação de outro pacote."""

  name: str

  def label(self) -> str:
    return f"import {self.name}"


@dataclass(frozen=True)
class Package(Node):
  """Package: o namespace que contém todas as declarações."""

  name: str
  declarations: list[Node]

  def label(self) -> str:
    return f"package {self.name}"

  def children(self) -> list[Node]:
    return list(self.declarations)


@dataclass(frozen=True)
class Program(Node):
  """Raiz da árvore: os imports e o pacote da especificação."""

  imports: list[Import]
  package: Package | None

  def label(self) -> str:
    return "program"

  def children(self) -> list[Node]:
    if self.package is None:
      return list(self.imports)

    return [*self.imports, self.package]
