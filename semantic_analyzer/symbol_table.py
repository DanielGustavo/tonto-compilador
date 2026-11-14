"""Tabela de símbolos encadeada: cada escopo aponta para o escopo que o envolve"""

from .symbol import Symbol


class SymbolTable:
  def __init__(self, scope_name: str, prev: "SymbolTable | None" = None):
    self.scope_name = scope_name
    self.prev = prev
    self.symbols: dict[str, Symbol] = {}
    self.children: list[SymbolTable] = []

    if prev is not None:
      prev.children.append(self)

  def put(self, symbol: Symbol) -> bool:
    if symbol.name in self.symbols:
      return False

    self.symbols[symbol.name] = symbol
    return True

  def get_local(self, name: str) -> Symbol | None:
    return self.symbols.get(name)

  def get(self, name: str) -> Symbol | None:
    table: SymbolTable | None = self

    while table is not None:
      symbol = table.symbols.get(name)

      if symbol is not None:
        return symbol

      table = table.prev

    return None
