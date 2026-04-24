# =============================================================================
# ANALISADOR GENÉRICO DE PLANILHAS — (Genérico + Configuração)
# =============================================================================
# Como funciona:
#   Para cada planilha nova, você preenche APENAS o bloco "CONFIGURAÇÃO"
#   abaixo. O restante do código nunca precisa ser alterado.
#
# Instalação das dependências (executar uma vez no terminal):
#   pip install pandas openpyxl plotly
#
# Formatos suportados: .csv  |  .xlsx  |  .xls
# =============================================================================


import sys
import pandas as pd
import plotly.express as px
import plotly.io as pio
from plotly.offline import plot as plotly_plot
from pathlib import Path


# =============================================================================
# >>>  CONFIGURAÇÃO  <<<  — edite apenas este bloco para cada planilha nova
# =============================================================================

CONFIG = {
    # ------------------------------------------------------------------
    # OBRIGATÓRIO
    # ------------------------------------------------------------------

    # Caminho para o arquivo (CSV, XLSX ou XLS)
    "arquivo": "cancelamentos.csv",

    # Nome da coluna que você quer analisar (a "coluna-alvo").
    # Ex.: "cancelou", "status", "resultado", "churn", "aprovado" ...
    # Se não houver uma coluna-alvo clara, deixe como None.
    "coluna_alvo": "cancelou",

    # ------------------------------------------------------------------
    # OPCIONAL — deixe None ou [] para usar o comportamento padrão
    # ------------------------------------------------------------------

    # Colunas a ignorar na análise (IDs, hashes, campos irrelevantes)
    "colunas_ignorar": ["CustomerID"],

    # Aba da planilha a ler — apenas para arquivos .xlsx/.xls
    # None = primeira aba
    "aba_excel": None,

    # Filtros a aplicar após a análise visual.
    # Cada filtro é um dicionário com:
    #   "coluna"    : nome da coluna
    #   "operador"  : "!=", "==", "<=", ">=", "<", ">"
    #   "valor"     : valor de comparação
    # Deixe como [] para não aplicar filtros.
    "filtros": [
        {"coluna": "duracao_contrato",    "operador": "!=", "valor": "Monthly"},
        {"coluna": "ligacoes_callcenter", "operador": "<=", "valor": 4},
        {"coluna": "dias_atraso",         "operador": "<=", "valor": 20},
    ],

    # Como exibir os gráficos:
    #   "vscode"  → painel interno do VS Code (requer extensão Jupyter)
    #   "html"    → salva um arquivo HTML offline (abre no navegador sem internet)
    #   "excel"   → exporta dados tabulados para .xlsx (usar no Excel / Power BI)
    #   "ambos"   → gera tanto o HTML quanto o Excel
    "saida_graficos": "html",

    # Nomes dos arquivos de saída (usados quando saida_graficos = "html"/"excel"/"ambos")
    "saida_html":  "graficos_analise.html",
    "saida_excel": "dados_analise.xlsx",
}

# =============================================================================
# FIM DA CONFIGURAÇÃO — não é necessário alterar nada abaixo desta linha
# =============================================================================


# -----------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# -----------------------------------------------------------------------------

def exibir_separador(titulo: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {titulo.upper()}")
    print(f"{'=' * 60}")


def exibir_distribuicao(df: pd.DataFrame, coluna: str, label: str = "") -> None:
    prefixo = f"[{label}] " if label else ""
    print(f"\n{prefixo}Distribuição — '{coluna}':")
    contagem   = df[coluna].value_counts()
    percentual = df[coluna].value_counts(normalize=True).map("{:.1%}".format)
    resumo = pd.DataFrame({"Quantidade": contagem, "Percentual": percentual})
    print(resumo.to_string())


def validar_dataframe(df: pd.DataFrame, etapa: str) -> None:
    if df.empty:
        print(f"\n[ERRO] DataFrame ficou vazio após: '{etapa}'. Verifique os filtros.")
        sys.exit(1)


def aplicar_operador(serie: pd.Series, operador: str, valor) -> pd.Series:
    ops = {
        "!=": serie != valor,
        "==": serie == valor,
        "<=": serie <= valor,
        ">=": serie >= valor,
        "<":  serie <  valor,
        ">":  serie >  valor,
    }
    if operador not in ops:
        print(f"[ERRO] Operador '{operador}' inválido. Use: !=, ==, <=, >=, <, >")
        sys.exit(1)
    return ops[operador]


def construir_grafico(df: pd.DataFrame, coluna: str, coluna_alvo) -> px.histogram:
    kwargs = dict(x=coluna, title=f"Distribuição: {coluna}", text_auto=True)
    if coluna_alvo and coluna_alvo in df.columns and coluna != coluna_alvo:
        kwargs["color"]   = coluna_alvo
        kwargs["barmode"] = "group"

    grafico = px.histogram(df, **kwargs)
    grafico.update_layout(
        xaxis_title=coluna,
        yaxis_title="Quantidade",
        legend_title=coluna_alvo or "",
        margin=dict(t=60, b=40),
    )
    return grafico


def exportar_html(graficos: list, caminho: str) -> None:
    blocos = []
    for i, (coluna, grafico) in enumerate(graficos):
        bloco = plotly_plot(grafico, output_type="div", include_plotlyjs=(i == 0))
        blocos.append(f"<h2 style='font-family:sans-serif;color:#555'>{coluna}</h2>{bloco}")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Análise — {Path(caminho).stem}</title>
    <style>
        body {{ font-family: sans-serif; background: #f5f5f5; padding: 24px; }}
        h1   {{ color: #333; }}
        h2   {{ margin-top: 40px; }}
        .g   {{ background: #fff; border-radius: 8px; padding: 16px;
                margin-bottom: 24px; box-shadow: 0 2px 6px rgba(0,0,0,.1); }}
    </style>
</head>
<body>
    <h1>📊 Análise: {Path(caminho).stem}</h1>
    {"".join(f'<div class="g">{b}</div>' for b in blocos)}
</body>
</html>"""

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✔ HTML salvo: '{caminho}' (funciona offline, sem internet)")


def exportar_excel(df, df_filtrado, comparacao, coluna_alvo: str, caminho: str) -> None:
    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:

        df.to_excel(writer, sheet_name="Dados Brutos", index=False)

        if coluna_alvo and coluna_alvo in df.columns:
            dist = pd.DataFrame({
                coluna_alvo:       df[coluna_alvo].value_counts().index,
                "Quantidade":      df[coluna_alvo].value_counts().values,
                "Percentual (%)":  (df[coluna_alvo].value_counts(normalize=True) * 100).round(2).values,
            })
            dist.to_excel(writer, sheet_name="Distribuição Geral", index=False)

            for coluna in df.columns:
                if coluna == coluna_alvo:
                    continue
                freq = (
                    df.groupby([coluna, coluna_alvo])
                    .size()
                    .reset_index(name="Quantidade")
                )
                freq["Percentual (%)"] = (freq["Quantidade"] / freq["Quantidade"].sum() * 100).round(2)
                freq.to_excel(writer, sheet_name=coluna[:31], index=False)

        if df_filtrado is not None:
            df_filtrado.to_excel(writer, sheet_name="Dados Pós-Filtros", index=False)

        if comparacao is not None:
            comparacao.to_excel(writer, sheet_name="Comparação Antes x Depois")

    print(f"  ✔ Excel salvo: '{caminho}' (importe no Excel ou Power BI)")


# -----------------------------------------------------------------------------
# PASSO 1 — CARREGAR O ARQUIVO
# -----------------------------------------------------------------------------

exibir_separador("Passo 1 — Carregar o arquivo")

arquivo  = CONFIG["arquivo"]
extensao = Path(arquivo).suffix.lower()

try:
    if extensao == ".csv":
        tabela = pd.read_csv(arquivo)
    elif extensao in (".xlsx", ".xls"):
        tabela = pd.read_excel(arquivo, sheet_name=CONFIG.get("aba_excel"))
    else:
        print(f"[ERRO] Formato '{extensao}' não suportado. Use .csv, .xlsx ou .xls.")
        sys.exit(1)

    print(f"Arquivo '{arquivo}' carregado com sucesso.")
    print(f"Dimensões: {tabela.shape[0]} linhas × {tabela.shape[1]} colunas")

except FileNotFoundError:
    print(f"[ERRO] Arquivo '{arquivo}' não encontrado.")
    sys.exit(1)


# -----------------------------------------------------------------------------
# PASSO 2 — REMOVER COLUNAS IGNORADAS
# -----------------------------------------------------------------------------

exibir_separador("Passo 2 — Limpeza inicial")

colunas_ignorar = [c for c in (CONFIG.get("colunas_ignorar") or []) if c in tabela.columns]
if colunas_ignorar:
    tabela = tabela.drop(columns=colunas_ignorar)
    print(f"Colunas removidas: {colunas_ignorar}")

print("\nPrimeiras linhas:")
print(tabela.head().to_string())
print("\nResumo das colunas:")
tabela.info()


# -----------------------------------------------------------------------------
# PASSO 3 — TRATAR VALORES AUSENTES
# -----------------------------------------------------------------------------

exibir_separador("Passo 3 — Valores ausentes")

total_nulos = tabela.isnull().sum().sum()
print(f"Total de valores ausentes: {total_nulos}")

if total_nulos > 0:
    print(tabela.isnull().sum()[tabela.isnull().sum() > 0].to_string())
    tabela = tabela.dropna()
    print(f"Linhas removidas. Novo total: {tabela.shape[0]} linhas.")

validar_dataframe(tabela, "remoção de valores ausentes")


# -----------------------------------------------------------------------------
# PASSO 4 — ESTATÍSTICAS DESCRITIVAS
# -----------------------------------------------------------------------------

exibir_separador("Passo 4 — Estatísticas descritivas")

print("\nColunas numéricas:")
print(tabela.describe().to_string())

print("\nColunas categóricas:")
for col in tabela.select_dtypes(include="object").columns:
    print(f"\n  '{col}' — {tabela[col].nunique()} valores únicos:")
    print(f"  {tabela[col].value_counts().head(5).to_string()}")

coluna_alvo = CONFIG.get("coluna_alvo")
if coluna_alvo:
    if coluna_alvo not in tabela.columns:
        print(f"[AVISO] Coluna-alvo '{coluna_alvo}' não encontrada. Análise prosseguirá sem ela.")
        coluna_alvo = None
    else:
        exibir_distribuicao(tabela, coluna_alvo, label="Base completa")


# -----------------------------------------------------------------------------
# PASSO 5 — GRÁFICOS
# -----------------------------------------------------------------------------

exibir_separador("Passo 5 — Geração dos gráficos")

saida    = CONFIG.get("saida_graficos", "html")
graficos = []

if saida == "vscode":
    pio.renderers.default = "vscode"

for coluna in tabela.columns:
    g = construir_grafico(tabela, coluna, coluna_alvo)
    graficos.append((coluna, g))
    if saida == "vscode":
        g.show()
    print(f"  ✔ Gráfico: {coluna}")

if saida in ("html", "ambos"):
    exportar_html(graficos, CONFIG["saida_html"])

if saida in ("excel", "ambos"):
    exportar_excel(tabela, None, None, coluna_alvo, CONFIG["saida_excel"])


# -----------------------------------------------------------------------------
# PASSO 6 — APLICAR FILTROS E COMPARAR IMPACTO
# -----------------------------------------------------------------------------

filtros_cfg = CONFIG.get("filtros") or []

if not filtros_cfg:
    print("\n[INFO] Nenhum filtro configurado. Pulando Passo 6.")
else:
    exibir_separador("Passo 6 — Impacto dos filtros (simulação)")

    antes           = tabela[coluna_alvo].value_counts(normalize=True) if coluna_alvo else None
    tabela_filtrada = tabela.copy()

    for f in filtros_cfg:
        col_f = f["coluna"]
        op_f  = f["operador"]
        val_f = f["valor"]

        if col_f not in tabela_filtrada.columns:
            print(f"  [AVISO] Coluna '{col_f}' não encontrada. Filtro ignorado.")
            continue

        tabela_filtrada = tabela_filtrada[aplicar_operador(tabela_filtrada[col_f], op_f, val_f)]
        validar_dataframe(tabela_filtrada, f"{col_f} {op_f} {val_f}")
        print(f"  ✔ {col_f} {op_f} {val_f} → {tabela_filtrada.shape[0]} linhas restantes")

    comparacao = None
    if coluna_alvo and antes is not None:
        depois     = tabela_filtrada[coluna_alvo].value_counts(normalize=True)
        comparacao = pd.DataFrame({
            "Antes (%)":  antes.map("{:.1%}".format),
            "Depois (%)": depois.map("{:.1%}".format),
        })
        print("\n--- Comparação: antes × depois ---")
        print(comparacao.to_string())
        exibir_distribuicao(tabela_filtrada, coluna_alvo, label="Pós-filtros")

    if saida in ("excel", "ambos"):
        exportar_excel(tabela, tabela_filtrada, comparacao, coluna_alvo, CONFIG["saida_excel"])


# -----------------------------------------------------------------------------

print("\n[ANÁLISE CONCLUÍDA]")

if saida in ("html", "ambos"):
    print(f"\n  📊 {CONFIG['saida_html']}  — Abra no navegador (offline)")
if saida in ("excel", "ambos"):
    print(f"  📁 {CONFIG['saida_excel']} — Importe no Excel ou Power BI")
