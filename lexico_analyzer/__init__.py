"""Pacote do Analisador Léxico da linguagem TONTO.

Organização didática do pacote (na ordem em que as peças são usadas):

1. `token_types`       -> o que é um token (TokenEnum + CustomToken);
2. `token_definitions` -> quais lexemas existem (palavras reservadas + regex);
3. `lexer_rules`       -> como o PLY reconhece cada lexema (regras t_*);
4. `analyzer`          -> fachada que roda a análise sobre um arquivo .tonto;
5. `reporter`          -> como o resultado é apresentado ao usuário.

O `main.py` (na raiz do projeto) só conversa com `analyzer` e `reporter`.
"""

from .analyzer import analisar_arquivo, analisar_codigo
from .reporter import imprimir_visao_analitica
from .token_types import CustomToken, TokenEnum

__all__ = [
  "CustomToken",
  "TokenEnum",
  "analisar_arquivo",
  "analisar_codigo",
  "imprimir_visao_analitica",
]
