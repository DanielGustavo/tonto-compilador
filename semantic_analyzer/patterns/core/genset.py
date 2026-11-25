from .hierarchy import has_identity_provider
from .index import OntologyIndex
from .model import ClassInfo, GensetInfo, PatternDiagnostic
from .utils import diagnostic


def collect_missing_edges(
  genset: GensetInfo,
  general: ClassInfo,
  specifics: list[ClassInfo],
  pattern: str,
  removal_phrase: str,
  errors: list[PatternDiagnostic],
) -> tuple[bool, list[ClassInfo]]:
  """
  Separa os específicos sem `specializes` e reporta os que apontam outro general

  Devolve `(válido, arestas_pendentes)`. Os pendentes só devem ser aplicados
  depois que a partição inteira for validada.
  """

  pending: list[ClassInfo] = []
  valid = True

  for info in specifics:
    if general.node.name in info.specializes:
      continue

    if not info.specializes:
      pending.append(info)
      continue

    valid = False
    errors.append(
      diagnostic(
        pattern,
        "error",
        (
          f"'{info.node.name}' não especializa o general "
          f"'{general.node.name}' do genset '{genset.node.name}'."
        ),
        info,
        (
          f"faça '{info.node.name}' especializar '{general.node.name}' ou "
          f"{removal_phrase} do genset '{genset.node.name}'."
        ),
      )
    )

  return valid, pending


def apply_missing_edges(
  index: OntologyIndex,
  genset: GensetInfo,
  general: ClassInfo,
  specifics: list[ClassInfo],
  pending: list[ClassInfo],
  pattern: str,
  specific_subject: str,
  stereotype_keyword: str,
  deductions: list[PatternDiagnostic],
  errors: list[PatternDiagnostic],
) -> bool:
  """
  Aplica as arestas deduzidas, valida a identidade e reporta ou desfaz

  As arestas entram temporariamente em `specializes` para que a checagem de
  identidade considere elas. Se a partição falhar, elas são removidas
  """

  for info in pending:
    info.specializes.append(general.node.name)

  valid = True

  if not has_identity_provider(general, index):
    valid = False
    errors.append(
      diagnostic(
        pattern,
        "error",
        (
          f"o general '{general.node.name}' do genset '{genset.node.name}' não "
          "alcança um kind/collective provedor de identidade."
        ),
        general,
        (
          f"faça '{general.node.name}' especializar direta ou indiretamente um "
          "kind ou collective."
        ),
      )
    )

  for info in specifics:
    if has_identity_provider(info, index):
      continue

    valid = False
    errors.append(
      diagnostic(
        pattern,
        "error",
        (
          f"{specific_subject} '{info.node.name}' do genset "
          f"'{genset.node.name}' não alcança um kind/collective provedor de "
          "identidade."
        ),
        info,
        (
          f"faça '{info.node.name}' especializar direta ou indiretamente um "
          "kind ou collective."
        ),
      )
    )

  if not valid:
    for info in pending:
      info.specializes.remove(general.node.name)

    return False

  for info in pending:
    deductions.append(
      diagnostic(
        pattern,
        "deduction",
        (
          f"'{info.node.name}' não declara 'specializes {general.node.name}', mas o "
          f"genset '{genset.node.name}' o agrupa sob '{general.node.name}'."
        ),
        info,
        (
          f"declare explicitamente '{stereotype_keyword} {info.node.name} specializes "
          f"{general.node.name}' (dedução pela sobrecarga do genset)."
        ),
      )
    )

  return True
