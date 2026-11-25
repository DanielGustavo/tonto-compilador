"""Funções utilitárias compartilhadas pelos matchers de padrões."""

from .model import (
  ClassInfo,
  ElementRef,
  GensetInfo,
  PatternDiagnostic,
  RelationInfo,
)


def ref_of(info: ClassInfo | GensetInfo | RelationInfo) -> ElementRef:
  """Converte uma classe, genset ou relação em uma referência de relatório"""

  name = info.node.name

  if name is None:
    name = "anônima"

  return ElementRef(
    name=name,
    line=info.node.line,
    column=info.node.column,
    origin=info.origin,
  )


def diagnostic(
  pattern: str,
  category: str,
  message: str,
  info: ClassInfo | GensetInfo | RelationInfo,
  suggestion: str | None = None,
) -> PatternDiagnostic:
  """Cria um diagnóstico usando linha, coluna e origem do nó"""

  return PatternDiagnostic(
    category=category,
    pattern=pattern,
    message=message,
    line=info.node.line,
    column=info.node.column,
    origin=info.origin,
    suggestion=suggestion,
  )


def unique_refs(infos: list[ClassInfo]) -> tuple[ElementRef, ...]:
  """Converte as classes em referências sem repetir o mesmo `(nome, linha)`"""

  refs: list[ElementRef] = []
  seen: set[tuple[str, int]] = set()

  for info in infos:
    key = (info.node.name, info.node.line)

    if key in seen:
      continue

    seen.add(key)
    refs.append(ref_of(info))

  return tuple(refs)
