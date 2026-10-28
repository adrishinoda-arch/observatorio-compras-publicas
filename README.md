<a id="topo"></a>

# Projeto: Auditoria e Inteligência em Compras Públicas (PNCP)

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

</div>

Esteira analítica ponta a ponta (End-to-End) para auditoria e inteligência de dados em compras públicas federais. Transforma dados brutos e corrompidos do PNCP em um ambiente analítico confiável, auditável e executivo para a Controladoria, utilizando **Python**, **PostgreSQL** e **Power BI**.

---

## 📑 Índice

- [1. Contexto e Problema de Negócio](#1-contexto)
- [2. Arquitetura da Solução e Tecnologias](#2-arquitetura)
- [3. Auditoria Inicial e Dicionário de Inconsistências](#3-auditoria)
  - [3.1. Pergunta 1 — Volumetria e duplicidade da chave](#31-volumetria)
  - [3.2. Pergunta 2 — Formatos de dinheiro, data, CNPJ e nulos](#32-formatos)
  - [3.3. Pergunta 3 — Encoding quebrado](#33-encoding)
  - [3.4. Pergunta 4 — Cronologia](#34-cronologia)
  - [3.5. Síntese para a Sprint 2](#35-sintese)
- [4. Decisões Técnicas e Regras de Negócio](#4-decisoes)
  - [4.1. Sanitização em Python (`src/limpeza.py`)](#41-sanitizacao)
  - [4.2. Regras de negócio da Controladoria](#42-regras-negocio)
- [5. Modelagem Dimensional (Star Schema)](#5-modelagem)
- [6. Perguntas de Negócio e Respostas](#6-perguntas)
- [7. Planejamento em Sprints e Lições Aprendidas](#7-sprints)
  - [7.1. Histórico de Sprints](#71-historico)
- [8. Guia de Execução](#8-execucao)
- [9. Melhorias Futuras e Vídeo de Defesa](#9-melhorias)

---

<a id="1-contexto"></a>
## 1. Contexto e Problema de Negócio

*[A preencher na Fase 1]*

[⬆ Voltar ao índice](#-índice)

---

<a id="2-arquitetura"></a>
## 2. Arquitetura da Solução e Tecnologias

*[A preencher na Fase 1]*

*(Python, PostgreSQL, Power BI, Git)*

### 2.3. Estratégia de Versionamento (Git Workflow)

O projeto adotou **Feature Branching por fase**, com **merge via Pull Request** ao final de cada uma. Objetivo: manter a `main` sempre estável e preservar o histórico granular da evolução.

**Ciclo por fase:**

1. `git checkout -b feat/fase-N-...` a partir da `main` atualizada;
2. Commits granulares na branch (`feat:`, `fix:`, `docs:`);
3. Pull Request descritivo para `main`, ao concluir o Checklist de Fechamento da fase;
4. **Create a merge commit** (não squash) — preserva os commits originais no histórico da `main`.

**Rollback:** como cada fase vive numa branch isolada, reverter uma entrega problemática é `git checkout main` + deletar a branch — a `main` permanece intacta no estado anterior. A granularidade dos commits (não-squash) permite ainda `git revert` cirúrgico de um único commit, sem desfazer a fase inteira. O Pull Request mergeado funciona como ponto de retorno documentado.

**Segurança:** a `main` é protegida por dois mecanismos — o `.gitignore` bloqueia o `.env` (credenciais do PostgreSQL nunca entram no repositório) e o fluxo de PR impede pushes diretos, forçando que todo código passe por validação contra a Prova Real antes do merge. As branches de fase são mantidas após o merge para auditoria retroativa no vídeo de defesa.

[⬆ Voltar ao índice](#-índice)

---

<a id="3-auditoria"></a>
## 3. Auditoria Inicial e Dicionário de Inconsistências

O script `src/auditoria.py` faz um raio-x **somente diagnóstico** (não altera os dados): carrega os 3 CSVs como texto (`dtype=str`) para preservar zeros à esquerda e evitar inferência equivocada de tipos. As subseções abaixo respondem, uma a uma, às 4 perguntas da Seção 7.4 do enunciado.

---

<a id="31-volumetria"></a>
### 3.1. Pergunta 1 — Volumetria e duplicidade da chave

> *"Quantas linhas tem cada arquivo? Há `numero_controle_pncp` repetido em `compras.csv`?"*

**Resposta:**

- **`compras.csv`:** 2.042 linhas × 25 colunas.
- **`itens.csv`:** 7.077 linhas × 14 colunas.
- **`resultados.csv`:** 15.896 linhas × 13 colunas.
- **`numero_controle_pncp` em `compras.csv`:** 2.042 linhas, 2.042 valores distintos → **zero duplicatas**. O grão "1 linha por contratação" está preservado.

**Chave de ligação:** `numero_controle_pncp` (liga `compras` → `itens` → `resultados`). A combinação `numero_controle_pncp` + `numero_item` identifica unicamente cada linha de `itens` e de `resultados`.

Os três números de linhas conferem **exatamente** com o Anexo 8 (Prova Real) do enunciado.

---

<a id="32-formatos"></a>
### 3.2. Pergunta 2 — Formatos de dinheiro, data, CNPJ e nulos

> *"Que formatos de dinheiro, de data e de CNPJ aparecem? Quais colunas têm N/A, -, 0, vazio?"*

**Resposta:**

- **Dinheiro:** a mesma coluna mistura `R$`, vírgula decimal e ponto decimal (inclusive o padrão invertido `250,782.10`). **Nenhum** valor veio como "só dígitos" — todos têm parte decimal. O formato **predominante é o inglês/ISO** (ponto decimal, 78%), com minoria brasileira (vírgula decimal, 22%).
- **Data:** **8 formatos distintos coexistem** na base — ISO 8601 com `T` (`aaaa-mm-ddThh:mm[:ss]`), ISO puro (`aaaa-mm-dd`), `dd/mm/aaaa`, `dd/mm/aaaa hh:mm`, `dd-mm-aaaa`, `dd.mm.aaaa`, `aaaammdd` e `aaaa/mm/dd`. Por isso, `pd.to_datetime(dayfirst=True)` sozinho **não resolve**: foi implementada a função `parse_data_robusto()` com **16 variações** (cobrindo combinações com e sem hora) para garantir 100% de cobertura.
- **CNPJ/CPF:** há mascarados, puros (14 dígitos), com zero perdido (13 dígitos) e CPF convivendo com CNPJ na mesma coluna.
- **Nulos disfarçados:** aparecem em 6 colunas, com destaque para `categoria_item` (100% `"NÃO SE APLICA"`) e `modo_disputa` (45%).
- **`"0"` em texto:** aparece em 4 colunas (`processo`, `modo_disputa`, `situacao_item`, `porte`) — será tratado como nulo **apenas** nessas colunas.
- **Vazio real (`NaN`):** destacam-se `catalogo_codigo_item` (99,9%), `ordem_classificacao_srp` (75%) e `data_cancelamento` (99,6%, equivalente a 62 cancelados). Há ainda 7 outras colunas com NaN em menor volume (detalhadas na Tabela 3.2.2).

**Detalhamento:**

#### 3.2.1. Nulos disfarçados (`N/A`, `NULL`, `-`, `SEM INFORMAÇÃO`, `NÃO SE APLICA`)

| Arquivo | Coluna | Ocorrências | Observação |
| :--- | :--- | ---: | :--- |
| `compras.csv` | `processo` | 32 | campo opcional |
| `compras.csv` | `modo_disputa` | 925 | **45% da base** |
| `itens.csv` | `categoria_item` | 7.077 | **100%** — coluna inútil |
| `itens.csv` | `situacao_item` | 79 | campo opcional |
| `itens.csv` | `criterio_julgamento` | 1.883 | 26,6% |
| `resultados.csv` | `porte` | 172 | campo opcional |

> **Decisão de projeto:** `"0"` **não** foi classificado como nulo nesta tabela. O enunciado alerta que `"0"` só é nulo em **campos de texto**; em quantidades e valores é número. A separação por tipo acontece na Sprint 2.

#### 3.2.2. Zeros e vazios

| Arquivo | Coluna | `"0"` | Vazios (`""`) | NaN real | Observação |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `compras.csv` | `processo` | 12 | 0 | 28 | — |
| `compras.csv` | `modo_disputa` | 7 | 0 | 26 | — |
| `compras.csv` | `data_abertura_proposta` | 0 | 0 | 617 | 30% sem data |
| `compras.csv` | `data_encerramento_proposta` | 0 | 0 | 617 | 30% sem data |
| `itens.csv` | `unidade_medida` | 0 | 0 | 9 | — |
| `itens.csv` | `situacao_item` | 25 | 0 | 92 | — |
| `itens.csv` | `catalogo_codigo_item` | 0 | 0 | 7.068 | **99,9% vazio** — descartar |
| `resultados.csv` | `ordem_classificacao_srp` | 0 | 0 | 11.976 | **75% vazio** — esperado em Credenciamento |
| `resultados.csv` | `porte` | 57 | 0 | 196 | — |
| `resultados.csv` | `data_cancelamento` | 0 | 0 | 15.834 | **só 62 cancelados** (0,4%) |

#### 3.2.3. Formatos monetários

A base mistura **prefixo `R$`**, **vírgula decimal** e **ponto decimal** na **mesma coluna**. Isso confirma a regra do enunciado: *"ponto ou vírgula sozinho é sempre decimal; só o separador repetido (1.234.567) é milhar; quando aparecem os dois símbolos, o último é o decimal"*.

**Tabela A — Presença do prefixo `R$`**

| Arquivo | Coluna | Com `R$` | Sem `R$` (implícito) |
| :--- | :--- | ---: | ---: |
| `compras.csv` | `valor_total_estimado` | 344 | 1.698 |
| `compras.csv` | `valor_total_homologado` | 346 | 1.696 |
| `itens.csv` | `valor_unitario_estimado` | 1.188 | 5.889 |
| `itens.csv` | `valor_total_estimado` | 1.171 | 5.906 |
| `resultados.csv` | `valor_unitario_homologado` | 2.650 | 13.246 |
| `resultados.csv` | `valor_total_homologado` | 2.647 | 13.249 |

**Tabela B — Separador decimal (última posição)**

> Esta tabela é **mutuamente exclusiva** e **soma exatamente o total** de cada coluna — a classificação está 100% completa.

| Arquivo | Coluna | Vírgula decimal (BR) | Ponto decimal (EN/ISO) | Total | ✓ |
| :--- | :--- | ---: | ---: | ---: | :---: |
| `compras.csv` | `valor_total_estimado` | 445 | 1.597 | 2.042 | ✅ |
| `compras.csv` | `valor_total_homologado` | 442 | 1.600 | 2.042 | ✅ |
| `itens.csv` | `valor_unitario_estimado` | 1.489 | 5.588 | 7.077 | ✅ |
| `itens.csv` | `valor_total_estimado` | 1.462 | 5.615 | 7.077 | ✅ |
| `resultados.csv` | `valor_unitario_homologado` | 3.356 | 12.540 | 15.896 | ✅ |
| `resultados.csv` | `valor_total_homologado` | 3.315 | 12.581 | 15.896 | ✅ |

> **Nota:** as duas tabelas **não podem ser somadas** entre si. Os valores com `R$` (Tabela A) também aparecem em uma das categorias de decimal (Tabela B). Ou seja, `"R$ 419.848,81"` conta em **"com R$"** e em **"vírgula decimal"** ao mesmo tempo.

**Exemplos que coexistem na mesma coluna:**

- `"20307804.45"` (ponto decimal, sem prefixo)
- `"R$ 419.848,81"` (ponto milhar + vírgula decimal + prefixo)
- `"250,782.10"` (vírgula milhar + ponto decimal — **inverso** do padrão brasileiro)
- `"19.290.383,46"` (formato brasileiro completo)
- `"900.0"`, `"151826.0"` (ponto decimal, apenas 1 casa)

**Achados para a Sprint 2:**

- O formato **predominante é o inglês/ISO** (ponto decimal): **78%** dos valores; o brasileiro (vírgula) representa **22%**.
- **Nenhum** valor aparece como "só dígitos" (0 ocorrências) e **nenhum** aparece como negativo entre parênteses (0 ocorrências). Todo valor monetário termina em `,XX` ou `.XX`.
- A regra do enunciado ("o último símbolo é o decimal") resolve 100% dos casos sem ambiguidade.

#### 3.2.4. Formatos de data

| Arquivo | Coluna | `dd/mm/aaaa` | `dd/mm/aaaa hh:mm` | ISO | `dd-mm-aaaa` | Outros |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| `compras.csv` | `data_publicacao` | 117 | 126 | 1.319 | 138 | 342 |
| `compras.csv` | `data_abertura_proposta` | 78 | 86 | 912 | 85 | 264 |
| `compras.csv` | `data_encerramento_proposta` | 78 | 101 | 926 | 75 | 245 |
| `resultados.csv` | `data_resultado` | 929 | 934 | 10.301 | 912 | 2.820 |

> **Nota:** a coluna "ISO" representa dois formatos distintos: `aaaa-mm-ddThh:mm[:ss]` (ISO **com** `T`) nas datas de `compras.csv` e `aaaa-mm-dd` (ISO **puro**, sem hora) em `data_resultado`. Nenhum arquivo mistura os dois — cada campo tem seu formato dominante.

**Formatos em "Outros":** `dd.mm.aaaa` (`02.01.2025`), `aaaammdd` (`20250103`), `aaaa/mm/dd` (`2025/01/02`).

> **Consequência:** a conversão exige **parser multi-formato** — implementado como `parse_data_robusto()` em `src/auditoria.py` e reaproveitado na Sprint 2.

#### 3.2.5. Formatos de CNPJ/CPF

| Arquivo | Coluna | Mascarado | 14 díg. | 13 díg. (zero perdido) | CPF mascarado | CPF 11 díg. |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| `compras.csv` | `cnpj_orgao` | 176 | 1.789 | **10** | — | **3** |
| `resultados.csv` | `ni_fornecedor` | 1.239 | 9.911 | **175** | 392 | 3.981 |

**Achados críticos:**

- **175 CNPJs perderam o zero à esquerda** em `ni_fornecedor` (13 dígitos em vez de 14) — o enunciado previu isso.
- **3 valores em `cnpj_orgao` são CPF (11 dígitos)** — inconsistência grave: `cnpj_orgao` deveria conter apenas CNPJ de órgão público. Esses 3 registros precisarão de atenção manual.
- `ni_fornecedor` tem **3.981 CPFs puros** e **392 CPFs mascarados** — a base mistura pessoa física e jurídica.

---

<a id="33-encoding"></a>
### 3.3. Pergunta 3 — Encoding quebrado

> *"Existe texto com acento quebrado (Ã§, Ã£)? Em quais colunas?"*

**Resposta:** **Sim.** O encoding quebrado aparece em **5 colunas de texto livre** — `objeto_compra`, `municipio`, `nome_unidade`, `descricao` e `nome_fornecedor`. Não há encoding quebrado em colunas de código, data ou valor.

**Detalhamento:**

| Arquivo | Coluna | Padrões quebrados detectados | Total aprox. |
| :--- | :--- | :--- | ---: |
| `compras.csv` | `objeto_compra` | `Ã§`, `Ã£`, `Ã©`, `Ã¡`, `Ã³`, `Ãº` | ~115 |
| `compras.csv` | `municipio` | `Ã§`, `Ã£`, `Ã©`, `Ã³` | ~23 |
| `compras.csv` | `nome_unidade` | `Ã§`, `Ã£`, `Ã©`, `Ã³` | ~4 |
| `itens.csv` | `descricao` | `Ã§`, `Ã£`, `Ã©`, `Ã¡`, `Ã³`, `Ãº` | ~216 |
| `resultados.csv` | `nome_fornecedor` | `Ã©` | ~1 |

> **"Total aproximado"** porque uma mesma célula pode conter mais de um padrão (ex: `"AÃ§Ã£o"` conta em `Ã§` e em `Ã£`).

> **Nota técnica:** o caractere `"Ã"` **isolado** foi removido dos padrões de detecção porque gera falso positivo — palavras legítimas como "SÃO", "AÇÃO" e "MUNICÍPIO" contêm `Ã` como grafia correta. O indicador real de dupla codificação é `Ã` **seguido de outro caractere** (`Ã§`, `Ã£`, `Ã©` etc.).

---

<a id="34-cronologia"></a>
### 3.4. Pergunta 4 — Cronologia: `data_resultado` vs. `data_publicacao`

> *"Existe `data_resultado` anterior a `data_publicacao`?"*

**Resposta:** **Sim.** Há **1.056 casos (6,64%)** de `data_resultado` anterior à `data_publicacao`, entre os 15.896 resultados da base. Esses registros serão anulados na Sprint 3 (regra 7 do enunciado), mantendo o item na Fato mas sem ciclo.

**Detalhamento:**

- Total de resultados: **15.896**;
- Resultados com ambas as datas válidas (parser multi-formato): **15.896 (100,0%)**;
- Datas invertidas (`data_resultado` < `data_publicacao`): **1.056 (6,64%)**.

**Parser utilizado:** `parse_data_robusto()` tenta sequencialmente **16 variações** (8 formatos-base × combinações com/sem hora e com/sem segundos), até esgotar. Os **8 formatos-base** observados na base são: ISO 8601 com `T`, ISO puro, `dd/mm/aaaa`, `dd/mm/aaaa hh:mm`, `dd-mm-aaaa`, `dd.mm.aaaa`, `aaaammdd` e `aaaa/mm/dd` — todos cobertos pelo parser, o que garante **100% de cobertura** (15.896 de 15.896).

**Impacto previsto na Sprint 3:** os 1.056 resultados com datas invertidas não correspondem, necessariamente, a 1.056 itens sem ciclo. Após a **regra 2** (escolher o vencedor por item), apenas os itens cujo **vencedor** tem `data_resultado` invertida perderão a data de homologação.

---

<a id="35-sintese"></a>
### 3.5. Síntese para a Sprint 2

| Inconsistência | Colunas afetadas | Estratégia prevista |
| :--- | :--- | :--- |
| **CNPJ/CPF mascarado** | `cnpj_orgao`, `ni_fornecedor` | Remover `.`, `/`, `-`; manter como `str`; devolver zero à esquerda até 14 dígitos |
| **CNPJ com zero perdido** | `cnpj_orgao` (10), `ni_fornecedor` (175) | `zfill(14)` após limpeza |
| **CPF em campo de órgão** | `cnpj_orgao` (3) | Marcar e documentar; tratar como "não informado" na Fase 3 |
| **Moeda: `R$`, vírgula, ponto** | 6 colunas monetárias | Normalizar pela regra do enunciado (último símbolo = decimal); validar que `vírgula + ponto = total` |
| **Datas em 8 formatos** | 4 colunas | `parse_data_robusto()` (já implementado) |
| **Nulos disfarçados** | 6 colunas | Substituir por `NaN`/`None` **após** classificar tipo |
| **`"0"` em campo de texto** | `processo`, `modo_disputa`, `situacao_item`, `porte` | Tratar como nulo **apenas** nessas colunas |
| **Encoding quebrado** | 5 colunas de texto | Reprocessar como `latin-1` → `utf-8` |
| **`catalogo_codigo_item` vazio** | `itens.csv` | Descartar (99,9% vazio) |
| **Datas invertidas** | `resultados.data_resultado` vs. `compras.data_publicacao` | Anular `data_homologacao` e `dias_ciclo` (regra 7) |

[⬆ Voltar ao índice](#-índice)

---

<a id="4-decisoes"></a>
## 4. Decisões Técnicas e Regras de Negócio

<a id="41-sanitizacao"></a>
### 4.1. Sanitização em Python (`src/limpeza.py`) — Fase 2 (Engenharia de Dados Python) — Sprint 2

O módulo `src/limpeza.py` foi concluído com **54/54 testes passando**. Cada função resolve uma classe de inconsistência identificada na Seção 3.

#### 4.1.1. Limpeza de texto

| Função | Inconsistência tratada | Decisão técnica |
| :--- | :--- | :--- |
| `remover_invisiveis()` | Caracteres zero-width (`\u200b`, `\u200c`, `\ufeff`) de sistemas antigos | Substituição literal por string vazia |
| `consertar_acento()` | Dupla codificação UTF-8→Latin-1 (`AquisiÃ§Ã£o` → `Aquisição`) | `encode("latin-1").decode("utf-8")` dentro de `try/except` — se falhar, devolve o texto como estava |
| `tirar_espacos()` | Espaços repetidos, tabs, quebras de linha, non-breaking space (`\xa0`) | `" ".join(texto.split())` — o `split()` sem argumento cobre **todos** os whitespaces |
| `eh_nulo()` | Nulos disfarçados (`N/A`, `-`, `NULL`, `"0"` em texto) | Retorna `True` se o texto (em maiúsculas) está no set `NULOS` |
| `limpar_texto()` | Pipeline de todas as anteriores | Remover invisíveis → corrigir acento → tirar espaços → checar se virou nulo |
| `padronizar_nome()` | Nomes de órgão/fornecedor escritos de formas diferentes | `upper()` + troca de `-` por `" - "` (o `tirar_espacos` absorve duplicados) |

#### 4.1.2. Ambiguidade do `"0"` — decisão de *design*

A Seção 3 registrou que `"0"` **não foi tratado como nulo na auditoria**, aguardando separação por tipo (texto vs. numérico). A `limpeza.py` resolve a ambiguidade através do parâmetro **`zero_eh_nulo`**:

- **`zero_eh_nulo=True`** (padrão, para campos de texto) — `"0"` é nulo disfarçado.
- **`zero_eh_nulo=False`** (para campos numéricos) — `"0"` é o valor `0.0`.

A função `converter_numero()` chama `limpar_texto(texto, zero_eh_nulo=False)` explicitamente. Os campos `processo`, `modo_disputa`, `situacao_item` e `porte` (identificados na Seção 3) usarão o padrão `True`.

#### 4.1.3. Documentos (CNPJ/CPF)

| Função | Decisão técnica |
| :--- | :--- |
| `limpar_documento()` | Extrai apenas dígitos (`c.isdigit()`), descarta máscaras. Usa `zfill(tamanho)` para restaurar zeros à esquerda perdidos. Tamanho = 14 (PJ), 11 (PF) ou inferido pelo comprimento. **Pessoa estrangeira (PE)** é preservada como texto em maiúsculas. Documentos com dígitos a mais são rejeitados (`None`). |

**Cobertura contra a Seção 3:**
- 175 CNPJs com zero à esquerda em `ni_fornecedor` → `zfill(14)` recupera;
- 10 CNPJs com zero perdido em `cnpj_orgao` → idem;
- 3.981 CPFs puros + 392 CPFs mascarados → extração limpa;
- 3 CPFs em `cnpj_orgao` → serão rejeitados pela função (`tipo_pessoa="PJ"` espera 14 dígitos). Decisão de destino final na Sprint 3.

#### 4.1.4. Dinheiro e números

| Função | Decisão técnica |
| :--- | :--- |
| `converter_numero()` | Implementa a regra do enunciado: **ponto ou vírgula sozinho é decimal; repetido é milhar; quando os dois aparecem, o último é o decimal**. Negativos detectados por `(`, `-` no início ou `-` no final. Usa `zero_eh_nulo=False` (aqui `"0"` é valor, não nulo). |

Todos os formatos monetários identificados na Seção 3 são convertidos corretamente (`R$ 419.848,81`, `19.290.383,46`, `250,782.10`, `900.0`, `1.234.567`, `(1.500,00)`, `1.500,00-`).

#### 4.1.5. Datas

| Função | Decisão técnica |
| :--- | :--- |
| `converter_data()` | Corta o texto em 10 caracteres (`[:10]`) para descartar a hora. Testa **6 formatos** em sequência. Retorna `datetime.date` (não `datetime`) — alinhado com o tipo `DATE` do PostgreSQL (Sprint 4). Valida faixa de ano **2000–2030** — datas fora disso (ex: `0001-01-01`) são rejeitadas como impossíveis. |

Os 8 formatos detectados na auditoria descrita na Seção 3 são cobertos pelos 6 formatos-base (combinados com/sem hora). Datas invertidas (1.056 casos) serão tratadas na Sprint 3 pela **regra 7** do enunciado.

#### 4.1.6. Limitações conhecidas (alimentam a Seção 9 — Melhorias Futuras)

- **`padronizar_nome()`** insere espaço ao redor de qualquer `-`. Resolve `"Pregão-Eletrônico"` → `"PREGÃO - ELETRÔNICO"`, mas alteraria códigos com hífen interno (ex: `"ABC-123"` → `"ABC - 123"`). Para o escopo atual (nomes de órgão/fornecedor), é aceitável.
- **`remover_invisiveis()`** usa caracteres zero-width literais no código-fonte (invisíveis no editor). Alternativa mais robusta: usar `\u200b` explícito como escape Unicode. Não impacta o resultado; é questão de manutenibilidade.

<a id="42-regras-negocio"></a>
### 4.2. Regras de negócio da Controladoria (`src/montar_tabelas.py`)

#### 4.2.1. Decisões herdadas da auditoria (Sprint 1) e da limpeza (Sprint 2)

Esta subseção registra decisões que **conectam** os achados da Seção 3 com a implementação da Sprint 3, evitando que pareçam "esquecimentos".

| Coluna | Achado (Seção 3) | Decisão na Sprint 3 |
| :--- | :--- | :--- |
| `categoria_item` | 100% `"NÃO SE APLICA"` | **Descartada** — não vai para nenhuma tabela |
| `catalogo_codigo_item` | 99,9% vazio (7.068 de 7.077) | **Descartada** |
| `ordem_classificacao_srp` | 75% NaN (11.976) | **NaN → 1** (regra 2 do enunciado: "vazio conta como 1") |
| `data_cancelamento` | 99,6% vazio (15.834 NaN) | **Lida como booleana** — preenchido = cancelado, independente do conteúdo |
| `cnpj_orgao` com CPF | 3 registros com 11 dígitos | **Rejeitados** por `limpar_documento(tipo_pessoa="PJ")` → `sk_orgao = -1` |
| Colunas monetárias | 6 colunas com formatos mistos | `converter_numero()` com `zero_eh_nulo=False` |
| Parser de data | 8 formatos-base coexistem | `converter_data()` cobre os 8 (6 formatos-base + corte `[:10]`) |

#### 4.2.2. Colunas numéricas com `zero_eh_nulo=False`

O parâmetro `zero_eh_nulo` (definido em 4.1.2) deve ser `False` para as seguintes colunas (onde `0` é valor legítimo, não nulo):

- `itens.csv`: `quantidade`, `valor_unitario_estimado`, `valor_total_estimado`
- `resultados.csv`: `quantidade_homologada`, `valor_unitario_homologado`, `valor_total_homologado`, `ordem_classificacao_srp`, `sequencial_resultado`

Todas as demais colunas usam `limpar_texto()` com o padrão `zero_eh_nulo=True`.

#### 4.2.3. Duplicação intencional de parser de data

Existem duas implementações de parser no projeto:

| Parser | Onde | Propósito | Estratégia |
| :--- | :--- | :--- | :--- |
| `parse_data_robusto()` | `auditoria.py` | **Diagnóstico** (Sprint 1) | 16 variações, sem corte — maximiza detecção |
| `converter_data()` | `limpeza.py` | **Operação** (Sprint 2 em diante) | 6 formatos-base + `[:10]` para descartar hora |

Ambas cobrem os 8 formatos-base identificados em 3.2.4. A duplicação é **intencional**: o diagnóstico exige robustez máxima; a operação exige clareza e velocidade.

#### 4.2.4. Colunas onde `padronizar_nome()` será aplicado

- `compras.razao_social_orgao` → `dim_orgao.nome_orgao`
- `resultados.nome_fornecedor` → `dim_fornecedor.nome_fornecedor`
- `itens.descricao` → vai para `fato_item_contratado.descricao_item` **sem** uppercase (preserva case original para legibilidade em auditoria)
- `compras.objeto_compra` → usado apenas como auxiliar da regra 8 (perfil do gasto), **sem** uppercase

#### 4.2.5. Implementação das 12 regras de negócio — resultado

O script `src/montar_tabelas.py` foi implementado com sucesso: **todos os 10 números da Prova Real batem** com o Anexo 8 do enunciado.

| Métrica | Obtido | Prova Real | ✓ |
| :--- | ---: | ---: | :---: |
| Itens na fato | 6.126 | 6.126 | ✅ |
| Contratações distintas | 1.962 | 1.962 | ✅ |
| Fornecedores | 2.652 | 2.652 | ✅ |
| Órgãos (CNPJ) | 363 | 363 | ✅ |
| Volume homologado | R$ 8.044.498.805,74 | R$ 8.044.498.805,74 | ✅ |
| Itens comparáveis | 5.457 | 5.457 | ✅ |
| Economia | 14,46% | 14,46% | ✅ |
| Ciclo médio / máximo | 48,1 / 611 | 48,1 / 611 | ✅ |
| Itens sem ciclo | 230 | 230 | ✅ |
| Perfil do gasto | Obras 60,8% / Serviços 36,6% / Bens 2,6% | idem | ✅ |

**Regras implementadas (referência: Seção 4.2 do enunciado):**

| Regra | Implementação |
| :--- | :--- |
| 1. Grão da fato | `numero_controle_pncp` + `numero_item` (garantido na Etapa 9 pelo `drop_duplicates`) |
| 2. Um vencedor por item | Filtrar cancelados → ordenar por `ordem` e `sequencial` → `drop_duplicates` mantém o 1º |
| 3. Só itens com resultado | `merge(how="inner")` — 6.225 itens com resultado (852 sem resultado ficaram fora) |
| 4. Itens rejeitados | 99 rejeitados (quantidade ≤ 0, estimado/homologado ≤ 0, sigiloso, valor < R$ 1, hom > 1000× est, > R$ 1 tri) |
| 5. Valores | `valor_total = valor_unitario × quantidade` (usando quantidade homologada quando > 0) |
| 6. Comparável e economia | `modalidade_id != 12` E `razão entre 0,1 e 10` → 5.457 comparáveis; economia só onde comparável |
| 7. Cronologia | Homologação anterior à publicação → `data_homologacao = None` (230 itens sem ciclo) |
| 8. Perfil do gasto | Regex `\b(OBRAS?|CONSTRUÇÃO|REFORMA|ENGENHARIA)\b` sobre `descricao + objeto_compra`; prioridade para Obras |
| 9. Modalidade | Padronização via dicionário `MODALIDADES[id]` |
| 10. Órgão | `limpar_documento(v, "PJ")` + `padronizar_nome` (363 unidades compradoras) |
| 11. Região | `uf_sigla → REGIAO` (dicionário do Anexo 7.6) |
| 12. Separadores numéricos | `converter_numero()` (Sprint 2) — regra do "último símbolo = decimal" |

**Itens rejeitados — critérios da regra 4:**

Foram rejeitados **99 itens** pelos 7 critérios da regra 4 do enunciado. Cada item foi classificado pelo **primeiro critério que disparou** a rejeição (se um item viola mais de um, conta apenas o primeiro):

| # | Critério de rejeição |
| :---: | :--- |
| 1 | Quantidade vazia ou ≤ 0 |
| 2 | Valor unitário estimado ausente ou ≤ 0 |
| 3 | Valor unitário homologado ausente ou ≤ 0 |
| 4 | Orçamento sigiloso (`sigiloso = True`) |
| 5 | Valor total estimado menor que R$ 1 |
| 6 | Valor total homologado mais de 1.000× o valor total estimado |
| 7 | Valor total (estimado ou homologado) acima de R$ 1 trilhão — limite definido para não estourar o tipo `DECIMAL(18,2)` do PostgreSQL na Sprint 4 |

Os itens rejeitados **não são carregados na tabela Fato** — a verificação é feita pelo total (99, conforme Anexo 8); são apenas contabilizados.

**Aprendizado:** a Prova Real foi batida na **primeira execução** após corrigir 1 erro de sintaxe (duplicação no `dias_ciclo`). A estratégia de implementar as 12 regras em ordem de dependência (limpeza → vencedor → merge → valores → rejeição → comparabilidade → cronologia → perfil → dimensões) evitou retrabalho.

[⬆ Voltar ao índice](#-índice)

---

<a id="5-modelagem"></a>
## 5. Modelagem Dimensional (Star Schema)

A camada analítica segue o modelo **Star Schema** (1 tabela Fato + 4 Dimensões), implementado no PostgreSQL pela Sprint 4.

### 5.1. Diagrama

![Diagrama do Star Schema](docs/img/diagrama.png)

### 5.2. Estrutura

| Tabela | Papel | Linhas | Chave natural (UNIQUE) | Chave substituta (PK) |
| :--- | :--- | ---: | :--- | :--- |
| `fato_item_contratado` | **FATO** — o que foi comprado | 6.126 | `numero_controle_pncp` + `numero_item` | `sk_fato` (SERIAL) |
| `dim_orgao` | Quem comprou | 363 | `cnpj_orgao` | `sk_orgao` |
| `dim_fornecedor` | Quem vendeu | 2.652 | `ni_fornecedor` | `sk_fornecedor` |
| `dim_modalidade` | Como comprou | 7 | `modalidade_id` | `sk_modalidade` |
| `dim_localidade` | Onde | 27 | `uf_sigla` | `sk_localidade` |

### 5.3. Decisões de modelagem

- **Surrogate keys (`sk_*`):** chaves substitutas inteiras, geradas em ordem crescente no `montar_tabelas.py`. Isolam a Fato das chaves naturais (CNPJ, sigla de UF), que podem mudar de formato;
- **Fato no grão do item:** 1 linha por `numero_controle_pncp` + `numero_item` (constraint `UNIQUE` composta);
- **Integridade referencial:** 4 FKs da Fato apontam para as 4 Dimensões, todas `NOT NULL`. A Prova Real confirmou que **não há FK órfã** — a linha `-1` ("Não informado") **não foi necessária**;
- **Tipos de dados:**
  - `DECIMAL(18,2)` para valores monetários totais
  - `DECIMAL(18,4)` para preços unitários e quantidades
  - `DATE` para datas
  - `SMALLINT` para a flag `comparavel` (0 ou 1)
- **CHECKs de integridade:** `quantidade > 0`; todos os valores `>= 0`; `comparavel IN (0, 1)`.
- **Campos vazios:** `data_homologacao`, `economia_valor` e `dias_ciclo` são `NULL` quando a regra de negócio anula o dado (230 itens sem ciclo, itens não comparáveis);
- **Tempo no Power BI:** a dimensão Calendário **não é tabela do banco** — é criada em DAX no Power BI (Sprint 6), relacionada a `data_publicacao` e `data_homologacao` via `USERELATIONSHIP`.

[⬆ Voltar ao índice](#-índice)

---

<a id="6-perguntas"></a>
## 6. Perguntas de Negócio e Respostas

As respostas abaixo foram extraídas com as queries de `sql/02_perguntas.sql` e validadas contra a Prova Real (Anexo 8 do enunciado).

### 6.1. Resumo

| # | Pergunta | Resposta | Query |
| :---: | :--- | :--- | :--- |
| 1 | Economia global | **14,46%** / **R$ 992,86 mi** | `P1` |
| 2 | Concentração de fornecedores | Top 10 = **41,43%** do orçamento | `P2a`, `P2b` |
| 3 | Eficácia por modalidade | Pregão Eletrônico: **24,02%** de deságio | `P3` |
| 4 | Ciclo de compras | Média **48,1 dias**, máximo **611** | `P4` |
| 5 | Distribuição regional | CO concentra **44,25%**; Norte tem **21,43%** de deságio | `P5a`, `P5b` |
| 6 | Perfil do gasto | Obras = **60,82%** do volume | `P6` |

### 6.2. P1 — Economia global do Poder Público

> *"Qual é o percentual e o valor financeiro nominal economizado pelo governo (diferença entre valor estimado e valor homologado)?"*

- **Valor estimado comparável:** R$ 6.867.663.469,91
- **Economia nominal:** **R$ 992.861.686,95**
- **Economia %:** **14,46%**

**Interpretação:** para cada R$ 100 estimados em itens comparáveis, o governo pagou R$ 85,54 — economia de **R$ 14,46 por R$ 100**. Dos R$ 8,04 bi de volume homologado, quase **R$ 1 bilhão** foi economizado.

### 6.3. P2 — Concentração e risco de fornecedores

> *"Quem são os maiores fornecedores em volume financeiro e qual percentual do orçamento público está concentrado neles?"*

**Top 5 fornecedores:**

| Fornecedor | Volume (R$) | % do total |
| :--- | ---: | ---: |
| NOW SEGUROS SA | 1.060.000.000,00 | 13,18% |
| CONSTRUTORA CIDADE LTDA | 524.935.394,97 | 6,53% |
| BANCO BRADESCO S.A. | 379.194.320,07 | 4,71% |
| CONSTRUTORA NORTE BRASIL LTDA | 335.401.470,80 | 4,17% |
| LCM CONSTRUÇÃO E COMÉRCIO S.A. | 228.885.493,53 | 2,85% |

- **Top 10 concentram 41,43%** do orçamento (R$ 3.332.484.029,86 de R$ 8,04 bi).
- **2.642 fornecedores menores** dividem os 58,57% restantes.

**Interpretação:** a concentração em 10 fornecedores (41% do gasto) é um **sinal de risco** para a Controladoria — dependência de poucos vendedores pode reduzir a competitividade futura. **7 dos 10 maiores são construtoras**, consistente com o perfil do gasto (P6).

### 6.4. P3 — Eficácia por modalidade

> *"Quais modalidades licitatórias trazem maior deságio/economia e quais concentram o maior volume de recursos?"*

| Modalidade | Volume (R$) | Deságio |
| :--- | ---: | ---: |
| Concorrência Eletrônica | 4.700.493.122,98 | 14,27% |
| Credenciamento | 2.141.301.557,16 | **NULL** *(esperado)* |
| Pregão Eletrônico | 502.223.491,28 | **24,02%** ⭐ |
| Concorrência Presencial | 444.752.757,18 | 6,79% |
| Inexigibilidade | 213.365.238,19 | 8,77% |
| Dispensa | 39.887.350,44 | 4,49% |
| Pregão Presencial | 2.475.288,51 | 0,02% |

**Interpretação:** há uma **inversão entre volume e deságio**. Pregão Eletrônico tem o **maior deságio (24,02%)**, mas absorve apenas 6% do volume. As modalidades de maior volume — Concorrência Eletrônica (58%) e Credenciamento (27%) — têm deságio **menor** (14,27%) ou **estruturalmente incalculável** (Credenciamento). **A Controladoria tem espaço para ampliar a competitividade onde o dinheiro está.**

### 6.5. P4 — Tempo do ciclo de compras

> *"Qual a duração média (em dias) entre o lançamento do edital e a sua homologação final, segmentada por órgão?"*

- **Ciclo médio geral:** **48,1 dias**
- **Ciclo máximo:** **611 dias** (COMANDO DO EXÉRCITO)
- **Órgão mais lento (com ≥ 5 itens):** UFCG — 266,3 dias
- **Itens sem ciclo:** 230 (homologação anterior à publicação — regra 7)

**Extremos:**

| Órgão | Itens com ciclo | Ciclo médio |
| :--- | ---: | ---: |
| UNIVERSIDADE FEDERAL DE CAMPINA GRANDE | 16 | **266,3 dias** |
| DNIT | 62 | 156,2 dias |
| COMANDO DO EXÉRCITO | 1.200 | 34,3 dias |
| COMANDO DA MARINHA | 453 | 35,3 dias |

**Interpretação:** há uma **desigualdade operacional de ~600× entre órgãos**. Os **3 Comandos Militares** (Exército, Marinha, Aeronáutica) são os maiores compradores (33% dos itens) e operam **abaixo da média** (34-56 dias). O **DNIT** (obras) é 4× mais lento que a média — e obras representam 60,82% do gasto (P6). **A lentidão em obras é o gargalo estrutural.**

### 6.6. P5 — Distribuição regional

> *"Quais estados e regiões concentram as maiores despesas e quais apresentam os melhores indicadores de desconto?"*

**Top 5 UFs por volume:**

| UF | Região | Volume (R$) | Deságio |
| :--- | :--- | ---: | ---: |
| DF | Centro-Oeste | 3.135.638.456,35 | 15,90% |
| RS | Sul | 820.584.056,64 | 7,18% |
| RJ | Sudeste | 461.925.602,27 | 11,57% |
| PI | Nordeste | 408.389.525,89 | **5,98%** ⚠️ |
| SP | Sudeste | 393.783.392,48 | 9,22% |

**Agregação por região:**

| Região | Volume (R$) | % | Deságio |
| :--- | ---: | ---: | ---: |
| **Centro-Oeste** | 3.559.879.991,73 | **44,25%** | 17,02% |
| Nordeste | 1.850.420.285,02 | 23,00% | 14,18% |
| Sudeste | 1.083.309.811,49 | 13,47% | 11,62% |
| **Sul** | 1.021.624.955,41 | 12,70% | **7,96%** ⚠️ |
| **Norte** | 529.263.762,09 | 6,58% | **21,43%** ⭐ |

**Interpretação:** há **inversão geográfica** entre volume e deságio. **Centro-Oeste concentra 44,25% do orçamento** (DF = sede dos órgãos federais) mas tem deságio médio. **Norte tem o maior deságio (21,43%)** com o menor volume — sinal de **mais competição local** ou **menor concentração de fornecedores**. **Sul é o caso mais crítico**: R$ 1,02 bi com deságio de apenas 7,96% (metade da média nacional).

**Custo de oportunidade:** se o Sul tivesse o deságio médio nacional (14,46%), economizaria ~**R$ 66 milhões adicionais**.

### 6.7. P6 — Perfil dos gastos

> *"Como os recursos se distribuem entre bens, serviços e obras e engenharia?"*

| Perfil | Itens | Volume (R$) | % Itens | % Volume |
| :--- | ---: | ---: | ---: | ---: |
| **Obras e engenharia** | 967 | 4.892.362.732,70 | 15,8% | **60,82%** |
| **Serviços** | 1.849 | 2.940.950.885,18 | 30,2% | 36,56% |
| **Bens** | 3.310 | 211.185.187,86 | 54,0% | **2,63%** |

**Interpretação:** **967 itens de obras consomem quase 2/3 do orçamento**, enquanto 3.310 itens de bens (o dobro em quantidade) consomem apenas 2,63%. **Obras são o gargalo financeiro** — e combinam com P3 (Concorrência Eletrônica, modalidade de obras, lidera o volume) e P4 (DNIT, órgão de obras, é 4× mais lento). **A auditoria da Controladoria deve priorizar obras: é onde o dinheiro está, onde o ciclo é maior e onde o deságio é menor.**

[⬆ Voltar ao índice](#-índice)

---

<a id="7-sprints"></a>
## 7. Planejamento em Sprints e Lições Aprendidas

O projeto foi executado em **5 Fases (Marcos)** e **8 Micro-Sprints**, adaptando o framework Scrum a um prazo de 9 dias úteis (20/10 a 30/10/2026), sem codificação em fins de semana. Cada Sprint tem um **MVP** e um **Critério de Aceite** explícitos, registrados no Trello.

![Sprints do projeto](docs/img/sprints.png)

<a id="71-historico"></a>
### 7.1. Histórico de Sprints

#### Fase 1 — Fundação e Auditoria (Sprints 0 e 1)

Realizados preparação da infraestrutura do projeto e diagnóstico de anomalias nos CSVs brutos.

**Entregas:**

- **Sprint 0:** repositório estruturado, `.gitignore` protegendo `.env`, README esqueleto, primeiro commit na branch `feat/fase-1-fundacao`.
- **Sprint 1:** `src/auditoria.py` com 9 funções cobrindo as 4 perguntas da Seção 7.4 do enunciado; Seção 3 do README preenchida com o dicionário de inconsistências.

**Desafios e adaptações:**

- **Falso positivo no encoding:** a primeira versão do script usava `"Ã"` isolado como padrão de detecção, gerando ~300 falsos positivos em palavras legítimas ("SÃO", "AÇÃO", "MUNICÍPIO"). Corrigido removendo o padrão isolado e mantendo só combinações de dupla codificação (`Ã§`, `Ã£`, `Ã©`...).
- **Parser de data incompleto:** `pd.to_datetime(dayfirst=True)` só reconhecia 1,9% dos resultados (310 de 15.896). Implementada `parse_data_robusto()` com 16 variações de formato, elevando a cobertura para **100%** e revelando **1.056 datas invertidas** (contra 142 no parser ingênuo — número anterior era enviesado).
- **Classificação monetária subestimada:** os regex estritos (`\d,\d{2}$`) só casavam valores curtos. Refinado com `.*` no prefixo e `\d+` no final, alcançando **classificação 100% completa** (vírgula + ponto = total em todas as 6 colunas).

**Aprendizado:** *bugs* de diagnóstico são **mais perigosos que *bugs* de produção** — eles enviesam as decisões seguintes. A regra "vírgula + ponto = total" foi adotada como critério de validação.

---

#### Fase 2 — Engenharia de Dados (Sprints 2 e 3) — concluída

##### Sprint 2 — Limpeza e Sanitização

**O que foi planejado:** completar `src/limpeza.py` (kit do professor) com funções de limpeza de texto, documentos, números e datas.

**O que foi entregue:**

- `src/limpeza.py` 100% preenchido (19 lacunas resolvidas).
- Autoteste: **54/54 exemplos certos** na primeira execução.

**Desafios e adaptações:**

- **Ambiguidade do `"0"`:** o número pode ser nulo (em campo de texto) ou valor legítimo (em campo numérico). Solução: parâmetro `zero_eh_nulo` controla o comportamento por contexto. Documentado na Seção 4.1.2.
- **Encoding resiliente:** a função `consertar_acento()` usa `try/except` — funciona tanto em textos corrompidos (`AquisiÃ§Ã£o` → `Aquisição`) quanto em textos já corretos (`Aquisição` permanece igual).
- **Datas em 6 formatos + corte de hora:** `converter_data()` testa os 6 formatos-base do arquivo do professor e usa `[:10]` para descartar a hora — decisão alinhada com o tipo `DATE` do PostgreSQL.

**Aprendizado:** a estratégia de "uma função por vez, testada antes de avançar" (conforme sugerido pelo próprio kit) evitou retrabalho. Todos os 54 testes passaram na **primeira execução** — sinal de que as 19 lacunas foram preenchidas com o conceito entendido, não por tentativa.

---

##### Sprint 3 — Modelagem e Regras de Negócio

**O que foi planejado:** implementar as 12 regras de negócio em `src/montar_tabelas.py` e bater todos os números da Prova Real (Anexo 8).

**O que foi entregue:**

- `src/montar_tabelas.py` 100% implementado (31 lacunas resolvidas).
- **Prova Real batida em todos os 10 números** do Anexo 8, na **primeira execução**.

**Desafios e adaptações:**

- **`config.py` e o `ImportError` inicial:** ao rodar `python src/montar_tabelas.py` (execução direta), o Python adiciona `src/` ao `sys.path[0]` — e `from src import config` falha com `ModuleNotFoundError: No module named 'src'`. O erro **não era ausência do arquivo**: o `config.py` oficial do kit (com `PASTA_RAIZ`, `PASTA_SQL`, `carregar_env()` e `PG_CONFIG`) já estava em `src/` desde o commit `c54a9fb`. A solução foi usar o **modo módulo** (`python -m src.montar_tabelas`), que adiciona a raiz do projeto ao `sys.path` e encontra o pacote `src` corretamente. Decisão registrada na docstring do próprio arquivo, que instrui: *"COMO RODAR: python -m src.montar_tabelas"*.
- **Erro de sintaxe no `dias_ciclo`:** a expressão `(h - p).days if ... else None` foi digitada com duplicação inicial (`(h - p).(h - p).days`), causando `SyntaxError`. Corrigido em 1 linha — o erro só apareceu na execução, não no editor, porque envolvia encadeamento de `if/else` em list comprehension.
- **99 itens rejeitados — critérios da regra 4:** a Prova Real confirma **exatamente 99 itens** descartados antes da carga na Fato. Os 7 critérios (cada item conta apenas o **primeiro** que dispara) estão detalhados na **Seção 4.2.5** e cobrem: quantidade ≤ 0; valor unitário estimado ≤ 0; valor unitário homologado ≤ 0; orçamento sigiloso; valor total estimado < R$ 1; valor total homologado > 1.000× o estimado; ou qualquer valor total > R$ 1 trilhão (limite para não estourar o tipo `DECIMAL(18,2)` do PostgreSQL).
- **Sprint 3 atravessou o fim de semana** (23/10 sexta → 26/10 segunda), exigindo divisão interna: regras 1-5 na sexta, regras 6-12 na segunda.

**Aprendizado:** a estratégia de implementar as 12 regras **em ordem de dependência** (limpeza → vencedor → merge → valores → rejeição → comparabilidade → cronologia → perfil → dimensões) permitiu **bater a Prova Real na primeira execução**. Se as regras fossem implementadas fora de ordem, um erro em uma etapa inicial contaminaria todas as etapas seguintes — e o diagnóstico seria muito mais trabalhoso.

---

#### Fase 3 — Banco de Dados (Sprints 4 e 5) — concluída

##### Sprint 4 — Banco de Dados e Carga

**O que foi planejado:** escrever o `sql/01_criar_banco.sql` (Star Schema: 1 Fato + 4 Dimensões), completar as 6 lacunas do `src/carregar.py` e validar as 5 contagens contra a Prova Real.

**O que foi entregue:**

- `sql/01_criar_banco.sql` criado do zero — 5 tabelas com PKs, FKs, UNIQUEs e CHECKs.
- `src/carregar.py` com as 6 lacunas preenchidas (`inserir_em_lote`, `executar_script`, `"Int64"`, `fato_item_contratado`, `COUNT(*)`).
- **Carregamento validado:** as 5 contagens batem exatamente com o Anexo 8.

| Tabela | Carregado | Prova Real |
| :--- | ---: | ---: |
| `fato_item_contratado` | 6.126 | 6.126 |
| `dim_orgao` | 363 | 363 |
| `dim_fornecedor` | 2.652 | 2.652 |
| `dim_modalidade` | 7 | 7 |
| `dim_localidade` | 27 | 27 |

**Desafios e adaptações:**

- **`pg_isready` não está no PATH do Windows:** a validação inicial do PostgreSQL foi feita com `Test-NetConnection -Port 5432` (porta aberta) + um teste de conexão real via Python (`psycopg2.connect` + `config.PG_CONFIG`). O `pg_isready` só está disponível se os binários do PostgreSQL estiverem no PATH — o que não é o padrão no Windows.
- **`ImportError` no botão ▶️ do VS Code:** a execução direta (`python src/carregar.py`) falha com `ModuleNotFoundError: No module named 'src'` porque o Python adiciona `src/` ao `sys.path[0]`. A execução via **modo módulo** (`python -m src.carregar`) funciona corretamente. Decisão registrada na docstring do arquivo do kit: *"COMO RODAR: python -m src.carregar"*.
- **Linha `-1` ("Não informado") não foi necessária:** a Seção 4.3 do enunciado indica criar a linha `-1` nas dimensões **se** houver FK órfã. A Prova Real confirmou zero FKs órfãs (as 5 contagens batem com o Anexo 8). Por isso, incluí-la faria as contagens divergirem (364, 2.653, 8, 28) — o script `01_criar_banco.sql` documenta isso com um comentário e fornece o template de INSERT caso um dia seja necessário.
- **Tratamento de exceções via `banco.py`:** o `banco.py` do kit já implementa controle de falhas — a função `inserir_em_lote()` chama `conexao.commit()` apenas no final de cada operação, garantindo rollback implícito em caso de violação de constraint. A `carregar.py` apenas orquestra — não reimplementamos `try/except` para não duplicar o que o kit já cobre.
- **Diagrama do Star Schema em Mermaid:** gerado em [mermaid.live](https://mermaid.live), exportado como PNG para `docs/img/diagrama.png`. O código-fonte Mermaid está versionado no README (Seção 5), permitindo regeneração futura — abordagem "Diagrams-as-Code".

**Aprendizado:** validar a conexão real via Python (`psycopg2.connect`) antes de escrever o DDL evita retrabalho. O `Test-NetConnection` só confirma que a porta está aberta — não confirma credenciais nem que o banco existe. Validar com a mesma stack que o pipeline vai usar (psycopg2 + config.py) elimina surpresas.

---

---

##### Sprint 5 — Perguntas de Negócio (SQL)

**O que foi planejado:** escrever as 6 queries em `sql/02_perguntas.sql` que respondem às dores da Controladoria (Seção 4.4 do enunciado), validando cada uma contra a Prova Real (Anexo 8).

**O que foi entregue:**

- `sql/02_perguntas.sql` com **8 queries** (P1, P2a/P2b, P3, P4, P5a/P5b, P6).
- **Todas as 6 perguntas validadas** contra o Anexo 8 do enunciado.

| # | Pergunta | Resultado | Prova Real |
| :---: | :--- | :--- | :--- |
| **P1** | Economia global | **14,46%** / **R$ 992.861.686,95** | 14,46% / R$ 992.861.686,95 |
| **P1** | Estimado comparável | **R$ 6.867.663.469,91** | R$ 6.867.663.469,91 |
| **P2a** | Top 10 fornecedores | 10 linhas, #1 com 13,18% | *(coerência)* |
| **P2b** | Concentração Top 10 | **41,43%** (R$ 3.332.484.029,86) | *(coerência)* |
| **P3** | Deságio por modalidade | Credenciamento = **NULL** | NULL *(esperado)* |
| **P4** | Ciclo máximo por órgão | **611 dias** (COMANDO DO EXÉRCITO) | 611 dias |
| **P5a** | Distribuição por UF | 27 UFs, soma = R$ 8,04 bi | R$ 8,04 bi |
| **P5b** | Distribuição por região | 5 regiões, soma = R$ 8,04 bi | R$ 8,04 bi |
| **P6** | Perfil do gasto | **60,82% Obras / 36,56% Serviços / 2,63% Bens** | 60,8 / 36,6 / 2,6 |

**Decisões técnicas aplicadas (Seção 4.4 do enunciado):**

- **Percentual = SOMA ÷ SOMA** em todas as queries (nunca média de percentuais) — usando `NULLIF(denominador, 0)` para evitar divisão por zero.
- **Economia só nos comparáveis:** `CASE WHEN comparavel = 1` + `SUM` (nunca `AVG` de percentuais).
- **Credenciamento (modalidade 12):** `desagio_pct` retorna **NULL** porque não tem item comparável — comportamento esperado, conforme o enunciado.
- **P2 (fornecedores):** `LIMIT 10` no ranking + subconsulta no denominador para o percentual do total.
- **P4 (ciclo):** `GROUP BY o.nome_orgao` (agrupando pelo nome padronizado, não pelo CNPJ) + `COUNT(dias_ciclo)` (só itens com ciclo) + `HAVING COUNT >= 5`.
- **P6 (perfil):** `GROUP BY perfil_gasto` direto na Fato — sem JOIN, conforme dica do enunciado.

**Desafios e adaptações:**

- **`current_database()` no pgAdmin:** a primeira execução falhou com `relation "fato_item_contratado" does not exist` porque o Query Tool estava conectado no banco administrativo `postgres`, não em `pncp_controladoria`. Solução: abrir o Query Tool a partir do banco correto (botão direito em `pncp_controladoria` → Query Tool). **O código SQL estava correto desde o início** — o erro era de conexão, não de sintaxe.
- **Divisão por zero no Credenciamento:** sem `NULLIF`, a query de P3 lançaria `division by zero` porque o denominador (estimado comparável) é 0. O `NULLIF(..., 0)` devolve NULL — exatamente o comportamento esperado (o enunciado avisa: *"em Credenciamento nenhum item é comparável, então a economia % dessa modalidade fica vazia"*).
- **Encoding quebrado na exibição do pgAdmin:** a query P3 mostrou `ConcorrÃªncia` e `PregÃ£o` no output do Query Tool — mas o dado no banco está correto (`Concorrência`, `Pregão`). É configuração do cliente SQL, não do dado. Solução para o vídeo: rodar `SET client_encoding = 'UTF8';` antes da query, ou mostrar direto no Power BI (que respeita UTF-8).
- **Validação incremental:** cada query foi validada **individualmente** no pgAdmin (selecionando o bloco e `F5`), em vez de rodar o arquivo inteiro. Isso permitiu identificar rapidamente que o problema inicial era de conexão no banco errado — não de lógica SQL. Rodar tudo de uma vez devolveria só o último resultado e mascararia a causa real.

**Achados analíticos (para o vídeo e para a Controladoria):**

- **P3 + P6 combinadas:** Pregão Eletrônico tem o **maior deságio (24,02%)**, mas absorve apenas 6% do volume. Concorrência Eletrônica concentra **58% do volume** (obras), com deságio de 14,27%. **Há espaço para ampliar a competitividade onde o dinheiro está.**
- **P4:** os **3 Comandos Militares** (Exército, Marinha, Aeronáutica) concentram 33% dos itens e operam **abaixo da média** (34-56 dias) — são os maiores compradores e os mais eficientes. O **DNIT** (obras) é 4× mais lento que a média.
- **P5b:** o **Sul** tem R$ 1,02 bi de volume com deságio de apenas **7,96%** (metade da média nacional de 14,46%). O **Norte** tem o **maior deságio (21,43%)** com o menor volume. Há uma **inversão geográfica** entre volume e deságio.
- **P6:** **967 itens de obras** consomem quase **2/3 do orçamento**, enquanto **3.310 itens de bens** (o dobro em quantidade) consomem **2,63%**.

**Aprendizado:** a validação incremental (uma query por vez) foi decisiva. O primeiro erro (`relation does not exist`) parecia grave — mas era simplesmente o Query Tool conectado no banco errado. Se eu tivesse rodado todas as queries de uma vez, o output seria apenas o último resultado, e a causa real demoraria a ser identificada. **Validar uma pergunta por vez, comparar com a Prova Real antes de avançar** — mesma lógica da Sprint 2 ("uma função por vez") e da Sprint 4 ("validar a conexão antes do DDL").

##### Sprint 6 — Dashboard Power BI

**O que foi planejado:** construir o dashboard executivo com as 6 páginas (storytelling), tabela Calendário, 15 medidas DAX, menu de navegação e tooltips.

**O que foi entregue:**
- `powerbi/dashboard.pbix` com as 6 páginas finalizadas.
- Tabela Calendário dinâmica em DAX (`CALENDARAUTO`), ordenação correta e `USERELATIONSHIP`.
- 16 medidas DAX na tabela `_Medidas`, organizadas por pastas (0. Base, 1. Economia, etc.).
- Menu lateral retrátil funcional (utilizando Marcadores/Bookmarks e botões de ação).
- Tooltip personalizado na página de Fornecedores.
- Aplicação dos princípios CRAP e Design System (Dark Tech).
- Extras implementados: Itens com Sobrepreço, Volume Acumulado no Ano e Variação Mensal %.

**Desafios e adaptações:**
- **Bug do Menu Retrátil (Desktop):** A versão mais recente do Power BI Desktop (Setembro/2026) apresentou um bug de renderização que impedia o funcionamento dos Marcadores (Bookmarks). A solução foi fazer o downgrade para a versão de Julho/2026 (2.156.951.0), que restaurou a funcionalidade.
- **Segurança:** As permissões de credenciais foram limpas antes do commit do arquivo `.pbix`.

**Aprendizado:** A construção do design system (CRAP) foi fundamental para dar coesão às 6 páginas. O domínio de recursos avançados, como Marcadores e Tooltips, elevou a experiência do usuário (UX) do relatório.

[⬆ Voltar ao índice](#-índice)

---

<a id="8-execucao"></a>
## 8. Guia de Execução (Como reproduzir)

> **Nota sobre `data/processed/`:** os arquivos gerados por `src/montar_tabelas.py` (fato + 4 dimensões em CSV) **não são versionados** — estão no `.gitignore`. Eles são regeneráveis a partir do código + `data/raw/`, conforme orientação do professor. Quem clonar o repositório reproduz os arquivos rodando o pipeline.

*[Passo a passo completo: instalar `requirements.txt`, configurar `.env`, rodar scripts na ordem correta — a preencher nas Sprints 4 e 5]*

[⬆ Voltar ao índice](#-índice)

---

<a id="9-melhorias"></a>
## 9. Melhorias Futuras e Vídeo de Defesa

*[A preencher na Fase 5 — link do vídeo no Google Drive]*

[⬆ Voltar ao índice](#-índice)