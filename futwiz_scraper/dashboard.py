import argparse, time, pandas as pd
from pathlib import Path
from .utils import now_iso

HTML = '''<!doctype html>
<html><head><meta charset="utf-8"><title>FUTWIZ V2 — Console</title>
<meta http-equiv="refresh" content="{refresh}">
<style>
body{{font-family:system-ui,Segoe UI,Arial,Helvetica,sans-serif;background:#101010;color:#eee;margin:16px}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #2b2b2b;padding:8px;font-size:14px}}
th{{background:#1b1b1b;position:sticky;top:0}}
tr:nth-child(even){{background:#161616}}
.bad{{color:#ff7676}} .good{{color:#8fff9f}} .warn{{color:#ffd166}} .muted{{color:#aaa;font-size:12px}}
.tag{{display:inline-block;padding:2px 6px;border-radius:6px;background:#222;margin-left:6px;font-size:12px}}
.sig{{background:#16381e;color:#9cffb0}}
</style></head><body>
<h2>FUTWIZ V2 — Quick Flips Console<span class="tag">PC</span></h2>
<div class="muted">Updated: {now}</div>
<h3>Oportunidades (últimas 24h)</h3>
<table><thead><tr>
<th>Player</th><th>Cur</th><th>Alvo</th><th>Lucro Líquido</th><th>Margem</th><th>Motivo</th><th>Link</th>
</tr></thead><tbody>
{sig_rows}
</tbody></table>

<h3>Mercado (agregado do seu histórico)</h3>
<table><thead><tr>
<th>Player</th><th>Current</th><th>% vs 3h</th><th>3h Avg</th>
<th>Low 12h</th><th>% from Low</th><th>High 6h</th><th>High 12h</th><th>Sold (PC)</th>
</tr></thead><tbody>
{rows}
</tbody></table>
</body></html>'''

def fmtc(x):
    if pd.isna(x): return ""
    try: return f"{int(x):,}".replace(",", ".")
    except: return str(x)

def pct(x):
    return "" if pd.isna(x) else f"{x:.2f}%"

def read_concat(glob):
    frames = []
    for p in sorted(glob):
        try:
            if p.stat().st_size == 0: continue
            frames.append(pd.read_csv(p))
        except Exception:
            continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def build_tables(logs: Path):
    hist = read_concat(list(logs.glob("history_*.csv")))
    sigs = read_concat(list(logs.glob("signals_*.csv")))

    sig_rows_html = "<tr><td colspan='7'>Sem sinais recentes.</td></tr>"
    if not sigs.empty:
        sigs = sigs.sort_values(["timestamp","margin_pct"], ascending=[False, False]).head(100)
        out=[]
        for _,r in sigs.iterrows():
            out.append(f"<tr class='sig'><td>{r.get('name','')}</td>"
                       f"<td>{fmtc(r.get('current_pc'))}</td>"
                       f"<td>{fmtc(r.get('target'))}</td>"
                       f"<td>{fmtc(r.get('net_profit'))}</td>"
                       f"<td>{pct(r.get('margin_pct'))}</td>"
                       f"<td>{r.get('reason','')}</td>"
                       f"<td><a style='color:#9cf' target='_blank' href='{r.get('source_url','')}'>futwiz</a></td></tr>")
        sig_rows_html = "\n".join(out)

    rows_html = "<tr><td colspan='9'>Sem histórico suficiente. Rode o monitor primeiro.</td></tr>"
    if not hist.empty:
        hist['timestamp'] = pd.to_datetime(hist['timestamp'], errors='coerce')
        hist = hist.dropna(subset=['timestamp'])
        now = pd.Timestamp.utcnow()
        recent = hist[hist['timestamp'] >= now - pd.Timedelta(hours=24)]
        out=[]
        for url, g in recent.groupby('source_url'):
            g=g.sort_values('timestamp')
            last = g.iloc[-1]
            g3 = g[g['timestamp'] >= now - pd.Timedelta(hours=3)]
            g6 = g[g['timestamp'] >= now - pd.Timedelta(hours=6)]
            g12= g[g['timestamp'] >= now - pd.Timedelta(hours=12)]
            avg3 = g3['current_pc'].mean()
            low12= g12['current_pc'].min()
            high6= g6['current_pc'].max()
            high12= g12['current_pc'].max()
            cur = last['current_pc']
            pct3 = ((cur-avg3)/avg3*100) if pd.notna(avg3) and avg3>0 else None
            pfl  = ((cur-low12)/low12*100) if pd.notna(low12) and low12>0 else None
            cls = "good" if (pct3 or 0)>=0 else "bad"
            out.append(f"<tr><td>{last.get('name','')}</td>"
                       f"<td>{fmtc(cur)}</td>"
                       f"<td class='{cls}'>{pct(pct3)}</td>"
                       f"<td>{fmtc(avg3)}</td><td>{fmtc(low12)}</td><td>{pct(pfl)}</td>"
                       f"<td>{fmtc(high6)}</td><td>{fmtc(high12)}</td>"
                       f"<td><a style='color:#9cf' target='_blank' href='{url.rstrip('/') + '/soldprices/pc'}'>sold</a></td></tr>")
        rows_html = "\n".join(out)

    return sig_rows_html, rows_html

def main():
    ap = argparse.ArgumentParser(description="Dashboard HTML (historico + sinais)")
    ap.add_argument("--logs", default=str(Path(__file__).parents[1]/"logs"))
    ap.add_argument("--outdir", default=str(Path(__file__).parents[1]/"console"))
    ap.add_argument("--refresh", type=int, default=30)
    ap.add_argument("--loop", action="store_true")
    args = ap.parse_args()

    logs = Path(args.logs); outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    def once():
        sig_rows, rows = build_tables(logs)
        html = HTML.format(refresh=args.refresh, now=now_iso(), sig_rows=sig_rows, rows=rows)
        (outdir/"index.html").write_text(html, encoding="utf-8")
        print(f"Dashboard -> {outdir/'index.html'}")

    if args.loop:
        try:
            while True:
                once()
                time.sleep(max(10, args.refresh))
        except KeyboardInterrupt:
            print("Encerrado.")
    else:
        once()

if __name__ == "__main__":
    main()
