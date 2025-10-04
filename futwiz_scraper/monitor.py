import argparse, time, pandas as pd
from pathlib import Path
import yaml
from .utils import now_iso, append_csv, month_path
from .scraper_requests import RequestsScraper

EA_TAX = 0.05

def to_int(x):
    try: return int(str(x).replace(",","").strip())
    except: return None

def main():
    ap = argparse.ArgumentParser(description="FUTWIZ monitor (loop + signals) — PC only")
    ap.add_argument("--input", required=True, help="CSV com coluna 'url'")
    ap.add_argument("--sleep-min", type=int, default=7, help="Intervalo entre coletas (min)")
    ap.add_argument("--buy-discount", type=float, default=0.12, help="Desconto vs alvo (0.12=12%% abaixo)")
    ap.add_argument("--sell-price", choices=["avg_bin","avg_auction"], default="avg_bin", help="Preço alvo")
    ap.add_argument("--min-profit", type=int, default=1500, help="Lucro líquido mínimo")
    ap.add_argument("--min-margin", type=float, default=5.0, help="Margem mínima %%")
    ap.add_argument("--max-price", type=int, default=999999, help="Ignorar cartas acima deste preço atual")
    ap.add_argument("--once", action="store_true", help="Executa uma rodada e sai")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(Path(__file__).with_name("config.yaml"), "r", encoding="utf-8"))
    headers = {"User-Agent": cfg.get("user_agent")}
    scraper = RequestsScraper(base_url=cfg.get("base_url"), headers=headers, selectors=cfg.get("selectors",{}))

    log_dir = str(Path(__file__).parents[1] / "logs")
    hist_path = month_path(log_dir, "history")
    sig_path = month_path(log_dir, "signals")

    def run_once():
        try:
            urls = pd.read_csv(args.input)["url"].dropna().tolist()
        except Exception as e:
            print(f"Erro abrindo {args.input}: {e}")
            return 0, 0

        rows, sigs = [], []
        ts = now_iso()
        for u in urls:
            try:
                p = scraper.scrape_player_pc(u)
                s = scraper.scrape_sold_averages_pc(u)
            except Exception as e:
                print(f"Falha em {u}: {e}")
                continue

            name, rating, pos = p.get("name",""), p.get("rating",""), p.get("position","")
            cur = to_int(p.get("pc_price"))
            avgbin = to_int(s.get("avg_bin"))
            avgauc = to_int(s.get("avg_auction"))
            target = avgbin if args.sell_price=="avg_bin" else avgauc

            row = {"timestamp": ts, "name": name, "rating": rating, "position": pos,
                   "current_pc": cur, "avg_bin": avgbin, "avg_auction": avgauc,
                   "target": target, "source_url": u}
            rows.append(row)

            if cur and target and cur <= args.max_price:
                net_after_tax = int(target * (1.0 - EA_TAX))
                net_profit = net_after_tax - cur
                margin = (net_profit / cur * 100) if cur > 0 else 0
                threshold = int(target * (1.0 - args.buy_discount))
                if cur <= threshold and net_profit >= args.min_profit and margin >= args.min_margin:
                    sigs.append({**row, "net_profit": net_profit, "margin_pct": round(margin,2),
                                 "reason": f"<= {(1-args.buy_discount)*100:.1f}% do {args.sell_price}, lucro≥{args.min_profit}, margem≥{args.min_margin}%"})

        if rows:
            append_csv(hist_path, pd.DataFrame(rows))
        if sigs:
            append_csv(sig_path, pd.DataFrame(sigs))
        print(f"[{ts}] Coletados: {len(rows)} | Sinais: {len(sigs)} | hist={hist_path} | sig={sig_path}")
        return len(rows), len(sigs)

    if args.once:
        run_once()
    else:
        try:
            while True:
                run_once()
                time.sleep(max(60, args.sleep-min*60) if False else args.sleep_min*60)
        except KeyboardInterrupt:
            print("\nMonitor encerrado.")

if __name__ == "__main__":
    main()
