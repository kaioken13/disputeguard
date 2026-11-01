# DisputeGuard AI

Agente autônomo de resolução de disputas de e-commerce e delivery, exposto como API REST via FastAPI.

**Versão:** 1.0.0

## Visão geral

O serviço recebe os dados de uma disputa aberta por um cliente (`CustomerDisputeInput`), delega a análise ao agente (`resolve_dispute`) e retorna uma decisão estruturada (`DisputeResolution`).

```
Cliente ──► POST /api/v1/dispute/resolve ──► resolve_dispute (src.agent) ──► DisputeResolution
```

## Estrutura do projeto

```
.
├── main.py              # Aplicação FastAPI (este arquivo)
└── src/
    ├── schemas.py       # CustomerDisputeInput, DisputeResolution
    └── agent.py         # resolve_dispute (lógica do agente)
```

## Requisitos

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic (usado nos schemas)

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install fastapi uvicorn pydantic
```

## Executando

```bash
uvicorn main:app --reload
```

> Ajuste `main` para o nome real do arquivo que contém a instância `app`.

A API sobe em `http://127.0.0.1:8000`. A documentação interativa fica disponível em:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### `GET /health`

Verifica se o serviço está no ar.

**Resposta `200`**

```json
{
  "status": "healthy",
  "service": "disputeguard"
}
```

### `POST /api/v1/dispute/resolve`

Processa uma disputa e retorna a resolução decidida pelo agente.

| Item | Valor |
|---|---|
| Corpo da requisição | `CustomerDisputeInput` |
| Resposta de sucesso | `DisputeResolution` (`200`) |
| Erro | `500` com `detail` contendo a mensagem da exceção |

**Exemplo de requisição**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/dispute/resolve \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

> Os campos de entrada e saída estão definidos em `src/schemas.py`. Consulte o Swagger em `/docs` para o contrato completo.

**Resposta de erro `500`**

```json
{
  "detail": "mensagem do erro"
}
```

## Tratamento de erros

Qualquer exceção levantada por `resolve_dispute` é capturada e convertida em `HTTPException` com status `500`, expondo `str(exc)` no campo `detail`.

## Licença

Defina a licença do projeto aqui.
