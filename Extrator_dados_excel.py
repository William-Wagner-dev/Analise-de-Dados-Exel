# =============================================================================
# ANÁLISE DE CANCELAMENTOS DE CLIENTES
# =============================================================================
# Objetivo: Identificar os principais fatores que levam ao cancelamento
# e propor ações corretivas com base nos dados.
#
# Instalação das dependências (executar uma vez no terminal):
#   pip install pandas openpyxl plotly
# =============================================================================

import sys
import pandas as pd
import plotly.express as px


# =============================================================================
# CONFIGURAÇÕES GERAIS
# =============================================================================

ARQUIVO_CSV      = "cancelamentos.csv"
COLUNA_ID        = "CustomerID"
COLUNA_ALVO      = "cancelou"
COLUNA_CONTRATO  = "duracao_contrato"
COLUNA_CALLCENTER = "ligacoes_callcenter"
COLUNA_ATRASO    = "dias_atraso"


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def exibir_separador(titulo: str) -> None:
    """Imprime um separador visual com título para organizar o output."""
    print(f"\n{'=' * 60}")
    print(f"  {titulo.upper()}")
    print(f"{'=' * 60}")


def exibir_distribuicao(df: pd.DataFrame, coluna: str, label: str = "") -> None:
    """Exibe contagem absoluta e percentual de uma coluna categórica."""
    prefixo = f"[{label}] " if label else ""
    print(f"\n{prefixo}Distribuição — '{coluna}':")
    contagem    = df[coluna].value_counts()
    percentual  = df[coluna].value_counts(normalize=True).map("{:.1%}".format)
    resumo = pd.DataFrame({"Quantidade": contagem, "Percentual": percentual})
    print(resumo.to_string())


def validar_dataframe(df: pd.DataFrame, etapa: str) -> None:
    """Interrompe a execução se o DataFrame estiver vazio após uma filtragem."""
    if df.empty:
        print(f"\n[ERRO] DataFrame ficou vazio após: '{etapa}'. Verifique os filtros.")
        sys.exit(1)


# =============================================================================
# PASSO 1 — IMPORTAR A BASE DE DADOS
# =============================================================================

exibir_separador("Passo 1 — Importar a base de dados")

try:
    tabela = pd.read_csv(ARQUIVO_CSV)
    print(f"Arquivo '{ARQUIVO_CSV}' carregado com sucesso.")
    print(f"Dimensões iniciais: {tabela.shape[0]} linhas × {tabela.shape[1]} colunas")
except FileNotFoundError:
    print(f"[ERRO] Arquivo '{ARQUIVO_CSV}' não encontrado. Verifique o caminho.")
    sys.exit(1)


# =============================================================================
# PASSO 2 — VISUALIZAR E LIMPAR A BASE DE DADOS
# =============================================================================

exibir_separador("Passo 2 — Visualizar e limpar a base de dados")

# Remove coluna de identificação (irrelevante para a análise)
if COLUNA_ID in tabela.columns:
    tabela = tabela.drop(columns=COLUNA_ID)
    print(f"Coluna '{COLUNA_ID}' removida (não agrega valor analítico).")

print("\nPrimeiras linhas da base:")
print(tabela.head().to_string())

print("\nInformações gerais das colunas:")
tabela.info()


# =============================================================================
# PASSO 3 — TRATAR VALORES AUSENTES
# =============================================================================

exibir_separador("Passo 3 — Tratar valores ausentes")

total_nulos = tabela.isnull().sum().sum()
print(f"Total de valores ausentes encontrados: {total_nulos}")

if total_nulos > 0:
    print("\nValores ausentes por coluna:")
    print(tabela.isnull().sum()[tabela.isnull().sum() > 0].to_string())
    tabela = tabela.dropna()
    print(f"\nLinhas removidas. Novo total: {tabela.shape[0]} linhas.")
else:
    print("Nenhum valor ausente encontrado. Nenhuma linha removida.")

validar_dataframe(tabela, "remoção de valores ausentes")


# =============================================================================
# PASSO 4 — ANÁLISE INICIAL DOS CANCELAMENTOS
# =============================================================================

exibir_separador("Passo 4 — Análise inicial dos cancelamentos")

if COLUNA_ALVO not in tabela.columns:
    print(f"[ERRO] Coluna '{COLUNA_ALVO}' não encontrada no arquivo.")
    sys.exit(1)

exibir_distribuicao(tabela, COLUNA_ALVO, label="Base completa")


# =============================================================================
# PASSO 5 — ANÁLISE DAS CAUSAS (GRÁFICOS POR COLUNA)
# =============================================================================

exibir_separador("Passo 5 — Análise visual das causas de cancelamento")

print("Gerando gráficos para cada coluna da base...")

for coluna in tabela.columns:
    grafico = px.histogram(
        tabela,
        x=coluna,
        color=COLUNA_ALVO,
        title=f"Distribuição de cancelamentos por: {coluna}",
        barmode="group",
        text_auto=True,
    )
    grafico.update_layout(
        xaxis_title=coluna,
        yaxis_title="Quantidade de clientes",
        legend_title="Cancelou?",
    )
    grafico.show()

# -----------------------------------------------------------------------------
# Insights identificados visualmente:
#
#   1. Contrato mensal     → 100% dos clientes cancelam.
#      Ação: Oferecer descontos nos planos anuais e trimestrais.
#
#   2. +4 ligações ao call center → taxa de cancelamento muito alta.
#      Ação: Resolver o problema do cliente em no máximo 3 contatos.
#
#   3. Atraso superior a 20 dias → clientes cancelam consistentemente.
#      Ação: Implementar política de resolução de atrasos em até 10 dias.
# -----------------------------------------------------------------------------


# =============================================================================
# PASSO 6 — APLICAR FILTROS E AVALIAR IMPACTO
# =============================================================================

exibir_separador("Passo 6 — Impacto das ações corretivas (simulação)")

# Guarda métricas antes dos filtros para comparação posterior
cancelamentos_antes = tabela[COLUNA_ALVO].value_counts(normalize=True)

# Filtragem baseada nos insights do Passo 5
filtros = {
    f"{COLUNA_CONTRATO} != 'Monthly'":  tabela[COLUNA_CONTRATO] != "Monthly",
    f"{COLUNA_CALLCENTER} <= 4":        tabela[COLUNA_CALLCENTER] <= 4,
    f"{COLUNA_ATRASO} <= 20":           tabela[COLUNA_ATRASO] <= 20,
}

tabela_filtrada = tabela.copy()

for descricao, condicao in filtros.items():
    tabela_filtrada = tabela_filtrada[condicao]
    validar_dataframe(tabela_filtrada, descricao)
    print(f"  ✔ Filtro aplicado: {descricao} → {tabela_filtrada.shape[0]} linhas restantes")

# Comparação antes × depois
cancelamentos_depois = tabela_filtrada[COLUNA_ALVO].value_counts(normalize=True)

print("\n--- Comparação: antes × depois dos ajustes ---")
comparacao = pd.DataFrame({
    "Antes (%)":  cancelamentos_antes.map("{:.1%}".format),
    "Depois (%)": cancelamentos_depois.map("{:.1%}".format),
})
print(comparacao.to_string())

exibir_distribuicao(tabela_filtrada, COLUNA_ALVO, label="Pós-filtros")

print("\n[ANÁLISE CONCLUÍDA]")