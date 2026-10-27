# hello-world-cicd

Exercício prático — Docker, GitHub Actions e Container Registry.

Aplicação Python/FastAPI (API de tarefas com banco SQLite), empacotada em Docker e publicada
automaticamente no Docker Hub por uma pipeline do GitHub Actions a cada push na branch `main`.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/hello` | Texto de boas-vindas |
| GET | `/health` | Status da aplicação e do banco |
| GET | `/tasks` | Lista as tarefas |
| POST | `/tasks` | Cria uma tarefa (`{"title": "...", "description": "..."}`) |
| GET | `/tasks/{id}` | Busca uma tarefa |
| PUT | `/tasks/{id}` | Atualiza uma tarefa (`title`, `description`, `done`) |
| DELETE | `/tasks/{id}` | Remove uma tarefa |

O banco SQLite fica em `DB_PATH` (na imagem: `/app/data/app.db`). Todas as queries são parametrizadas.

| Item | Local |
|---|---|
| Código da aplicação | [`app/main.py`](app/main.py), [`app/db.py`](app/db.py), [`app/schemas.py`](app/schemas.py) |
| Testes | [`tests/test_api.py`](tests/test_api.py) |
| Dockerfile | [`Dockerfile`](Dockerfile) |
| Pipeline | [`.github/workflows/docker.yml`](.github/workflows/docker.yml) |
| Versão da imagem | [`VERSION`](VERSION) (vira a tag da imagem) |
| Imagem no registry | https://hub.docker.com/r/paulohenrique64/hello-world-cicd/tags |
| Execuções da pipeline | https://github.com/paulohenrique64/hello-world-cicd/actions |

## Executar localmente

```bash
# Testes
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/pytest --cov=app

# Container
docker build -t hello-world-cicd:3.0 .
docker run -p 8080:8080 hello-world-cicd:3.0
curl http://localhost:8080/health
curl -X POST http://localhost:8080/tasks -H 'Content-Type: application/json' -d '{"title":"Estudar"}'
curl http://localhost:8080/tasks
```

## Executar a imagem publicada

```bash
docker pull paulohenrique64/hello-world-cicd:1.0
docker run -p 8080:8080 paulohenrique64/hello-world-cicd:1.0
curl http://localhost:8080/hello   # Hello World

docker pull paulohenrique64/hello-world-cicd:2.0
docker run -p 8080:8080 paulohenrique64/hello-world-cicd:2.0
curl http://localhost:8080/hello   # Hello World 2
```

## Pipeline

Disparada por push na `main`: checkout → testes unitários → build da imagem → verificação da imagem → smoke test do
endpoint → login no Docker Hub → push das tags `<VERSION>` e `latest`.

As credenciais ficam nos Secrets do repositório (`REGISTRY_USERNAME` e `REGISTRY_TOKEN`) e nunca
aparecem no arquivo da pipeline.

## Evidências

Ver a pasta [`evidencias/`](evidencias/).

### Configuração
- Secrets do repositório (somente nomes visíveis): `evidencias/00-secrets.png`

### Versão 1.0 — Hello World
- Build local: `evidencias/01-build-local-v1.txt` / `.png`
- Execução local + curl: `evidencias/02-run-local-v1.txt` / `.png`
- Pipeline disparada por push: `evidencias/03-pipeline-v1-lista.png`
- Passos da pipeline (build, teste, push): `evidencias/03-pipeline-v1-passos.png`
- Registry com tag 1.0: `evidencias/04-registry-v1.png`
- Pull + execução da imagem do registry: `evidencias/05-pull-run-v1.txt` / `.png`

### Versão 2.0 — Hello World 2
- Pipeline disparada pelo push da v2: `evidencias/06-pipeline-v2-lista.png`
- Passos da pipeline v2: `evidencias/06-pipeline-v2-passos.png`
- Registry com tags 1.0 e 2.0: `evidencias/07-registry-v2.png`
- Pull + execução das imagens 1.0 e 2.0 do registry: `evidencias/08-pull-run-v2.txt` / `.png`
