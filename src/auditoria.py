# Script de auditoria inicial dos dados brutos do PNCP.
# Lê os 3 CSVs como texto (dtype=str) e imprime um raio-x da base (APENAS CONSULTA, SEM ALTERAÇÃO)

# Responde às 4 perguntas da Seção 7.4 do enunciado:
# 1. Quantas linhas? Há numero_controle_pncp repetido?
# 2. Que formatos de dinheiro, data e CNPJ? Quais colunas têm N/A, -, 0, vazio?
# 3. Existe texto com acento quebrado (Ã§, Ã£)? Em quais colunas?
# 4. Existe data_resultado anterior a data_publicacao?

import re
import sys
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------- Constantes
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Strings que representam nulos disfarçados em campos de texto
# ("0" NÃO está aqui de propósito: só é nulo em campos de texto;
#  em quantidades/valores é um número — tratado na Sprint 2.)
NULOS_DISFARCADOS = [
    "N/A", "NULL", "-", "SEM INFORMAÇÃO", "NÃO SE APLICA",
    "SEM INFORMACAO", "NAO SE APLICA",
]

# Caracteres típicos de Latin-1 mal interpretado como UTF-8 (dupla codificação)
# Nota: "Ã" isolado NÃO está aqui — gera falso positivo em palavras
# legítimas como "SÃO", "AÇÃO", "MUNICÍPIO".
PADROES_ENCODING = ["Ã§", "Ã£", "Ã©", "Ã¡", "Ã³", "Ãº"]


# ---------------------------------------------------------------- Bloco 1
def carregar_csv(nome_arquivo: str) -> pd.DataFrame:
    """Carrega um CSV da pasta data/raw como texto puro (sem inferência de tipos)."""
    caminho = RAW_DIR / nome_arquivo
    return pd.read_csv(caminho, dtype=str, sep=",", encoding="utf-8")


# ---------------------------------------------------------------- Bloco 2
def verificar_duplicatas_pncp(compras: pd.DataFrame) -> None:
    """Pergunta 1: o numero_controle_pncp se repete em compras.csv?"""
    print("\n=== [P1] Duplicatas em compras.csv ===")
    total = len(compras)
    distintos = compras["numero_controle_pncp"].nunique(dropna=False)
    duplicados = total - distintos
    print(f"Total de linhas:                 {total:>6,}")
    print(f"numero_controle_pncp distintos:  {distintos:>6,}")
    print(f"Linhas duplicadas:               {duplicados:>6,}")
    if duplicados == 0:
        print("OK: nenhuma duplicata (grão correto: 1 linha por contratação).")
    else:
        print("ATENCAO: há duplicatas. Investigar antes da modelagem.")


def detectar_nulos_disfarcados(df: pd.DataFrame, nome_arquivo: str) -> None:
    """Pergunta 2 (parcial): conta N/A, NULL, -, SEM INFORMAÇÃO, NÃO SE APLICA."""
    print(f"\n=== [P2] Nulos disfarçados em {nome_arquivo} ===")
    alvos = {s.upper() for s in NULOS_DISFARCADOS}
    algum = False
    for col in df.columns:
        serie = df[col].astype(str).str.strip().str.upper()
        qtd = serie.isin(alvos).sum()
        if qtd > 0:
            print(f"  {col:<35} {qtd:>6} ocorrências")
            algum = True
    if not algum:
        print("  (nenhuma ocorrência detectada)")


def detectar_encoding_quebrado(df: pd.DataFrame, nome_arquivo: str) -> None:
    """Pergunta 3: procura caracteres de Latin-1 mal interpretado como UTF-8."""
    print(f"\n=== [P3] Encoding quebrado em {nome_arquivo} ===")
    algum = False
    for col in df.columns:
        for padrao in PADROES_ENCODING:
            qtd = df[col].astype(str).str.contains(padrao, regex=False, na=False).sum()
            if qtd > 0:
                print(f"  {col:<35} '{padrao}' -> {qtd} ocorrências")
                algum = True
    if not algum:
        print("  (nenhum indício de encoding quebrado)")


# ---------------------------------------------------------------- Bloco 3
def amostrar_formatos_monetarios(df: pd.DataFrame, nome_arquivo: str,
                                  colunas: list[str]) -> None:
    """Pergunta 2: classifica formatos monetários (R$, separadores, negativos)."""
    print(f"\n=== [P2] Formatos monetários em {nome_arquivo} ===")
    padroes = {
        "com R$":             re.compile(r"^\s*R\$\s*"),
        "negativo (parênt)":  re.compile(r"^\(.*\)$"),
        "vírgula decimal":    re.compile(r".*\d,\d+$"),
        "ponto decimal":      re.compile(r".*\d\.\d+$"),
        "só dígitos":         re.compile(r"^\d+$"),
    }
    for col in colunas:
        if col not in df.columns:
            continue
        valores = df[col].dropna().astype(str).str.strip()
        valores = valores[valores != ""]
        if valores.empty:
            print(f"\n  {col}: (coluna vazia)")
            continue
        print(f"\n  {col} — {len(valores):,} valores não vazios")
        print(f"    Amostra: {list(valores.unique()[:5])}")
        for rotulo, regex in padroes.items():
            qtd = valores.str.match(regex).sum()
            if qtd > 0:
                print(f"      {rotulo:<20} {qtd:>6}")


def amostrar_formatos_data(df: pd.DataFrame, nome_arquivo: str,
                            colunas: list[str]) -> None:
    """Pergunta 2: classifica formatos de data (dd/mm/aaaa, ISO, etc.)."""
    print(f"\n=== [P2] Formatos de data em {nome_arquivo} ===")
    padroes = {
        "dd/mm/aaaa":         re.compile(r"^\d{2}/\d{2}/\d{4}$"),
        "dd/mm/aaaa hh:mm":   re.compile(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}"),
        "aaaa-mm-dd":         re.compile(r"^\d{4}-\d{2}-\d{2}$"),
        "aaaa-mm-ddThh:mm":   re.compile(r"^\d{4}-\d{2}-\d{2}T"),
        "dd-mm-aaaa":         re.compile(r"^\d{2}-\d{2}-\d{4}$"),
    }
    for col in colunas:
        if col not in df.columns:
            continue
        valores = df[col].dropna().astype(str).str.strip()
        valores = valores[valores != ""]
        if valores.empty:
            print(f"\n  {col}: (coluna vazia)")
            continue
        print(f"\n  {col} — {len(valores):,} valores não vazios")
        print(f"    Amostra: {list(valores.unique()[:3])}")
        nao_classificados = valores.copy()
        for rotulo, regex in padroes.items():
            mask = valores.str.match(regex)
            qtd = mask.sum()
            if qtd > 0:
                print(f"      {rotulo:<20} {qtd:>6}")
                nao_classificados = nao_classificados[~mask]
        if len(nao_classificados) > 0:
            print(f"      {'OUTROS':<20} {len(nao_classificados):>6} "
                  f"(amostra: {list(nao_classificados.unique()[:3])})")


def amostrar_formatos_cnpj(df: pd.DataFrame, nome_arquivo: str,
                            colunas: list[str]) -> None:
    """Pergunta 2: classifica formatos de CNPJ/CPF (mascarado, puro, zero perdido)."""
    print(f"\n=== [P2] Formatos de CNPJ/CPF em {nome_arquivo} ===")
    padroes = {
        "CNPJ mascarado":              re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$"),
        "CNPJ 14 dígitos":             re.compile(r"^\d{14}$"),
        "CNPJ 13 díg (zero perdido)":  re.compile(r"^\d{13}$"),
        "CPF mascarado":               re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$"),
        "CPF 11 dígitos":              re.compile(r"^\d{11}$"),
    }
    for col in colunas:
        if col not in df.columns:
            continue
        valores = df[col].dropna().astype(str).str.strip()
        valores = valores[valores != ""]
        if valores.empty:
            print(f"\n  {col}: (coluna vazia)")
            continue
        print(f"\n  {col} — {len(valores):,} valores não vazios")
        print(f"    Amostra: {list(valores.unique()[:3])}")
        for rotulo, regex in padroes.items():
            qtd = valores.str.match(regex).sum()
            if qtd > 0:
                print(f"      {rotulo:<30} {qtd:>6}")


def detectar_zeros_e_vazios(df: pd.DataFrame, nome_arquivo: str) -> None:
    """Pergunta 2: conta '0', strings vazias reais e NaN por coluna."""
    print(f"\n=== [P2] Zeros e vazios em {nome_arquivo} ===")
    print(f"  {'coluna':<35} {'zeros':>7} {'vazios':>8} {'NaN':>7}")
    algum = False
    for col in df.columns:
        serie_str = df[col].astype(str).str.strip()
        zeros  = int((serie_str == "0").sum())
        vazios = int((serie_str == "").sum())      # NaN vira "nan", não conta
        nans   = int(df[col].isna().sum())
        if zeros or vazios or nans:
            print(f"  {col:<35} {zeros:>7} {vazios:>8} {nans:>7}")
            algum = True
    if not algum:
        print("  (nenhuma ocorrência)")


def parse_data_robusto(serie: pd.Series) -> pd.Series:
    """
    Converte uma série de strings em datetime, tentando múltiplos formatos.
    Retorna NaT para valores que não casam com nenhum formato conhecido.

    Esta mesma função será reaproveitada em src/limpeza.py na Sprint 2.
    """
    formatos = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y%m%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y",
    ]
    texto = serie.astype(str).str.strip()
    texto = texto.where(~texto.isin(["nan", "None", ""]), None)

    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")
    for fmt in formatos:
        pendentes = resultado.isna() & texto.notna()
        if not pendentes.any():
            break
        tentativa = pd.to_datetime(texto[pendentes], format=fmt, errors="coerce")
        resultado[pendentes] = tentativa

    return resultado


def verificar_cronologia(compras: pd.DataFrame,
                          resultados: pd.DataFrame) -> None:
    #Pergunta 4: conta data_resultado anterior a data_publicacao."""
    print("\n=== [P4] Cronologia: data_resultado vs. data_publicacao ===")
    pub = parse_data_robusto(compras["data_publicacao"])
    mapa_pub = dict(zip(compras["numero_controle_pncp"], pub))

    res = resultados.copy()
    res["data_pub"] = res["numero_controle_pncp"].map(mapa_pub)
    res["data_res"] = parse_data_robusto(res["data_resultado"])

    total_resultados = len(res)
    comparaveis = res.dropna(subset=["data_pub", "data_res"])
    invertidas = int((comparaveis["data_res"] < comparaveis["data_pub"]).sum())
    cobertura = len(comparaveis) / total_resultados * 100

    print(f"Total de resultados:                          {total_resultados:>6,}")
    print(f"Resultados com ambas as datas válidas:        {len(comparaveis):>6,} ({cobertura:.1f}%)")
    print(f"Datas invertidas (resultado < publicação):    {invertidas:>6,}")
    if invertidas == 0:
        print("OK: nenhuma data invertida.")
    else:
        print("ATENCAO: datas invertidas detectadas — "
              "serão anuladas na Sprint 3 (regra 7).")


# ---------------------------------------------------------------- Main
def main():
    # Força UTF-8 no stdout (evita UnicodeEncodeError no PowerShell do Windows)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    arquivos = ["compras.csv", "itens.csv", "resultados.csv"]
    dados = {}
    for nome in arquivos:
        df = carregar_csv(nome)
        dados[nome] = df
        print(f"\n=== {nome} ===")
        print(f"Linhas: {df.shape[0]:,} | Colunas: {df.shape[1]}")

    # ---- Pergunta 1
    verificar_duplicatas_pncp(dados["compras.csv"])

    # ---- Pergunta 2 (nulos, zeros, vazios, formatos)
    for nome, df in dados.items():
        detectar_nulos_disfarcados(df, nome)

    for nome, df in dados.items():
        detectar_zeros_e_vazios(df, nome)

    amostrar_formatos_monetarios(dados["compras.csv"], "compras.csv",
                                  ["valor_total_estimado", "valor_total_homologado"])
    amostrar_formatos_monetarios(dados["itens.csv"], "itens.csv",
                                  ["valor_unitario_estimado", "valor_total_estimado"])
    amostrar_formatos_monetarios(dados["resultados.csv"], "resultados.csv",
                                  ["valor_unitario_homologado", "valor_total_homologado"])

    amostrar_formatos_data(dados["compras.csv"], "compras.csv",
                            ["data_publicacao", "data_abertura_proposta",
                             "data_encerramento_proposta"])
    amostrar_formatos_data(dados["resultados.csv"], "resultados.csv",
                            ["data_resultado"])

    amostrar_formatos_cnpj(dados["compras.csv"], "compras.csv", ["cnpj_orgao"])
    amostrar_formatos_cnpj(dados["resultados.csv"], "resultados.csv", ["ni_fornecedor"])

    # ---- Pergunta 3
    for nome, df in dados.items():
        detectar_encoding_quebrado(df, nome)

    # ---- Pergunta 4
    verificar_cronologia(dados["compras.csv"], dados["resultados.csv"])


if __name__ == "__main__":
    main()