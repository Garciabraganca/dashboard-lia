#!/usr/bin/env python3
"""
Script para verificar a conexão com a API Meta Ads
Executa diagnósticos e exibe o status da conexão
"""

import sys
from config import Config
from meta_integration import MetaAdsIntegration


def print_separator(char="-", length=60):
    print(char * length)


def print_header(title):
    print_separator("=")
    print(f"  {title}")
    print_separator("=")


def main():
    print_header("VERIFICAÇÃO DE CONEXÃO META ADS")
    print()

    # 1. Verificar configuração das credenciais
    print("[1/3] Verificando credenciais...")
    print_separator()

    token = Config.get_meta_access_token()
    account_id = Config.get_meta_ad_account_id()

    token_status = "✓ Configurado" if token else "✗ NÃO CONFIGURADO"
    token_preview = f"...{token[-10:]}" if token and len(token) > 10 else "(vazio)"

    print(f"  META_ACCESS_TOKEN: {token_status}")
    if token:
        print(f"    Preview: {token_preview}")

    print(f"  META_AD_ACCOUNT_ID: {account_id or '(não configurado)'}")
    print()

    if not token:
        print("❌ ERRO: Token de acesso não configurado!")
        print()
        print("Para configurar, defina a variável de ambiente:")
        print("  export META_ACCESS_TOKEN='seu_token_aqui'")
        print()
        print("Ou adicione ao arquivo .streamlit/secrets.toml:")
        print('  META_ACCESS_TOKEN = "seu_token_aqui"')
        print()
        return 1

    # 2. Inicializar cliente e testar conexão
    print("[2/3] Testando conexão com a API Meta...")
    print_separator()

    try:
        client = MetaAdsIntegration(
            access_token=token,
            ad_account_id=account_id
        )

        result = client.verify_connection()

        if result["connected"]:
            print(f"  ✓ {result['message']}")
            print()
            print("  Informações da conta:")
            info = result["account_info"]
            print(f"    ID:        {info.get('id', 'N/A')}")
            print(f"    Nome:      {info.get('name', 'N/A')}")
            print(f"    Empresa:   {info.get('business_name', 'N/A')}")
            print(f"    Status:    {info.get('status', 'N/A')}")
            print(f"    Moeda:     {info.get('currency', 'N/A')}")
            print(f"    Timezone:  {info.get('timezone', 'N/A')}")
        else:
            print(f"  ✗ {result['message']}")
            if result["error_code"]:
                print(f"    Código do erro: {result['error_code']}")
            if result["error_details"]:
                print(f"    Detalhes: {result['error_details']}")

    except Exception as e:
        print(f"  ✗ Erro ao inicializar cliente: {str(e)}")
        return 1

    print()

    # 3. Testar busca de campanhas (se conexão OK)
    if result["connected"]:
        print("[3/3] Testando busca de campanhas...")
        print_separator()

        try:
            campaigns = client.get_campaigns()
            if not campaigns.empty:
                print(f"  ✓ {len(campaigns)} campanha(s) encontrada(s)")
                print()
                print("  Campanhas ativas:")
                for _, row in campaigns.head(5).iterrows():
                    name = row.get('name', 'N/A')
                    status = row.get('effective_status', 'N/A')
                    print(f"    - {name} ({status})")
                if len(campaigns) > 5:
                    print(f"    ... e mais {len(campaigns) - 5} campanha(s)")
            else:
                print("  ⚠ Nenhuma campanha ativa encontrada")
                print("    (Isso pode ser normal se não houver campanhas ativas)")

        except Exception as e:
            print(f"  ✗ Erro ao buscar campanhas: {str(e)}")

        print()

        # Testar busca de insights
        print("  Testando busca de insights (últimos 7 dias)...")
        try:
            insights = client.get_ad_insights(date_range="last_7d")
            if not insights.empty:
                total_spend = insights['spend'].sum() if 'spend' in insights.columns else 0
                total_impressions = insights['impressions'].sum() if 'impressions' in insights.columns else 0
                print(f"  ✓ Insights obtidos com sucesso")
                print(f"    Gasto total: ${total_spend:,.2f}")
                print(f"    Impressões: {total_impressions:,.0f}")
            else:
                print("  ⚠ Nenhum insight encontrado para o período")
        except Exception as e:
            print(f"  ✗ Erro ao buscar insights: {str(e)}")

    else:
        print("[3/3] Pulando teste de campanhas (conexão não estabelecida)")
        print_separator()

    print()
    print_separator("=")

    if result["connected"]:
        print("✅ RESULTADO: Conexão com Meta Ads funcionando corretamente!")
        return 0
    else:
        print("❌ RESULTADO: Falha na conexão com Meta Ads")
        print()
        print("Possíveis soluções:")
        print("  1. Verifique se o token de acesso está válido")
        print("  2. Verifique se o ID da conta está correto")
        print("  3. Verifique as permissões do token no Meta Business Suite")
        print("  4. Gere um novo token se o atual expirou")
        return 1


if __name__ == "__main__":
    sys.exit(main())
