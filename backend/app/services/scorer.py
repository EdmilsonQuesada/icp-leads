from dataclasses import dataclass

INTENTION_KEYWORDS = [
    # intenção explícita de contratar/agendar
    "quero fazer sessão", "quero agendar", "como faço sessão",
    "onde encontro terapeuta", "onde agendar", "quanto custa",
    "quero marcar", "como me inscrevo", "quero uma sessão",
    "quero sessão", "agendar sessão", "como faço para",
    # busca ativa por ajuda
    "preciso de ajuda", "preciso muito", "estou precisando",
    "estou sofrendo", "estou passando por", "situação difícil",
    "não sei o que fazer", "alguém me ajuda", "por favor me ajuda",
    "quero tentar", "vou tentar", "vou fazer",
    # interesse genuíno / experiência positiva
    "me ajudou muito", "mudou minha vida", "transformou",
    "quero participar", "participei", "fiz a constelação",
    "fiz uma sessão", "já fiz", "tenho vontade", "tenho interesse",
    "onde posso fazer", "como funciona", "quero saber mais",
    "gostaria de fazer", "gostaria de participar",
    # expressão emocional de busca
    "preciso curar", "quero curar", "busco cura",
    "busco paz", "quero paz", "quero me libertar",
    "estou buscando", "estou procurando ajuda",
]

NEGATIVE_KEYWORDS = [
    "é vudu", "e vudu", "é diabo", "e diabo", "coisa do diabo",
    "é satânico", "e satanico", "é macumba", "e macumba",
    "é mentira", "e mentira", "é fraude", "e fraude",
    "é charlatanice", "pseudociência", "pseudociencia",
    "não acredito", "nao acredito", "balela", "bobagem",
    "não funciona", "nao funciona", "enganação", "enganacao",
    "não vale", "nao vale", "perda de tempo",
]

SPIRITUAL_BIO_KEYWORDS = [
    "terapia", "autoconhecimento", "cura", "espiritualidade",
    "constelação", "meditação", "yoga", "ayurveda", "xamanismo",
    "alma", "despertar", "consciência", "equilíbrio", "holístico",
    "psicologia", "terapeuta", "coach", "desenvolvimento pessoal",
]

@dataclass
class ScoreResult:
    engagement_score: int
    intention_score: int
    profile_score: int
    total: int
    category: str

class LeadScorer:
    def _classify(self, total: int) -> str:
        if total >= 75:
            return "quente"
        elif total >= 50:
            return "morno"
        elif total >= 25:
            return "frio"
        return "descarte"

    def _calc_engagement(self, events: list[dict]) -> int:
        if not events:
            return 0
        score = 0
        # até 30 pts por frequência (10 pts por evento, máx 3 eventos contados)
        score += min(len(events) * 10, 30)
        # bônus por tipo "comment" (engajamento mais forte)
        comment_count = sum(1 for e in events if e.get("type") == "comment")
        score += min(comment_count * 5, 10)
        # variedade de contextos
        variety = len(set(e.get("context", "") for e in events))
        score += min(variety * 2, 6)
        return min(score, 40)

    def _is_negative(self, text: str) -> bool:
        text = text.lower()
        return any(kw in text for kw in NEGATIVE_KEYWORDS)

    def _calc_intention(self, comments: list[dict]) -> int:
        if not comments:
            return 0
        score = 0
        for comment in comments:
            text = comment.get("text", "").lower()
            if self._is_negative(text):
                continue
            for kw in INTENTION_KEYWORDS:
                if kw in text:
                    score += 15
                    break
        return min(score, 35)

    def _calc_profile(self, lead: dict) -> int:
        score = 0
        if lead.get("country") == "BR":
            score += 10
        if not lead.get("is_business", False):
            score += 5
        followers = lead.get("followers", 0)
        if 100 <= followers <= 10000:
            score += 5
        bio = lead.get("bio", "").lower()
        for kw in SPIRITUAL_BIO_KEYWORDS:
            if kw in bio:
                score += 5
                break
        return min(score, 25)

    def score(self, lead: dict) -> ScoreResult:
        eng = self._calc_engagement(lead.get("engagement_events", []))
        intention = self._calc_intention(lead.get("comments", []))
        profile = self._calc_profile(lead)
        total = eng + intention + profile
        return ScoreResult(
            engagement_score=eng,
            intention_score=intention,
            profile_score=profile,
            total=total,
            category=self._classify(total),
        )
