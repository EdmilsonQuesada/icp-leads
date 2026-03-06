import re
import logging
from datetime import datetime, date
from app.core.config import settings

logger = logging.getLogger(__name__)

MONTH_MAP = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

class FacebookEnricher:
    def _parse_birthdate(self, text: str) -> date | None:
        if not text:
            return None

        # Formato DD/MM/YYYY ou DD-MM-YYYY
        match = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", text)
        if match:
            try:
                return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
            except ValueError:
                pass

        # Formato "15 de março de 1990"
        match = re.search(
            r"(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?",
            text.lower()
        )
        if match:
            day = int(match.group(1))
            month = MONTH_MAP.get(match.group(2))
            year = int(match.group(3)) if match.group(3) else None
            if month:
                try:
                    return date(year or datetime.now().year, month, day)
                except ValueError:
                    pass
        return None

    async def enrich(self, name: str, username: str) -> dict:
        """Tenta encontrar perfil público no Facebook e extrair dados demográficos."""
        result = {"birthdate": None, "age": None, "city": None, "source": "facebook"}

        if not settings.FACEBOOK_EMAIL:
            logger.info("Facebook enrichment desativado (sem credenciais)")
            return result

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()

                search_url = f"https://www.facebook.com/search/people?q={name.replace(' ', '+')}"
                await page.goto(search_url, timeout=15000)
                await page.wait_for_timeout(3000)

                content = await page.content()
                birthdate = self._parse_birthdate(content)
                if birthdate:
                    result["birthdate"] = birthdate
                    result["age"] = datetime.now().year - birthdate.year

                await browser.close()

        except Exception as e:
            logger.warning(f"Facebook enrichment falhou para {name}: {e}")

        return result
