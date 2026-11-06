"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

Uso:
    python src/push_prompts.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
PROMPT_FILE = ROOT_DIR / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"

# Única variável que o dataset de avaliação fornece
EXPECTED_VARIABLES = {"bug_report"}


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """Monta o ChatPromptTemplate (system + user) a partir do YAML."""
    return ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])


def build_readme(prompt_data: dict) -> str:
    """README exibido na página do prompt no Hub, com as técnicas aplicadas."""
    techniques = "\n".join(f"- {t}" for t in prompt_data.get("techniques_applied", []))
    return (
        f"# {PROMPT_KEY}\n\n"
        f"{prompt_data.get('description', '').strip()}\n\n"
        f"**Versão:** {prompt_data.get('version', '')}\n\n"
        f"## Técnicas aplicadas\n\n{techniques}\n"
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    client = Client()
    prompt = build_chat_prompt(prompt_data)

    techniques = prompt_data.get("techniques_applied", [])
    tags = list(dict.fromkeys(
        list(prompt_data.get("tags", []))
        + [prompt_data.get("version", "v2")]
        + [t.lower().replace(" ", "-") for t in techniques]
    ))

    metadata = {
        "is_public": True,
        "description": prompt_data.get("description", "").strip(),
        "readme": build_readme(prompt_data),
        "tags": tags,
    }

    try:
        url = client.push_prompt(prompt_name, object=prompt, **metadata)
    except Exception as e:
        message = str(e)
        if "nothing to commit" in message.lower():
            # O conteúdo já é o mais recente no Hub: atualiza só os metadados.
            client.update_prompt(prompt_name, **metadata)
            print(f"   ✓ Conteúdo inalterado desde o último commit; metadados atualizados: {prompt_name}")
            print(f"   ✓ Tags: {', '.join(tags)}")
            print(f"   ✓ URL: https://smith.langchain.com/hub/{prompt_name}")
            return True
        print(f"❌ Erro ao fazer push de '{prompt_name}': {message}")
        if "handle" in message.lower() or "403" in message or "404" in message:
            print("\nConfira se USERNAME_LANGSMITH_HUB é o seu handle público do Hub")
            print("(veja as instruções no .env.example para criar o handle).")
        return False

    print(f"   ✓ Push concluído: {prompt_name}")
    print(f"   ✓ Tags: {', '.join(tags)}")
    print(f"   ✓ URL: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)

    if not str(prompt_data.get("user_prompt", "")).strip():
        errors.append("user_prompt está vazio")

    try:
        variables = set(build_chat_prompt(prompt_data).input_variables)
    except Exception as e:  # chaves {} soltas no texto quebram o template
        errors.append(f"Template inválido: {e}")
    else:
        if variables != EXPECTED_VARIABLES:
            errors.append(
                f"Variáveis do template devem ser {sorted(EXPECTED_VARIABLES)}, "
                f"encontradas: {sorted(variables)}"
            )

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(str(PROMPT_FILE))
    if not data or PROMPT_KEY not in data:
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE}")
        return 1

    prompt_data = data[PROMPT_KEY]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1
    print(f"   ✓ Prompt validado ({len(prompt_data.get('techniques_applied', []))} técnicas)")

    username = os.getenv("USERNAME_LANGSMITH_HUB").strip()
    prompt_name = f"{username}/{PROMPT_KEY}"

    if not push_prompt_to_langsmith(prompt_name, prompt_data):
        return 1

    print("\n✅ Prompt publicado. Próximo passo: python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
