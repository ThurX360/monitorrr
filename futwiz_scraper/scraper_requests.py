import requests
from bs4 import BeautifulSoup

class RequestsScraper:
    def __init__(self, base_url: str, headers: dict, selectors: dict, timeout=20):
        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.selectors = selectors
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, url: str):
        url = (url or "").strip()
        r = self.session.get(url, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return r.text

    def scrape_player_pc(self, url: str):
        html = self._get(url)
        soup = BeautifulSoup(html, "html.parser")
        def pick(sel):
            el = soup.select_one(sel)
            return el.get_text(strip=True) if el else ""
        return {
            "name": pick(self.selectors.get("name",".card-26-name")),
            "rating": pick(self.selectors.get("rating",".card-26-rating")),
            "position": pick(self.selectors.get("position",".card-26-position")),
            "pc_price": pick(self.selectors.get("price",".player-price-block.pc-block .price-num")),
        }

    def scrape_sold_averages_pc(self, player_url: str):
        url = player_url.rstrip("/") + "/soldprices/pc"
        html = self._get(url)
        soup = BeautifulSoup(html, "html.parser")
        def pick(sel):
            el = soup.select_one(sel)
            return el.get_text(strip=True) if el else ""
        return {"avg_bin": pick(self.selectors.get("sold_avg_bin","span.avgbin")),
                "avg_auction": pick(self.selectors.get("sold_avg_auction","span.avgauction")),
                "sold_url": url}
