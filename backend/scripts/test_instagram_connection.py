"""
Script de diagnóstico: Testa conectividade com Instagram
Útil para identificar se é rate limit, IP bloqueado ou outro problema
"""
import sys
import time

sys.path.insert(0, "/app")
from app.core.config import settings

def test_connection():
    from instagrapi import Client
    import json

    username = settings.INSTAGRAM_USERNAME
    password = settings.INSTAGRAM_PASSWORD

    print("=" * 60)
    print("🔍 TESTE DE CONECTIVIDADE COM INSTAGRAM")
    print("=" * 60)
    print(f"⏱️  Início: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📱 Username: @{username}\n")

    cl = Client()

    # Teste 1: Conexão básica
    print("1️⃣  Testando conexão básica...")
    try:
        # Tenta fazer uma requisição simples
        cl.get_timeline_feed()
        print("   ✅ Conexão OK (conseguiu acessar timeline)")
        return True
    except Exception as e:
        error_str = str(e).lower()

        if "json" in error_str or "expecting value" in error_str:
            print("   ❌ RESPOSTA HTTP INVÁLIDA (Instagram retornou HTML/vazio)")
            print("      Causas prováveis:")
            print("      → Rate limit ainda ativo")
            print("      → IP bloqueado")
            print("      → Cloudflare/WAF ativo")
            return False

        elif "429" in error_str or "rate" in error_str.lower():
            print("   ❌ RATE LIMITED (429 Too Many Requests)")
            print("      Aguarde mais alguns minutos...")
            return False

        elif "403" in error_str or "forbidden" in error_str:
            print("   ❌ ACESSO PROIBIDO (403 Forbidden)")
            print("      IP ou conta podem estar bloqueados")
            return False

        elif "connection" in error_str or "timeout" in error_str:
            print("   ❌ PROBLEMA DE CONECTIVIDADE")
            print("      Verifique conexão de rede do container")
            return False
        else:
            print(f"   ❌ ERRO: {type(e).__name__}: {e}")
            return False

def retry_with_backoff(max_attempts=5):
    """Tenta múltiplas vezes com espera crescente"""
    print("\n🔄 RETRY COM BACKOFF EXPONENCIAL")
    print("=" * 60)

    for attempt in range(1, max_attempts + 1):
        wait_time = min(2 ** (attempt - 1), 60)  # 1, 2, 4, 8, 16... segundos, máx 60

        print(f"\n🔁 Tentativa {attempt}/{max_attempts}...")

        if test_connection():
            print(f"\n✅ SUCESSO na tentativa {attempt}!")
            return True

        if attempt < max_attempts:
            print(f"   ⏳ Aguardando {wait_time}s antes de próxima tentativa...")
            time.sleep(wait_time)

    print("\n❌ Falha em todas as tentativas.")
    print("\n📋 RECOMENDAÇÕES:")
    print("   1. Aguarde 15-30 minutos antes de tentar novamente")
    print("   2. Se Instagram continuar bloqueado:")
    print("      - Acesse pelo celular para desbloquear")
    print("      - Verifique alertas de segurança")
    print("      - Considere usar conta separada (como você sugeriu)")
    return False

if __name__ == "__main__":
    if not retry_with_backoff(max_attempts=3):
        sys.exit(1)

    print(f"\n⏱️  Fim: {time.strftime('%Y-%m-%d %H:%M:%S')}")
