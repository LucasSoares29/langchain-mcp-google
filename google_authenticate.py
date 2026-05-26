import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow


# Carrega as variáveis do arquivo .env
load_dotenv()

# 1. DESLIGA A TRAVA DE SEGURANÇA DO OAUTH PARA LOCALHOST (Resolve o InsecureTransportError)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configurando o scope:
# A API padrão do Google Calendar (que testamos agora) só quer saber: "Você tem acesso a essa agenda?".
# Já a Calendar MCP API é um serviço hospedado na infraestrutura do Google Cloud. Para usá-la, o Google Cloud 
# exige uma camada extra de segurança: ele quer saber se o seu token tem permissão para usar recursos de 
# Cloud Platform no seu projeto, e não apenas o calendário.

SCOPES = ['https://www.googleapis.com/auth/calendar']

CLIENT_CONFIG = {
        "installed": {
            "client_id": os.environ['GOOGLE_CLIENT_ID'],
            "client_secret": os.environ['GOOGLE_CLIENT_SECRET'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

def pegar_tokens_colab():
    try:
      print("Carregando arquivo 'credentials.json'...")
      flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes=SCOPES)
    except FileNotFoundError:
      print("Arquivo de json não encontrado. Tentando carregar a credecial de novo...")
      flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)

    try:
        print("Tentando iniciar servidor local...")
        creds = flow.run_local_server(port=0)

    except Exception as e:
        print("Servidor local falhou. Iniciando modo manual...")

        flow.redirect_uri = 'http://localhost:8080/'

        auth_url, _ = flow.authorization_url(prompt='consent')

        print("\n" + "="*60)
        print("🚨 AÇÃO NECESSÁRIA 🚨")
        print("1. Clique neste link para abrir o login do Google:")
        print(auth_url)
        print("\n2. Faça o login e autorize.")
        print("3. Ao dar a tela de erro no navegador, COPIE a URL inteira.")
        print("="*60 + "\n")

        # Pega a URL e remove espaços em branco acidentais do início ou fim
        url_resposta = input("Cole a URL completa do erro aqui: ").strip()

        # 2. A SUA VALIDAÇÃO: Garante que a URL comece com http:// ou https://
        if not url_resposta.startswith("http://") and not url_resposta.startswith("https://"):
             print("Prefixo ausente. Inserindo http:// automaticamente...")
             url_resposta = "http://" + url_resposta

        # Se a pessoa colou com https (como você sugeriu), o OAUTHLIB_INSECURE_TRANSPORT ali em cima já evita que a lib quebre!

        flow.fetch_token(authorization_response=url_resposta)
        creds = flow.credentials

    print("\n✅ Os tokens foram gerados com sucesso!")

    # comentar esta linha após teste
    # print(creds.token, creds.refresh_token) 
    return (creds.token, creds.refresh_token)

if __name__ == "__main__":
    pegar_tokens_colab()