"""
Script de login único no Instagram com suporte a 2FA.
Salva a sessão em /app/instagram_session.json para uso posterior.

Uso:
    docker compose exec -it backend python scripts/instagram_login.py
"""
import sys
import os

SESSION_PATH = "/app/instagram_session.json"


def main():
    from instagrapi import Client
    from instagrapi.exceptions import TwoFactorRequired, BadPassword, ChallengeRequired
    import time
    import json

    # Lê credenciais do .env via pydantic-settings
    sys.path.insert(0, "/app")
    from app.core.config import settings

    username = settings.INSTAGRAM_USERNAME
    password = settings.INSTAGRAM_PASSWORD

    if not username or not password:
        print("❌ INSTAGRAM_USERNAME e INSTAGRAM_PASSWORD não estão definidos no .env")
        sys.exit(1)

    print(f"⏱️  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔐 Username: @{username}")

    cl = Client()

    # Tenta carregar sessão existente para reaproveitar cookies
    if os.path.exists(SESSION_PATH):
        print(f"📂 Sessão existente encontrada em {SESSION_PATH}. Carregando...")
        try:
            cl.load_settings(SESSION_PATH)
            print("   ✅ Sessão carregada com sucesso")
        except Exception as e:
            print(f"   ⚠️  Erro ao carregar sessão (ignorando): {e}")

    print(f"🔐 Tentando login...")

    try:
        print("   → Enviando credenciais para Instagram...")
        cl.login(username, password)
        print("✅ Login bem-sucedido!")

    except TwoFactorRequired:
        print("📱 Autenticação de dois fatores necessária.")
        code = input("   Digite o código 2FA do seu aplicativo autenticador: ").strip()
        try:
            print("   → Enviando código 2FA...")
            cl.login(username, password, verification_code=code)
            print("✅ Login com 2FA bem-sucedido!")
        except Exception as e:
            print(f"❌ Falha no login com 2FA: {e}")
            print(f"   Tipo do erro: {type(e).__name__}")
            sys.exit(1)

    except ChallengeRequired:
        print("⚠️  Instagram solicitou verificação por e-mail ou SMS.")
        print("   Acesse o Instagram pelo celular, complete a verificação e tente novamente.")
        sys.exit(1)

    except BadPassword:
        print("❌ Senha incorreta. Verifique o INSTAGRAM_PASSWORD no .env")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")
        print(f"   String do erro: {str(e)}")

        # Se for erro JSON, pode ser rate limit
        if "json" in str(e).lower() or "expecting value" in str(e).lower():
            print("\n⚠️  DIAGNÓSTICO: Parece ser erro de resposta HTTP inválida")
            print("   Possíveis causas:")
            print("   1. Rate limit ainda ativo (aguarde mais alguns minutos)")
            print("   2. IP bloqueado pelo Instagram")
            print("   3. Problema de conectividade")
            print("\n   Sugestão: Aguarde 5-10 minutos e tente novamente")
        sys.exit(1)

    # Salva sessão
    cl.dump_settings(SESSION_PATH)
    print(f"💾 Sessão salva em {SESSION_PATH}")
    print("   Os próximos logins não precisarão de 2FA.")

    # Verifica se funcionou
    user = cl.user_info_by_username(username)
    print(f"✅ Verificado: conta @{user.username} com {user.follower_count} seguidores")


if __name__ == "__main__":
    main()
