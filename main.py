"""Ponto de entrada do compilador TONTO.

Orquestra o fluxo: escolhe o arquivo de entrada (por argumento ou pelo menu de
exemplos), chama o Analisador Léxico e manda o resultado para a apresentação.

Uso:
    python3 main.py                          # menu com os exemplos disponíveis
    python3 main.py tonto_examples/car.tonto # analisa um arquivo específico
"""

import sys
from pathlib import Path

from lexico_analyzer.analyzer import analisar_arquivo
from lexico_analyzer.reporter import (
  count_tokens_by_category,
  export_tokens_json,
  imprimir_erros,
  imprimir_visao_analitica,
  print_token_count,
)

PASTA_DE_EXEMPLOS = Path(__file__).parent / "tonto_examples"


def listar_e_mapear_exemplos(pasta: Path) -> dict[str, Path] | None:
  """Imprime um menu numerado com os `.tonto` da pasta e devolve o mapa."""
  if not pasta.is_dir():
    print(f"ERRO: a pasta '{pasta}' não foi encontrada.")
    return None

  exemplos = sorted(item for item in pasta.iterdir() if item.suffix == ".tonto")

  if not exemplos:
    print(f"Nenhum arquivo .tonto encontrado em '{pasta}'.")
    return None

  print("\n--- Exemplos TONTO disponíveis ---\n")

  mapa = {}

  for i, arquivo in enumerate(exemplos):
    chave = f"{i:02}"
    mapa[chave] = arquivo
    print(f"[{chave}]  {arquivo.name}")

  return mapa


def escolher_arquivo() -> Path | None:
  """Resolve o arquivo de entrada: argumento da linha de comando ou menu."""
  if len(sys.argv) > 2:
    print(f"uso: python3 {Path(__file__).name} [caminho_do_arquivo.tonto]")
    return None

  if len(sys.argv) == 2:
    caminho = Path(sys.argv[1])

    if not caminho.is_file():
      print(f"arquivo não encontrado: {caminho}")
      return None

    return caminho

  mapa = listar_e_mapear_exemplos(PASTA_DE_EXEMPLOS)

  if not mapa:
    return None

  escolha = input("\nEscolha o número do arquivo a analisar: ").strip()
  caminho = mapa.get(escolha)

  if caminho is None:
    print(f"ERRO: opção '{escolha}' inválida.")

  return caminho


def main() -> None:
  caminho = escolher_arquivo()

  if caminho is None:
    sys.exit(1)

  print(f"\n>>> Analisando: {caminho.name}\n")

  tokens, erros, codigo_fonte = analisar_arquivo(caminho)

  imprimir_visao_analitica(tokens, codigo_fonte)

  count = count_tokens_by_category(tokens)
  print_token_count(count)
  export_tokens_json(caminho, tokens, count)

  imprimir_erros(erros)


if __name__ == "__main__":
  main()
