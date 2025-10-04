# FUTWIZ V2 — PC Only (Loop 7 min + Signals + Dashboard)

**O que faz**
- Coleta **preço de PC** + **médias** (Average BIN / Average Auction).
- Roda em **loop** (ex.: `--sleep-min 7`) e grava histórico.
- Gera **sinais de compra** com filtros (`--min-profit`, `--min-margin`, `--max-price`).
- Cria **dashboard HTML** mostrando métricas (3h avg, lows/highs) e **oportunidades**.

## Como usar (PowerShell)
```powershell
cd <PASTA>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1) edite data\player_urls.csv (coluna 'url')
# 2) rode o monitor em LOOP a cada 7 min:
python -m futwiz_scraper.monitor --input data\player_urls.csv --sleep-min 7 --buy-discount 0.12 --sell-price avg_bin --min-profit 1500 --min-margin 5 --max-price 999999

# (ou rode uma vez só para testar)
python -m futwiz_scraper.monitor --input data\player_urls.csv --once --buy-discount 0.12 --sell-price avg_bin --min-profit 1500 --min-margin 5

# 3) abra o dashboard (auto-refresh 30s)
python -m futwiz_scraper.dashboard --refresh 30 --loop
# Abre: console\index.html
```

### Notas
- Taxa EA de 5% aplicada ao preço de venda alvo.
- `--sell-price avg_bin` usa Average BIN como alvo (recomendado). Alternativa: `avg_auction`.
- Sinais são salvos em `logs/signals_YYYYMM.csv`. Histórico em `logs/history_YYYYMM.csv`.
