# Compilador para TONTO (Textual Ontology Language)

Projeto da disciplina de **Compiladores** (UFERSA/CCEN). O objetivo é reconhecer
os elementos da linguagem TONTO — estereótipos de classe e de relação, palavras
reservadas, símbolos especiais, identificadores (classes, relações e
instâncias), tipos nativos, novos tipos e meta-atributos — indicando **linha e
coluna** de cada token e tratando erros léxicos sem interromper a análise.
Além da análise léxica, o projeto também faz **análise sintática** (gramática
PLY/YACC) e **análise semântica** (tabela de símbolos por escopo, resolução
de `import` entre arquivos `.tonto`), produzindo uma AST e uma **tabela de
síntese** da ontologia declarada, e reportando erros das três fases sem
interromper a análise. Sobre a AST, a análise semântica ainda valida **padrões
de projeto de ontologias (ODPs)**: Subkind, Role, Phase, Relator, Mode e
RoleMixin, com detecção de coerções, erros não coercíveis e dedução de padrões
incompletos por sobrecarga.

A automação parcial é feita com **PLY** (versão Python do LEX/YACC).

# Sumário

1. [Estrutura do Projeto](#estrutura-do-projeto)
    * [Organização das pastas](#organizacao-das-pastas)
    * [Descrição dos componentes](#descricao-dos-componentes)
    * [Como as peças se conectam](#como-as-pecas-se-conectam)
2. [Instalação](#instalacao)
3. [Como executar](#como-executar)
    * [Entrada do sistema](#entrada-do-sistema)
    * [Saída do sistema](#saida-do-sistema)
4. [Padrões de projeto de ontologias (ODPs)](#padroes-de-projeto)
5. [Conceitos da linguagem reconhecidos](#conceitos-reconhecidos)

# <a name="estrutura-do-projeto"></a> Estrutura do Projeto

### <a name="organizacao-das-pastas"></a> Organização das pastas

```
tonto-compilador/
│
├── main.py                        (ponto de entrada / orquestrador: CLI --lexic/--syntax/--semantic)
├── table_printer.py                (utilitário de tabelas, usado pelos dois reporters)
├── README.md
├── requirements.txt               (dependências do projeto)
├── pyproject.toml                 (metadados do projeto)
├── ruff.toml / .editorconfig      (padrão de formatação do código)
├── .gitignore
│
├── lexico_analyzer/               (pacote do Analisador Léxico)
│   ├── __init__.py                (API pública do pacote)
│   ├── token_types.py             (o que é um token: TokenEnum + CustomToken)
│   ├── token_definitions.py       (quais lexemas existem: reservadas + regex)
│   ├── lexer_rules.py             (como o PLY reconhece: regras t_*, erros)
│   ├── errors.py                  (LexicalError)
│   ├── analyzer.py                (fachada: analisa arquivo/código)
│   ├── reporter.py                (como o resultado léxico é exibido/exportado)
│   └── exports/                   (JSON exportado por reporter.py, um por arquivo)
│
├── syntax_analyzer/               (pacote do Analisador Sintático)
│   ├── __init__.py                (API pública do pacote)
│   ├── ast_nodes.py               (nós da AST: Program, Package, ClassDeclaration, ...)
│   ├── errors.py                  (SyntacticError)
│   ├── grammar_rules.py           (a gramática PLY/YACC propriamente dita)
│   ├── error_handling.py          (hook de erro do PLY + sugestões de correção)
│   ├── parser.py                  (monta o parser, faz o parse isolado de imports)
│   └── reporter.py                (erros sintáticos + tabela de síntese)
│
├── semantic_analyzer/             (pacote do Analisador Semântico)
│   ├── __init__.py                (API pública do pacote)
│   ├── symbol.py                  (o que é um símbolo: Symbol + SymbolCategory)
│   ├── symbol_table.py            (tabela de símbolos encadeada por escopo)
│   ├── errors.py                  (SemanticError)
│   ├── semantic_actions.py        (motor que a gramática chama para declarar/verificar nomes)
│   ├── imports.py                 (resolve quais imports casam com quais arquivos vizinhos)
│   ├── reporter.py                (erros semânticos)
│   └── patterns/                  (análise de padrões de projeto sobre a AST)
│       ├── __init__.py            (fachada: analyze_patterns + tipos de resultado)
│       ├── reporter.py            (relatório (1) padrões, (2) coerções/erros, (3) deduções)
│       ├── core/                  (modelo, índice, hierarquia, gensets, mediações)
│       └── matchers/              (subkind, role, phase, relator, mode, role_mixin)
│
└── tonto_examples/                (exemplos .tonto agrupados por cenário)
    ├── pizzaria/
    │   ├── Pizzaria.tonto         (pacote principal, importa os demais)
    │   ├── Pizzaria_Pessoa.tonto, Pizzaria_Cliente.tonto,
    │   │   Pizzaria_Empresa.tonto, Pizzaria_Endereco.tonto,
    │   │   Pizzaria_Pizza.tonto, Pizzaria_CoberturasDePizza.tonto,
    │   │   Pizzaria_ItensDaPizzaria.tonto  
    │   │                                   
    │   ├── Pizzaria_MONO.tonto             (mesma ontologia em um único pacote, sem imports)
    │   └── Pizzaria_Erros.tonto            (casos propositais de erro léxico/sintático/semântico)
    ├── hospital/                           (6 arquivos multi-pacote; entrada em UBS.tonto)
    ├── festa/                              (exemplo de coerção, dedução e erro)
    └── design_patterns/                    (exemplos de ODPs)
```

### <a name="descricao-dos-componentes"></a> Descrição dos componentes

* `main.py`

    * Ponto de entrada e "orquestrador" do compilador. Resolve o modo
      (`--lexic`, `--syntax`, `--semantic`, ou nenhum deles — e então roda as
      três fases) e o arquivo de entrada (por argumento na linha de comando ou
      pelo menu de exemplos), chama o(s) analisador(es) correspondente(s) e
      entrega o resultado aos módulos de apresentação. Todos os erros
      acumulados (léxicos, sintáticos e semânticos) só são impressos juntos
      no final da execução, depois de qualquer tabela.

* `table_printer.py`

    * Utilitário de desenho de tabelas em modo texto (bordas `┌─┬─┐`),
      compartilhado por `lexico_analyzer/reporter.py` (visão analítica de
      tokens) e por `syntax_analyzer/reporter.py` (tabela de síntese).

* `lexico_analyzer/` (Diretório)

    * Pacote Python que encapsula toda a lógica do **Analisador Léxico**. Está
      dividido em arquivos com responsabilidade única, na ordem em que são
      usados:

    * `__init__.py`: torna o diretório um módulo importável e reexporta o que é
      de uso externo (`analisar_arquivo`, `imprimir_visao_analitica`, ...). O
      `main.py` também importa diretamente de `analyzer`/`reporter` quando
      precisa de outras funções do reporter (contagem por categoria,
      exportação JSON, impressão de erros) que não estão reexportadas aqui.

    * `token_types.py`: define **o que é um token**. `TokenEnum` lista as
      categorias (estereótipos de classe, de relação, palavras reservadas,
      identificadores, símbolos especiais, ...) e `CustomToken` é o token
      devolvido pelo analisador, com lexema, categoria, linha e coluna.

    * `token_definitions.py`: define **quais lexemas existem**. É a "tabela" da
      linguagem: `reserved_words` com as palavras de significado fixo e
      `token_definitions` com as expressões regulares dos demais tokens.

    * `lexer_rules.py`: define **como o PLY reconhece** cada lexema. É o
      equivalente ao arquivo LEX: monta a lista `tokens`, gera as funções `t_*`
      (a partir da fábrica `token_def`, evitando repetir o mesmo código dezenas
      de vezes), declara o que é ignorado (espaços e comentários) e trata erros
      léxicos em `t_error`, reportando linha e coluna e seguindo a análise.
      **Atenção à ordem das regras**: o PLY ordena regras-função pela linha de
      definição e, como todas vêm da mesma linha da fábrica `token_def`, o
      desempate acaba alfabético — veja a nota no início da seção de regras.

    * `errors.py`: define `LexicalError`, o registro de um erro léxico
      (valor, linha, coluna e mensagem).

    * `analyzer.py`: **fachada** do pacote. Constrói o lexer uma única vez com
      `lex.lex(module=lexer_rules)` e expõe `analisar_codigo` (a partir de uma
      string) e `analisar_arquivo` (a partir de um `.tonto`), devolvendo a lista
      de tokens e a lista de erros encontrados.

    * `reporter.py`: cuida apenas da **apresentação**. A análise produz dados; a
      forma de exibir fica isolada aqui (tabela por linha, contagem por
      categoria, exportação para JSON em `exports/`), então acrescentar outra
      visualização mexe só neste arquivo.

* `syntax_analyzer/` (Diretório)

    * Pacote Python que encapsula a **Análise Sintática**, construído sobre
      os tokens produzidos pelo `lexico_analyzer`. Também dividido por
      responsabilidade única:

    * `__init__.py`: fachada do pacote, reexporta `Node`, `SyntacticError`,
      `analisar_arquivo`/`analisar_codigo` e os printers sintáticos. Assim
      como no pacote léxico, `main.py` também importa alguns submódulos
      diretamente (`parser`, `reporter`, `ast_nodes`).

    * `ast_nodes.py`: define a **AST**. Um `Node(line, column)` base e um
      dataclass por construção da linguagem (`Literal`, `Enumeration`,
      `Attribute`, `ClassDeclaration`, `Relation`, `DataTypeDeclaration`,
      `GeneralizationSet`, `Import`, `Package`, `Program`).

    * `errors.py`: define `SyntacticError` (emitido pela gramática), com
      valor/lexema, linha, coluna, mensagem e sugestão de correção. O
      equivalente semântico, `SemanticError`, vive em `semantic_analyzer/`.

    * `grammar_rules.py`: a **gramática PLY/YACC** propriamente dita —
      equivalente ao arquivo YACC, parceiro de `lexer_rules.py` ser o arquivo
      LEX. Organizada em seções (programa/pacote, enums, classes, datatypes,
      gensets, relações); cada regra monta um nó de `ast_nodes` e, quando a
      construção declara ou usa um nome, chama `semantic_actions` (do pacote
      `semantic_analyzer`). Inclui o truque de "regras-marcadoras" (produções
      vazias que rodam no meio de outra regra, via `p[-1]`/`p[-2]`) para abrir
      o escopo de uma classe, enum ou datatype antes do corpo ser lido.

    * `error_handling.py`: o hook `p_error` do PLY mais um conjunto de
      heurísticas privadas que olham a pilha de símbolos do parser
      (`symstack`) para sugerir a causa provável de um erro sintático, em vez
      de só reportar "token inesperado".

    * `parser.py`: monta o parser PLY a partir de `grammar_rules`
      (`yacc.yacc`), liga `error_handling`, e implementa o **parse isolado**
      de um arquivo importado (`_parse_file_isolated`): zera e depois
      restaura tabelas de símbolo e listas de erro próprias, para que
      analisar um import não contamine o arquivo principal. Delega a
      `semantic_analyzer.imports.resolve_imports` a decisão de **quais**
      imports casam com **quais** arquivos vizinhos, passando essa função de
      parse isolado como parâmetro. Expõe `analisar_codigo`/`analisar_arquivo`.

    * `reporter.py`: apresentação da fase sintática — lista de erros
      sintáticos e `print_tabela_sintese`, que mescla declarações próprias
      com as trazidas por imports resolvidos (ver `semantic_analyzer/imports.py`)
      e desenha as sub-tabelas (Pacotes, Classes, Relações internas,
      Datatypes, Enums, Gensets, Relações externas) via `table_printer`.

* `semantic_analyzer/` (Diretório)

    * Pacote Python que encapsula a **Análise Semântica**, construído sobre
      a AST produzida pelo `syntax_analyzer`. Dividido por responsabilidade
      única:

    * `__init__.py`: fachada do pacote, reexporta `SemanticError`, `Symbol`,
      `SymbolCategory`, `SymbolTable` e `print_semantic_errors`. Os
      submódulos `semantic_actions` e `imports` são importados diretamente
      por `syntax_analyzer` (mesma convenção dos outros pacotes).

    * `symbol.py`: define **o que é um símbolo**. `SymbolCategory` enumera as
      categorias de nomes que a linguagem declara (classe, datatype, enum,
      genset, relação, atributo, literal) e `Symbol` é o registro guardado na
      `SymbolTable` (nome, categoria, linha, coluna e pacote de origem, se
      importado).

    * `symbol_table.py`: a **tabela de símbolos**, encadeada por escopo — cada
      escopo aponta para o escopo que o envolve (`put`/`get_local`/`get`, este
      último percorrendo a cadeia até achar o nome ou esgotar os escopos).

    * `errors.py`: define `SemanticError` (emitido pelas ações semânticas e
      pela resolução de imports), com valor/lexema, linha, coluna, mensagem e
      sugestão de correção.

    * `semantic_actions.py`: o **motor da análise semântica**, chamado pelas
      ações da gramática (em `syntax_analyzer/grammar_rules.py`) para
      declarar símbolos, entrar/sair de escopos e marcar nomes usados para
      verificação posterior (`resolve_later`), que só é resolvida no fim do
      parse (`finalize`) — depois que o pacote e seus imports já foram vistos
      por inteiro. O par `snapshot`/`restore` existe para que
      `syntax_analyzer/parser.py` consiga analisar um arquivo importado
      isoladamente, sem que a tabela de símbolos desse arquivo substitua a do
      arquivo principal em andamento.

    * `imports.py`: decide **quais** `import <Nome>` casam com **quais**
      arquivos `.tonto` vizinhos (pelo cabeçalho `package <Nome>`), declara
      os símbolos que eles exportam (`semantic_actions.declare_imported`) e
      percorre o grafo de imports em busca em largura (BFS), evitando
      ciclos/duplicatas. Quem efetivamente faz o parse isolado de cada
      arquivo importado é recebido de fora (parâmetro `parse_file`), pois
      essa mecânica depende do parser PLY, que vive em `syntax_analyzer`.

    * `reporter.py`: apresentação dos erros da fase semântica
      (`print_semantic_errors`), paralelo aos reporters léxico e sintático. O
      relatório de padrões tem reporter próprio em `patterns/reporter.py`.

    * `patterns/` (Diretório): a **análise de padrões de projeto de
      ontologias (ODPs)**, executada depois que o parse e
      `semantic_actions.finalize()` terminam. É dividida em:

      * `__init__.py`: fachada `analyze_patterns(program, imported)`. Monta o
        índice da ontologia e roda os matchers na ordem necessária para que as
        coerções de um padrão não sejam desfeitas por outro; devolve um
        `PatternReport` com um `PatternResult` por ODP (`matches`, `coercions`,
        `errors`, `deductions`).

      * `core/`: infraestrutura compartilhada — `model.py` (classes de
        resultado, `ClassInfo`, diagnósticos), `index.py` (`OntologyIndex` com
        classes, gensets e relações do pacote e dos imports), `hierarchy.py`
        (pais, filhos, subtipo, identidade), `genset.py` (arestas ausentes,
        identidade e dedução), `mediation.py` (mediações/material), `stereotypes.py`
        (conjuntos de estereótipos aceitos) e `utils.py` (referências e
        diagnósticos).

      * `matchers/`: um módulo por ODP — `subkind.py`, `role.py`, `phase.py`,
        `relator.py`, `mode.py` e `role_mixin.py`. Cada matcher reconhece as
        variantes do padrão, aplica as coerções cabíveis e produz as deduções
        de padrões incompletos.

      * `reporter.py`: imprime o relatório em três blocos — (1) padrões
        encontrados por linhas de código, (2) erros a corrigir por coerção
        (separados dos erros não coercíveis) e (3) padrões incompletos
        deduzidos por sobrecarga.

* `tonto_examples/` (Diretório)

    * Arquivos de código-fonte em TONTO usados como casos de teste,
      agrupados por cenário em subpastas (`pizzaria/`, `hospital/`,
      `festa/`, `design_patterns/`). O menu do
      `main.py` percorre a pasta recursivamente e mostra o caminho relativo
      de cada arquivo.

    * Os imports entre pacotes são resolvidos casando o nome em
      `import <Nome>` com o cabeçalho `package <Nome>` de um arquivo
      **vizinho no mesmo diretório do arquivo analisado**. Por isso cada
      cenário mantém seus arquivos lado a lado na própria subpasta; a busca
      em largura de `parser.py` evita loop infinito mesmo em ciclos como
      `Pizza` ⇄ `CoberturasDePizza`. Passar um caminho arbitrário no
      terminal funciona, mas os imports só são encontrados no diretório
      daquele arquivo.

* `requirements.txt`, `pyproject.toml`, `ruff.toml`, `.editorconfig`

    * Dependências, metadados do projeto e padronização de formatação do código
      (indentação de 2 espaços, aspas duplas, `ruff` como linter/formatador).

### <a name="como-as-pecas-se-conectam"></a> Como as peças se conectam

```
                            tonto_examples/<grupo>/*.tonto
                                        │
                                        ▼
                              main.py (orquestrador)
                       ┌────────────────┴────────────────┐
                       ▼                                 ▼
             [--lexic] lexico_analyzer   [--syntax] syntax_analyzer + semantic_analyzer
                                         [--semantic] semantic_analyzer/patterns
             ┌─────────────────────┐           ┌──────────────────────────────────────────┐
             │ lexer_rules.py      │           │ parser.py monta o parser PLY a partir de  │
             │   ▲                 │           │ grammar_rules.py e liga error_handling.py │
             │   │                 │           │                 │                         │
             │ token_definitions/  │           │                 ▼ (ações chamam)          │
             │ token_types.py      │           │ grammar_rules.py ──► semantic_actions.py   │
             │   │                 │           │                      (semantic_analyzer)   │
             │   ▼                 │           │                       │        │           │
             │ reporter.py         │           │                       ▼        ▼ (constrói) │
             └─────────┬───────────┘           │     symbol_table.py/symbol.py  ast_nodes.py │
                       │                       │              ▲                              │
                       │                       │              │ (declara símbolos importados)│
                       │                       │     imports.py (semantic_analyzer)           │
                       │                       │       resolve quais import <Nome> casam com  │
                       │                       │       quais package <Nome> vizinhos, chamando│
                       │                       │       parser.py::_parse_file_isolated passado│
                       │                       │       como parâmetro (sem import circular)   │
                       │                       │              │                               │
                       │                       │              ▼                               │
                       │                       │  syntax_analyzer/reporter.py (tabela de       │
                       │                       │  síntese) + semantic_analyzer/reporter.py     │
                       │                       │  (erros semânticos)                           │
                       │                       └──────────────────┬─────────────────────────────┘
                       └──────────────────────────┬────────────────┘
                                                    ▼
                                             table_printer.py
                                                    │
                                                    ▼
                                             saída no terminal
```

Dentro de cada pacote a dependência anda em uma única direção: a apresentação
não conhece o PLY, a gramática não conhece o reporter, e as definições da
linguagem não conhecem quem as usa. Entre pacotes, `syntax_analyzer` depende
de `semantic_analyzer` (gramática e parser chamam o motor semântico e a
resolução de imports) e a única dependência no sentido contrário é
`semantic_analyzer/imports.py` lendo os *tipos* de `ast_nodes.py` — que são
só dados (dataclasses), não lógica — para decidir a categoria de cada
declaração importada; isso não chega a ser um ciclo real. `table_printer.py`
é o ponto onde as três fases convergem antes de chegar ao terminal.

# <a name="instalacao"></a> Instalação

Requer **Python 3.12+**. Recomenda-se um ambiente virtual, criado dentro do
diretório do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate       # Linux/WSL/macOS
```

Instalação das dependências (`ply` para os analisadores e `ruff` para o lint):

```bash
pip install -r requirements.txt
```

# <a name="como-executar"></a> Como executar

Sem flag, roda as três fases (léxica, sintática e semântica) em sequência,
no modo interativo com o menu de exemplos:

```bash
python3 main.py
```

Analisando um arquivo específico, com as três fases:

```bash
python3 main.py tonto_examples/pizzaria/Pizzaria.tonto
```

Rodando só uma das fases — a flag, quando usada, deve vir **antes** do
caminho do arquivo:

```bash
python3 main.py --lexic tonto_examples/pizzaria/Pizzaria.tonto     # só análise léxica
python3 main.py --syntax tonto_examples/pizzaria/Pizzaria.tonto    # tabela de síntese + erros
python3 main.py --semantic tonto_examples/pizzaria/Pizzaria.tonto  # relatório de padrões + erros semânticos
python3 main.py --lexic                                   # só léxica, com menu de exemplos
python3 main.py --syntax                                  # só sintática, com menu de exemplos
python3 main.py --semantic                                # só semântica, com menu de exemplos
```

### <a name="entrada-do-sistema"></a> Entrada do sistema

Sem argumento de arquivo, o programa lista os `.tonto` da pasta
`tonto_examples/` numerados; basta digitar o número correspondente e teclar
`enter`:

```
--- Exemplos TONTO disponíveis ---

[00]  design_patterns/Mode_Pattern.tonto
...
[06]  festa/Festa.tonto
...
[11]  hospital/UBS.tonto
...
[13]  pizzaria/Pizzaria.tonto
...
[22]  pizzaria/Pizzaria_Pizza.tonto

Escolha o número do arquivo a analisar:
```

### <a name="saida-do-sistema"></a> Saída do sistema

**Análise léxica** — visão analítica dos tokens: cada linha do código-fonte
seguida de uma tabela com os tokens que ela gerou (valor, coluna, tipo e
classificação). A classificação é só um agrupamento didático dos tipos —
usado apenas na exibição, não muda o tipo real atribuído pelo lexer. Símbolos
(parênteses, chaves, associação, cardinalidade, ...) não pertencem a nenhuma
classificação, então a coluna fica em branco para eles.

```
linha 15: "role Pizzaria specializes Empresa"
┌─────────────┬────────┬───────────────────┬────────────────────────┐
│ Valor       │ Coluna │ Tipo              │ Classificação          │
├─────────────┼────────┼───────────────────┼────────────────────────┤
│ role        │ 1      │ CLASS_STEREOTYPES │ Estereótipo de classe  │
│ Pizzaria    │ 6      │ CLASS_ID          │ Classe                 │
│ specializes │ 15     │ KEYWORDS          │ Palavra reservada      │
│ Empresa     │ 27     │ CLASS_ID          │ Classe                 │
└─────────────┴────────┴───────────────────┴────────────────────────┘
```

Em seguida, a contagem de tokens reconhecidos por classificação (tipos sem
classificação, como símbolos, não entram nesse resumo, mas continuam
contados no total). Os tokens e a contagem por tipo também são exportados
para `lexico_analyzer/exports/<nome_do_arquivo>.json`:

```
--- Contagem de tokens por classificação ---
  Palavra reservada: 3
  Classe: 7
  Relação: 4
  Instância: 0
  Estereótipo de classe: 2
  Estereótipo de relação: 0
  Tipo nativo: 2
  Novo tipo: 0

Total: 28 tokens

Tokens e contagem exportados para: lexico_analyzer/exports/Pizzaria_Empresa.json
```

**Análise sintática/semântica** — ao terminar o parse, se o pacote foi
reconhecido, é impressa a **tabela de síntese**: contagens gerais e uma
sub-tabela por tipo de declaração (própria ou trazida por import resolvido,
identificada pela coluna "Pacote de origem"). O exemplo abaixo é a saída real
de `python3 main.py --syntax tonto_examples/pizzaria/Pizzaria_Empresa.tonto` —
`Pizzaria_Empresa.tonto` importa `Pizzaria_Endereco.tonto` (que declara os
datatypes `Endereco` e `Contato`, usados como tipo dos atributos `endereco` e
`contato` em `Empresa`):

```
============ TABELA DE SÍNTESE ============

Pacote: Empresa
  Classes: 2  |  Datatypes: 2  |  Enums: 0  |  Gensets: 0  |  Relações externas: 0

Pacotes
  ┌──────────┬─────────┬───────────┬───────┬─────────┐
  │ Nome     │ Classes │ Datatypes │ Enums │ Gensets │
  ├──────────┼─────────┼───────────┼───────┼─────────┤
  │ Empresa  │ 2       │ 0         │ 0     │ 0       │
  │ Endereco │ 0       │ 2         │ 0     │ 0       │
  └──────────┴─────────┴───────────┴───────┴─────────┘

Classes
  ┌──────────┬─────────────┬─────────────┬───────────┬───────────────────┬──────────────────┐
  │ Nome     │ Estereótipo │ Especializa │ Atributos │ Relações internas │ Pacote de origem │
  ├──────────┼─────────────┼─────────────┼───────────┼───────────────────┼──────────────────┤
  │ Empresa  │ kind        │ -           │ 4         │ 0                 │ -                │
  │ Pizzaria │ role        │ Empresa     │ 0         │ 0                 │ -                │
  └──────────┴─────────────┴─────────────┴───────────┴───────────────────┴──────────────────┘

Relações internas
  (nenhum)

Relações externas
  (nenhum)

Datatypes
  ┌──────────┬───────────┬──────────────────┐
  │ Nome     │ Atributos │ Pacote de origem │
  ├──────────┼───────────┼──────────────────┤
  │ Endereco │ 5         │ Endereco         │
  │ Contato  │ 3         │ Endereco         │
  └──────────┴───────────┴──────────────────┘

Enums
  (nenhum)

Gensets
  (nenhum)

Nenhum erro léxico encontrado.

Nenhum erro sintático encontrado.

Nenhum erro semântico encontrado.
```

Quando há erro, os blocos de erro léxico/sintático/semântico são sempre
impressos juntos, nessa ordem, ao final da execução — depois de qualquer
tabela — cada um com linha, coluna, mensagem e uma sugestão de correção:

```
--- Erros sintáticos (1) ---
  linha 6, coluna 5: token inesperado ':' (COLON)
    sugestão: verifique se o atributo está no formato 'nome : tipo'.

--- Erros semânticos (1) ---
  linha 3, coluna 8: 'Pessoa' não foi declarado(a)
    sugestão: declare uma classe 'Pessoa' em algum ponto do pacote.
```

Um `import` que não encontra um arquivo `.tonto` vizinho com o
`package <Nome>` correspondente também gera um erro semântico
("pacote importado '<nome>' não foi encontrado").

**Análise semântica de padrões (ODPs)** com `--semantic`, depois do parse,
`semantic_analyzer/patterns` valida os seis ODPs e imprime três blocos: (1)
padrões encontrados por linhas, (2) erros a corrigir por coerção (separados
dos erros não coercíveis) e (3) padrões incompletos deduzidos por sobrecarga.
O exemplo abaixo é a saída real de
`python3 main.py --semantic tonto_examples/festa/Festa.tonto`:

```
============ PADRÕES DE PROJETO ============

(1) PADRÕES ENCONTRADOS POR LINHAS DE CÓDIGO

Padrões Subkind
  ┌──────────┬────────┬─────────┬────────────────────┬────────────────────────────────────┬────────────┐
  │ Variante │ Pacote │ General │ Específicos        │ Genset                             │ Linhas     │
  ├──────────┼────────┼─────────┼────────────────────┼────────────────────────────────────┼────────────┤
  │ 1        │ Festa  │ Pessoa  │ Participante       │ -                                  │ 3, 4       │
  │ 2        │ Festa  │ Bebida  │ Suco, Refrigerante │ TiposDeBebida [disjoint, complete] │ 6, 7, 8, 9 │
  └──────────┴────────┴─────────┴────────────────────┴────────────────────────────────────┴────────────┘

(2) ERROS A SEREM CORRIGIDOS POR COERÇÃO
  linha 4, coluna 1 [Festa]: kind 'Participante' especializa sortal rígido, estereótipo coercido de 'kind' para 'subkind'.
    sugestão: declare 'Participante' explicitamente como 'subkind Participante specializes Pessoa' (coerção kind -> subkind).

  Erros de padrão não coercíveis:
  linha 14, coluna 1 [Festa]: role 'ConvidadoEspecial' não declara um general válido para o padrão Role.
    sugestão: faça 'ConvidadoEspecial' especializar kind, subkind, collective, phase, role ou roleMixin.

(3) PADRÕES INCOMPLETOS DEDUZIDOS POR SOBRECARGA
  linha 7, coluna 1 [Festa]: 'Suco' não declara 'specializes Bebida', mas o genset 'TiposDeBebida' o agrupa sob 'Bebida'.
    sugestão: declare explicitamente 'subkind Suco specializes Bebida' (dedução pela sobrecarga do genset).
  linha 8, coluna 1 [Festa]: 'Refrigerante' não declara 'specializes Bebida', mas o genset 'TiposDeBebida' o agrupa sob 'Bebida'.
    sugestão: declare explicitamente 'subkind Refrigerante specializes Bebida' (dedução pela sobrecarga do genset).

Nenhum erro semântico encontrado.
```

# <a name="padroes-de-projeto"></a> Padrões de projeto de ontologias (ODPs)

A análise de padrões é dividida em um matcher por ODP. Cada um reconhece as
variantes do padrão, aplica as coerções cabíveis e produz as deduções de
padrões incompletos:

| ODP | O que valida | Coerção aplicada | Dedução |
|---|---|---|---|
| Subkind | subkind especializando sortal rígido; genset `disjoint` de subkinds | `kind → subkind` | específico do genset sem `specializes` |
| Role | role com general válido, dependência relacional e genset dos irmãos | `@material → @mediation` | dependência herdada de supertipo mediado |
| Phase | phases com general sortal e genset `disjoint` (completo opcional, mínimo 2 fases) | `subkind → phase` | partição de fases incompleta |
| Relator | relator mediando ao menos 2 universais substanciais | `kind → relator`, `@material → @mediation` | mediação faltante derivada de uma `@material` |
| Mode | mode com `@characterization`/`@inherence` para um endurante | `kind → mode` | mode sem relação de inerência |
| RoleMixin | roleMixin com roles e genset `disjoint`, identidade herdada de kind/collective | `category/mixin → roleMixin` | role sem `specializes` do roleMixin |

# <a name="conceitos-reconhecidos"></a> Conceitos da linguagem reconhecidos

| Categoria (`TokenEnum`) | Exemplos |
|---|---|
| `CLASS_STEREOTYPES` | `kind`, `subkind`, `phase`, `role`, `relator`, `mixin`, `event` |
| `RELATION_STEREOTYPES` | `material`, `mediation`, `componentOf`, `characterization` |
| `KEYWORDS` | `package`, `import`, `specializes`, `genset`, `where`, `of` |
| `NATIVE_TYPES` | `number`, `string`, `boolean`, `date`, `time`, `datetime` |
| `META_ATTRIBUTES` | `ordered`, `const`, `derived`, `subsets`, `redefines` |
| `NEW_TYPE` | `CPFDataType`, `PhoneNumberDataType` |
| `CLASS_ID` | `Person`, `Child`, `Second_Baptist_Church` |
| `RELATION_ID` | `has`, `hasParent`, `is_part_of` |
| `INSTANCE_ID` | `Planeta1`, `pizza03` |
| Composições/associações | `<>--`, `--<>`, `<o>--`, `--<o>`, `--` |
| `CARDINALITY` | `[1]`, `[0..*]`, `[1..*]` |
| Símbolos especiais | `{`, `}`, `(`, `)`, `.`, `,`, `+`, `<`, `>`, `@`, `-`, `*`, `:` |

Além dos tokens acima, o Analisador Sintático e o Analisador Semântico
reconhecem, juntos, as seguintes construções e verificações:

| Construção / Verificação | Descrição |
|---|---|
| Pacote e imports | `package <Nome>`, `import <Nome>` (resolvido contra o `package` de um arquivo vizinho) |
| Declaração de classe | estereótipo + nome, `specializes` (uma ou mais classes), atributos e relações internas |
| Declaração de datatype | `datatype <Nome> { ... }`, com atributos |
| Enumeração | `enum <Nome> { Literal1, Literal2, ... }` |
| Generalization set (genset) | `genset <Nome> where ... specializes ...` ou com bloco `{ general ... specifics ... }`, com disjunção/completude opcionais |
| Relação | interna a uma classe ou externa (`relation`), com estereótipo (`@mediation`, ...), cardinalidades e símbolo de associação/composição |
| Declaração duplicada | nome já declarado no mesmo escopo (erro semântico) |
| Nome não declarado / tipo incompatível | uso de um nome antes de declarado, ou declarado com categoria diferente da esperada (erro semântico, resolvido ao final do parse) |
| Import não resolvido / em conflito | pacote importado sem arquivo correspondente, ou símbolo importado conflitando com um já declarado (erro semântico) |
| Erro sintático com sugestão | token inesperado, com uma sugestão de correção baseada no contexto do erro |
