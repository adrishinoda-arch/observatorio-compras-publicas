# Projeto PNCP - Controladoria

## 1. Contexto e Problema de Negócio
*[A preencher na Fase 1]*

## 2. Arquitetura da Solução e Tecnologias
*[A preencher na Fase 1]*
*(Python, PostgreSQL, Power BI, Git)*

## 3. Auditoria Inicial e Dicionário de Inconsistências

O script `src/auditoria.py` faz um raio-x **somente diagnóstico** (não altera os dados): carrega os 3 CSVs como texto (`dtype=str`) para preservar zeros à esquerda e evitar inferência equivocada de tipos, e responde às 4 perguntas da Seção 7.4 do enunciado.

### 3.1. Volumetria e integridade da chave

| Arquivo | Linhas | Colunas |
| :--- | ---: | ---: |
| `compras.csv` | 2.042 | 25 |
| `itens.csv` | 7.077 | 14 |
| `resultados.csv` | 15.896 | 13 |

**Chave de ligação:** `numero_controle_pncp` + `numero_item`.

- **`numero_controle_pncp` em `compras.csv`:** 2.042 linhas, 2.042 valores distintos → **zero duplicatas**. O grão "1 linha por contratação" está preservado, conforme esperado.

### 3.2. Nulos disfarçados, zeros, vazios e formatos

#### 3.2.1. Nulos disfarçados (`N/A`, `NULL`, `-`, `SEM INFORMAÇÃO`, `NÃO SE APLICA`)

| Arquivo | Coluna | Ocorrências | Observação |
| :--- | :--- | ---: | :--- |
| `compras.csv` | `processo` | 32 | campo opcional |
| `compras.csv` | `modo_disputa` | 925 | **45% da base** — tratar com cuidado |
| `itens.csv` | `categoria_item` | 7.077 | **100%** — coluna inútil, como o enunciado avisa |
| `itens.csv` | `situacao_item` | 79 | campo opcional |
| `itens.csv` | `criterio_julgamento` | 1.883 | 26,6% |
| `resultados.csv` | `porte` | 172 | campo opcional |

> **Decisão de projeto:** `"0"` **não** foi classificado como nulo em nenhuma coluna nesta etapa. O enunciado alerta que `"0"` só é nulo em **campos de texto**; em quantidades e valores é número. A separação por tipo acontece na Sprint 2.

#### 3.2.2. Zeros e vazios

| Arquivo | Coluna | `"0"` | Vazios (`""`) | NaN real | Observação |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `compras.csv` | `processo` | 12 | 0 | 28 | — |
| `compras.csv` | `modo_disputa` | 7 | 0 | 26 | — |
| `compras.csv` | `data_abertura_proposta` | 0 | 0 | 617 | 30% sem data |
| `compras.csv` | `data_encerramento_proposta` | 0 | 0 | 617 | 30% sem data |
| `itens.csv` | `unidade_medida` | 0 | 0 | 9 | — |
| `itens.csv` | `situacao_item` | 25 | 0 | 92 | — |
| `itens.csv` | `catalogo_codigo_item` | 0 | 0 | 7.068 | **99,9% vazio** — coluna descartável |
| `resultados.csv` | `ordem_classificacao_srp` | 0 | 0 | 11.976 | **75% vazio** — esperado em Credenciamento |
| `resultados.csv` | `porte` | 57 | 0 | 196 | — |
| `resultados.csv` | `data_cancelamento` | 0 | 0 | 15.834 | **só 62 cancelados** (0,4%) — base limpa nesse quesito |

> **Impacto na Sprint 2:** `catalogo_codigo_item` será descartado; `ordem_classificacao_srp` precisará de tratamento específico (o desempate por `sequencial_resultado` será essencial); `data_cancelamento` precisa ser lida como **booleana** (preenchido = cancelado), não como data.

#### 3.2.3. Formatos monetários

A base mistura **prefixo `R$`**, **vírgula decimal** e **ponto decimal** na **mesma coluna**. Isso confirma a regra do enunciado: *"ponto ou vírgula sozinho é sempre decimal; só o separador repetido (1.234.567) é milhar; quando aparecem os dois símbolos, o último é o decimal"*.

| Arquivo | Coluna | Com `R$` | Vírgula decimal | Ponto decimal |
| :--- | :--- | ---: | ---: | ---: |
| `compras.csv` | `valor_total_estimado` | 344 | 3 | 22 |
| `compras.csv` | `valor_total_homologado` | 346 | 3 | 19 |
| `itens.csv` | `valor_unitario_estimado` | 1.188 | 52 | 648 |
| `itens.csv` | `valor_total_estimado` | 1.171 | 5 | 20 |
| `resultados.csv` | `valor_unitario_homologado` | 2.650 | 112 | 1.007 |
| `resultados.csv` | `valor_total_homologado` | 2.647 | 17 | 92 |

**Exemplos reais que coexistem na base (mesma coluna):**
- `"20307804.45"` (ponto decimal, sem prefixo)
- `"R$ 419.848,81"` (ponto milhar + vírgula decimal + prefixo)
- `"250,782.10"` (vírgula milhar + ponto decimal — o **inverso** do padrão brasileiro)
- `"19.290.383,46"` (formato brasileiro completo)

> **Nenhum** valor monetário apareceu como "só dígitos" — **todos têm parte decimal**. Isso simplifica a conversão: basta tratar a posição do decimal.

#### 3.2.4. Formatos de data

| Arquivo | Coluna | `dd/mm/aaaa` | `dd/mm/aaaa hh:mm` | ISO (`aaaa-mm-ddThh:mm`) | `dd-mm-aaaa` | Outros |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| `compras.csv` | `data_publicacao` | 117 | 126 | 1.319 | 138 | 342 |
| `compras.csv` | `data_abertura_proposta` | 78 | 86 | 912 | 85 | 264 |
| `compras.csv` | `data_encerramento_proposta` | 78 | 101 | 926 | 75 | 245 |
| `resultados.csv` | `data_resultado` | 929 | 934 | 10.301 | 912 | 2.820 |

**Formatos em "Outros" (identificados por amostragem):** `dd.mm.aaaa` (`02.01.2025`), `aaaammdd` (`20250103`), `aaaa/mm/dd` (`2025/01/02`).

> **Consequência:** a conversão de datas na Sprint 2 exigirá **parser multi-formato** com fallback ordenado — `pd.to_datetime(dayfirst=True)` sozinho **não resolve**.

#### 3.2.5. Formatos de CNPJ/CPF

| Arquivo | Coluna | Mascarado | 14 díg. | 13 díg. (zero perdido) | CPF mascarado | CPF 11 díg. |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| `compras.csv` | `cnpj_orgao` | 176 | 1.789 | **10** | — | **3** |
| `resultados.csv` | `ni_fornecedor` | 1.239 | 9.911 | **175** | 392 | 3.981 |

**Achados críticos:**
- **175 CNPJs perderam o zero à esquerda** em `ni_fornecedor` (13 dígitos em vez de 14) — o enunciado previu isso.
- **3 valores em `cnpj_orgao` são CPF (11 dígitos)** — inconsistência grave: `cnpj_orgao` deveria conter apenas CNPJ de órgão público. Esses 3 registros precisarão de atenção manual na Sprint 2.
- `ni_fornecedor` tem **3.981 CPFs puros** e **392 CPFs mascarados** — a base mistura pessoa física e jurídica, como previsto.

### 3.3. Encoding quebrado

| Arquivo | Coluna | Caracteres quebrados detectados | Total |
| :--- | :--- | :--- | ---: |
| `compras.csv` | `objeto_compra` | `Ã§`, `Ã£`, `Ã©`, `Ã¡`, `Ã³`, `Ãº` | 119 |
| `compras.csv` | `municipio` | `Ã§`, `Ã£`, `Ã©`, `Ã³` | 23 |
| `compras.csv` | `nome_unidade` | `Ã§`, `Ã£`, `Ã©`, `Ã³` | 4 |
| `itens.csv` | `descricao` | `Ã§`, `Ã£`, `Ã©`, `Ã¡`, `Ã³`, `Ãº` | 217 |
| `resultados.csv` | `nome_fornecedor` | `Ã©` | 1 |

> **Nota técnica:** o caractere `"Ã"` **isolado** foi removido dos padrões de detecção porque gera **falso positivo** — palavras legítimas como "SÃO", "AÇÃO" e "MUNICÍPIO" contêm `Ã` como grafia correta. O indicador real de dupla codificação é `Ã` **seguido de outro caractere** (`Ã§`, `Ã£`, `Ã©` etc.). Esse ajuste será aplicado no script `src/limpeza.py` da Sprint 2.

### 3.4. Cronologia: `data_resultado` vs. `data_publicacao`

- Resultados com ambas as datas parseáveis pelo parser atual: **310** de 15.896 (1,9%).
- Datas invertidas (homologação < publicação): **142** — o equivalente a 45,8% da amostra comparável.

> ⚠️ **Resultado provisório.** O parser da Sprint 1 usou `pd.to_datetime(dayfirst=True)`, que falha em formatos como `2025-01-06T11:51:06` (ISO), `02.01.2025` (ponto) e `20250103` (AAAAMMDD). A amostra comparável (310 casos) é pequena demais para responder à pergunta com confiança. O número será **recalculado na Sprint 2** com parser multi-formato, e a **regra 7** do enunciado (anular datas invertidas) será aplicada em seguida.

### 3.5. Síntese para a Sprint 2

| Inconsistência | Colunas afetadas | Estratégia prevista |
| :--- | :--- | :--- |
| **CNPJ/CPF mascarado** | `cnpj_orgao`, `ni_fornecedor` | Remover `.`, `/`, `-`; manter como `str`; devolver zero à esquerda até 14 dígitos |
| **CNPJ com zero perdido** | `cnpj_orgao` (10), `ni_fornecedor` (175) | `zfill(14)` após limpeza |
| **CPF em campo de órgão** | `cnpj_orgao` (3) | Marcar e documentar; tratar como "não informado" na Fase 3 |
| **Moeda: `R$`, vírgula, ponto, negativos** | 6 colunas monetárias | Normalizar pela regra do enunciado (último símbolo = decimal) |
| **Datas em 5+ formatos** | 4 colunas | Parser multi-formato com fallback |
| **Nulos disfarçados** | 6 colunas | Substituir por `NaN`/`None` **após** classificar tipo (texto vs. numérico) |
| **`"0"` em campo de texto** | `processo`, `modo_disputa`, `situacao_item`, `porte` | Tratar como nulo **apenas** nessas colunas |
| **Encoding quebrado** | `objeto_compra`, `municipio`, `nome_unidade`, `descricao`, `nome_fornecedor` | Reprocessar como `latin-1` → `utf-8` |
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