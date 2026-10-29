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
interromper a análise.

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
4. [Conceitos da linguagem reconhecidos](#conceitos-reconhecidos)

# <a name="estrutura-do-projeto"></a> Estrutura do Projeto

### <a name="organizacao-das-pastas"></a> Organização das pastas

```
tonto-compilador/
│
├── main.py                        (ponto de entrada / orquestrador: CLI --lexic/--syntax)
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
├── syntax_analyzer/               (pacote do Analisador Sintático/Semântico)
│   ├── __init__.py                (API pública do pacote)
│   ├── ast_nodes.py               (nós da AST: Program, Package, ClassDeclaration, ...)
│   ├── symbol.py                  (o que é um símbolo: Symbol + SymbolCategory)
│   ├── symbol_table.py            (tabela de símbolos encadeada por escopo)
│   ├── errors.py                  (SyntacticError, SemanticError)
│   ├── grammar_rules.py           (a gramática PLY/YACC propriamente dita)
│   ├── semantic_actions.py        (motor que a gramática chama para declarar/verificar nomes)
│   ├── error_handling.py          (hook de erro do PLY + sugestões de correção)
│   ├── parser.py                  (monta o parser, resolve imports entre arquivos)
│   └── reporter.py                (erros sintáticos/semânticos + tabela de síntese)
│
└── tonto_examples/                (27 arquivos .tonto usados como teste, pasta plana)
    ├── car.tonto, Hospital.tonto, ...        (exemplos gerais / Ontology Design Patterns)
    ├── class_declaration.tonto / _errors.tonto
    ├── datatype_declaration.tonto / _errors.tonto
    ├── genset_declaration.tonto / _errors.tonto
    ├── relation_declaration.tonto / _errors.tonto
    ├── error_recovery_class_body.tonto, error_recovery_package_level.tonto
    ├── semantic_errors.tonto, syntax_errors.tonto, syntax.tonto
    └── Bookstore.tonto, Library.tonto, Catalog.tonto  (exemplo de import entre pacotes)
```

### <a name="descricao-dos-componentes"></a> Descrição dos componentes

* `main.py`

    * Ponto de entrada e "orquestrador" do compilador. Resolve o modo
      (`--lexic`, `--syntax`, ou nenhum dos dois — e então roda as duas
      fases) e o arquivo de entrada (por argumento na linha de comando ou
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

    * Pacote Python que encapsula a **Análise Sintática** e a **Análise
      Semântica**, construído sobre os tokens produzidos pelo
      `lexico_analyzer`. Também dividido por responsabilidade única:

    * `__init__.py`: fachada do pacote, reexporta `Node`, os dois tipos de
      erro, `analisar_arquivo`/`analisar_codigo`, os printers e os tipos de
      tabela de símbolos. Assim como no pacote léxico, `main.py` também
      importa alguns submódulos diretamente (`parser`, `reporter`,
      `ast_nodes`).

    * `ast_nodes.py`: define a **AST**. Um `Node(line, column)` base e um
      dataclass por construção da linguagem (`Literal`, `Enumeration`,
      `Attribute`, `ClassDeclaration`, `Relation`, `DataTypeDeclaration`,
      `GeneralizationSet`, `Import`, `Package`, `Program`).

    * `symbol.py`: define **o que é um símbolo**. `SymbolCategory` enumera as
      categorias de nomes que a linguagem declara (classe, datatype, enum,
      genset, relação, atributo, literal) e `Symbol` é o registro guardado na
      `SymbolTable` (nome, categoria, linha, coluna e pacote de origem, se
      importado).

    * `symbol_table.py`: a **tabela de símbolos**, encadeada por escopo — cada
      escopo aponta para o escopo que o envolve (`put`/`get_local`/`get`, este
      último percorrendo a cadeia até achar o nome ou esgotar os escopos).

    * `errors.py`: define `SyntacticError` (emitido pela gramática) e
      `SemanticError` (emitido pelas ações semânticas), ambos com
      valor/lexema, linha, coluna, mensagem e sugestão de correção.

    * `grammar_rules.py`: a **gramática PLY/YACC** propriamente dita —
      equivalente ao arquivo YACC, parceiro de `lexer_rules.py` ser o arquivo
      LEX. Organizada em seções (programa/pacote, enums, classes, datatypes,
      gensets, relações); cada regra monta um nó de `ast_nodes` e, quando a
      construção declara ou usa um nome, chama `semantic_actions`. Inclui o
      truque de "regras-marcadoras" (produções vazias que rodam no meio de
      outra regra, via `p[-1]`/`p[-2]`) para abrir o escopo de uma classe,
      enum ou datatype antes do corpo ser lido.

    * `semantic_actions.py`: o **motor da análise semântica**, chamado pelas
      ações da gramática para declarar símbolos, entrar/sair de escopos e
      marcar nomes usados para verificação posterior (`resolve_later`), que
      só é resolvida no fim do parse (`finalize`) — depois que o pacote e seus
      imports já foram vistos por inteiro. O par `snapshot`/`restore` existe
      para que `parser.py` consiga analisar um arquivo importado
      isoladamente, sem que a tabela de símbolos desse arquivo substitua a do
      arquivo principal em andamento.

    * `error_handling.py`: o hook `p_error` do PLY mais um conjunto de
      heurísticas privadas que olham a pilha de símbolos do parser
      (`symstack`) para sugerir a causa provável de um erro sintático, em vez
      de só reportar "token inesperado".

    * `parser.py`: monta o parser PLY a partir de `grammar_rules`
      (`yacc.yacc`), liga `error_handling`, e implementa a resolução de
      `import` entre arquivos `.tonto` do mesmo diretório: indexa os arquivos
      vizinhos pelo cabeçalho `package <Nome>`, analisa cada import
      isoladamente e percorre o grafo de imports em busca em largura (BFS),
      evitando ciclos/duplicatas. Expõe `analisar_codigo`/`analisar_arquivo`.

    * `reporter.py`: apresentação da fase sintática/semântica — listas de
      erro e `print_tabela_sintese`, que mescla declarações próprias com as
      trazidas por imports resolvidos e desenha as sub-tabelas (Pacotes,
      Classes, Relações internas, Datatypes, Enums, Gensets, Relações
      externas) via `table_printer`.

* `tonto_examples/` (Diretório)

    * Arquivos de código-fonte em TONTO usados como casos de teste: os
      exemplos do repositório da disciplina, os *Ontology Design Patterns*
      (`Relator_Pattern.tonto`, `Role_Pattern.tonto`, `Phase_Pattern.tonto`,
      ...), exemplos dedicados a cada construção sintática e seus respectivos
      casos de erro (`class_declaration.tonto`/`_errors`,
      `datatype_declaration.tonto`/`_errors`, `genset_declaration.tonto`/`_errors`,
      `relation_declaration.tonto`/`_errors`), exemplos de recuperação de erro
      (`error_recovery_class_body.tonto`, `error_recovery_package_level.tonto`)
      e de erros semânticos/sintáticos dedicados (`semantic_errors.tonto`,
      `syntax_errors.tonto`, `syntax.tonto`). Os imports entre pacotes são
      resolvidos casando o nome em `import <Nome>` com o cabeçalho
      `package <Nome>` de um arquivo **vizinho na mesma pasta** — não há
      estrutura de subpastas — como no encadeamento `Bookstore` → `Library` →
      `Catalog`.

* `requirements.txt`, `pyproject.toml`, `ruff.toml`, `.editorconfig`

    * Dependências, metadados do projeto e padronização de formatação do código
      (indentação de 2 espaços, aspas duplas, `ruff` como linter/formatador).

### <a name="como-as-pecas-se-conectam"></a> Como as peças se conectam

```
                       tonto_examples/*.tonto
                                 │
                                 ▼
                       main.py (orquestrador)
                   ┌─────────────┴──────────────┐
                   ▼                            ▼
       [--lexic]  analyzer.py        [--syntax]  parser.py
                  (fachada léxica)               (monta o parser PLY,
                   │                              resolve imports)
                   ▼                              │          │
            lexer_rules.py                        ▼          ▼
                   │                     grammar_rules.py  error_handling.py
                   ▼                           │  (ações chamam)
      token_definitions.py /                    ▼
         token_types.py             semantic_actions.py ──► symbol_table.py / symbol.py
                   │                            │
                   │                            ▼ (constrói)
                   │                     ast_nodes.py (Program/Package/...)
                   ▼                            ▼
       lexico_analyzer/reporter.py   syntax_analyzer/reporter.py
                   │                            │
                   └─────────────┬──────────────┘
                                  ▼
                           table_printer.py
                                  │
                                  ▼
                           saída no terminal
```

A dependência anda sempre em uma direção só: a apresentação não conhece o PLY,
a gramática/ações semânticas não conhecem o reporter, e as definições da
linguagem não conhecem quem as usa. `table_printer.py` é o ponto onde as duas
fases convergem antes de chegar ao terminal.

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

Sem flag, roda as duas fases (léxica e sintática/semântica) em sequência,
no modo interativo com o menu de exemplos:

```bash
python3 main.py
```

Analisando um arquivo específico, com as duas fases:

```bash
python3 main.py tonto_examples/car.tonto
```

Rodando só uma das fases — a flag, quando usada, deve vir **antes** do
caminho do arquivo:

```bash
python3 main.py --lexic tonto_examples/car.tonto   # só análise léxica
python3 main.py --syntax tonto_examples/car.tonto  # só análise sintática/semântica
python3 main.py --lexic                            # só léxica, com menu de exemplos
python3 main.py --syntax                           # só sintática, com menu de exemplos
```

### <a name="entrada-do-sistema"></a> Entrada do sistema

Sem argumento de arquivo, o programa lista os `.tonto` da pasta
`tonto_examples/` numerados; basta digitar o número correspondente e teclar
`enter`:

```
--- Exemplos TONTO disponíveis ---

[00]  Bookstore.tonto
[01]  Catalog.tonto
[02]  Hospital.tonto
...

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
linha 4: "subkind CarAgency specializes Organization"
┌──────────────┬────────┬───────────────────┬─────────────────────────┐
│ Valor        │ Coluna │ Tipo              │ Classificação           │
├──────────────┼────────┼───────────────────┼─────────────────────────┤
│ subkind      │ 1      │ CLASS_STEREOTYPES │ Estereótipos de classe  │
│ CarAgency    │ 9      │ CLASS_ID          │ Classes                 │
│ specializes  │ 19     │ KEYWORDS          │ Palavras reservadas     │
│ Organization │ 31     │ CLASS_ID          │ Classes                 │
└──────────────┴────────┴───────────────────┴─────────────────────────┘
```

Em seguida, a contagem de tokens reconhecidos por classificação (tipos sem
classificação, como símbolos, não entram nesse resumo, mas continuam
contados no total). Os tokens e a contagem por tipo também são exportados
para `lexico_analyzer/exports/<nome_do_arquivo>.json`:

```
--- Contagem de tokens por classificação ---
  Palavras reservadas: 4
  Classes: 8
  Estereótipos de classe: 4
  ...

Total: 37 tokens

Tokens e contagem exportados para: lexico_analyzer/exports/car.json
```

**Análise sintática/semântica** — ao terminar o parse, se o pacote foi
reconhecido, é impressa a **tabela de síntese**: contagens gerais e uma
sub-tabela por tipo de declaração (própria ou trazida por import resolvido,
identificada pela coluna "Pacote de origem"). O exemplo abaixo é a saída real
de `python3 main.py --syntax tonto_examples/Library.tonto` — `Library.tonto`
importa `Catalog.tonto` (que declara a classe `Genre`, usada como tipo do
atributo `genre` em `Book`):

```
============ TABELA DE SÍNTESE ============

Pacote: Library
  Classes: 3  |  Datatypes: 0  |  Enums: 0  |  Gensets: 0  |  Relações externas: 0

Pacotes
  ┌─────────┬─────────┬───────────┬───────┬─────────┐
  │ Nome    │ Classes │ Datatypes │ Enums │ Gensets │
  ├─────────┼─────────┼───────────┼───────┼─────────┤
  │ Library │ 2       │ 0         │ 0     │ 0       │
  │ Catalog │ 1       │ 0         │ 0     │ 0       │
  └─────────┴─────────┴───────────┴───────┴─────────┘

Classes
  ┌────────┬─────────────┬─────────────┬───────────┬───────────────────┬──────────────────┐
  │ Nome   │ Estereótipo │ Especializa │ Atributos │ Relações internas │ Pacote de origem │
  ├────────┼─────────────┼─────────────┼───────────┼───────────────────┼──────────────────┤
  │ Book   │ kind        │ -           │ 3         │ 0                 │ -                │
  │ Author │ kind        │ -           │ 0         │ 0                 │ -                │
  │ Genre  │ kind        │ -           │ 0         │ 0                 │ Catalog          │
  └────────┴─────────────┴─────────────┴───────────┴───────────────────┴──────────────────┘

Relações internas
  (nenhum)

Datatypes
  (nenhum)

Enums
  (nenhum)

Gensets
  (nenhum)

Relações externas
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

Além dos tokens acima, o Analisador Sintático/Semântico reconhece as
seguintes construções e verificações:

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
