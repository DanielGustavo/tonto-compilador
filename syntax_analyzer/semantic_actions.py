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


_pending_references: list[PendingReference] = []

_LABEL_BY_CATEGORY: dict[SymbolCategory, str] = {
  SymbolCategory.CLASS: "uma classe",
  SymbolCategory.DATATYPE: "um datatype",
  SymbolCategory.ENUM: "um enum",
  SymbolCategory.GENSET: "um genset",
  SymbolCategory.RELATION: "uma relação",
  SymbolCategory.ATTRIBUTE: "um atributo",
  SymbolCategory.LITERAL: "um literal",
}


def _describe_expected(expected: set[SymbolCategory]) -> str:
  ordered = [category for category in SymbolCategory if category in expected]

  if len(ordered) == 1:
    return _LABEL_BY_CATEGORY[ordered[0]]

  options = [category.value for category in ordered]
  return f"um tipo ({', '.join(options[:-1])} ou {options[-1]})"


def reset() -> None:
  global package_table, current_table

  package_table = SymbolTable("pacote")
  current_table = package_table
  semantic_errors.clear()
  _pending_references.clear()


def snapshot() -> dict:
  return {
    "package_table": package_table,
    "current_table": current_table,
    "semantic_errors": list(semantic_errors),
    "pending_references": list(_pending_references),
  }


def restore(snap: dict) -> None:
  global package_table, current_table

  package_table = snap["package_table"]
  current_table = snap["current_table"]

  semantic_errors.clear()
  semantic_errors.extend(snap["semantic_errors"])

  _pending_references.clear()
  _pending_references.extend(snap["pending_references"])


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


def declare_imported(
  name: str, category: SymbolCategory, line: int, column: int, package_name: str
) -> None:
  symbol = Symbol(
    name=name, category=category, line=line, column=column, source=package_name
  )

  if not package_table.put(symbol):
    original = package_table.get_local(name)
    origin = (
      f"no pacote importado '{original.source}'"
      if original is not None and original.source
      else "neste pacote"
    )

    semantic_errors.append(
      SemanticError(
        value=name,
        line=line,
        column=column,
        message=(
          f"{category.value} '{name}' do pacote importado '{package_name}' "
          f"conflita com um símbolo já declarado {origin} "
          f"(linha {original.line if original else '?'})"
        ),
        suggestion="renomeie um dos dois símbolos ou remova o import duplicado.",
      )
    )


def report_unresolved_import(name: str, line: int, column: int) -> None:
  semantic_errors.append(
    SemanticError(
      value=name,
      line=line,
      column=column,
      message=f"pacote importado '{name}' não foi encontrado",
      suggestion=(
        f"verifique se existe um arquivo '{name}.tonto' com 'package {name}' "
        "no mesmo diretório."
      ),
    )
  )


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


def resolve_later(token, expected: set[SymbolCategory]) -> None:
  _pending_references.append(
    PendingReference(
      name=token.value,
      line=token.line,
      column=token.column,
      expected=expected,
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
          suggestion=(
            f"declare {_describe_expected(reference.expected)} '{reference.name}' "
            "em algum ponto do pacote."
          ),
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
            f"{_describe_expected(reference.expected)}"
          ),
          suggestion="confira se o nome usado está correto.",
        )
      )

  return list(semantic_errors)
