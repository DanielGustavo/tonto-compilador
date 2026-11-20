"""Pacote do Analisador Semântico da linguagem TONTO.

Construído sobre a AST produzida pelo `syntax_analyzer`. Organização
didática do pacote (na ordem em que as peças colaboram):

1. `symbol`             -> o que é um símbolo (Symbol + SymbolCategory);
2. `symbol_table`       -> onde os símbolos ficam guardados, por escopo;
3. `errors`             -> o que é um erro semântico (SemanticError);
4. `semantic_actions`   -> o motor chamado durante o parse para declarar/
                           verificar nomes e resolver referências pendentes;
5. `imports`            -> a resolução de `import <Nome>` entre arquivos
                           `.tonto`, que declara os símbolos importados via
                           `semantic_actions`;
6. `reporter`           -> como a lista de `SemanticError` é apresentada;
7. `patterns`           -> análise de padrões de projeto sobre a AST

`syntax_analyzer` é quem chama este pacote: `grammar_rules.py` e
`error_handling.py` importam `semantic_actions` diretamente, e `parser.py`
importa `imports.resolve_imports` (passando como ele mesmo faz o parse
isolado de um arquivo importado). Por isso `semantic_actions` e `imports`
não são reexportados aqui. Assim como em `syntax_analyzer`, quem precisa
deles importa o submódulo diretamente.
"""

from .errors import SemanticError
from .reporter import print_semantic_errors
from .symbol import Symbol, SymbolCategory
from .symbol_table import SymbolTable

__all__ = [
  "SemanticError",
  "Symbol",
  "SymbolCategory",
  "SymbolTable",
  "print_semantic_errors",
]
