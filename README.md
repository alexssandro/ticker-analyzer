# 📊 Ticker Analyzer — Análise de FIIs

Análise automatizada de **Fundos Imobiliários (FIIs)** brasileiros com base em 20 critérios de qualidade.

## ⚙️ Pré-requisitos

- Python 3.8+
- pip

## 🚀 Instalação

```bash
git clone https://github.com/alexssandro/ticker-analyzer.git
cd ticker-analyzer
pip install -r requirements.txt
```

## ▶️ Como usar

```bash
python analyzer.py
```

Os resultados serão gerados na pasta `output/`:
- `resultado_fiis_YYYY-MM-DD.html` — Tabela visual colorida
- `dados_brutos_fiis_YYYY-MM-DD.csv` — Dados numéricos brutos

## 📋 Critérios analisados

| # | Critério |
|---|----------|
| 1 | Imóveis em regiões nobres |
| 2 | Propriedades novas (< 15 anos) |
| 3 | P/VP abaixo de 1,0 (descarte automático acima de 1,5) |
| 4 | Dividendos consistentes há mais de 4 anos |
| 5 | Sem dependência de único inquilino (< 30%) |
| 6 | Dividend Yield acima da média do setor |
| 7 | Gestão sem uso de derivativos/opções |
| 8 | Dívida líquida/PL < 50% |
| 9 | Menos de 4 anos de lucro para quitar dívidas |
| 10 | Vacância < 10% |
| 11 | Menos de 10% em cotas de outros FIIs |
| 12 | Cap Rate > 8% a.a. |
| 13 | Cota patrimonial valorizada nos últimos 3 anos |
| 14 | Imóveis em pelo menos 3 estados |
| 15 | Taxa de adm + gestão < 1,5% a.a. |
| 16 | Menos de 2 emissões nos últimos 24 meses |
| 17 | Liquidez média diária > R$ 1 milhão |
| 18 | Mais de 70% dos inquilinos investment grade |
| 19 | Prazo médio dos contratos > 5 anos |
| 20 | Reserva de pelo menos 1 mês de distribuição |

## ⚠️ Disclaimer

Este projeto é para fins educacionais e informativos apenas. Não constitui recomendação de investimento. Os dados estáticos são aproximações baseadas em RIs públicos e podem não refletir a situação atual dos fundos. Sempre consulte fontes oficiais como CVM, B3 e os RIs dos próprios fundos antes de tomar decisões de investimento.

## 📦 FIIs analisados

GGRC11, BTAL11, VISC11, ALZR11, BTLG11, HGLG11, TRXF11, RZTR11, BRCO11, JURO11
