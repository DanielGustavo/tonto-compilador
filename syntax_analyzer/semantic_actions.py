from dataclasses import dataclass

from .errors import SemanticError
from .symbol import Symbol, SymbolCategory
from .symbol_table import SymbolTable

package_table: SymbolTable = SymbolTable("pacote")
current_table: SymbolTable = package_table

semantic_errors: list[SemanticError] = []


@dataclass
class PendingReference:
  name: str
  line: int
  column: int
  expected: set[SymbolCategory]
  expected_label: str


_pending_references: list[PendingReference] = []


def reset() -> None:
  global package_table, current_table

  package_table = SymbolTable("pacote")
  current_table = package_table
  semantic_errors.clear()
  _pending_references.clear()


def declare(token, category: SymbolCategory) -> Symbol:
  symbol = Symbol(
    name=token.value, category=category, line=token.line, column=token.column
  )

  if not current_table.put(symbol):
    original = current_table.get_local(token.value)
    semantic_errors.append(
      SemanticError(
        value=token.value,
        line=token.line,
        column=token.column,
        message=(
          f"{category.value} '{token.value}' já foi declarado(a) neste escopo "
          f"(primeira declaração na linha {original.line if original else '?'})"
        ),
        suggestion="escolha um nome diferente ou remova a declaração duplicada.",
      )
    )

  return symbol


def enter_scope(scope_name: str) -> SymbolTable:
  global current_table

  current_table = SymbolTable(scope_name, prev=current_table)
  return current_table


def exit_scope() -> None:
  global current_table

  if current_table.prev is not None:
    current_table = current_table.prev


def recover_to_package_scope() -> None:
  global current_table

  current_table = package_table


def resolve_later(token, expected: set[SymbolCategory], expected_label: str) -> None:
  _pending_references.append(
    PendingReference(
      name=token.value,
      line=token.line,
      column=token.column,
      expected=expected,
      expected_label=expected_label,
    )
  )


def finalize() -> list[SemanticError]:
  for reference in _pending_references:
    symbol = package_table.get(reference.name)

    if symbol is None:
      semantic_errors.append(
        SemanticError(
          value=reference.name,
          line=reference.line,
          column=reference.column,
          message=f"'{reference.name}' não foi declarado(a)",
          suggestion=f"declare {reference.expected_label} '{reference.name}' em algum ponto do pacote.",
        )
      )
    elif symbol.category not in reference.expected:
      semantic_errors.append(
        SemanticError(
          value=reference.name,
          line=reference.line,
          column=reference.column,
          message=(
            f"'{reference.name}' é {symbol.category.value}, mas aqui era esperado "
            f"{reference.expected_label}"
          ),
          suggestion="confira se o nome usado está correto.",
        )
      )

  return list(semantic_errors)
