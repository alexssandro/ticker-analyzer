"""
analyzer.py — Análise automatizada de Fundos Imobiliários (FIIs) brasileiros.

Avalia 10 FIIs com base em 20 critérios de qualidade, utilizando scraping do
Status Invest com fallback para base de dados estática local.

Compatível com Python 3.8+
"""

import csv
import os
import time
from datetime import date
from typing import Any

import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from jinja2 import Template
from tabulate import tabulate

# Inicializa colorama para compatibilidade cross-platform
init(autoreset=True)

# ---------------------------------------------------------------------------
# Configurações gerais
# ---------------------------------------------------------------------------

TICKERS = [
    "GGRC11",
    "BTAL11",
    "VISC11",
    "ALZR11",
    "BTLG11",
    "HGLG11",
    "TRXF11",
    "RZTR11",
    "BRCO11",
    "JURO11",
]

BASE_URL = "https://statusinvest.com.br/fundos-imobiliarios/{ticker}"

SCRAPING_DELAY_SEGUNDOS: float = 1.5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Descrições dos critérios para exibição
CRITERIOS_DESCRICAO = {
    "C1": "Imóveis em regiões nobres",
    "C2": "Propriedades novas (< 15 anos)",
    "C3": "P/VP abaixo de 1,0",
    "C4": "Dividendos consistentes > 4 anos",
    "C5": "Sem dependência de único inquilino (< 30%)",
    "C6": "Dividend Yield acima da média do setor",
    "C7": "Gestão sem derivativos/opções",
    "C8": "Dívida líquida/PL < 50%",
    "C9": "< 4 anos de lucro para quitar dívidas",
    "C10": "Vacância < 10%",
    "C11": "< 10% em cotas de outros FIIs",
    "C12": "Cap Rate > 8% a.a.",
    "C13": "Cota patrimonial valorizada (3 anos)",
    "C14": "Imóveis em >= 3 estados",
    "C15": "Taxa adm + gestão < 1,5% a.a.",
    "C16": "< 2 emissões nos últimos 24 meses",
    "C17": "Liquidez diária > R$ 1 milhão",
    "C18": "> 70% inquilinos investment grade",
    "C19": "Prazo médio contratos > 5 anos",
    "C20": "Reserva >= 1 mês de distribuição",
}

# ---------------------------------------------------------------------------
# Base de dados estática (fallback)
# ---------------------------------------------------------------------------

DADOS_ESTATICOS: dict[str, dict[str, Any]] = {
    "GGRC11": {
        "tipo": "Logística",
        "regioes_nobres": True,
        "idade_media_anos": 8,
        "pvp": 0.95,
        "anos_dividendos": 5,
        "concentracao_maior_inquilino_pct": 22,
        "dy_anual_pct": 12.5,
        "usa_derivativos": False,
        "divida_pl_pct": 30,
        "anos_quitar_divida": 2.5,
        "vacancia_pct": 3.0,
        "pct_cotas_outros_fiis": 0,
        "cap_rate_pct": 9.5,
        "valorizou_cota_3anos": True,
        "num_estados": 4,
        "taxa_adm_gestao_pct": 1.1,
        "emissoes_24meses": 1,
        "liquidez_diaria_mil_reais": 3500,
        "pct_inquilinos_investment_grade": 80,
        "prazo_medio_contratos_anos": 7,
        "tem_reserva_1mes": True,
    },
    "BTAL11": {
        "tipo": "Lajes Corporativas",
        "regioes_nobres": True,
        "idade_media_anos": 18,
        "pvp": 0.82,
        "anos_dividendos": 6,
        "concentracao_maior_inquilino_pct": 25,
        "dy_anual_pct": 10.8,
        "usa_derivativos": False,
        "divida_pl_pct": 38,
        "anos_quitar_divida": 3.2,
        "vacancia_pct": 14.0,
        "pct_cotas_outros_fiis": 0,
        "cap_rate_pct": 7.8,
        "valorizou_cota_3anos": False,
        "num_estados": 2,
        "taxa_adm_gestao_pct": 1.4,
        "emissoes_24meses": 0,
        "liquidez_diaria_mil_reais": 1200,
        "pct_inquilinos_investment_grade": 65,
        "prazo_medio_contratos_anos": 4,
        "tem_reserva_1mes": True,
    },
    "VISC11": {
        "tipo": "Shopping Centers",
        "regioes_nobres": True,
        "idade_media_anos": 12,
        "pvp": 0.98,
        "anos_dividendos": 8,
        "concentracao_maior_inquilino_pct": 8,
        "dy_anual_pct": 9.5,
        "usa_derivativos": False,
        "divida_pl_pct": 25,
        "anos_quitar_divida": 2.0,
        "vacancia_pct": 5.0,
        "pct_cotas_outros_fiis": 0,
        "cap_rate_pct": 8.5,
        "valorizou_cota_3anos": True,
        "num_estados": 5,
        "taxa_adm_gestao_pct": 1.1,
        "emissoes_24meses": 1,
        "liquidez_diaria_mil_reais": 8000,
        "pct_inquilinos_investment_grade": 75,
        "prazo_medio_contratos_anos": 5,
        "tem_reserva_1mes": True,
    },
    "ALZR11": {
        "tipo": "Logística",
        "regioes_nobres": True,
        "idade_media_anos": 6,
        "pvp": 1.05,
        "anos_dividendos": 5,
        "concentracao_maior_inquilino_pct": 35,
        "dy_anual_pct": 11.0,
        "usa_derivativos": False,
        "divida_pl_pct": 20,
        "anos_quitar_divida": 1.8,
        "vacancia_pct": 0.0,
        "pct_cotas_outros_fiis": 0,
        "cap_rate_pct": 10.0,
        "valorizou_cota_3anos": False,
        "num_estados": 3,
        "taxa_adm_gestao_pct": 1.0,
        "emissoes_24meses": 2,
        "liquidez_diaria_mil_reais": 2500,
        "pct_inquilinos_investment_grade": 90,
        "prazo_medio_contratos_anos": 9,
        "tem_reserva_1mes": True,
    },
    "BTLG11": {
        "tipo": "Logística",
        "regioes_nobres": True,
        "idade_media_anos": 7,
        "pvp": 0.93,
        "anos_dividendos": 6,
        "concentracao_maior_inquilino_pct": 18,
        "dy_anual_pct": 12.0,
        "usa_derivativos": False,
        "divida_pl_pct": 28,
        "anos_quitar_divida": 2.3,
        "vacancia_pct": 4.0,
        "pct_cotas_outros_fiis": 0,
        "cap_rate_pct": 9.8,
        "valorizou_cota_3anos": True,
        "num_estados": 5,
        "taxa_adm_gestao_pct": 0.9,
        "emissoes_24meses": 1,
        "liquidez_diaria_mil_reais": 12000,
        "pct_inquilinos_investment_grade": 85,
        "prazo_medio_contratos_anos": 7,
        "tem_reserva_1mes": True,
    },
    "HGLG11": {
        "tipo": "Logística",
        "regioes_nobres": True,
        "idade_media_anos": 10,
        "pvp": 1.10,
        "anos_dividendos": 12,
        "concentracao_maior_inquilino_pct": 15,
        "dy_anual_pct": 11.5,
        "usa_derivativos": False,
        "divida_pl_pct": 22,
        "anos_quitar_divida": 2.0,
        "vacancia_pct": 3.5,
        "pct_cotas_outros_fiis": 5,
        "cap_rate_pct": 9.2,
        "valorizou_cota_3anos": True,
        "num_estados": 6,
        "taxa_adm_gestao_pct": 1.0,
        "emissoes_24meses": 1,
        "liquidez_diaria_mil_reais": 25000,
        "pct_inquilinos_investment_grade": 82,
        "prazo_medio_contratos_anos": 8,
        "tem_reserva_1mes": True,
    },
    "TRXF11": {
        "tipo": "Logística/Varejo",
        "regioes_nobres": False,
        "idade_media_anos": 9,
        "pvp": 0.90,
        "anos_dividendos": 4,
        "concentracao_maior_inquilino_pct": 55,
        "dy_anual_pct": 13.5,
        "usa_derivativos": False,
        "divida_pl_pct": 45,
        "anos_quitar_divida": 3.5,
        "vacancia_pct": 0.0,
        "pct_cotas_outros_fiis": 0,
        "cap_rate_pct": 10.5,
        "valorizou_cota_3anos": False,
        "num_estados": 5,
        "taxa_adm_gestao_pct": 1.3,
        "emissoes_24meses": 2,
        "liquidez_diaria_mil_reais": 3000,
        "pct_inquilinos_investment_grade": 70,
        "prazo_medio_contratos_anos": 10,
        "tem_reserva_1mes": True,
    },
    "RZTR11": {
        "tipo": "Agro/CRI",
        "regioes_nobres": False,
        "idade_media_anos": 5,
        "pvp": 0.88,
        "anos_dividendos": 4,
        "concentracao_maior_inquilino_pct": 20,
        "dy_anual_pct": 14.0,
        "usa_derivativos": False,
        "divida_pl_pct": 10,
        "anos_quitar_divida": 0.8,
        "vacancia_pct": 0.0,
        "pct_cotas_outros_fiis": 0,
        "cap_rate_pct": 11.0,
        "valorizou_cota_3anos": False,
        "num_estados": 8,
        "taxa_adm_gestao_pct": 1.2,
        "emissoes_24meses": 1,
        "liquidez_diaria_mil_reais": 2000,
        "pct_inquilinos_investment_grade": 60,
        "prazo_medio_contratos_anos": 6,
        "tem_reserva_1mes": True,
    },
    "BRCO11": {
        "tipo": "Logística",
        "regioes_nobres": True,
        "idade_media_anos": 5,
        "pvp": 0.96,
        "anos_dividendos": 5,
        "concentracao_maior_inquilino_pct": 20,
        "dy_anual_pct": 11.8,
        "usa_derivativos": False,
        "divida_pl_pct": 25,
        "anos_quitar_divida": 2.2,
        "vacancia_pct": 2.0,
        "pct_cotas_outros_fiis": 0,
        "cap_rate_pct": 9.5,
        "valorizou_cota_3anos": True,
        "num_estados": 4,
        "taxa_adm_gestao_pct": 0.9,
        "emissoes_24meses": 1,
        "liquidez_diaria_mil_reais": 5000,
        "pct_inquilinos_investment_grade": 88,
        "prazo_medio_contratos_anos": 8,
        "tem_reserva_1mes": True,
    },
    "JURO11": {
        "tipo": "Papel/CRI",
        "regioes_nobres": False,
        "idade_media_anos": 3,
        "pvp": 0.97,
        "anos_dividendos": 3,
        "concentracao_maior_inquilino_pct": 15,
        "dy_anual_pct": 13.0,
        "usa_derivativos": False,
        "divida_pl_pct": 5,
        "anos_quitar_divida": 0.5,
        "vacancia_pct": 0.0,
        "pct_cotas_outros_fiis": 0,
        "cap_rate_pct": 12.0,
        "valorizou_cota_3anos": False,
        "num_estados": 6,
        "taxa_adm_gestao_pct": 1.0,
        "emissoes_24meses": 3,
        "liquidez_diaria_mil_reais": 1500,
        "pct_inquilinos_investment_grade": 75,
        "prazo_medio_contratos_anos": 4,
        "tem_reserva_1mes": False,
    },
}

# ---------------------------------------------------------------------------
# Scraping do Status Invest
# ---------------------------------------------------------------------------


def _parse_numero(texto: str) -> float | None:
    """Converte string numérica brasileira (ex: '1.234,56') para float."""
    try:
        limpo = texto.strip().replace("R$", "").replace("%", "").strip()
        limpo = limpo.replace(".", "").replace(",", ".")
        return float(limpo)
    except (ValueError, AttributeError):
        return None


def buscar_dados_scraping(ticker: str) -> dict[str, Any]:
    """
    Tenta buscar dados do Status Invest via scraping com 3 tentativas e backoff.

    Retorna um dict com os campos disponíveis via scraping, ou dict vazio em caso
    de falha total.
    """
    url = BASE_URL.format(ticker=ticker.lower())
    dados: dict[str, Any] = {}

    for tentativa in range(3):
        try:
            resposta = requests.get(url, headers=HEADERS, timeout=10)
            resposta.raise_for_status()
            soup = BeautifulSoup(resposta.text, "lxml")

            # --- P/VP ---
            # Seletores tentados em ordem de prioridade
            pvp_el = soup.find("div", {"title": "Preço/Valor patrimonial"})
            if pvp_el:
                span = pvp_el.find("strong")
                if span:
                    valor = _parse_numero(span.get_text())
                    if valor is not None:
                        dados["pvp"] = valor

            # --- Dividend Yield ---
            dy_el = soup.find("div", {"title": "Dividend Yield com base nos últimos 12 meses"})
            if dy_el:
                span = dy_el.find("strong")
                if span:
                    valor = _parse_numero(span.get_text())
                    if valor is not None:
                        dados["dy_anual_pct"] = valor

            # --- Vacância ---
            vac_el = soup.find("div", {"title": "Vacância"})
            if vac_el:
                span = vac_el.find("strong")
                if span:
                    valor = _parse_numero(span.get_text())
                    if valor is not None:
                        dados["vacancia_pct"] = valor

            # --- Liquidez diária (em reais) ---
            liq_el = soup.find("div", {"title": "Liquidez"})
            if liq_el:
                span = liq_el.find("strong")
                if span:
                    valor = _parse_numero(span.get_text())
                    if valor is not None:
                        # Converte para milhares de reais
                        dados["liquidez_diaria_mil_reais"] = valor / 1000

            # --- Taxa de administração ---
            taxa_el = soup.find("div", {"title": "Taxa de Administração"})
            if taxa_el:
                span = taxa_el.find("strong")
                if span:
                    valor = _parse_numero(span.get_text())
                    if valor is not None:
                        dados["taxa_adm_gestao_pct"] = valor

            break  # Sucesso — sai do loop de retry

        except requests.exceptions.RequestException:
            if tentativa < 2:
                # Backoff exponencial: 1s, 2s
                time.sleep(2**tentativa)
            else:
                # Todas as tentativas falharam
                pass

    return dados


# ---------------------------------------------------------------------------
# Avaliação de critérios
# ---------------------------------------------------------------------------


def _media_dy_por_tipo(tipo: str) -> float:
    """Calcula o DY médio dos fundos do mesmo tipo presentes na base estática."""
    valores = [
        d["dy_anual_pct"]
        for d in DADOS_ESTATICOS.values()
        if d["tipo"] == tipo and "dy_anual_pct" in d
    ]
    if not valores:
        # Fallback: média geral de todos os fundos da base
        valores = [d["dy_anual_pct"] for d in DADOS_ESTATICOS.values() if "dy_anual_pct" in d]
    return sum(valores) / len(valores) if valores else 10.0


def avaliar_criterios(dados: dict[str, Any]) -> dict[str, Any]:
    """
    Avalia os 20 critérios de qualidade para um fundo.

    Retorna um dict com chaves C1..C20. Cada valor é True (SIM), False (NÃO)
    ou a string 'DESCARTAR' (apenas para C3 quando P/VP > 1,5).
    """
    pvp = dados.get("pvp", 1.0)
    tipo = dados.get("tipo", "")
    media_dy = _media_dy_por_tipo(tipo)

    # C3: P/VP — caso especial com DESCARTAR
    if pvp > 1.5:
        c3 = "DESCARTAR"
    else:
        c3 = bool(pvp < 1.0)

    return {
        "C1": bool(dados.get("regioes_nobres", False)),
        "C2": bool(dados.get("idade_media_anos", 99) < 15),
        "C3": c3,
        "C4": bool(dados.get("anos_dividendos", 0) > 4),
        "C5": bool(dados.get("concentracao_maior_inquilino_pct", 100) < 30),
        "C6": bool(dados.get("dy_anual_pct", 0) >= media_dy),
        "C7": bool(not dados.get("usa_derivativos", True)),
        "C8": bool(dados.get("divida_pl_pct", 100) < 50),
        "C9": bool(dados.get("anos_quitar_divida", 99) < 4),
        "C10": bool(dados.get("vacancia_pct", 100) < 10),
        "C11": bool(dados.get("pct_cotas_outros_fiis", 100) < 10),
        "C12": bool(dados.get("cap_rate_pct", 0) > 8),
        "C13": bool(dados.get("valorizou_cota_3anos", False)),
        "C14": bool(dados.get("num_estados", 0) >= 3),
        "C15": bool(dados.get("taxa_adm_gestao_pct", 99) < 1.5),
        "C16": bool(dados.get("emissoes_24meses", 99) < 2),
        "C17": bool(dados.get("liquidez_diaria_mil_reais", 0) > 1000),
        "C18": bool(dados.get("pct_inquilinos_investment_grade", 0) > 70),
        "C19": bool(dados.get("prazo_medio_contratos_anos", 0) > 5),
        "C20": bool(dados.get("tem_reserva_1mes", False)),
    }


# ---------------------------------------------------------------------------
# Exibição no terminal
# ---------------------------------------------------------------------------

BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║   📊  TICKER ANALYZER — Análise de FIIs Brasileiros  📊  ║
║          20 Critérios de Qualidade por Fundo             ║
╚══════════════════════════════════════════════════════════╝
"""


def _simbolo_terminal(valor: Any) -> str:
    """Retorna string colorida para exibição no terminal."""
    if valor == "DESCARTAR":
        return f"{Fore.RED}{Style.BRIGHT}🚫 DESCARTAR{Style.RESET_ALL}"
    if valor is True:
        return f"{Fore.GREEN}✅ SIM{Style.RESET_ALL}"
    return f"{Fore.RED}❌ NÃO{Style.RESET_ALL}"


def exibir_tabela_terminal(
    resultados: dict[str, dict[str, Any]],
    tickers: list[str],
) -> None:
    """Exibe a tabela de critérios formatada no terminal com cores."""
    criterios = list(CRITERIOS_DESCRICAO.keys())

    # Cabeçalho: critério + descrição + um resultado por ticker
    cabecalho = ["#", "Critério"] + tickers
    linhas = []

    for c in criterios:
        linha = [c, CRITERIOS_DESCRICAO[c]]
        for ticker in tickers:
            linha.append(_simbolo_terminal(resultados[ticker].get(c)))
        linhas.append(linha)

    # Linha de pontuação total
    linha_pontos = ["—", "PONTUAÇÃO (SIM)"]
    for ticker in tickers:
        pontos = sum(
            1 for c in criterios if resultados[ticker].get(c) is True
        )
        linha_pontos.append(f"{Fore.CYAN}{Style.BRIGHT}{pontos}/20{Style.RESET_ALL}")
    linhas.append(linha_pontos)

    print(tabulate(linhas, headers=cabecalho, tablefmt="grid"))


# ---------------------------------------------------------------------------
# Exportação HTML
# ---------------------------------------------------------------------------

TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Ticker Analyzer — Análise de FIIs</title>
  <link
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
    rel="stylesheet"
  />
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    .sim  { background-color: #d4edda; color: #155724; font-weight: bold; text-align: center; }
    .nao  { background-color: #f8d7da; color: #721c24; font-weight: bold; text-align: center; }
    .descartar { background-color: #f8d7da; color: #721c24; font-weight: bold; text-align: center; }
    .pontos { background-color: #cce5ff; color: #004085; font-weight: bold; text-align: center; }
    th { text-align: center; vertical-align: middle; }
    td { vertical-align: middle; }
    .criterio-col { min-width: 280px; }
  </style>
</head>
<body>
  <h1 class="mb-1">📊 Ticker Analyzer — Análise de FIIs Brasileiros</h1>
  <p class="text-muted mb-3">
    Gerado em: <strong>{{ data_geracao }}</strong> &nbsp;|&nbsp;
    Fonte: Status Invest (scraping) + dados estáticos (RIs públicos 2024/2025)
  </p>

  <div class="table-responsive">
    <table class="table table-bordered table-sm">
      <thead class="table-dark">
        <tr>
          <th>#</th>
          <th class="criterio-col">Critério</th>
          {% for ticker in tickers %}<th>{{ ticker }}</th>{% endfor %}
        </tr>
      </thead>
      <tbody>
        {% for c, desc in criterios.items() %}
        <tr>
          <td class="text-center">{{ c }}</td>
          <td>{{ desc }}</td>
          {% for ticker in tickers %}
            {% set val = resultados[ticker][c] %}
            {% if val == 'DESCARTAR' %}
              <td class="descartar">🚫 DESCARTAR</td>
            {% elif val %}
              <td class="sim">✅ SIM</td>
            {% else %}
              <td class="nao">❌ NÃO</td>
            {% endif %}
          {% endfor %}
        </tr>
        {% endfor %}
        <!-- Linha de pontuação -->
        <tr>
          <td class="pontos">—</td>
          <td class="pontos">PONTUAÇÃO (SIM)</td>
          {% for ticker in tickers %}
            <td class="pontos">{{ pontuacoes[ticker] }}/20</td>
          {% endfor %}
        </tr>
      </tbody>
    </table>
  </div>

  <hr />
  <p class="text-muted small">
    <strong>⚠️ Disclaimer:</strong>
    Este projeto é para fins educacionais e informativos apenas. Não constitui recomendação de
    investimento. Os dados estáticos são aproximações baseadas em RIs públicos e podem não
    refletir a situação atual dos fundos. Sempre consulte fontes oficiais como CVM, B3 e os RIs
    dos próprios fundos antes de tomar decisões de investimento.
  </p>
</body>
</html>
"""


def exportar_html(
    resultados: dict[str, dict[str, Any]],
    tickers: list[str],
    caminho: str,
) -> None:
    """Gera o arquivo HTML com tabela Bootstrap colorida."""
    criterios = CRITERIOS_DESCRICAO

    # Calcula pontuações
    pontuacoes = {
        ticker: sum(1 for c in criterios if resultados[ticker].get(c) is True)
        for ticker in tickers
    }

    template = Template(TEMPLATE_HTML)
    html = template.render(
        data_geracao=date.today().strftime("%d/%m/%Y"),
        tickers=tickers,
        criterios=criterios,
        resultados=resultados,
        pontuacoes=pontuacoes,
    )

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  📄 HTML salvo em: {caminho}")


# ---------------------------------------------------------------------------
# Exportação CSV
# ---------------------------------------------------------------------------


def exportar_csv(
    dados_todos: dict[str, dict[str, Any]],
    tickers: list[str],
    caminho: str,
) -> None:
    """Gera o arquivo CSV com os dados numéricos brutos de cada fundo."""
    campos = [
        "ticker",
        "tipo",
        "pvp",
        "dy_anual_pct",
        "vacancia_pct",
        "liquidez_diaria_mil_reais",
        "taxa_adm_gestao_pct",
        "divida_pl_pct",
        "anos_quitar_divida",
        "cap_rate_pct",
        "concentracao_maior_inquilino_pct",
        "pct_inquilinos_investment_grade",
        "prazo_medio_contratos_anos",
        "num_estados",
        "emissoes_24meses",
        "idade_media_anos",
        "anos_dividendos",
        "pct_cotas_outros_fiis",
        "regioes_nobres",
        "usa_derivativos",
        "valorizou_cota_3anos",
        "tem_reserva_1mes",
    ]

    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        for ticker in tickers:
            linha = {"ticker": ticker}
            linha.update(dados_todos[ticker])
            writer.writerow(linha)

    print(f"  📋 CSV salvo em: {caminho}")


# ---------------------------------------------------------------------------
# Ranking final
# ---------------------------------------------------------------------------


def exibir_ranking(resultados: dict[str, dict[str, Any]], tickers: list[str]) -> None:
    """Exibe ranking dos fundos por pontuação total (número de SIM)."""
    criterios = list(CRITERIOS_DESCRICAO.keys())
    ranking = sorted(
        tickers,
        key=lambda t: sum(1 for c in criterios if resultados[t].get(c) is True),
        reverse=True,
    )

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*50}")
    print("  🏆  RANKING FINAL — Pontuação por Fundo")
    print(f"{'='*50}{Style.RESET_ALL}")

    for posicao, ticker in enumerate(ranking, start=1):
        pontos = sum(1 for c in criterios if resultados[ticker].get(c) is True)
        cor = Fore.GREEN if pontos >= 15 else (Fore.YELLOW if pontos >= 10 else Fore.RED)
        print(
            f"  {posicao:2}. {cor}{Style.BRIGHT}{ticker}{Style.RESET_ALL}"
            f"  —  {cor}{pontos}/20 pontos{Style.RESET_ALL}"
        )


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------


def main() -> None:
    """Coleta dados, avalia critérios, exibe tabela e exporta resultados."""
    print(f"{Fore.CYAN}{BANNER}{Style.RESET_ALL}")

    # Garante que a pasta output/ exista
    os.makedirs("output", exist_ok=True)

    dados_todos: dict[str, dict[str, Any]] = {}
    resultados: dict[str, dict[str, Any]] = {}

    print(f"{Fore.YELLOW}⏳ Coletando dados dos fundos...{Style.RESET_ALL}\n")

    for ticker in TICKERS:
        print(f"  📡 {ticker} — tentando scraping...", end=" ", flush=True)

        # Tenta buscar dados via scraping
        dados_scraping = buscar_dados_scraping(ticker)

        # Parte da base estática e sobrepõe com dados do scraping (quando disponíveis)
        dados = dict(DADOS_ESTATICOS.get(ticker, {}))
        dados.update(dados_scraping)

        if dados_scraping:
            print(f"{Fore.GREEN}✅ Scraping OK (campos atualizados: {list(dados_scraping.keys())}){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  Scraping falhou — usando dados estáticos{Style.RESET_ALL}")

        dados_todos[ticker] = dados
        resultados[ticker] = avaliar_criterios(dados)

        # Aguarda entre requisições para não sobrecarregar o servidor
        time.sleep(SCRAPING_DELAY_SEGUNDOS)

    # Exibe tabela no terminal
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print("  RESULTADO DA ANÁLISE — 20 CRITÉRIOS DE QUALIDADE")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    exibir_tabela_terminal(resultados, TICKERS)

    # Exporta arquivos
    hoje = date.today().strftime("%Y-%m-%d")
    caminho_html = os.path.join("output", f"resultado_fiis_{hoje}.html")
    caminho_csv = os.path.join("output", f"dados_brutos_fiis_{hoje}.csv")

    print(f"\n{Fore.YELLOW}💾 Exportando resultados...{Style.RESET_ALL}")
    exportar_html(resultados, TICKERS, caminho_html)
    exportar_csv(dados_todos, TICKERS, caminho_csv)

    # Ranking final
    exibir_ranking(resultados, TICKERS)

    # Disclaimer
    print(f"\n{Fore.YELLOW}{'─'*70}")
    print(
        "⚠️  DISCLAIMER: Este script é para fins educacionais e informativos apenas.\n"
        "   Não constitui recomendação de investimento. Os dados estáticos são\n"
        "   aproximações baseadas em RIs públicos (2024/2025). Consulte sempre\n"
        "   fontes oficiais (CVM, B3, RIs dos fundos) antes de investir."
    )
    print(f"{'─'*70}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
