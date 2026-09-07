# Analisador Léxico para TONTO (Textual Ontology Language)

Projeto da disciplina de **Compiladores** (UFERSA/CCEN). O objetivo é reconhecer
os elementos da linguagem TONTO — estereótipos de classe e de relação, palavras
reservadas, símbolos especiais, identificadores (classes, relações e
instâncias), tipos nativos, novos tipos e meta-atributos — indicando **linha e
coluna** de cada token e tratando erros léxicos sem interromper a análise.

A automação parcial é feita com **PLY** (versão Python do LEX).

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
├── main.py                        (ponto de entrada / orquestrador)
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
│   ├── analyzer.py                (fachada: analisa arquivo/código)
│   └── reporter.py                (como o resultado é exibido)
│
└── tonto_examples/                (exemplos .tonto usados como teste)
    ├── car.tonto
    ├── Hospital.tonto
    └── ...demais exemplos
```

### <a name="descricao-dos-componentes"></a> Descrição dos componentes

* `main.py`

    * Ponto de entrada e "orquestrador" do compilador. Resolve qual arquivo será
      analisado (por argumento na linha de comando ou pelo menu de exemplos),
      chama o analisador léxico e entrega o resultado ao módulo de apresentação.
      Ele **não** conhece detalhes do PLY — só a fachada do pacote.

* `lexico_analyzer/` (Diretório)

    * Pacote Python que encapsula toda a lógica do **Analisador Léxico**. Está
      dividido em cinco arquivos, cada um com uma responsabilidade única, na
      ordem em que são usados:

    * `__init__.py`: torna o diretório um módulo importável e reexporta o que é
      de uso externo (`analisar_arquivo`, `imprimir_visao_analitica`, ...).

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

    * `analyzer.py`: **fachada** do pacote. Constrói o lexer uma única vez com
      `lex.lex(module=lexer_rules)` e expõe `analisar_codigo` (a partir de uma
      string) e `analisar_arquivo` (a partir de um `.tonto`), devolvendo a lista
      de tokens e a lista de erros encontrados.

    * `reporter.py`: cuida apenas da **apresentação**. A análise produz dados; a
      forma de exibir fica isolada aqui, então acrescentar outra visualização
      (tabela, JSON, CSV) mexe só neste arquivo.

* `tonto_examples/` (Diretório)

    * Arquivos de código-fonte em TONTO usados como casos de teste, incluindo os
      exemplos do repositório da disciplina e os *Ontology Design Patterns*
      (`Relator_Pattern.tonto`, `Role_Pattern.tonto`, `Phase_Pattern.tonto`, ...).

* `requirements.txt`, `pyproject.toml`, `ruff.toml`, `.editorconfig`

    * Dependências, metadados do projeto e padronização de formatação do código
      (indentação de 2 espaços, aspas duplas, `ruff` como linter/formatador).

### <a name="como-as-pecas-se-conectam"></a> Como as peças se conectam

```
                 tonto_examples/car.tonto
                            │
                            ▼
        main.py  ──►  analyzer.py  ──►  lexer_rules.py
     (orquestrador)    (fachada)      (regras do PLY)
                            │                │
                            │                ▼
                            │        token_definitions.py
                            │                │
                            │                ▼
                            │          token_types.py
                            ▼
                       reporter.py  ──►  saída no terminal
```

A dependência anda sempre em uma direção só: a apresentação não conhece o PLY, e
as definições da linguagem não conhecem quem as usa.

# <a name="instalacao"></a> Instalação

Requer **Python 3.12+**. Recomenda-se um ambiente virtual, criado dentro do
diretório do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate       # Linux/WSL/macOS
```

Instalação das dependências (`ply` para o analisador e `ruff` para o lint):

```bash
pip install -r requirements.txt
```

# <a name="como-executar"></a> Como executar

Modo interativo, com o menu de exemplos:

```bash
python3 main.py
```

Analisando um arquivo específico:

```bash
python3 main.py tonto_examples/car.tonto
```

### <a name="entrada-do-sistema"></a> Entrada do sistema

Sem argumentos, o programa lista os arquivos `.tonto` da pasta `tonto_examples/`
numerados; basta digitar o número correspondente e teclar `enter`:

```
--- Exemplos TONTO disponíveis ---

[00]  Hospital.tonto
[01]  Mode_Pattern.tonto
[02]  Phase_Pattern.tonto
...

Escolha o número do arquivo a analisar:
```

### <a name="saida-do-sistema"></a> Saída do sistema

Visão analítica dos tokens: cada linha do código-fonte seguida dos tokens que
ela gerou, com categoria, lexema, linha e coluna.

```
4: subkind CarAgency specializes Organization
  CUSTOM_TOKEN(TokenEnum.CLASS_STEREOTYPES, subkind, line=4, column=1)
  CUSTOM_TOKEN(TokenEnum.CLASS_ID, CarAgency, line=4, column=9)
  CUSTOM_TOKEN(TokenEnum.KEYWORDS, specializes, line=4, column=19)
  CUSTOM_TOKEN(TokenEnum.CLASS_ID, Organization, line=4, column=31)
```

Ao final, o resumo dos erros léxicos encontrados (ou a confirmação de que não
houve nenhum). Cada erro é reportado pela linha e coluna em que ocorreu e a
análise continua a partir do próximo caractere.

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
