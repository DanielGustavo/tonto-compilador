"""Pacote do Analisador Sintático/Semântico da linguagem TONTO.

Construído sobre os tokens produzidos pelo `lexico_analyzer`. Organização
didática do pacote (na ordem em que as peças colaboram):

1. `ast_nodes`          -> o que é um nó da AST (Program, Package, ...);
2. `symbol`             -> o que é um símbolo (Symbol + SymbolCategory);
3. `symbol_table`       -> onde os símbolos ficam guardados, por escopo;
4. `grammar_rules`      -> a gramática PLY/YACC propriamente dita;
5. `semantic_actions`   -> o que a gramática chama para declarar/verificar nomes;
6. `error_handling`     -> o hook de erro sintático do PLY e suas sugestões;
7. `parser`             -> monta o parser e resolve imports entre arquivos;
8. `reporter`           -> como o resultado (erros e tabela de síntese) é apresentado ao usuário.

Assim como em `lexico_analyzer`, o `main.py` usa esta fachada mas também
importa alguns submódulos diretamente (`parser`, `reporter`, `ast_nodes`)
quando precisa de funções que não estão reexportadas aqui.
"""

from .ast_nodes import Node
from .errors import SemanticError, SyntacticError
from .parser import analisar_arquivo, analisar_codigo
from .reporter import print_semantic_errors, print_syntax_errors, print_tabela_sintese
from .symbol import Symbol, SymbolCategory
from .symbol_table import SymbolTable

__all__ = [
  "Node",
  "SemanticError",
  "Symbol",
  "SymbolCategory",
  "SymbolTable",
  "SyntacticError",
  "analisar_arquivo",
  "analisar_codigo",
  "print_semantic_errors",
  "print_syntax_errors",
  "print_tabela_sintese",
]
