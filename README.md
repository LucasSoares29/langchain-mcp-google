# langchain-mcp-google
Demonstração de uso de MCP Tavily para busca na Web + biblioteca da Langchain Google Community para Integração com o Google Calendar

# Passo 1
Obter ```GOOGLE_CLIENT_ID``` e ```GOOGLE_CLIENT_SECRET```

Estes dois são as "identidades" da sua aplicação perante o Google. Eles são fixos e gerados no painel do Google Cloud.

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/welcome?_gl=1*bat110*_up*MQ..*_gs*MQ..&gclid=Cj0KCQjw_b_QBhCSARIsAP6hR4enszcfC3D5hicDWNqVg5XEdHIzVoJpEVwFbI_2vvJGmF5ltrwi5tkaAhJoEALw_wcB&gclsrc=aw.ds&project=gentle-analyst-473214-t9).

2. Crie um novo projeto (ou selecione um existente).

3. No menu lateral, vá em APIs e Serviços > Biblioteca.

4. Pesquise por Google Calendar API e clique em Ativar.

5. Vá em APIs e Serviços > Tela de permissão OAuth:

    * Escolha Externo (se seu e-mail for @gmail.com comum) e clique em Criar.

    * Preencha os campos obrigatórios (Nome do App, e-mails de suporte).

    * Na aba "Publico Alvo" adicione os e-mails como usuários de teste (isso é crucial para conseguir logar enquanto o app não é aprovado pelo Google).

    * Vá na aba "Clientes" vá em "Criar cliente"

    * Em Tipo de aplicativo: Escolha App para computador (ou Desktop app).

    * Dê um nome e clique em Criar.

    * Uma janela vai aparecer com o seu **Client ID** e **Client Secret**. Baixe como JSON e salve num local seguro.



# Passo 2
Crie um arquivo **.env** para armazenar as seguintes chaves:
```
OPENAI_API_KEY = Chave gerada pela OpenAI para executar o LLM
PROJECT_ID = ID do projeto do Google Cloud Platform
TAVILY_API_KEY = Chave gerada pela Tavily para uso do MCP
GOOGLE_CLIENT_ID = Gerada no passo 1
GOOGLE_CLIENT_SECRET = Gerada no passo 1
GOOGLE_ACESS_TOKEN = Deverá ser incluida após o passo 3
GOOGLE_REFRESH_TOKEN = Deverá ser incluída após o passo 3
```

# Passo 3
Obter ```GOOGLE_ACCESS_TOKEN``` e ```GOOGLE_REFRESH_TOKEN```

Diferente do ID e Secret, os tokens não ficam no painel. Eles são gerados quando um usuário (neste caso, você mesmo) clica em "Fazer login com o Google" e permite que o seu código acesse a agenda dele. Esta parte é feita pela função ```pegar_tokens_collab()``` dentro do arquivo ```google_authenticate.py```

# Passo 4

Abra o prompt de comando como administrador e execute o **run.bat**. Ele irá fazer os seguintes passos:
1. Criará um ambiente virtual python chamado ```venv```
2. Instalará as dependências listadas no arquivo ```requirements.txt```
3. Executará o script ```agent-google-langchain-plus-tavily.py```
