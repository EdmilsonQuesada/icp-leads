import re
import logging
import asyncio
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class LinkedInEnricher:
    def _extract_city(self, location_text: str | None) -> str | None:
        if not location_text:
            return None
        parts = location_text.split(",")
        return parts[0].strip() if parts else location_text.strip()

    def _estimate_age_from_graduation_year(self, year: int) -> int:
        # Assume graduação ~22 anos
        return datetime.now().year - year + 22

    async def enrich(self, name: str) -> dict:
        """Enriquece perfil via LinkedIn (conservador - apenas perfis públicos via Google)."""
        result = {"city": None, "age": None, "source": "linkedin"}

        if not settings.LINKEDIN_EMAIL:
            logger.info("LinkedIn enrichment desativado (sem credenciais)")
            return result

        # Rate limit conservador para LinkedIn
        await asyncio.sleep(10)

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()

                # Busca pública via Google (evita login direto no LinkedIn)
                search_url = f"https://www.google.com/search?q=site:linkedin.com+\"{name}\"+Brasil"
                await page.goto(search_url, timeout=15000)
                await page.wait_for_timeout(5000)

                content = await page.content()

                # Extrai cidade se aparecer no snippet do Google
                city_match = re.search(
                    r"·\s*([A-ZÀ-Ú][a-zà-ú\s]+(?:,\s*[A-Z][a-z]+)?)\s*·",
                    content
                )
                if city_match:
                    result["city"] = self._extract_city(city_match.group(1))

                await browser.close()

        except Exception as e:
            logger.warning(f"LinkedIn enrichment falhou para {name}: {e}")

        return result
