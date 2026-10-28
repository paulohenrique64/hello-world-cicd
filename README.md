# hello-world-cicd — Pipeline DevSecOps com GitHub Actions

API de tarefas em Python/FastAPI com banco SQLite, empacotada em Docker e publicada no Docker Hub por um
pipeline do GitHub Actions com **verificações de segurança integradas** (DevSecOps / *shift-left security*):
detecção de segredos (Gitleaks), análise estática com Quality Gate (SonarCloud), análise de
vulnerabilidades em dependências e na imagem (Trivy) e geração de SBOM (Syft).

Os problemas de segurança são encontrados **no Pull Request, antes de qualquer alteração chegar à
branch `main`**, e a imagem só é publicada se todas as verificações obrigatórias passarem.

| Item | Local |
|---|---|
| Código da aplicação | [`app/main.py`](app/main.py), [`app/db.py`](app/db.py), [`app/schemas.py`](app/schemas.py) |
| Testes | [`tests/test_api.py`](tests/test_api.py) |
| Dockerfile | [`Dockerfile`](Dockerfile) |
| Pipeline (workflow YAML) | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |
| Configuração do SonarCloud | [`sonar-project.properties`](sonar-project.properties) |
| Configuração do Gitleaks | [`.gitleaks.toml`](.gitleaks.toml) |
| Dependências (travadas com hash) | [`requirements.in`](requirements.in) → [`requirements.txt`](requirements.txt), [`requirements-dev.in`](requirements-dev.in) → [`requirements-dev.txt`](requirements-dev.txt) |
| Versão da imagem | [`VERSION`](VERSION) (vira a tag da imagem) |
| Execuções do pipeline | https://github.com/paulohenrique64/hello-world-cicd/actions |
| SonarCloud | https://sonarcloud.io/project/overview?id=paulohenrique64_hello-world-cicd |
| Imagem no registry | https://hub.docker.com/r/paulohenrique64/hello-world-cicd/tags |
| Evidências | [`evidencias/`](evidencias/) e [`ENTREGA.md`](ENTREGA.md) |

---

## Aplicação

| Método | Rota | Descrição |
|---|---|---|
| GET | `/hello` | Texto de boas-vindas |
| GET | `/health` | Status da aplicação e do banco |
| GET | `/tasks` | Lista as tarefas |
| POST | `/tasks` | Cria uma tarefa (`{"title": "...", "description": "..."}`) |
| POST | `/tasks/import` | Importa tarefas de um arquivo CSV (`title,description`) via upload |
| GET | `/tasks/{id}` | Busca uma tarefa |
| PUT | `/tasks/{id}` | Atualiza uma tarefa (`title`, `description`, `done`) |
| DELETE | `/tasks/{id}` | Remove uma tarefa |

O banco SQLite fica em `DB_PATH` (na imagem: `/app/data/app.db`). Todas as queries são parametrizadas.
A imagem roda com usuário sem privilégios e sem o `pip` (que não é usado em runtime).

---

## Pipeline DevSecOps

Arquivo: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

**Gatilhos**

- `pull_request` para a `main` nos eventos `opened`, `synchronize` e `reopened` — as verificações rodam
  automaticamente na **abertura e em cada atualização** do PR.
- `push` na `main` (após o merge) — roda tudo de novo e, se passar, publica a imagem.
- `workflow_dispatch` — execução manual.

**Jobs e dependências**

```
Gitleaks ─────────────────────────────┐
Testes ──┬── SonarCloud ──────────────┤
         └── Build, Trivy (imagem) e SBOM ──┤──► Publicar imagem  (só em push na main)
Trivy (dependências) ─────────────────┘
```

| Job | Ferramenta | O que verifica | Bloqueia quando |
|---|---|---|---|
| **Gitleaks** | Gitleaks 8.30.1 | Segredos (senhas, tokens, chaves privadas, API keys) em **todo o histórico** do repositório | Qualquer segredo encontrado |
| **Testes** | pytest + pytest-cov | Testes unitários da API e cobertura (`coverage.xml`, usado pelo SonarCloud) | Algum teste falha |
| **SonarCloud** | SonarCloud (SAST) | Vulnerabilidades, bugs, code smells e security hotspots do código Python e do Dockerfile | Quality Gate do **código novo** = Failed |
| **Trivy (dependências)** | Trivy 0.75.0 (`trivy fs`) | CVEs das dependências Python (`requirements.txt`, incluindo transitivas) | CVE **CRITICAL ou HIGH com correção disponível** |
| **Build, Trivy (imagem) e SBOM** | Docker, Trivy (`trivy image`), Syft | Build e smoke test da imagem; CVEs do sistema operacional e dos pacotes da imagem; geração do SBOM | CVE **CRITICAL ou HIGH com correção disponível** |
| **Publicar imagem** | Docker Hub | Push das tags `<VERSION>` e `latest` | Só executa em **push na `main`** e com `needs:` em **todos** os jobs acima |

As etapas que já existiam nas atividades anteriores (build, verificação da imagem, smoke test e push para o
registry) foram preservadas dentro dos jobs **Build…** e **Publicar imagem**. A imagem publicada é exatamente a
mesma que foi escaneada (passada entre os jobs via `docker save` / `docker load`).

---

## Ferramentas e regras de bloqueio

### 1. Gitleaks — detecção de segredos

- Checkout com `fetch-depth: 0` e `gitleaks git --log-opts="--full-history HEAD"`: analisa **todos os commits**
  do histórico, não só os arquivos atuais.
- Regras padrão do Gitleaks ([`.gitleaks.toml`](.gitleaks.toml) com `useDefault = true`), **sem allowlist**.
- `--redact`: o valor do segredo nunca aparece no log.
- **Bloqueio:** o Gitleaks termina com código ≠ 0 se encontrar qualquer segredo e o job falha.
- Relatório: artifact `gitleaks-report` (JSON).
- Binário baixado do release oficial com verificação de checksum SHA-256.

### 2. SonarCloud — análise estática (SAST) e Quality Gate

- Análise via CI (análise automática desligada no SonarCloud), com a cobertura dos testes.
- Em PRs o SonarCloud analisa só o **código novo do PR** e comenta o resultado no próprio PR.
- New Code definido como **Previous version** (`sonar.projectVersion` = conteúdo de `VERSION`).
- **Quality Gate (condições sobre o código novo):**

  | Métrica (New Code) | Condição para passar |
  |---|---|
  | Security Rating | A (nenhuma vulnerabilidade) |
  | Reliability Rating | A (nenhum bug) |
  | Maintainability Rating | A |
  | Security Hotspots Reviewed | 100% |
  | Duplicated Lines | ≤ 3% |

- **Bloqueio:** `sonar.qualitygate.wait=true` faz o scanner esperar o resultado e falhar o job
  (exit code 3) quando o Quality Gate é reprovado.

### 3. Trivy — dependências e imagem

Cada scan roda em **dois passos**:

| Passo | Severidades | Comportamento |
|---|---|---|
| Relatório completo | LOW, MEDIUM, HIGH, CRITICAL | `--exit-code 0` (**nunca bloqueia**). Vai para o resumo da execução (*Summary*), para os artifacts `trivy-deps-report` / `trivy-image-report` (tabela + SARIF) e para a aba **Security → Code scanning** |
| Gate | CRITICAL, HIGH | `--ignore-unfixed --exit-code 1`: **bloqueia** quando existe CVE CRITICAL/HIGH **com correção disponível** |

Ou seja:

- **CRITICAL/HIGH com correção** → bloqueia o PR e impede a publicação.
- **LOW/MEDIUM** → ficam registradas no relatório, sem bloquear.
- **CRITICAL/HIGH sem correção** (ex.: pacotes do Debian ainda sem patch) → registradas no relatório, sem
  bloquear, pois não há ação possível além de acompanhar a correção.

### 4. Syft — SBOM

- Gera o SBOM da imagem Docker construída, nos formatos **SPDX** (`sbom-<VERSION>.spdx.json`) e
  **CycloneDX** (`sbom-<VERSION>.cyclonedx.json`), com todos os componentes e versões (pacotes do Debian e
  pacotes Python).
- Publicado como artifact **`sbom-<VERSION>`** de cada execução. Cópia da versão 3.1 em
  [`evidencias/sbom-3.1.spdx.json`](evidencias/sbom-3.1.spdx.json) e
  [`evidencias/sbom-3.1.cyclonedx.json`](evidencias/sbom-3.1.cyclonedx.json).

### Proteção da branch `main`

Ruleset na `main` exigindo Pull Request e os status checks `Gitleaks`, `Testes`, `SonarCloud`,
`Trivy (dependências)` e `Build, Trivy (imagem) e SBOM`, sem permissão de bypass, com force push e deleção
bloqueados. Com isso, um PR com qualquer verificação reprovada **não pode ser mergeado**.

### Outras medidas de segurança

- Actions de terceiros fixadas por **SHA de commit** (proteção contra tags comprometidas).
- `permissions: contents: read` por padrão; `security-events: write` só nos jobs que enviam SARIF.
- Dependências travadas com **hash** (`pip-compile --generate-hashes`) e instaladas com
  `--only-binary :all: --require-hashes` (sem execução de `setup.py`, pacote adulterado é recusado).
- Credenciais apenas em Secrets (`REGISTRY_USERNAME`, `REGISTRY_TOKEN`, `SONAR_TOKEN`).

---

## Demonstrações (falha → bloqueio → correção → sucesso)

| PR | O que foi introduzido | Verificação que falhou | Correção |
|---|---|---|---|
| [#1](https://github.com/paulohenrique64/hello-world-cicd/pull/1) | `pip install` sem travar versões/hashes e sem `--only-binary` no Dockerfile | **SonarCloud**: Quality Gate reprovado (Security Rating C; regras `docker:S8541` e `docker:S8544`) | Lock com hashes + `--only-binary :all: --require-hashes` → Quality Gate passou |
| [#2](https://github.com/paulohenrique64/hello-world-cicd/pull/2) | `python-multipart==0.0.6` (CVE-2024-24762 e outras 4 HIGH) para a importação via CSV | **Trivy** (dependências e imagem): 5 HIGH com correção | Atualização para `0.0.32` no mesmo PR → todos os checks verdes → merge e publicação da 3.2 |
| [#3](https://github.com/paulohenrique64/hello-world-cicd/pull/3) | Reintrodução de `python-multipart==0.0.6` com a proteção da `main` ativa | **Trivy** + **merge bloqueado** pela branch protection | PR fechado sem merge (a correção já está na `main`) |

Também encontrado pelo Trivy antes do PR #1 (scan local): bibliotecas embutidas no `pip` da imagem base
(`msgpack`, `urllib3`) com HIGH corrigível → `pip` removido da imagem final.

A versão vulnerável **nunca foi publicada**: em PRs o job *Publicar imagem* fica *skipped*, e o Docker Hub
só tem as versões 3.0, 3.1 e 3.2 (corrigida).

---

## Executar localmente

```bash
# Testes
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements.txt -r requirements-dev.txt
.venv/bin/pytest --cov=app

# Verificações de segurança
gitleaks git . --redact -v
trivy fs --scanners vuln --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 .
docker build -t hello-world-cicd:local .
trivy image --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 hello-world-cicd:local
syft hello-world-cicd:local -o spdx-json=sbom.spdx.json

# Container
docker run -p 8080:8080 hello-world-cicd:local
curl http://localhost:8080/health
curl -X POST http://localhost:8080/tasks -H 'Content-Type: application/json' -d '{"title":"Estudar"}'
curl -F "file=@tarefas.csv" http://localhost:8080/tasks/import
curl http://localhost:8080/tasks
```

Para atualizar dependências: editar o `.in` e regenerar o lock com
`pip-compile --generate-hashes --allow-unsafe requirements.in`.

## Executar a imagem publicada

```bash
docker pull paulohenrique64/hello-world-cicd:3.2
docker run -p 8080:8080 paulohenrique64/hello-world-cicd:3.2
curl http://localhost:8080/health
```

---

## Evidências

Mapeamento completo por entregável em [`ENTREGA.md`](ENTREGA.md). Arquivos em [`evidencias/`](evidencias/):

**Atividades anteriores (v1.0 e v2.0):** `00` a `08`.

**Preparação**
- `09-sonarcloud-analise-automatica-off.png` — análise automática do SonarCloud desligada (análise via CI)
- `10-sonarcloud-quality-gate.png` — Quality Gate e condições sobre o código novo
- `11-sonarcloud-new-code.png` — definição de New Code
- `12-secrets.png` — secrets do repositório (somente nomes)
- `13-gitleaks-historico-local.png` — Gitleaks local no histórico: nenhum vazamento

**Aplicação v3.0**
- `14-testes-locais.txt` — testes e cobertura
- `15-trivy-local-baseline.txt` / `.png` — Trivy local (encontrou HIGH no `pip` da imagem)
- `16-app-v3-endpoints.txt` / `.png` — endpoints funcionando no container

**PR #1 — pipeline DevSecOps (SonarCloud bloqueando e depois aprovando)**
- `17-pr1-sonar-gate-falhou.png` — check SonarCloud reprovado no PR
- `18-sonar-pr1-security-rating.png` — Security Rating C no código novo
- `19-sonar-pr1-issues-dockerfile.png` — vulnerabilidades S8541/S8544 no Dockerfile
- `20-pr1-checks-verdes.png` — após a correção, todos os checks verdes
- `21-pr1-sonarcloud-comentario.png` — Quality Gate passed
- `22-pr1-grafo-publicacao-skipped.png` — em PR, *Publicar imagem* não executa

**Execução na `main` após o merge do PR #1**
- `23-main-grafo-completo.png` — todos os jobs verdes, inclusive a publicação
- `24-trivy-relatorio-nao-bloqueante.png` — relatório do Trivy com LOW/MEDIUM sem bloquear
- `25-artifacts.png` — artifacts: SBOM, relatórios Trivy/Gitleaks, cobertura
- `26-sbom-conteudo.txt` — componentes e versões do SBOM (+ `sbom-3.1.spdx.json` / `sbom-3.1.cyclonedx.json`)
- `27-registry-v3.1.png` — imagem 3.1 no Docker Hub

**PR #2 — Requisito 5: dependência com CVE**
- `28-pr-cve-diff.png` — `python-multipart==0.0.6` introduzido
- `29-pr-cve-alerta-trivy.png` — alerta do Trivy no PR: CVE-2024-24762, HIGH, instalada 0.0.6, corrigida 0.0.7
- `30-pr-cve-checks-falhando.png` — checks do Trivy reprovados, *Publicar imagem* skipped
- `31-trivy-cve-relatorio.png` — trecho do relatório do Trivy com as CVEs
- `32-pr-cve-publicacao-skipped.png` — grafo: falha no Trivy, publicação não executada
- `33-pr-cve-execucoes.png` — execução na abertura (falhou) e na atualização (passou)
- `34-pr-cve-corrigido.png` — PR com a correção e todos os checks verdes
- `35-trivy-cve-corrigido.png` — gate do Trivy aprovado após a correção
- `36-main-pos-correcao.png` — execução na `main` após o merge, com publicação
- `37-registry-v3.2.png` — Docker Hub com a 3.2 corrigida

**Proteção de branch e PR #3 — merge bloqueado**
- `38-branch-protection-regra.png` — ruleset da `main` (PR obrigatório, sem bypass)
- `39-branch-protection-checks.png` — status checks obrigatórios
- `40-pr3-merge-bloqueado.png` — PR com CVE: checks reprovados e **merge bloqueado**
