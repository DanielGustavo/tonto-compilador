"""Define o que é um símbolo para o Analisador Semântico.

`SymbolCategory` enumera as categorias de nomes que a linguagem TONTO permite
declarar (classe, datatype, enum, genset, relação, atributo, literal).
`Symbol` é o registro guardado em uma `SymbolTable`: nome, categoria, linha e
coluna da declaração, e o pacote de origem (`source`) quando o símbolo veio
de um import resolvido por `parser.py`.
"""

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
