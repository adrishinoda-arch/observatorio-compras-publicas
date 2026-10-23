-- sql/01_criar_banco.sql
-- Star Schema: 1 tabela Fato + 4 Dimensões
-- Executado por: src/carregar.py, logo após banco.recriar_banco()
-- Referência: Seção 4.3 do enunciado

-- -----------------------------------------------------------------------------
-- Limpeza idempotente
-- Ordem: Fato primeiro (tem FKs para as dimensões), depois as dimensões
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS fato_item_contratado CASCADE;
DROP TABLE IF EXISTS dim_localidade CASCADE;
DROP TABLE IF EXISTS dim_modalidade CASCADE;
DROP TABLE IF EXISTS dim_fornecedor CASCADE;
DROP TABLE IF EXISTS dim_orgao CASCADE;

-- -----------------------------------------------------------------------------
-- DIMENSÕES (criadas primeiro — a Fato tem FK para elas)
-- Chave natural UNIQUE; chave substituta (sk_) como PK
-- -----------------------------------------------------------------------------

-- Quem comprou: uma linha por CNPJ de órgão (unidade compradora)
CREATE TABLE dim_orgao (
    sk_orgao   INTEGER       PRIMARY KEY,
    cnpj_orgao VARCHAR(14)   NOT NULL UNIQUE,
    nome_orgao VARCHAR(255)  NOT NULL,
    poder      VARCHAR(20)   NOT NULL
);

-- Quem vendeu: uma linha por CNPJ/CPF de fornecedor
CREATE TABLE dim_fornecedor (
    sk_fornecedor   INTEGER      PRIMARY KEY,
    ni_fornecedor   VARCHAR(20)  NOT NULL UNIQUE,
    nome_fornecedor VARCHAR(255) NOT NULL,
    tipo_pessoa     VARCHAR(2)   NOT NULL,
    porte           VARCHAR(30)
);

-- Como comprou: uma linha por modalidade
CREATE TABLE dim_modalidade (
    sk_modalidade   INTEGER     PRIMARY KEY,
    modalidade_id   INTEGER     NOT NULL UNIQUE,
    nome_modalidade VARCHAR(50) NOT NULL
);

-- Onde: uma linha por UF
CREATE TABLE dim_localidade (
    sk_localidade INTEGER     PRIMARY KEY,
    uf_sigla      VARCHAR(2)  NOT NULL UNIQUE,
    uf_nome       VARCHAR(50) NOT NULL,
    regiao        VARCHAR(20) NOT NULL
);

-- -----------------------------------------------------------------------------
-- FATO: uma linha por item de contratação (vencedor por item)
-- sk_fato é auto-gerada (SERIAL) — o carregar.py não inclui essa coluna no INSERT
-- -----------------------------------------------------------------------------

CREATE TABLE fato_item_contratado (
    sk_fato                   SERIAL         PRIMARY KEY,
    numero_controle_pncp      VARCHAR(50)    NOT NULL,
    numero_item               INTEGER        NOT NULL,

    -- Ligações (FOREIGN KEYS)
    sk_orgao                  INTEGER        NOT NULL REFERENCES dim_orgao(sk_orgao),
    sk_fornecedor             INTEGER        NOT NULL REFERENCES dim_fornecedor(sk_fornecedor),
    sk_modalidade             INTEGER        NOT NULL REFERENCES dim_modalidade(sk_modalidade),
    sk_localidade             INTEGER        NOT NULL REFERENCES dim_localidade(sk_localidade),

    -- Datas (data_homologacao pode ser NULL — regra 7 anula)
    data_publicacao           DATE,
    data_homologacao          DATE,

    -- Item
    descricao_item            TEXT,
    perfil_gasto              VARCHAR(30)    NOT NULL,   -- Bens | Serviços | Obras e engenharia

    -- Números
    quantidade                DECIMAL(18,4)  NOT NULL,
    valor_unitario_estimado   DECIMAL(18,4)  NOT NULL,
    valor_total_estimado      DECIMAL(18,2)  NOT NULL,
    valor_unitario_homologado DECIMAL(18,4)  NOT NULL,
    valor_total_homologado    DECIMAL(18,2)  NOT NULL,

    -- Calculados
    comparavel                SMALLINT       NOT NULL,   -- 1 ou 0 (regra 6)
    economia_valor            DECIMAL(18,2),            -- NULL nos não comparáveis
    dias_ciclo                INTEGER,                  -- NULL nos 230 sem ciclo

    -- Restrições
    UNIQUE (numero_controle_pncp, numero_item),
    CHECK  (quantidade > 0),
    CHECK  (valor_unitario_estimado   >= 0),
    CHECK  (valor_unitario_homologado >= 0),
    CHECK  (valor_total_estimado      >= 0),
    CHECK  (valor_total_homologado    >= 0),
    CHECK  (comparavel IN (0, 1))
);

-- -----------------------------------------------------------------------------
-- Nota: linha "Não informado" (sk = -1)
-- -----------------------------------------------------------------------------
-- A Seção 4.3 do enunciado indica criar uma linha com sk = -1 nas dimensões
-- SE houver FK órfã na Fato. A Prova Real confirma que, após as 12 regras,
-- todas as FKs têm destino (contagens 363 / 2652 / 7 / 27 batem).
-- Portanto, a linha -1 NÃO é necessária nesta base.
--
-- Se um dia a base mudar e o carregar.py falhar com
-- "insert or update on table ... violates foreign key constraint",
-- insira manualmente, por exemplo:
--
--   INSERT INTO dim_orgao (sk_orgao, cnpj_orgao, nome_orgao, poder)
--   VALUES (-1, '00000000000000', 'NAO INFORMADO', 'Não informado');