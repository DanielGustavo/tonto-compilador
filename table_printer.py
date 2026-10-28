"""Utilitário para desenhar tabelas"""


def format_table(header: tuple[str, ...], rows: list[tuple[str, ...]]) -> list[str]:
  widths = [
    max(len(header[i]), *(len(row[i]) for row in rows)) if rows else len(header[i])
    for i in range(len(header))
  ]

  def border(left: str, middle: str, right: str) -> str:
    return left + middle.join("─" * (width + 2) for width in widths) + right

  def row_line(row: tuple[str, ...]) -> str:
    cells = (f" {value.ljust(width)} " for value, width in zip(row, widths))
    return "│" + "│".join(cells) + "│"

  lines = [border("┌", "┬", "┐"), row_line(header), border("├", "┼", "┤")]
  lines += [row_line(row) for row in rows]
  lines.append(border("└", "┴", "┘"))

  return lines


def print_table(
  title: str, header: tuple[str, ...], rows: list[tuple[str, ...]], indent: str = ""
) -> None:
  print(f"\n{title}")

  if not rows:
    print(f"{indent}(nenhum)")
    return

  for line in format_table(header, rows):
    print(indent + line)
