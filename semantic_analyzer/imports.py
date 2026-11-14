"""Resolução semântica de imports entre arquivos `.tonto`."""

import re
from collections.abc import Callable
from pathlib import Path

from syntax_analyzer import ast_nodes
from syntax_analyzer.ast_nodes import Node

from . import semantic_actions
from .symbol import SymbolCategory

_PACKAGE_NAME_RE = re.compile(r"^\s*package\s+([A-Z][a-zA-Z_]*)", re.MULTILINE)


def _index_packages_by_name(base_dir: Path) -> dict[str, Path]:
  indice: dict[str, Path] = {}

  for arquivo in base_dir.glob("*.tonto"):
    match = _PACKAGE_NAME_RE.search(arquivo.read_text(encoding="utf-8"))

    if match is not None:
      indice[match.group(1)] = arquivo

  return indice


def resolve_imports(
  programa: ast_nodes.Program,
  base_dir: Path | None,
  parse_file: Callable[[Path], ast_nodes.Program | None],
) -> list[tuple[Node, str]]:
  importados: list[tuple[Node, str]] = []

  if base_dir is None or not programa.imports:
    return importados

  pacote_atual = programa.package.name if programa.package else None
  indice = _index_packages_by_name(base_dir)

  # Busca em grafo sobre os imports: cada pacote resolvido também pode
  # importar outros, então os imports do arquivo importado são enfileirados
  # de volta (`fila.extend(...)` mais abaixo). `visitados` evita reprocessar
  # o mesmo pacote em caso de import cíclico ou duplicado.
  visitados: set[str] = {pacote_atual} if pacote_atual else set()
  fila: list[ast_nodes.Import] = list(programa.imports)

  while fila:
    importacao = fila.pop(0)

    if importacao.name in visitados:
      continue

    visitados.add(importacao.name)
    caminho = indice.get(importacao.name)

    if caminho is None:
      semantic_actions.report_unresolved_import(
        importacao.name, importacao.line, importacao.column
      )
      continue

    arvore_importada = parse_file(caminho)

    if arvore_importada is None or arvore_importada.package is None:
      continue

    pacote_importado = arvore_importada.package

    for declaracao in pacote_importado.declarations:
      if isinstance(declaracao, ast_nodes.ClassDeclaration):
        categoria = SymbolCategory.CLASS
      elif isinstance(declaracao, ast_nodes.DataTypeDeclaration):
        categoria = SymbolCategory.DATATYPE
      elif isinstance(declaracao, ast_nodes.Enumeration):
        categoria = SymbolCategory.ENUM
      elif isinstance(declaracao, ast_nodes.GeneralizationSet):
        categoria = SymbolCategory.GENSET
      elif isinstance(declaracao, ast_nodes.Relation):
        categoria = SymbolCategory.RELATION
      else:
        continue

      if declaracao.name is not None:
        semantic_actions.declare_imported(
          declaracao.name,
          categoria,
          declaracao.line,
          declaracao.column,
          importacao.name,
        )
      importados.append((declaracao, importacao.name))

    fila.extend(arvore_importada.imports)

  return importados
