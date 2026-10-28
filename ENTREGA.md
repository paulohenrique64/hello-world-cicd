# Trabalho Prático — Pipeline DevSecOps com GitHub Actions

**Aluno:** Paulo Henrique
**Disciplina:** DevOps — UFLA / DCC
**Aplicação:** API de tarefas em Python/FastAPI + SQLite, imagem Docker publicada no Docker Hub

Este documento segue a ordem dos entregáveis do enunciado. Todas as imagens e arquivos citados estão em
[`evidencias/`](evidencias/). A documentação técnica completa está no [`README.md`](README.md).

---

## 1. Repositório GitHub com código-fonte e workflows YAML

**https://github.com/paulohenrique64/hello-world-cicd**

| Arquivo | Conteúdo |
|---|---|
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | Pipeline DevSecOps (Gitleaks, testes, SonarCloud, Trivy, Syft, build e publicação) |
| [`sonar-project.properties`](sonar-project.properties) | Configuração da análise do SonarCloud |
| [`.gitleaks.toml`](.gitleaks.toml) | Configuração do Gitleaks (regras padrão, sem allowlist) |
| [`Dockerfile`](Dockerfile) | Imagem `python:3.13-slim`, sem root, sem `pip`, dependências com hash |
| [`app/`](app/), [`tests/`](tests/) | Código da aplicação e testes (100% de cobertura) |

| Recurso | Link |
|---|---|
| Execuções do pipeline | https://github.com/paulohenrique64/hello-world-cicd/actions |
| Pull Requests | https://github.com/paulohenrique64/hello-world-cicd/pulls?q=is%3Apr |
| SonarCloud | https://sonarcloud.io/project/overview?id=paulohenrique64_hello-world-cicd |
| Docker Hub | https://hub.docker.com/r/paulohenrique64/hello-world-cicd/tags |

---

## 2. Evidência de execução do pipeline com as ferramentas integradas

Execução na `main` após o merge do PR #1:
https://github.com/paulohenrique64/hello-world-cicd/actions/runs/40620022197

| Evidência | O que comprova |
|---|---|
| `23-main-grafo-completo.png` | Os 6 jobs (Gitleaks, Testes, SonarCloud, Trivy dependências, Build/Trivy imagem/SBOM, Publicar imagem) executados com sucesso |
| `22-pr1-grafo-publicacao-skipped.png` | Em Pull Request todas as verificações rodam e a publicação **não** executa |
| `24-trivy-relatorio-nao-bloqueante.png` | Relatório do Trivy com LOW/MEDIUM registrados **sem bloquear** |
| `21-pr1-sonarcloud-comentario.png` | SonarCloud integrado ao PR: Quality Gate passed |
| `09`, `10`, `11` | SonarCloud: análise via CI, Quality Gate sobre o código novo, definição de New Code |
| `12-secrets.png` | Credenciais apenas em Secrets (`REGISTRY_*`, `SONAR_TOKEN`) |
| `13-gitleaks-historico-local.png` | Gitleaks no histórico completo: nenhum vazamento |
| `38`, `39` | Proteção da `main` exigindo os checks de segurança |
| `27-registry-v3.1.png`, `37-registry-v3.2.png` | Publicação no Docker Hub somente após as verificações |

---

## 3. Pull Request bloqueado e trecho do relatório que aponta a vulnerabilidade

**Requisito 5** — branch de teste `teste/dependencia-vulneravel`, PR
[#2](https://github.com/paulohenrique64/hello-world-cicd/pull/2): a feature de importação via CSV introduziu
`python-multipart==0.0.6`, com CVE conhecida e correção disponível.

Execução reprovada: https://github.com/paulohenrique64/hello-world-cicd/actions/runs/40622011050

| Evidência | O que comprova |
|---|---|
| `28-pr-cve-diff.png` | Dependência vulnerável introduzida no PR |
| `29-pr-cve-alerta-trivy.png` | Trivy aponta **CVE-2024-24762**, pacote `python-multipart`, severidade **HIGH**, instalada **0.0.6**, corrigida em **0.0.7** |
| `31-trivy-cve-relatorio.png` | Trecho do relatório do Trivy: 5 CVEs HIGH com correção disponível |
| `30-pr-cve-checks-falhando.png` | Checks `Trivy (dependências)` e `Build, Trivy (imagem) e SBOM` reprovados |
| `32-pr-cve-publicacao-skipped.png` | A publicação não executou — a versão vulnerável **não foi publicada** |
| `40-pr3-merge-bloqueado.png` | Com a proteção da `main` ativa (PR [#3](https://github.com/paulohenrique64/hello-world-cicd/pull/3)), o PR com a mesma CVE fica com o **merge bloqueado** |

Gate adicional demonstrado no PR [#1](https://github.com/paulohenrique64/hello-world-cicd/pull/1) (SonarCloud):

| Evidência | O que comprova |
|---|---|
| `17-pr1-sonar-gate-falhou.png` | Check `SonarCloud` reprovado: Quality Gate failed |
| `18-sonar-pr1-security-rating.png` | Security Rating C no código novo |
| `19-sonar-pr1-issues-dockerfile.png` | Vulnerabilidades `docker:S8541` e `docker:S8544` apontadas no Dockerfile |

---

## 4. Execução aprovada após a correção

No mesmo PR #2 a dependência foi atualizada para `python-multipart==0.0.32`.

Execução aprovada no PR: https://github.com/paulohenrique64/hello-world-cicd/actions/runs/40622812484
Execução na `main` após o merge: https://github.com/paulohenrique64/hello-world-cicd/actions/runs/40623062635

| Evidência | O que comprova |
|---|---|
| `33-pr-cve-execucoes.png` | Execução na abertura do PR (falhou) e na atualização (passou) — disparo automático |
| `34-pr-cve-corrigido.png` | PR com o commit de correção e todos os checks verdes |
| `35-trivy-cve-corrigido.png` | Gate do Trivy aprovado após a correção |
| `36-main-pos-correcao.png` | Pipeline completo na `main`, incluindo a publicação |
| `37-registry-v3.2.png` | Somente a versão corrigida (3.2) publicada |

SonarCloud após a correção do PR #1: `20-pr1-checks-verdes.png` e `21-pr1-sonarcloud-comentario.png`.

---

## 5. Arquivo SBOM publicado como artifact do GitHub Actions

| Evidência | O que comprova |
|---|---|
| `25-artifacts.png` | Artifact **`sbom-3.1`** publicado na execução da `main` (junto com os relatórios do Trivy e do Gitleaks) |
| [`evidencias/sbom-3.1.spdx.json`](evidencias/sbom-3.1.spdx.json) | SBOM no formato SPDX baixado do artifact |
| [`evidencias/sbom-3.1.cyclonedx.json`](evidencias/sbom-3.1.cyclonedx.json) | SBOM no formato CycloneDX baixado do artifact |
| `26-sbom-conteudo.txt` | Componentes e versões listados no SBOM (pacotes do Debian e Python: `fastapi 0.162.0`, `uvicorn 0.54.0`, …) |

Cada execução do pipeline gera o artifact `sbom-<VERSION>`.

---

## 6. README.md

[`README.md`](README.md): aplicação, gatilhos e jobs do pipeline, **uma seção por ferramenta com a regra de
bloqueio exata**, proteção de branch, demonstrações, execução local e lista de evidências.

---

## Resumo por critério de avaliação

| Critério | Onde está |
|---|---|
| Gitleaks integrado e bloqueante | Job `Gitleaks` (histórico completo, falha com qualquer segredo, check obrigatório) — README §1; evidências `13`, `23`, `38`/`39` |
| SonarCloud e Quality Gate | Quality Gate sobre o código novo, `qualitygate.wait=true`; falha real e correção no PR #1 — evidências `09`–`11`, `17`–`21` |
| Trivy e critérios de bloqueio | Gate CRITICAL/HIGH com correção, relatório LOW/MEDIUM não bloqueante, deps + imagem — evidências `24`, `29`–`31`, `35` |
| SBOM gerado e disponibilizado | Syft (SPDX + CycloneDX), artifact `sbom-<VERSION>` — evidências `25`, `26`, `sbom-3.1.*.json` |
| Evidências de bloqueio e correção | PR #2 (falha → correção → sucesso), PR #3 (merge bloqueado), versão vulnerável nunca publicada — evidências `28`–`40` |
| Organização e documentação | README, ENTREGA.md, commits pequenos e descritivos, evidências numeradas |
