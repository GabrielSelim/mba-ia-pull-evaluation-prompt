# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Desafio do módulo **Prompt Engineering** (MBA em Engenharia de Software com IA — Full Cycle).

O projeto faz **pull** de um prompt de baixa qualidade do LangSmith Prompt Hub, **refatora** esse prompt com técnicas
de Prompt Engineering, faz **push** da versão otimizada de volta ao Hub e **avalia** a nova versão contra um dataset de
15 bugs com 5 métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision), com meta de **≥ 0.8 em todas**.

A tarefa do prompt: transformar um **relato de bug** em uma **User Story** ágil com critérios de aceitação.

---

## Técnicas Aplicadas (Fase 2)

O prompt otimizado está em [`prompts/bug_to_user_story_v2.yml`](prompts/bug_to_user_story_v2.yml) e usa quatro técnicas
(listadas em `techniques_applied` no próprio YAML).

### 1. Role Prompting

**Por quê:** o v1 dizia apenas "você é um assistente". Uma persona experiente puxa o vocabulário e o padrão de
qualidade de quem escreve User Stories no dia a dia (formato "Como/eu quero/para que", Gherkin, foco em valor de
negócio), o que melhora Clarity e Precision.

**Como apliquei:**

```
Você é um Product Manager sênior, com 10 anos de experiência em times ágeis (Scrum) de produtos web, mobile e SaaS B2B.
Sua especialidade é transformar relatos de bugs escritos por usuários, QA ou suporte em User Stories claras, testáveis
e prontas para o refinamento do time de desenvolvimento.
```

### 2. Few-shot Learning (obrigatória)

**Por quê:** as referências do dataset seguem um padrão bem específico (frase da história, "Critérios de Aceitação:"
com Dado/Quando/Então/E, seções extras como "Contexto Técnico:" e, nos bugs complexos, blocos `=== ... ===`).
Descrever esse padrão só com instruções é ambíguo; mostrar exemplos completos de entrada → saída é a forma mais
confiável de o modelo reproduzir o formato e o nível de detalhe esperados — isso puxa principalmente F1-Score (recall).

**Como apliquei:** 3 exemplos **criados por mim** (não copiados do dataset, para não "vazar" o gabarito), um por nível
de complexidade:

| Exemplo | Bug | O que ensina |
|---|---|---|
| 1 — Simples | Link "Esqueci minha senha" não abre | História + 5 critérios, nada além |
| 2 — Médio | PDF de nota fiscal corrompido com 4+ páginas | Critérios + "Contexto Técnico:" com os fatos do relato |
| 3 — Complexo | Agendamento com concorrência, SMS e UX | Blocos A/B/C por problema, critérios técnicos, contexto, tasks |

### 3. Chain of Thought (silencioso)

**Por quê:** converter um bug em história exige raciocinar: quem é afetado, o que ele quer fazer quando o sistema
funciona, qual o valor, quais fatos do relato precisam aparecer e qual a complexidade. Pedir esse raciocínio
explicitamente reduz histórias com persona errada ou critérios genéricos. Mas o raciocínio **não** pode aparecer na
resposta — texto extra derruba Clarity (concisão) e Precision (foco).

**Como apliquei:** uma seção "PROCESSO DE RACIOCÍNIO (pense passo a passo, sem mostrar este raciocínio na resposta)"
com 6 passos (persona → objetivo → valor → fatos → complexidade → esqueleto) e a regra 1: "Responda SOMENTE com a
User Story final".

### 4. Skeleton of Thought

**Por quê:** o dataset mistura bugs de uma linha com relatos de 4 problemas e impacto de negócio. Um formato único
ou fica raso nos complexos (recall baixo) ou inflado nos simples (Clarity/Precision baixos). Um esqueleto por nível de
complexidade deixa a resposta proporcional ao bug.

**Como apliquei:** a seção "FORMATO" define três esqueletos — **SIMPLES**, **MÉDIO** (com seções opcionais como
"Critérios Técnicos:", "Exemplo de Cálculo:", "Contexto de Segurança:") e **COMPLEXO** (`=== USER STORY PRINCIPAL ===`,
`=== CRITÉRIOS DE ACEITAÇÃO ===`, `=== CRITÉRIOS TÉCNICOS ===`, `=== CONTEXTO DO BUG ===`,
`=== TASKS TÉCNICAS SUGERIDAS ===`). O passo 5 do raciocínio classifica o bug e o passo 6 escolhe o esqueleto.

### Regras explícitas e edge cases

Além das técnicas, o prompt tem 8 regras numeradas (formato da primeira linha, Gherkin, fidelidade ao relato,
cálculos, proporcionalidade) e uma seção de **casos especiais**: relato vago, vários problemas no mesmo relato, falha
de segurança (severidade + OWASP), desempenho (sintoma → meta mensurável), bug específico de plataforma/tela e
entrada vazia ou que não é bug.

### System vs User prompt

- **System:** papel, tarefa, raciocínio, regras, formatos, edge cases e exemplos — tudo que é fixo.
- **User:** só a instrução curta e o `{bug_report}` delimitado por `"""`. No v1 o `{bug_report}` aparecia
  duplicado no system e no user.

---

## Resultados Finais

> Os números abaixo são preenchidos com a saída real de `python src/evaluate.py` (ver "Como Executar").

### Evidências no LangSmith

- **Dataset de avaliação (público, com os experimentos):** _link gerado por `share_dataset` — ver passo 7 de "Como Executar"_
- **Prompt otimizado no Hub:** `https://smith.langchain.com/hub/<seu_handle>/bug_to_user_story_v2`

### Notas da versão final (v2)

| Métrica | Nota | Status |
|---|---|---|
| Helpfulness | — | — |
| Correctness | — | — |
| F1-Score | — | — |
| Clarity | — | — |
| Precision | — | — |
| **Média** | — | — |

Screenshots (pasta `docs/`):

- Resumo do experimento com as 5 métricas ≥ 0.8
- Dataset com os 15 exemplos
- Tracing detalhado de 3 exemplos (um simples, um médio e um complexo)

### Comparação v1 × v2

| Aspecto | v1 (original) | v2 (otimizado) | Por que mudou |
|---|---|---|---|
| Persona | "um assistente" | Product Manager sênior em times ágeis | Vocabulário e padrão de qualidade de User Story |
| Instruções | "crie uma user story" | Tarefa + 8 regras explícitas | Reduz ambiguidade e alucinação |
| Formato de saída | Não definido | 3 esqueletos (simples/médio/complexo) | Resposta proporcional ao bug |
| Critérios de aceitação | Não pedidos | Gherkin obrigatório (Dado/Quando/Então/E) | Testável e igual ao padrão das referências |
| Exemplos | Nenhum | 3 exemplos few-shot de entrada/saída | Ensina formato e profundidade |
| Raciocínio | Nenhum | CoT silencioso em 6 passos | Persona, valor e fatos corretos sem poluir a saída |
| Edge cases | Nenhum | 6 casos especiais | Bugs vagos, múltiplos, segurança, desempenho |
| `{bug_report}` | Duplicado no system e no user | Só no user, delimitado | Separação correta system × user |
| Metadados | Tags | Tags + `techniques_applied` + descrição | Rastreabilidade no Hub |

### Histórico de iterações

| Iteração | Mudança no prompt | Resultado |
|---|---|---|
| 1 | Versão inicial do v2 (persona + few-shot + CoT + esqueletos) | — |

---

## Como Executar

### Pré-requisitos

- Python 3.10+
- Conta no [LangSmith](https://smith.langchain.com) com API key (Settings → API Keys)
- Handle público do LangSmith Hub (ver abaixo)
- API key do Gemini ([Google AI Studio](https://aistudio.google.com/app/apikey), plano gratuito) **ou** da OpenAI

**Criar o handle do Hub** (necessário antes do push): LangSmith → Prompts → abra/crie um prompt qualquer → três
pontinhos ao lado de *Playground* → **Make Public** → defina o handle. Ele é definitivo.

### 1. Instalar

```bash
git clone https://github.com/GabrielSelim/mba-ia-pull-evaluation-prompt.git
cd mba-ia-pull-evaluation-prompt

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar o `.env`

```bash
cp .env.example .env              # Windows: copy .env.example .env
```

Preencha:

```env
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=mba-ia-pull-evaluation-prompt
USERNAME_LANGSMITH_HUB=seu_handle
LLM_PROVIDER=google               # ou openai
GOOGLE_API_KEY=...                # se google
OPENAI_API_KEY=...                # se openai
LLM_MODEL=gemini-2.5-flash
EVAL_MODEL=gemini-2.5-flash
```

### 3. Pull do prompt original (v1)

```bash
python src/pull_prompts.py
```

Puxa `leonanluppi/bug_to_user_story_v1` e salva em `prompts/bug_to_user_story_v1.yml`.

### 4. Testes de validação do prompt v2

```bash
pytest tests/test_prompts.py -v
```

Verifica system prompt, persona, formato, few-shot, ausência de TODO, mínimo de técnicas, estrutura e a variável
`{bug_report}`.

### 5. Push do prompt otimizado (v2)

```bash
python src/push_prompts.py
```

Valida o YAML e publica `<seu_handle>/bug_to_user_story_v2` como **público**, com descrição, README, tags e técnicas.

### 6. Avaliação

```bash
python src/evaluate.py
```

Cria o dataset `<LANGSMITH_PROJECT>-eval` (15 exemplos) na primeira execução, roda o v2 contra ele como experimento e
grava as 5 notas como feedback. No plano gratuito do Gemini a avaliação é sequencial e leva alguns minutos.

Se alguma métrica ficar abaixo de 0.8: ajuste `prompts/bug_to_user_story_v2.yml`, rode o push e a avaliação de novo.

### 7. Link público do dataset (evidência)

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; from langsmith import Client; print(Client().share_dataset(dataset_name=os.getenv('LANGSMITH_PROJECT') + '-eval')['url'])"
```

Rode **uma vez** e cole o link na seção "Resultados Finais" (compartilhar de novo gera outro link).

---

## Estrutura

```
├── .env.example
├── requirements.txt
├── README.md
├── prompts/
│   ├── bug_to_user_story_v1.yml   # Prompt original (pull do Hub)
│   └── bug_to_user_story_v2.yml   # Prompt otimizado
├── datasets/
│   └── bug_to_user_story.jsonl    # 15 bugs (5 simples, 7 médios, 3 complexos)
├── src/
│   ├── pull_prompts.py            # Pull do Hub → YAML
│   ├── push_prompts.py            # YAML → Hub (público, com metadados)
│   ├── evaluate.py                # Avaliação (fornecido)
│   ├── metrics.py                 # Métricas LLM-as-judge (fornecido)
│   └── utils.py                   # Auxiliares (fornecido)
└── tests/
    └── test_prompts.py            # Testes de validação do v2
```
