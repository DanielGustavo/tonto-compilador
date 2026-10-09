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
