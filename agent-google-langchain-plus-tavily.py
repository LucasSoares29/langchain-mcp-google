import asyncio
from json import tool
import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from google.oauth2.credentials import Credentials
from langchain.agents import create_agent
from google_authenticate import pegar_tokens_colab
from google_oauth_class import GoogleOAuth2Auth 

# Importando o construtor oficial do Google em vez do utilitário do Langchain
from googleapiclient.discovery import build 
from langchain_google_community import CalendarToolkit


# Carrega as variáveis do arquivo .env
load_dotenv()

async def iniciar_assistente():

    GOOGLE_ACCESS_TOKEN, GOOGLE_REFRESH_TOKEN = pegar_tokens_colab()

    # 1. Instanciar a classe oficial Credentials do Google
    # Para que a renovação funcione, precisa de passar o refresh_token, client_id e client_secret
    google_credentials = Credentials(
        token= GOOGLE_ACCESS_TOKEN or os.environ["GOOGLE_ACCESS_TOKEN"],
        refresh_token= GOOGLE_REFRESH_TOKEN or os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"]
    )

    # 2. Criar o api_resource nativamente com o googleapiclient
    api_resource = build("calendar", "v3", credentials=google_credentials)

    # 3. Gerando as tools do Langchain a partir da biblioteca da comunidade que se conecta a api do Google (Não-MCP)
    toolkit = CalendarToolkit(api_resource=api_resource)

    tools = toolkit.get_tools()

    print("Tools disponíveis no CalendarToolkit:")
    print(tools)

    # 4. Gerando as tools MCP da Ferramenta de Busca da Internet
    client = MultiServerMCPClient(
        {
            "web": {
                "transport": "http",  # HTTP-based remote server
                "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={os.environ["TAVILY_API_KEY"]}",
            }
        }
    )

    tools_mcp = await client.get_tools()
    print("Tools disponíveis via MCP:")
    for tool in tools_mcp:
        print(f"""{tool.name}: {tool.description}""")
        print("="*50)

    # 5. Criando o agente
    openai_api_key = os.environ['OPENAI_API_KEY']
    llm = ChatOpenAI(model="gpt-5.4-mini", openai_api_key=openai_api_key)

    data_atual = datetime.now().strftime("%d/%m/%Y")

    system_prompt = f"""
                    # CONTEXTO
                    Você é um Assistente Virtual Especialista na Gestão de Agendas focado no Google Calendar.
                    A data de hoje é {data_atual}.
                    O fuso horário padrão para todas as operações é America/Sao_Paulo.

                    # REGRAS E FLUXO DE TRABALHO
                    Siga rigorosamente as etapas abaixo ao processar solicitações:

                    1. Extração e Busca de Dados:
                    - Ao ser solicitado a criar um evento, verifique se o usuário forneceu todos os dados essenciais (Nome, Data, Hora de Início e Término).
                    - Se faltarem informações, utilize a ferramenta de busca na internet (tavily_search) para encontrar os detalhes oficiais do evento.
                    - IMPORTANTE PARA BUSCA (TAVILY): Se a ferramenta de busca exigir o parâmetro 'topic', o valor DEVE SER 
                    SEMPRE "general". Nunca invente ou categorize o tópico com palavras como "sports", "news", etc.

                    2. REGRA DE OURO PARA INCLUSÕES (PARADA OBRIGATÓRIA):
                    - NUNCA utilize a ferramenta de criação de eventos na mesma interação em que os dados foram buscados na internet.
                    - Após encontrar os dados, PARE e pergunte ao usuário: "Encontrei as seguintes informações sobre o evento [Nome]: Data: [Data], Horário: [Início - Fim]. Deseja que eu adicione à sua agenda?"
                    - VOCÊ SÓ PODE CHAMAR A FERRAMENTA 'create_calendar_event' DEPOIS QUE O USUÁRIO RESPONDER "SIM" OU CONFIRMAR A INCLUSÃO.

                    3. Tratamento de Fuso Horário e Exceções:
                    - Se não encontrar as informações exatas na web, não crie o evento. Informe ao usuário o que faltou.
                    - Eventos internacionais devem ser convertidos para o horário oficial de Brasília (Fuso horário 'America/Sao_Paulo') antes da confirmação e do cadastro.
                    - Se nenhuma descrição for encontrada/fornecida, use: "Evento criado a partir do Toolkit do LangChain".

                    4. Para BUSCAR, ALTERAR ou EXCLUIR eventos existentes na agenda:
                    - Você DEVE SEMPRE usar 'get_calendars_info' PRIMEIRO.
                    - NUNCA chame 'search_events' sem o resultado de 'get_calendars_info'. 
                    - O parâmetro 'calendars_info' de 'search_events' NUNCA pode ser vazio.

                    # DIRETRIZES DE SAÍDA FINAL
                    Somente após a confirmação do usuário e a chamada bem-sucedida da ferramenta de inclusão/exclusão, responda no formato:

                    - Para EXCLUSÃO: "O evento [Nome do Evento] foi excluído com sucesso."

                    - Para INCLUSÃO:
                    "O evento foi incluído com sucesso!"
                    * **Nome do Evento:** [Nome do Evento]
                    * **Data:** [DD/MM/AAAA]
                    * **Horário de Início:** [HH:MM]
                    * **Horário de Término Estimado:** [HH:MM]

                    - Para ALTERAÇÃO:
                    "O evento foi alterado com sucesso!"
                    * **Nome do Evento:** [Nome do Evento]
                    * **Data:** [DD/MM/AAAA]
                    * **Horário de Início:** [HH:MM]
                    * **Horário de Término Estimado:** [HH:MM]
                    """

    agent = create_agent(
        model=llm, 
        tools=tools + tools_mcp, # Passamos as tools do Google Calendar e da Busca na Web juntas
        system_prompt=system_prompt
    )

    # 6. Criamos uma lista vazia para armazenar a memória da conversa
    historico_mensagens = []

    print("\n\n🤖 Assistente de Agenda iniciado! (Digite 'sair' para encerrar)\n")

    # 7. Iniciamos o loop infinito do chatbot
    while True:
        mensagem = input("Você: ")
        
        # Condição de parada do chatbot
        if mensagem.lower() in ['sair', 'exit', 'quit']:
            print("🤖 Assistente: Até logo! Encerrando o sistema...")
            break

        # Se o usuário apertar Enter sem digitar nada, ignoramos
        if not mensagem.strip():
            continue

        # 3. Adicionamos a nova mensagem do usuário ao histórico
        historico_mensagens.append({"role": "user", "content": mensagem})
        
        # 4. Passamos o histórico COMPLETO como input, não apenas a última mensagem
        inputs = {"messages": historico_mensagens}

        # Variável para capturar a resposta final da IA nesta rodada
        resposta_final_ai = None

        # Usamos stream para receber as atualizações passo a passo
        async for chunk in agent.astream(inputs, stream_mode="updates"):
            for node, values in chunk.items():
                # (Opcional) Você pode comentar este print se quiser um chat mais limpo
                print(f"\n--- INICIANDO NÓ: {node.upper()} ---")

                for message in values.get("messages", []):
                    # Se for o agente pensando/chamando a tool
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        print("🧠 [O Agente está consultando a agenda/ferramenta...]")
                        
                    # Se for o resultado da ferramenta
                    elif message.type == "tool":
                        print(f"🛠️ [Retorno da ferramenta '{message.name}' recebido]")

                    # Se for a resposta final do agente
                    elif message.type == "ai" and not message.tool_calls:
                        print(f"\n🤖 Assistente: {message.content}\n")
                        resposta_final_ai = message # Guardamos a resposta da IA

        # 8. Após o fim do processamento, salvamos a resposta da IA no histórico
        # Isso garante que na próxima iteração do 'while', o agente lembre do que ele mesmo disse
        if resposta_final_ai:
            historico_mensagens.append(resposta_final_ai)
            
        print("-" * 50) # Separador visual para a próxima rodada

if __name__ == "__main__":
    asyncio.run(iniciar_assistente())
