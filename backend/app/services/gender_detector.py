"""
Detector de gênero baseado em nome brasileiro.
Retorna (gender: str, confidence: int) onde gender é 'F', 'M' ou 'ND'
e confidence é 0-100.
"""

# Nomes femininos brasileiros comuns
FEMALE_NAMES = {
    "ana", "maria", "julia", "julia", "luiza", "luisa", "beatriz", "amanda",
    "fernanda", "gabriela", "gabrielle", "camila", "patricia", "patricia",
    "aline", "andressa", "bruna", "carolina", "carla", "claudia", "cristiane",
    "daniela", "deborah", "debora", "diana", "elaine", "eliana", "erica",
    "fabiana", "flavia", "franciele", "francesca", "giovana", "graciela",
    "helen", "helena", "ingrid", "isabela", "isabele", "jessica", "joana",
    "josiane", "karina", "katia", "kelly", "larissa", "laura", "leticia",
    "livia", "lorena", "lucia", "luciana", "magda", "mara", "marcela",
    "marcia", "marina", "marisa", "marta", "melissa", "michele", "milena",
    "nadia", "natalia", "natasha", "nicole", "pamela", "paula", "priscila",
    "rafaela", "rebeca", "renata", "rosa", "rosana", "rosangela", "sabrina",
    "sandra", "sara", "sarah", "simone", "solange", "stefania", "stephanie",
    "susana", "tatiana", "tais", "thalita", "thais", "valeria", "vanessa",
    "vera", "veronica", "viviane", "wanessa", "yasmin", "yara",
    # Diminutivos/apelidos femininos comuns
    "nanda", "bela", "bia", "lara", "isa", "gabi", "dani", "cris", "carol",
    "bru", "tati", "rafa", "lulu", "lulinha", "nana", "vivi",
}

# Nomes masculinos brasileiros comuns
MALE_NAMES = {
    "joao", "jose", "pedro", "paulo", "carlos", "antonio", "marcos",
    "lucas", "mateus", "matheus", "gabriel", "rafael", "daniel", "felipe",
    "guilherme", "henrique", "igor", "ivan", "jorge", "julio", "fabio",
    "fernando", "francisco", "gustavo", "leandro", "leonardo", "luis",
    "luiz", "marcelo", "mario", "mauricio", "miguel", "nelson", "nilson",
    "patrick", "rafael", "raimundo", "renato", "ricardo", "roberto",
    "rodrigo", "rogerio", "ronaldo", "sergio", "tiago", "thiago",
    "vagner", "vitor", "victor", "wagner", "walter", "wellington",
    "willian", "william", "wilson", "caio", "claudio", "cleverton",
    "davi", "david", "diego", "dylan", "eder", "edson", "eduardo",
    "elias", "emerson", "eric", "erick", "everton", "ezequiel",
    "flavio", "frederico", "giovani", "giovanni", "heitor", "herbert",
    "jardel", "jean", "jefferson", "jonathan", "jonatas",
    "kaio", "kaique", "kayque", "laercio", "luan", "murilo",
    "nathan", "nicolas", "oberon", "otavio", "renan", "samuel",
    "theo", "thales", "ubiratan", "vinicius", "yago",
    # Diminutivos/apelidos masculinos
    "rafa", "guga", "kaka", "neto", "beto", "zé", "ze", "kiko",
    "dudu", "duda", "leko", "teco",
}

# Sufixos que indicam gênero (para nomes não encontrados na lista)
# Alta confiança: terminações muito fortes
FEMALE_ENDINGS_HIGH = ("inha", "ella", "ette", "isse")
MALE_ENDINGS_HIGH = ("inho", "aldo", "ardo", "erto", "undo", "ando")

# Média confiança: terminações comuns mas não exclusivas
FEMALE_ENDINGS_MED = ("a",)
MALE_ENDINGS_MED = ("o", "os", "on", "er", "el")


def _normalize(name: str) -> str:
    """Normaliza nome: lowercase, remove acentos."""
    import unicodedata
    name = name.lower().strip()
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    return name


def detect_gender(full_name: str | None) -> tuple[str, int]:
    """
    Detecta gênero a partir do nome completo.
    Retorna (gender, confidence) onde:
    - gender: 'F', 'M' ou 'ND'
    - confidence: 0-100
    """
    if not full_name or not full_name.strip():
        return ("ND", 0)

    # Pegar apenas o primeiro nome
    first_name = _normalize(full_name.split()[0])

    if not first_name:
        return ("ND", 0)

    # Verificar em listas de nomes (alta confiança: 95%)
    if first_name in FEMALE_NAMES:
        return ("F", 95)
    if first_name in MALE_NAMES:
        return ("M", 95)

    # Verificar sufixos de alta confiança (85%)
    for ending in FEMALE_ENDINGS_HIGH:
        if first_name.endswith(ending):
            return ("F", 85)
    for ending in MALE_ENDINGS_HIGH:
        if first_name.endswith(ending):
            return ("M", 85)

    # Verificar sufixos de média confiança (70%)
    for ending in FEMALE_ENDINGS_MED:
        if first_name.endswith(ending) and len(first_name) > 3:
            return ("F", 70)
    for ending in MALE_ENDINGS_MED:
        if first_name.endswith(ending) and len(first_name) > 2:
            return ("M", 70)

    # Não determinado
    return ("ND", 0)
