from dataclasses import dataclass
from enum import Enum


class SymbolCategory(Enum):
  CLASS = "classe"
  DATATYPE = "datatype"
  ENUM = "enum"
  GENSET = "genset"
  RELATION = "relação"
  ATTRIBUTE = "atributo"
  LITERAL = "literal"


@dataclass
class Symbol:
  name: str
  category: SymbolCategory
  line: int
  column: int
  source: str | None = None
