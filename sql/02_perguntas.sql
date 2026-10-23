-- sql/02_perguntas.sql
-- As 6 perguntas de negócio da Controladoria 
-- Rode no pgAdmin (Query Tool) e compare com os números da Prova Real

-- -----------------------------------------------------------------------------
-- P1 — Economia global: % e valor financeiro nominal
-- Resposta esperada: economia = R$ 992.861.686,95 / economia % = 14,46%
-- -----------------------------------------------------------------------------
SELECT
    ROUND(SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado   ELSE 0 END)::numeric, 2) AS valor_estimado_comparavel,
    ROUND(SUM(CASE WHEN comparavel = 1 THEN valor_total_homologado ELSE 0 END)::numeric, 2) AS valor_homologado_comparavel,
    ROUND(
        SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END)
      - SUM(CASE WHEN comparavel = 1 THEN valor_total_homologado ELSE 0 END),
    2) AS economia_nominal,
    ROUND(
        100.0 * (
            SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END)
          - SUM(CASE WHEN comparavel = 1 THEN valor_total_homologado ELSE 0 END)
        )
        / NULLIF(SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END), 0),
    2) AS economia_pct
FROM fato_item_contratado;


-- -----------------------------------------------------------------------------
-- P2a — Top 10 fornecedores por volume financeiro (individual)
-- -----------------------------------------------------------------------------
SELECT
    f.nome_fornecedor,
    f.ni_fornecedor,
    ROUND(SUM(fat.valor_total_homologado)::numeric, 2) AS volume,
    ROUND(
        100.0 * SUM(fat.valor_total_homologado)
        / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado),
    2) AS pct_do_total
FROM fato_item_contratado fat
JOIN dim_fornecedor f ON fat.sk_fornecedor = f.sk_fornecedor
GROUP BY f.sk_fornecedor, f.nome_fornecedor, f.ni_fornecedor
ORDER BY volume DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- P2b — Concentração agregada dos Top 10 (percentual do orçamento)
-- -----------------------------------------------------------------------------
WITH top10 AS (
    SELECT SUM(fat.valor_total_homologado) AS volume
    FROM fato_item_contratado fat
    JOIN dim_fornecedor f ON fat.sk_fornecedor = f.sk_fornecedor
    GROUP BY f.sk_fornecedor
    ORDER BY volume DESC
    LIMIT 10
)
SELECT
    ROUND(SUM(volume)::numeric, 2) AS volume_top10,
    ROUND(
        100.0 * SUM(volume) / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado),
    2) AS pct_top10
FROM top10;


-- -----------------------------------------------------------------------------
-- P3 — Eficácia por modalidade (volume e deságio)
-- Observação: Credenciamento (modalidade 12) não tem item comparável →
-- o deságio fica NULL (esperado, conforme o enunciado)
-- -----------------------------------------------------------------------------
SELECT
    m.nome_modalidade,
    COUNT(*)                                                          AS total_itens,
    COUNT(*) FILTER (WHERE fat.comparavel = 1)                        AS itens_comparaveis,
    ROUND(SUM(fat.valor_total_homologado)::numeric, 2)                AS volume,
    ROUND(SUM(fat.economia_valor)::numeric, 2)                        AS economia,
    ROUND(
        100.0 * SUM(fat.economia_valor)
        / NULLIF(SUM(CASE WHEN fat.comparavel = 1 THEN fat.valor_total_estimado ELSE 0 END), 0),
    2) AS desagio_pct
FROM fato_item_contratado fat
JOIN dim_modalidade m ON fat.sk_modalidade = m.sk_modalidade
GROUP BY m.sk_modalidade, m.nome_modalidade
ORDER BY volume DESC;


-- -----------------------------------------------------------------------------
-- P4 — Ciclo médio por órgão (agrupado pelo NOME padronizado)
-- HAVING >= 5 itens com ciclo, para evitar médias instáveis
-- -----------------------------------------------------------------------------
SELECT
    o.nome_orgao,
    COUNT(fat.dias_ciclo)                   AS itens_com_ciclo,
    ROUND(AVG(fat.dias_ciclo)::numeric, 1)  AS ciclo_medio_dias,
    MAX(fat.dias_ciclo)                     AS ciclo_maximo_dias
FROM fato_item_contratado fat
JOIN dim_orgao o ON fat.sk_orgao = o.sk_orgao
WHERE fat.dias_ciclo IS NOT NULL
GROUP BY o.nome_orgao
HAVING COUNT(fat.dias_ciclo) >= 5
ORDER BY ciclo_medio_dias DESC;


-- -----------------------------------------------------------------------------
-- P5a — Distribuição regional por UF
-- -----------------------------------------------------------------------------
SELECT
    l.uf_sigla,
    l.regiao,
    ROUND(SUM(fat.valor_total_homologado)::numeric, 2) AS volume,
    ROUND(
        100.0 * SUM(fat.economia_valor)
        / NULLIF(SUM(CASE WHEN fat.comparavel = 1 THEN fat.valor_total_estimado ELSE 0 END), 0),
    2) AS desagio_pct
FROM fato_item_contratado fat
JOIN dim_localidade l ON fat.sk_localidade = l.sk_localidade
GROUP BY l.uf_sigla, l.regiao
ORDER BY volume DESC;


-- -----------------------------------------------------------------------------
-- P5b — Distribuição regional agregada por região
-- -----------------------------------------------------------------------------
SELECT
    l.regiao,
    ROUND(SUM(fat.valor_total_homologado)::numeric, 2) AS volume,
    ROUND(
        100.0 * SUM(fat.economia_valor)
        / NULLIF(SUM(CASE WHEN fat.comparavel = 1 THEN fat.valor_total_estimado ELSE 0 END), 0),
    2) AS desagio_pct
FROM fato_item_contratado fat
JOIN dim_localidade l ON fat.sk_localidade = l.sk_localidade
GROUP BY l.regiao
ORDER BY volume DESC;


-- -----------------------------------------------------------------------------
-- P6 — Perfil do gasto (Bens / Serviços / Obras e engenharia)
-- Resposta esperada: Obras 60,8% / Serviços 36,6% / Bens 2,6%
-- -----------------------------------------------------------------------------
SELECT
    perfil_gasto,
    COUNT(*)                                                          AS itens,
    ROUND(SUM(valor_total_homologado)::numeric, 2)                    AS volume,
    ROUND(
        100.0 * SUM(valor_total_homologado)
        / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado),
    2) AS pct_do_total
FROM fato_item_contratado
GROUP BY perfil_gasto
ORDER BY volume DESC;