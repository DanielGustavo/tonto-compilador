"""Pacote do Analisador Sintático da linguagem TONTO.

Construído sobre os tokens produzidos pelo `lexico_analyzer`. Organização
didática do pacote (na ordem em que as peças colaboram):

1. `ast_nodes`          -> o que é um nó da AST (Program, Package, ...);
2. `grammar_rules`      -> a gramática PLY/YACC propriamente dita, que chama
                           `semantic_actions` (pacote `semantic_analyzer`)
                           para declarar/verificar nomes;
3. `error_handling`     -> o hook de erro sintático do PLY e suas sugestões;
4. `parser`             -> monta o parser, resolve imports entre arquivos
                           (delegando a decisão a `semantic_analyzer.imports`)
                           e devolve os erros das três fases;
5. `reporter`           -> como o resultado sintático (erros e tabela de
                           síntese) é apresentado ao usuário.

A tabela de símbolos e a lista de `SemanticError` vivem em `semantic_analyzer`,
não aqui. Assim como em `lexico_analyzer`, o `main.py` usa esta fachada mas
também importa alguns submódulos diretamente (`parser`, `reporter`,
`ast_nodes`) quando precisa de funções que não estão reexportadas aqui.
"""

from .ast_nodes import Node
from .errors import SyntacticError
from .parser import analisar_arquivo, analisar_codigo
from .reporter import print_syntax_errors, print_tabela_sintese

__all__ = [
  "Node",
  "SyntacticError",
  "analisar_arquivo",
  "analisar_codigo",
  "print_syntax_errors",
  "print_tabela_sintese",
]
