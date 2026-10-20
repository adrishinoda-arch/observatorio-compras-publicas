# Projeto: Auditoria e Inteligência em Compras Públicas (PNCP)

Esteira analítica ponta a ponta (End-to-End) para auditoria e inteligência de dados em compras públicas federais. Transforma dados brutos e corrompidos do PNCP em um ambiente analítico confiável, auditável e executivo para a Controladoria, utilizando **Python**, **PostgreSQL** e **Power BI**.

## 1. Contexto e Problema de Negócio
*[A preencher na Fase 1]*

## 2. Arquitetura da Solução e Tecnologias
*[A preencher na Fase 1]*
*(Python, PostgreSQL, Power BI, Git)*

## 3. Auditoria Inicial e Dicionário de Inconsistências

O script `src/auditoria.py` faz um raio-x **somente diagnóstico** (não altera os dados): carrega os 3 CSVs como texto (`dtype=str`) para preservar zeros à esquerda e evitar inferência equivocada de tipos. As subseções abaixo respondem, uma a uma, às 4 perguntas da Seção 7.4 do enunciado.

---

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

## 4. Decisões Técnicas e Regras de Negócio
*[A preencher na Fase 2 e 3]*
*Como tratamos os nulos, a regra do vencedor, os itens rejeitados (e seus motivos).*

## 5. Modelagem Dimensional (Star Schema)
*[A preencher na Fase 3]*
*Explicação do modelo e link para a imagem do diagrama (docs/img/diagrama.png).*

## 6. Planejamento em Sprints e Lições Aprendidas
*[A preencher em todas as fases]*
*![Sprints do projeto](docs/img/sprints.png)*
*Registro histórico do que foi entregue e desafios superados em cada fase.*

## 7. Guia de Execução (Como reproduzir)
*[A preencher na Fase 3 e finalizar na Fase 5]*
*Passo a passo: instalar requirements, configurar .env, rodar scripts na ordem correta.*

## 8. Melhorias Futuras e Vídeo de Defesa
*[A preencher na Fase 5]*
*Link do vídeo no Google Drive.*