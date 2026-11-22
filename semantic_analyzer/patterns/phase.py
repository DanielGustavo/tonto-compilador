"""Reconhecimento do padrão Phase

O padrão Phase: um genset disjoint com duas ou mais phases que especializam o
mesmo sortal. Além disso, o matcher trata a coerção de um subkind sob uma phase
e deduz o que falta.
"""

from .index import OntologyIndex
from .model import (
  ClassInfo,
  ElementRef,
  GensetInfo,
  PatternDiagnostic,
  PhaseMatch,
  PhaseReport,
)
from .subkind import has_identity_provider

PATTERN = "Phase"

PHASE_GENERALS = {"kind", "subkind", "collective", "phase"}
MIN_PHASES = 2


def analyze_phase_patterns(index: OntologyIndex) -> PhaseReport:
  """
  Analisa as phases do índice e monta o relatório do padrão Phase

  Aplica a coerção subkind -> phase, valida as partições explícitas e trata as
  phases que ficaram fora de um genset válido
  """

  coercions: list[PatternDiagnostic] = []
  deductions: list[PatternDiagnostic] = []
  errors: list[PatternDiagnostic] = []
  matches: list[PhaseMatch] = []
  covered: set[str] = set()

  # A coerção precisa vir antes das partições para que um subkind sob phase
  # já seja tratado como phase na validação do genset.
  _coerce_subkinds_under_phase(index, coercions)

  # Partições explícitas: genset + general sortal + duas ou mais phases.
  _partitions(index, matches, deductions, errors, covered)

  # O que sobrou: phases sem partição válida (padrão incompleto ou erro).
  _uncovered_phases(index, deductions, errors, covered)

  return PhaseReport(
    matches=matches,
    coercions=coercions,
    deductions=deductions,
    errors=errors,
  )


def _ref(info) -> ElementRef:
  """Converte uma classe ou genset em uma referência de relatório"""
  return ElementRef(
    name=info.name,
    line=info.line,
    column=info.column,
    origin=info.origin,
  )


def _diagnostic(
  category: str,
  message: str,
  info,
  suggestion: str | None = None,
) -> PatternDiagnostic:
  """Cria um diagnóstico do Phase usando linha, coluna e origem do nó"""
  return PatternDiagnostic(
    category=category,
    pattern=PATTERN,
    message=message,
    line=info.line,
    column=info.column,
    origin=info.origin,
    suggestion=suggestion,
  )


def _coerce_subkinds_under_phase(
  index: OntologyIndex,
  coercions: list[PatternDiagnostic],
) -> None:
  """
  Subkind -> Phase, para subkinds que especializam uma phase
  """

  # Repete até estabilizar para tratar cadeias de subkinds sob phase
  changed = True

  while changed:
    changed = False

    for info in index.classes.values():
      # Só interessa quem foi declarado subkind e ainda não virou phase
      if info.declared_stereotype != "subkind" or info.coerced_stereotype == "phase":
        continue

      parent = _phase_parent(info, index)

      if parent is None:
        continue

      info.coerced_stereotype = "phase"
      changed = True
      coercions.append(
        _diagnostic(
          "coercion",
          (
            f"subkind '{info.name}' especializa a phase '{parent.name}', "
            "estereótipo coercido de 'subkind' para 'phase'."
          ),
          info,
          (
            f"declare '{info.name}' explicitamente como 'phase {info.name} "
            f"specializes {parent.name}' (coerção subkind -> phase)."
          ),
        )
      )


def _phase_parent(info: ClassInfo, index: OntologyIndex) -> ClassInfo | None:
  """Devolve o primeiro general de `info` que é uma phase"""

  for parent_name in info.specializes:
    parent = index.classes.get(parent_name)

    if parent is not None and parent.coerced_stereotype == "phase":
      return parent

  return None


def _partitions(
  index: OntologyIndex,
  matches: list[PhaseMatch],
  deductions: list[PatternDiagnostic],
  errors: list[PatternDiagnostic],
  covered: set[str],
) -> None:
  """
  Valida as partições explícitas de phases

  Uma partição é um genset onde o general é sortal e os specifics são
  phases (duas ou mais). Partições válidas viram matches, e as inválidas geram
  erro
  """

  for genset in index.gensets:
    general = index.classes.get(genset.general)

    # gensets de outros padrões ou com general desconhecido
    if general is None or general.coerced_stereotype not in PHASE_GENERALS:
      continue

    specific_infos = [
      index.classes[name] for name in genset.specifics if name in index.classes
    ]
    phase_infos = [
      info for info in specific_infos if info.coerced_stereotype == "phase"
    ]

    # sem nenhuma phase, o genset faz parte de outro padrão
    if not phase_infos:
      continue

    # Partição não pode misturar phases com outros estereótipos
    if len(phase_infos) != len(specific_infos):
      invalid = ", ".join(
        info.name for info in specific_infos if info.coerced_stereotype != "phase"
      )

      errors.append(
        _diagnostic(
          "error",
          (
            f"genset de fases '{genset.name}' mistura phases com outros "
            f"estereótipos ({invalid})."
          ),
          genset,
          "inclua no genset apenas classes declaradas como 'phase'.",
        )
      )
      continue

    # uma partição precisa de pelo menos duas fases complementares
    if len(phase_infos) < MIN_PHASES:
      errors.append(
        _diagnostic(
          "error",
          (
            f"genset de fases '{genset.name}' possui {len(phase_infos)} fase(s); "
            f"uma partição exige ao menos {MIN_PHASES}."
          ),
          genset,
          "acrescente outra phase ao genset para completar a partição.",
        )
      )
      continue

    # Partição exige disjunção
    if genset.disjointness != "disjoint":
      errors.append(
        _diagnostic(
          "error",
          f"genset de fases '{genset.name}' deve ser disjoint.",
          genset,
          f"declare '{genset.name}' como 'disjoint'.",
        )
      )
      continue

    # Valida as arestas `specializes` e a cadeia de identidade do general e das fases.
    edges_ok, edges_deduced = _partition_edges(
      index, genset, general, phase_infos, deductions, errors
    )

    if not edges_ok:
      continue

    lines = sorted(
      {
        genset.line,
        general.line,
        *(info.line for info in phase_infos),
      }
    )

    matches.append(
      PhaseMatch(
        general=_ref(general),
        specifics=tuple(_ref(info) for info in phase_infos),
        genset=_ref(genset),
        lines=tuple(lines),
        disjointness=genset.disjointness,
        completeness=genset.completeness,
        deduced=edges_deduced,
      )
    )

    covered.update(info.name for info in phase_infos)


def _partition_edges(
  index: OntologyIndex,
  genset: GensetInfo,
  general: ClassInfo,
  phase_infos: list[ClassInfo],
  deductions: list[PatternDiagnostic],
  errors: list[PatternDiagnostic],
) -> tuple[bool, bool]:
  """
  cada phase precisa especializar o general. Uma phase sem `specializes` tem a
  aresta deduzida. Uma phase que especializa outro general gera erro. Devolve
  `(válido, houve_dedução_de_aresta)`
  """

  pending: list[ClassInfo] = []
  valid = True

  for info in phase_infos:
    if general.name in info.specializes:
      continue

    # Sem nenhum general, a aresta é deduzida a partir do genset
    if not info.specializes:
      pending.append(info)
      continue

    # Especializa outro general: a partição está inconsistente
    valid = False
    errors.append(
      _diagnostic(
        "error",
        (
          f"'{info.name}' não especializa o general "
          f"'{general.name}' do genset '{genset.name}'."
        ),
        info,
        (
          f"faça '{info.name}' especializar '{general.name}' ou remova "
          f"do genset '{genset.name}'."
        ),
      )
    )

  if not valid:
    return False, False

  # As deduções entram temporariamente no índice para que a checagem de
  # identidade considere o general. Se algo falhar, elas são desfeitas
  for info in pending:
    info.specializes.append(general.name)

  # O general precisa alcançar um provedor de identidade (sortal).
  if not has_identity_provider(general, index):
    valid = False
    errors.append(
      _diagnostic(
        "error",
        (
          f"o general '{general.name}' do genset '{genset.name}' não "
          "alcança um kind/collective provedor de identidade."
        ),
        general,
        (
          f"faça '{general.name}' especializar direta ou indiretamente um "
          "kind ou collective."
        ),
      )
    )

  for info in phase_infos:
    if has_identity_provider(info, index):
      continue

    valid = False
    errors.append(
      _diagnostic(
        "error",
        (
          f"a phase '{info.name}' do genset '{genset.name}' não alcança um "
          "kind/collective provedor de identidade."
        ),
        info,
        (
          f"faça '{info.name}' especializar direta ou indiretamente um "
          "kind ou collective."
        ),
      )
    )

  # Falhou a identidade: desfaz as arestas deduzidas e não emite dedução.
  if not valid:
    for info in pending:
      info.specializes.remove(general.name)
    return False, False

  # Tudo certo: as arestas deduzidas passam a valer e são reportadas.
  for info in pending:
    deductions.append(
      _diagnostic(
        "deduction",
        (
          f"'{info.name}' não declara 'specializes {general.name}', mas o "
          f"genset '{genset.name}' o agrupa sob '{general.name}'."
        ),
        info,
        (
          f"declare explicitamente 'phase {info.name} specializes "
          f"{general.name}' (dedução pela sobrecarga do genset)."
        ),
      )
    )

  return True, bool(pending)


def _uncovered_phases(
  index: OntologyIndex,
  deductions: list[PatternDiagnostic],
  errors: list[PatternDiagnostic],
  covered: set[str],
) -> None:
  """
  Trata as phases que não entraram em nenhuma partição válida

  Valida o general de cada phase. E para um general que tem fases sem
  genset, emite a dedução de partição incompleta
  """

  # Valida cada phase individualmente (general e identidade)
  for info in index.classes.values():
    if info.coerced_stereotype != "phase":
      continue

    if not info.specializes:
      errors.append(
        _diagnostic(
          "error",
          f"phase '{info.name}' não declara nenhum general.",
          info,
          f"adicione 'specializes <Sortal>' na declaração de '{info.name}'.",
        )
      )
      continue

    parents = [
      index.classes[name] for name in info.specializes if name in index.classes
    ]
    valid_generals = [
      parent for parent in parents if parent.coerced_stereotype in PHASE_GENERALS
    ]

    if not valid_generals:
      invalid = ", ".join(parent.name for parent in parents) or "-"
      errors.append(
        _diagnostic(
          "error",
          (
            f"phase '{info.name}' especializa general inválido ({invalid}); "
            "o padrão Phase exige kind, subkind, collective ou phase."
          ),
          info,
          (f"faça '{info.name}' especializar kind, subkind, collective ou phase."),
        )
      )
      continue

    if not has_identity_provider(info, index):
      errors.append(
        _diagnostic(
          "error",
          (
            f"phase '{info.name}' não alcança um kind/collective provedor de "
            "identidade."
          ),
          info,
          (
            f"faça '{info.name}' especializar direta ou indiretamente um "
            "kind ou collective."
          ),
        )
      )

  # agrupa por general para deduzir partições incompletas
  for general in index.classes.values():
    if general.coerced_stereotype not in PHASE_GENERALS:
      continue

    # Fases irmãs que especializam este general.
    children = [
      info
      for info in index.classes.values()
      if info.coerced_stereotype == "phase" and general.name in info.specializes
    ]

    # Um genset desse general já foi reportado na partição.
    # Não repetimos como dedução as fases que ele agrupa
    genset_specifics: set[str] = set()

    for candidate in index.gensets:
      if candidate.general == general.name:
        genset_specifics.update(candidate.specifics)

    uncovered = [
      info
      for info in children
      if info.name not in covered and info.name not in genset_specifics
    ]

    if not uncovered:
      continue

    # restam fases sem genset: a partição é deduzida como incompleta.
    names = ", ".join(info.name for info in uncovered)
    deductions.append(
      _diagnostic(
        "deduction",
        (
          f"a partição de fases de '{general.name}' está incompleta: "
          f"'{names}' não participa de um genset de fases válido."
        ),
        general,
        (
          f"declare um genset 'disjoint' com general '{general.name}' "
          f"e specifics {names} (dedução do padrão Phase incompleto)."
        ),
      )
    )
