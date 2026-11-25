"""Reconhecimento do padrão Phase

O padrão Phase: um genset disjoint com duas ou mais phases que especializam o
mesmo sortal. Além disso, o matcher trata a coerção de um subkind sob uma phase
e deduz o que falta.
"""

from ..core.genset import apply_missing_edges, collect_missing_edges
from ..core.hierarchy import children, has_identity_provider
from ..core.index import OntologyIndex
from ..core.model import (
  ClassInfo,
  PatternDiagnostic,
  PhaseMatch,
  PhaseReport,
)
from ..core.stereotypes import PHASE, PHASE_GENERALS, SUBKIND
from ..core.utils import diagnostic, ref_of

PATTERN = "Phase"

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
      if info.node.stereotype != SUBKIND or info.coerced_stereotype == PHASE:
        continue

      parent = _phase_parent(info, index)

      if parent is None:
        continue

      info.coerced_stereotype = PHASE
      changed = True
      coercions.append(
        diagnostic(
          PATTERN,
          "coercion",
          (
            f"subkind '{info.node.name}' especializa a phase '{parent.node.name}', "
            "estereótipo coercido de 'subkind' para 'phase'."
          ),
          info,
          (
            f"declare '{info.node.name}' explicitamente como 'phase {info.node.name} "
            f"specializes {parent.node.name}' (coerção subkind -> phase)."
          ),
        )
      )


def _phase_parent(info: ClassInfo, index: OntologyIndex) -> ClassInfo | None:
  """Devolve o primeiro general de `info` que é uma phase"""

  for parent_name in info.specializes:
    parent = index.classes.get(parent_name)

    if parent is not None and parent.coerced_stereotype == PHASE:
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
    general = index.classes.get(genset.node.general)

    # gensets de outros padrões ou com general desconhecido
    if general is None or general.coerced_stereotype not in PHASE_GENERALS:
      continue

    specific_infos = [
      index.classes[name] for name in genset.node.specifics if name in index.classes
    ]
    phase_infos = [
      info for info in specific_infos if info.coerced_stereotype == PHASE
    ]

    # sem nenhuma phase, o genset faz parte de outro padrão
    if not phase_infos:
      continue

    # Partição não pode misturar phases com outros estereótipos
    if len(phase_infos) != len(specific_infos):
      invalid = ", ".join(
        info.node.name for info in specific_infos if info.coerced_stereotype != PHASE
      )

      errors.append(
        diagnostic(
          PATTERN,
          "error",
          (
            f"genset de fases '{genset.node.name}' mistura phases com outros "
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
        diagnostic(
          PATTERN,
          "error",
          (
            f"genset de fases '{genset.node.name}' possui {len(phase_infos)} fase(s); "
            f"uma partição exige ao menos {MIN_PHASES}."
          ),
          genset,
          "acrescente outra phase ao genset para completar a partição.",
        )
      )
      continue

    # Partição exige disjunção
    if genset.node.disjointness != "disjoint":
      errors.append(
        diagnostic(
          PATTERN,
          "error",
          f"genset de fases '{genset.node.name}' deve ser disjoint.",
          genset,
          f"declare '{genset.node.name}' como 'disjoint'.",
        )
      )
      continue

    # Valida as arestas `specializes` e a cadeia de identidade do general e das fases.
    edges_ok, pending = collect_missing_edges(
      genset,
      general,
      phase_infos,
      pattern=PATTERN,
      removal_phrase="remova",
      errors=errors,
    )

    if not edges_ok:
      continue

    if not apply_missing_edges(
      index,
      genset,
      general,
      phase_infos,
      pending,
      pattern=PATTERN,
      specific_subject="a phase",
      stereotype_keyword=PHASE,
      deductions=deductions,
      errors=errors,
    ):
      continue

    lines = sorted(
      {
        genset.node.line,
        general.node.line,
        *(info.node.line for info in phase_infos),
      }
    )

    matches.append(
      PhaseMatch(
        general=ref_of(general),
        specifics=tuple(ref_of(info) for info in phase_infos),
        genset=ref_of(genset),
        lines=tuple(lines),
        disjointness=genset.node.disjointness,
        completeness=genset.node.completeness,
        deduced=bool(pending),
      )
    )

    covered.update(info.node.name for info in phase_infos)


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
    if info.coerced_stereotype != PHASE:
      continue

    if not info.specializes:
      errors.append(
        diagnostic(
          PATTERN,
          "error",
          f"phase '{info.node.name}' não declara nenhum general.",
          info,
          f"adicione 'specializes <Sortal>' na declaração de '{info.node.name}'.",
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
      invalid = ", ".join(parent.node.name for parent in parents) or "-"
      errors.append(
        diagnostic(
          PATTERN,
          "error",
          (
            f"phase '{info.node.name}' especializa general inválido ({invalid}); "
            "o padrão Phase exige kind, subkind, collective ou phase."
          ),
          info,
          (f"faça '{info.node.name}' especializar kind, subkind, collective ou phase."),
        )
      )
      continue

    if not has_identity_provider(info, index):
      errors.append(
        diagnostic(
          PATTERN,
          "error",
          (
            f"phase '{info.node.name}' não alcança um kind/collective provedor de "
            "identidade."
          ),
          info,
          (
            f"faça '{info.node.name}' especializar direta ou indiretamente um "
            "kind ou collective."
          ),
        )
      )

  # agrupa por general para deduzir partições incompletas
  for general in index.classes.values():
    if general.coerced_stereotype not in PHASE_GENERALS:
      continue

    # Fases irmãs que especializam este general.
    sibling_phases = children(index, general.node.name, stereotype=PHASE)

    # Um genset desse general já foi reportado na partição.
    # Não repetimos como dedução as fases que ele agrupa
    genset_specifics: set[str] = set()

    for candidate in index.gensets:
      if candidate.node.general == general.node.name:
        genset_specifics.update(candidate.node.specifics)

    uncovered = [
      info
      for info in sibling_phases
      if info.node.name not in covered and info.node.name not in genset_specifics
    ]

    if not uncovered:
      continue

    # restam fases sem genset: a partição é deduzida como incompleta.
    names = ", ".join(info.node.name for info in uncovered)
    deductions.append(
      diagnostic(
        PATTERN,
        "deduction",
        (
          f"a partição de fases de '{general.node.name}' está incompleta: "
          f"'{names}' não participa de um genset de fases válido."
        ),
        general,
        (
          f"declare um genset 'disjoint' com general '{general.node.name}' "
          f"e specifics {names} (dedução do padrão Phase incompleto)."
        ),
      )
    )
