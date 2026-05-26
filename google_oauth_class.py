import httpx
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

class GoogleOAuth2Auth(httpx.Auth):
    def __init__(self, credentials: Credentials):
        self.credentials = credentials

    def auth_flow(self, request: httpx.Request):
        # Se o token estiver expirado ou inválido, a classe oficial renova-o automaticamente
        if not self.credentials.valid:
            print("🔄 Token expirado. A renovar as credenciais do Google automaticamente...")
            # O Request() aqui é o transportador oficial exigido pelo Google para a renovação
            self.credentials.refresh(Request())

        # Injeta o token atualizado (seja o original ou o renovado) no cabeçalho
        request.headers["Authorization"] = f"Bearer {self.credentials.token}"
        yield request