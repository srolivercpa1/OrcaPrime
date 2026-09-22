# API de licenciamento — v1

Base: domínio HTTPS do proprietário. Corpos e respostas em JSON; nenhuma credencial em parâmetros de URL. A chave privada Ed25519 e o segredo HMAC nunca deixam o servidor. Endpoints administrativos exigem HTTP Basic (usuário e senha), sempre sobre TLS.

## Cliente

`POST /v1/activate`

```json
{"code":"AB23-CD45-EF67-GH89-JK23","device_id":"identificador-aleatorio-da-instalacao","nonce":"nonce-aleatorio-unico-por-pedido"}
```

O código acima é somente um exemplo, não é uma licença válida. Dispositivo: 16–64 caracteres alfanuméricos, `_` ou `-`. Nonce: 16–100, mesmo alfabeto. Não são enviados nome do computador, usuário do Windows, endereço MAC, serial ou documento do cliente.

`POST /v1/validate`

```json
{"token":"TOKEN_DE_DISPOSITIVO_RECEBIDO_NA_ATIVACAO","device_id":"identificador-aleatorio-da-instalacao","nonce":"outro-nonce-aleatorio-por-pedido"}
```

Sucesso: `{"payload":"BASE64_JSON","signature":"BASE64_ASSINATURA"}`. A assinatura cobre exatamente os bytes do JSON decodificado, sem reserialização no cliente. Conteúdo: license_id, mask, plan, status, device_id, nonce, issued_at (Unix UTC), expires_at (Unix UTC ou null), lease_seconds (até 900). Somente a resposta de ativação inclui device_token.

O cliente verifica assinatura, dispositivo, nonce, status e validade relativa à hora do servidor. A autorização local dura o lease medido com relógio monotônico e exige nova validação ao abrir. Uma resposta guardada não ativa novamente o cliente, porque o nonce é novo a cada chamada. O executável de desktop não é inviolável contra alguém que o modifique; esta arquitetura não promete impedir engenharia reversa.

Erros 400: `code` = invalid, blocked, expired, cancelled, limit; `detail` = mensagem em português. Erros de campos: 422, sem reproduzir códigos/tokens recebidos. 401 para autenticação administrativa ausente/inválida; 403 para origem incorreta; 413 para excesso de Content-Length; 429 para limite de chamadas; 503 para capacidade do limitador. Cliente trata falha de conexão e 5xx como indisponibilidade temporária, sem estender o lease.

## Administração

| Método / caminho | Função / corpo |
|---|---|
| GET /admin | Interface do proprietário |
| GET /admin/licenses?q= | Busca por ID, máscara, plano e situação |
| POST /admin/licenses | `{"plan":"PRO","days":30,"device_limit":1}` |
| GET /admin/licenses/{id} | Metadados e lista de dispositivos |
| PATCH /admin/licenses/{id} | Campos opcionais: plan, status, expires_at, device_limit |
| POST /admin/licenses/{id}/renew | `{"days":90}`; 0 = permanente |
| DELETE /admin/licenses/{id}/devices/{device} | Libera a ativação |
| GET /health | Disponibilidade do processo |

Status aceitos: ATIVA/BLOQUEADA/EXPIRADA/CANCELADA. Planos: GRATIS/PRO/EMPRESA. Períodos: 0/30/90/365; limite: 1–1000. Expiração pode ser alterada somente após a primeira ativação; para licença pendente use renovar para ajustar duração. As operações ficam no registro audit (ação, licença, hora), sem código de ativação ou token.

Não há endpoint para recuperar códigos completos: emita outra licença e cancele a anterior se o código se perder. A busca nunca exige ou expõe o código completo. Na administração, a data é exibida no fuso do navegador; o armazenamento é UTC.
