"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    data = load_prompts(PROMPT_FILE)
    assert data and PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt):
    return prompt.get("system_prompt") or ""


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt, system_prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt, "Campo 'system_prompt' não existe"
        assert system_prompt.strip(), "Campo 'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        match = re.search(r"Você é (um|uma) [^.\n]+", system_prompt, re.IGNORECASE)
        assert match, "O system_prompt não define uma persona ('Você é um ...')"
        persona = match.group(0).lower()
        assert any(
            role in persona for role in ("product manager", "product owner", "analista", "especialista")
        ), f"Persona sem papel profissional claro: {match.group(0)}"

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        text = system_prompt.lower()
        assert "user story" in text, "O prompt não menciona User Story"
        # Formato padrão: Como um ..., eu quero ..., para que ...
        for part in ("como um", "eu quero", "para que"):
            assert part in text, f"Formato padrão de User Story incompleto: falta '{part}'"
        # Critérios de aceitação em Gherkin
        assert "critérios de aceitação" in text, "O prompt não exige critérios de aceitação"
        for part in ("dado que", "quando", "então"):
            assert part in text, f"Formato Gherkin incompleto: falta '{part}'"

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        examples = re.findall(r"^#+\s*Exemplo \d+", system_prompt, re.MULTILINE)
        inputs = re.findall(r"^\s*Entrada:\s*$", system_prompt, re.MULTILINE)
        outputs = re.findall(r"^\s*Saída:\s*$", system_prompt, re.MULTILINE)
        assert len(examples) >= 2, f"Few-shot exige ao menos 2 exemplos, encontrados: {len(examples)}"
        assert len(inputs) == len(outputs) == len(examples), (
            f"Cada exemplo deve ter Entrada e Saída "
            f"(exemplos={len(examples)}, entradas={len(inputs)}, saídas={len(outputs)})"
        )

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        full_text = yaml.safe_dump(prompt, allow_unicode=True)
        assert "[TODO]" not in full_text, "Ainda há [TODO] no prompt"
        assert not re.search(r"\bTODO\b", full_text), "Ainda há TODO no prompt"

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied") or []
        assert isinstance(techniques, list), "techniques_applied deve ser uma lista"
        assert len(techniques) >= 2, f"Mínimo de 2 técnicas, encontradas: {len(techniques)}"
        assert any("few-shot" in t.lower() for t in techniques), "Few-shot Learning é obrigatório"

    def test_prompt_structure_is_valid(self, prompt):
        """Validação geral do utils (campos obrigatórios, sem TODO, técnicas)."""
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, f"Estrutura inválida: {errors}"

    def test_user_prompt_uses_bug_report_variable(self, prompt):
        """O user_prompt deve receber {bug_report}, chave usada pelo dataset."""
        assert "{bug_report}" in prompt.get("user_prompt", ""), "user_prompt sem a variável {bug_report}"
        assert "{bug_report}" not in prompt.get("system_prompt", ""), (
            "{bug_report} duplicado no system_prompt (problema do v1)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
