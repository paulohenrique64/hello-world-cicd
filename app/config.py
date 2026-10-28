"""Configuração da integração com o serviço de notificações."""

import os

NOTIFICATIONS_URL = "https://notificacoes.example.com/v1/send"
# A chave nunca fica no código: é injetada pelo ambiente (secret do orquestrador/CI).
NOTIFICATIONS_API_KEY = os.environ.get("NOTIFICATIONS_API_KEY", "")
