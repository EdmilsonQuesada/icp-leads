#!/usr/bin/env python
"""
Test script: Apify API Integration
Testa a coleta de dados do Instagram via Apify
"""
from apify_client import ApifyClient
import json

# Your Apify token
api_token = "YOUR_APIFY_API_TOKEN_HERE"

print("=" * 70)
print("🚀 TESTE DE API APIFY - INSTAGRAM HASHTAG SCRAPER")
print("=" * 70)

try:
    # Initialize client
    print("\n1️⃣ Inicializando cliente Apify...")
    client = ApifyClient(api_token)
    print("   ✅ Cliente criado com sucesso")

    # Prepare input
    run_input = {
        "hashtags": ["constelação familiar"],
        "searchPostsFirst": True,
        "postsPerHashtag": 5,  # Small number for quick test
    }

    print("\n2️⃣ Iniciando ator (Instagram Hashtag Scraper)...")
    print(f"   Input: {json.dumps(run_input, indent=2)}")

    # Run actor
    actor_run = client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)

    print(f"\n3️⃣ Ator finalizado!")
    print(f"   Status: {actor_run['status']}")
    print(f"   Run ID: {actor_run['id']}")
    print(f"   Dataset ID: {actor_run['defaultDatasetId']}")

    # Fetch results
    print(f"\n4️⃣ Buscando resultados do dataset...")
    dataset = client.dataset(actor_run["defaultDatasetId"])
    items = dataset.list_items().items

    print(f"   📊 Total de items: {len(items)}")

    if items:
        print(f"\n5️⃣ Estrutura do primeiro item (POST):")
        print("   " + "=" * 66)
        print(json.dumps(items[0], indent=2, ensure_ascii=False))
        print("   " + "=" * 66)

        # Analyze structure
        print(f"\n6️⃣ ANÁLISE DA ESTRUTURA:")
        first_item = items[0]

        print(f"\n   📌 Post Author:")
        if "owner" in first_item:
            owner = first_item["owner"]
            print(f"      - username: {owner.get('username')}")
            print(f"      - name: {owner.get('name')}")
            print(f"      - followers: {owner.get('followers')}")

        print(f"\n   💬 Comments: {len(first_item.get('comments', []))} found")
        if first_item.get('comments'):
            print(f"      First commenter: {first_item['comments'][0].get('owner', {}).get('username')}")

        print(f"\n   📝 Post Fields Available:")
        for key in first_item.keys():
            print(f"      - {key}")

        print(f"\n✅ SUCESSO! Apify está funcionando corretamente!")
        print(f"   Você pode usar esses dados para criar leads no seu sistema")

    else:
        print("⚠️  Nenhum item encontrado no resultado")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    print(f"   Tipo: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
