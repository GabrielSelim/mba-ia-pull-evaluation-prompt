"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

Uso:
    python src/pull_prompts.py
"""

import os
import sys
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent

# Prompt semente do desafio e onde ele é salvo localmente
SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
LOCAL_KEY = "bug_to_user_story_v1"
OUTPUT_FILE = ROOT_DIR / "prompts" / "bug_to_user_story_v1.yml"


def _message_role(message) -> str:
    """Identifica o papel (system/user/ai) de uma mensagem do ChatPromptTemplate."""
    class_name = type(message).__name__.lower()
    if "system" in class_name:
        return "system"
    if "human" in class_name or "user" in class_name:
        return "user"
    if "ai" in class_name or "assistant" in class_name:
        return "ai"
    return getattr(message, "role", "user")


def _message_text(message) -> str:
    """Extrai o texto do template de uma mensagem."""
    prompt = getattr(message, "prompt", None)
    if prompt is not None and hasattr(prompt, "template"):
        return prompt.template
    # Mensagens fixas (SystemMessage/HumanMessage) guardam o texto em .content
    return str(getattr(message, "content", ""))


def prompt_to_dict(prompt) -> dict:
    """Converte o ChatPromptTemplate puxado do Hub para o formato YAML do projeto."""
    system_parts, user_parts = [], []

    for message in prompt.messages:
        role = _message_role(message)
        text = _message_text(message)
        if role == "system":
            system_parts.append(text)
        else:
            user_parts.append(text)

    metadata = getattr(prompt, "metadata", None) or {}

    return {
        LOCAL_KEY: {
            "description": metadata.get(
                "description", "Prompt para converter relatos de bugs em User Stories"
            ),
            "system_prompt": "\n\n".join(system_parts),
            "user_prompt": "\n\n".join(user_parts),
            "input_variables": list(getattr(prompt, "input_variables", [])),
            "source": SOURCE_PROMPT,
            "version": "v1",
            "pulled_at": date.today().isoformat(),
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }


def pull_prompts_from_langsmith() -> bool:
    """Faz pull do prompt semente e salva em prompts/bug_to_user_story_v1.yml."""
    client = Client()

    print(f"Puxando prompt do LangSmith Hub: {SOURCE_PROMPT}")
    try:
        # dangerously_pull_public_prompt=True é obrigatório para identificadores
        # "owner/nome": o Hub devolve um objeto LangChain serializado de terceiros.
        # Aqui é o prompt semente do desafio, então o risco é conhecido.
        prompt = client.pull_prompt(SOURCE_PROMPT, dangerously_pull_public_prompt=True)
    except Exception as e:
        print(f"❌ Erro ao fazer pull de '{SOURCE_PROMPT}': {e}")
        print("\nVerifique LANGSMITH_API_KEY no .env e sua conexão com a internet.")
        return False

    data = prompt_to_dict(prompt)
    info = data[LOCAL_KEY]
    print(f"   ✓ Prompt carregado ({len(prompt.messages)} mensagens)")
    print(f"   ✓ Variáveis de entrada: {', '.join(info['input_variables']) or '(nenhuma)'}")

    if not save_yaml(data, str(OUTPUT_FILE)):
        return False

    print(f"   ✓ Salvo em: {OUTPUT_FILE.relative_to(ROOT_DIR)}")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    if not pull_prompts_from_langsmith():
        return 1

    print("\n✅ Pull concluído. Próximo passo: otimizar o prompt em prompts/bug_to_user_story_v2.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
