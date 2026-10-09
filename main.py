"""Ponto de entrada do compilador TONTO.

Orquestra o fluxo: escolhe o arquivo de entrada (por argumento ou pelo menu de
exemplos), chama o Analisador Léxico e/ou o Analisador Sintático e entrega o
resultado aos módulos de apresentação.

Uso:
    python3 main.py
    python3 main.py tonto_examples/car.tonto
    python3 main.py --lexic tonto_examples/car.tonto
    python3 main.py --syntax tonto_examples/car.tonto
    python3 main.py --lexic
    python3 main.py --syntax
"""

import sys
from pathlib import Path

from lexico_analyzer.analyzer import analisar_arquivo as analisar_lexicamente
from lexico_analyzer.reporter import (
  count_tokens_by_category,
  export_tokens_json,
  imprimir_erros,
  imprimir_visao_analitica,
  print_token_count,
)

from syntax_analyzer.parser import analisar_arquivo as analisar_sintaticamente

PASTA_DE_EXEMPLOS = Path(__file__).parent / "tonto_examples"
MODOS = {"--lexic": "lexic", "--syntax": "syntax"}


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


def escolher_modo(argumentos):
  if argumentos and argumentos[0] in MODOS:
    return (MODOS[argumentos[0]]), argumentos[1:]

  return MODOS.values(), argumentos


def escolher_arquivo(argumentos: list[str]) -> Path | None:
  """Resolve o arquivo de entrada: argumento da linha de comando ou menu."""
  if len(argumentos) > 1:
    print(
      f"uso: python3 {Path(__file__).name} "
      "[--lexic|--syntax] [caminho_do_arquivo.tonto]"
    )
    return None

  if len(argumentos) == 1:
    caminho = Path(argumentos[0])

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


def executar_analise_lexica(caminho: Path) -> None:
  print("\n============ ANÁLISE LÉXICA ============")

  tokens, erros, codigo_fonte = analisar_lexicamente(caminho)

  imprimir_visao_analitica(tokens, codigo_fonte)

  count = count_tokens_by_category(tokens)
  print_token_count(count)
  export_tokens_json(caminho, tokens, count)

  imprimir_erros(erros)


def executar_analise_sintatica(caminho: Path) -> None:
  print("\n============ ANÁLISE SINTÁTICA ============")

  node, erros, codigo_fonte = analisar_sintaticamente(caminho)

  def print_node(node, ident=0):
    print(f"{' ' * ident * 4}{node.label()}")

    if node.children:
      for childrenNode in node.children():
        print_node(childrenNode, ident + 1)

  if node:
    print_node(node)
  # imprimir_visao_analitica(tokens, codigo_fonte)

  # count = count_tokens_by_category(tokens)
  # print_token_count(count)
  # export_tokens_json(caminho, tokens, count)

  # imprimir_erros(erros)


def main() -> None:
  argumentos = sys.argv[1:]

  modo, argumentos = escolher_modo(argumentos)
  caminho = escolher_arquivo(argumentos)

  if caminho is None:
    sys.exit(1)

  print(f"\n>>> Analisando: {caminho.name}")

  if "lexic" in modo:
    executar_analise_lexica(caminho)
  if "syntax" in modo:
    executar_analise_sintatica(caminho)


if __name__ == "__main__":
  main()
