import httpx
import asyncio
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from langchain_mcp_adapters.client import MultiServerMCPClient
from google_oauth_class import GoogleOAuth2Auth 
from langchain_openai import ChatOpenAI
from google_authenticate import pegar_tokens_colab
from langchain.agents import create_agent
from dotenv import load_dotenv


### OBSERVAÇÃO: 
# Atualmente, o servidor MCP (Model Context Protocol) remoto oficial do Google Calendar 
# (cujo endpoint é calendarmcp.googleapis.com) está classificado como Developer Preview. 
# Isso significa que ele só pode ser ativado e utilizado por contas que foram aceitas 
# no Google Workspace Developer Preview Program.
#
# Sem estar no programa, você não conseguirá ativar o serviço do MCP no seu 
# projeto do Google Cloud. 
# 
# Veja mais detalhes em https://developers.google.com/workspace/preview?hl=pt-br

# Carrega as variáveis do arquivo .env
load_dotenv()

class GoogleAuthenticateTest():

    @staticmethod    
    async def teste_listar_calendario_google():
        print("--- Iniciando teste das credenciais e conexão com o Google Calendar ---")

        GOOGLE_ACCESS_TOKEN, GOOGLE_REFRESH_TOKEN = pegar_tokens_colab()

        # 1. Obter credenciais do google que estão no .env
        google_client_id = os.environ["GOOGLE_CLIENT_ID"]
        google_client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
        google_access_token = GOOGLE_ACCESS_TOKEN 
        google_refresh_token = GOOGLE_REFRESH_TOKEN 
        project_id = os.environ["PROJECT_ID"]
        openai_api_key = os.environ["OPENAI_API_KEY"]

        missing_creds = []
        if not google_client_id: missing_creds.append("GOOGLE_CLIENT_ID")
        if not google_client_secret: missing_creds.append("GOOGLE_CLIENT_SECRET")
        if not google_access_token: missing_creds.append("GOOGLE_ACCESS_TOKEN")
        if not google_refresh_token: missing_creds.append("GOOGLE_REFRESH_TOKEN")
        if not openai_api_key: missing_creds.append("OPENAI_API_KEY")
        if not project_id: missing_creds.append("PROJECT_ID")

        if missing_creds:
            print(f"❌ ERRO: As seguintes credenciais estão faltando no `userdata`: {', '.join(missing_creds)}.")
            return False

        try:
            # 2. Instanciar a classe oficial Credentials do Google
            google_credentials = Credentials(
                token=google_access_token,
                refresh_token=google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=google_client_id,
                client_secret=google_client_secret,
                quota_project_id=project_id
            )

            # 3. Tentar renovar as credenciais
            print("Verificando validade e tentando renovar o token de acesso, se necessário...")
            if not google_credentials.valid:
                google_credentials.refresh(Request())
            print("✅ Credenciais do Google (token de acesso) validadas/renovadas com sucesso.")

        except Exception as e:
            print(f"❌ As credenciais não foram cadastradas com sucesso: {e}")
            return False

        temp_mcp_client = None

        try:
            # 4. Configurar o MultiServerMCPClient da forma suportada pela v0.1.0
            temp_mcp_client = MultiServerMCPClient(
                {
                    "calendar": {
                        "transport": "http", # Nota: algumas implementações MCP exigem "sse" aqui. Se o erro persistir, tente trocar para "sse".
                        "url": "https://calendarmcp.googleapis.com/mcp/v1",
                        "auth": GoogleOAuth2Auth(google_credentials)
                    }
                }
            )

            # 5. Obter as ferramentas do calendário
            print("Obtendo ferramentas do Google Calendar...")
            calendar_tools = await temp_mcp_client.get_tools()

            list_calendars_tool_found = any(tool.name == 'list_calendars' for tool in calendar_tools)
            if not list_calendars_tool_found:
                print("❌ ERRO: A ferramenta 'list_calendars' não foi encontrada através do MCP Client.")
                return False
            print("✅ Ferramenta 'list_calendars' encontrada.")

            # 6. Criar um agente temporário para testar a ferramenta
            print("Criando agente temporário para testar a ferramenta 'list_calendars'...")
            llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=openai_api_key)

            test_system_prompt = "Você é um assistente que testa a conexão com o Google Calendar. " \
            "Use a ferramenta 'list_calendars' para verificar a conexão. Se a ferramenta retornar " \
            "calendários, reporte sucesso. Se falhar, reporte o erro."

            test_agent = create_agent(
                model=llm,
                tools=calendar_tools,
                system_prompt=test_system_prompt
            )

            # 7. Invocar a ferramenta list_calendars
            print("Executando o agente para listar calendários...")
            test_inputs = {"messages": [{"role": "user", "content": "Liste meu calendário de 2026."}]}

            agent_output_messages = []

            async for chunk in test_agent.astream(test_inputs, stream_mode="updates"):
                for node, values in chunk.items():
                    for message in values.get("messages", []):
                        print(message)
                        agent_output_messages.append(message)
                        print("\n")

            # 8. Analisar a saída do agente
            found_tool_call = False
            tool_succeeded = False
            final_ai_message = ""

            for message in agent_output_messages:
                if hasattr(message, "tool_calls") and message.tool_calls:
                    if any(tc.name == 'list_calendars' for tc in message.tool_calls):
                        found_tool_call = True
                elif message.type == "tool":
                    if "error" in message.content.lower():
                        print(f"❌ ERRO: A ferramenta retornou um erro: {message.content}")
                        tool_succeeded = False
                    else:
                        print(f"✅ Ferramenta executada com sucesso. Conteúdo: {message.content[:200]}...")
                        tool_succeeded = True
                elif message.type == "ai":
                    final_ai_message = message.content

            if found_tool_call and tool_succeeded:
                print("✅ TESTE DE CONEXÃO COM GOOGLE CALENDAR BEM-SUCEDIDO!")
                if final_ai_message:
                    print(f"Mensagem final do agente: {final_ai_message}")
                return True
            else:
                print("❌ TESTE DE CONEXÃO COM GOOGLE CALENDAR FALHOU.")
                if final_ai_message:
                    print(f"Mensagem final do agente: {final_ai_message}")
                return False

        except Exception as e:
            print(f"❌ ERRO GERAL durante a conexão MCP ou execução do agente: {e}")
            # Aqui extraímos o ERRO REAL que o TaskGroup estava escondendo
            if hasattr(e, 'exceptions'):
                print("🔍 Detalhes do erro interno do TaskGroup:")
                for idx, sub_e in enumerate(e.exceptions):
                    print(f"   Sub-erro {idx + 1}: {type(sub_e).__name__}: {sub_e}")
            return False

        finally:
            # Tenta fechar o cliente adequadamente para evitar processos zumbis
            if temp_mcp_client:
                if hasattr(temp_mcp_client, 'close') and callable(temp_mcp_client.close):
                    await temp_mcp_client.close()
                elif hasattr(temp_mcp_client, 'aclose') and callable(temp_mcp_client.aclose):
                    await temp_mcp_client.aclose()

    @staticmethod
    def verificar_escopos_token():
        token = os.environ["GOOGLE_ACCESS_TOKEN"]
        if not token:
            print("❌ Token não encontrado no userdata.")
            return

        # Endpoint oficial do Google para auditar tokens
        url = f"https://oauth2.googleapis.com/tokeninfo?access_token={token}"

        print("Inspecionando as permissões (scopes) do seu token atual...")
        response = httpx.get(url)

        if response.status_code == 200:
            dados_token = response.json()
            escopos_string = dados_token.get("scope", "")
            lista_escopos = escopos_string.split(" ")

            print("\n✅ Token válido! Ele possui as seguintes permissões:")
            for escopo in lista_escopos:
                if "cloud-platform" in escopo:
                    print(f" ☁️  -> {escopo} (✓ ENCONTRADO)")
                elif "calendar" in escopo:
                    print(f" 📅 -> {escopo} (✓ ENCONTRADO)")
                else:
                    print(f" 🔹 -> {escopo}")

            # Validação final
            if "https://www.googleapis.com/auth/cloud-platform" in lista_escopos:
                print("\n🎉 SUCESSO! O escopo 'cloud-platform' ESTÁ presente.")
                print("Se a API estiver ativada no painel, o MCP já deve funcionar. Pode rodar o código do agente!")
            else:
                print("\n❌ FALHA: O escopo 'cloud-platform' NÃO está no token.")
                print("Você precisará gerar o token novamente garantindo que solicitou esta URL exata nos escopos.")
        else:
            print("❌ Ocorreu um erro ao inspecionar o token. Ele pode estar expirado.")
            print("Detalhes:", response.text)

if __name__ == "__main__":
    print("\n\n--- VERIFICAÇÃO DE ESCOPO DO TOKEN DE ACESSO ---\n")
    GoogleAuthenticateTest.verificar_escopos_token()
    print("\n\n--- INICIANDO O TESTE DE CONEXÃO COM GOOGLE CALENDAR ---\n")
    asyncio.run(GoogleAuthenticateTest.teste_listar_calendario_google())
    