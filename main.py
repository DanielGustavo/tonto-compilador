"""Ponto de entrada do compilador TONTO.

Orquestra o fluxo: escolhe o arquivo de entrada (por argumento ou pelo menu de
exemplos), chama o Analisador Léxico e/ou o Analisador Sintático e entrega o
resultado aos módulos de apresentação.

Uso:
    python3 main.py
    python3 main.py tonto_examples/Pizzaria.tonto
    python3 main.py --lexic tonto_examples/Pizzaria.tonto
    python3 main.py --syntax tonto_examples/Pizzaria.tonto
    python3 main.py --semantic tonto_examples/Pizzaria.tonto
    python3 main.py --lexic
    python3 main.py --syntax
    python3 main.py --semantic
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
from semantic_analyzer.patterns import (
  analyze_patterns,
  print_pattern_report,
)
from semantic_analyzer.reporter import print_semantic_errors
from syntax_analyzer import ast_nodes
from syntax_analyzer.parser import analisar_arquivo as analisar_sintaticamente
from syntax_analyzer.reporter import print_syntax_errors, print_tabela_sintese

PASTA_DE_EXEMPLOS = Path(__file__).parent / "tonto_examples"
MODOS = {"--lexic": "lexic", "--syntax": "syntax", "--semantic": "semantic"}
MODOS_PADRAO = set(MODOS.values())


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
    return set({MODOS[argumentos[0]]}), argumentos[1:]

  return MODOS_PADRAO, argumentos


def escolher_arquivo(argumentos: list[str]) -> Path | None:
  """Resolve o arquivo de entrada: argumento da linha de comando ou menu."""
  if len(argumentos) > 1:
    print(
      f"uso: python3 {Path(__file__).name} "
      "[--lexic|--syntax|--semantic] [caminho_do_arquivo.tonto]"
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


def executar_analise_lexica(caminho: Path) -> list:
  print("\n============ ANÁLISE LÉXICA ============")

  tokens, erros, codigo_fonte = analisar_lexicamente(caminho)

  imprimir_visao_analitica(tokens, codigo_fonte)

  count = count_tokens_by_category(tokens)
  print_token_count(count)
  export_tokens_json(caminho, tokens, count)

  return erros


def executar_parse(caminho: Path) -> tuple:
  """Roda o parse (e a análise semântica) sem apresentar resultados."""
  return analisar_sintaticamente(caminho)


def apresentar_tabela_sintese(node, declaracoes_importadas) -> None:
  if isinstance(node, ast_nodes.Program) and node.package:
    print_tabela_sintese(node.package, declaracoes_importadas)


def apresentar_padroes(node, declaracoes_importadas) -> None:
  if isinstance(node, ast_nodes.Program) and node.package:
    pattern_report = analyze_patterns(node, declaracoes_importadas)
    print_pattern_report(pattern_report)


def main() -> None:
  argumentos = sys.argv[1:]

  modo, argumentos = escolher_modo(argumentos)
  caminho = escolher_arquivo(argumentos)

  if caminho is None:
    sys.exit(1)

  print(f"\n>>> Analisando: {caminho.name}")

  erros_lexicos = []
  erros_sintaticos = []
  erros_semanticos = []
  node = None
  declaracoes_importadas = []

  if "lexic" in modo:
    erros_lexicos = executar_analise_lexica(caminho)

  if "syntax" in modo or "semantic" in modo:
    (
      node,
      erros_lexicos,
      erros_sintaticos,
      erros_semanticos,
      declaracoes_importadas,
      _codigo_fonte,
    ) = executar_parse(caminho)

    if "syntax" in modo:
      apresentar_tabela_sintese(node, declaracoes_importadas)
    if "semantic" in modo:
      apresentar_padroes(node, declaracoes_importadas)

  if "lexic" in modo or "syntax" in modo:
    imprimir_erros(erros_lexicos)
  if "syntax" in modo:
    print_syntax_errors(erros_sintaticos)
  if "syntax" in modo or "semantic" in modo:
    print_semantic_errors(erros_semanticos)


if __name__ == "__main__":
  main()
