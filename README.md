# hello-world-cicd

Exercício prático — Docker, GitHub Actions e Container Registry.

Aplicação Python/FastAPI com o endpoint `GET /hello`, empacotada em Docker e publicada automaticamente
no Docker Hub por uma pipeline do GitHub Actions a cada push na branch `main`.

| Item | Local |
|---|---|
| Código da aplicação | [`app/main.py`](app/main.py) |
| Dockerfile | [`Dockerfile`](Dockerfile) |
| Pipeline | [`.github/workflows/docker.yml`](.github/workflows/docker.yml) |
| Versão da imagem | [`VERSION`](VERSION) (vira a tag da imagem) |
| Imagem no registry | https://hub.docker.com/r/paulohenrique64/hello-world-cicd/tags |
| Execuções da pipeline | https://github.com/paulohenrique64/hello-world-cicd/actions |

## Executar localmente

```bash
docker build -t hello-world-cicd:1.0 .
docker run -p 8080:8080 hello-world-cicd:1.0
curl http://localhost:8080/hello   # Hello World
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

Disparada por push na `main`: checkout → build da imagem → verificação da imagem → smoke test do
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
