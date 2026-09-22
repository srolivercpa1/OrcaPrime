# Servidor de licenças e painel do proprietário

## Requisitos

Servidor Linux sob seu controle, domínio apontando para ele, Docker Engine/Compose, proxy HTTPS Caddy (incluído no Compose), Python 3.12 para a preparação inicial. O custo e a contratação do servidor não estão incluídos. Não use hospedagem sem disco persistente: o banco precisa permanecer entre reinicializações.

## Preparar

Transfira o projeto para uma pasta privada no servidor e execute:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-server.txt
python -m scripts.setup_server
```

Informe o domínio HTTPS real, nome de usuário e senha administrativa de pelo menos 16 caracteres. O comando gera:

- `secrets/signing.pem`: chave privada Ed25519; somente no servidor.
- `.env`: hash scrypt da senha, segredo HMAC e caminhos de produção.
- `config/client.json`: URL e chave pública, utilizadas no aplicativo.

O comando recusa sobrescrever uma configuração existente. Guarde backup privado de `.env`, `secrets/signing.pem` e banco. Perder o segredo HMAC impede validar códigos existentes; perder a chave de assinatura exige distribuir clientes com nova chave pública.

O container executa como usuário 10001. Permita que esse usuário leia a chave montada, sem torná-la pública:

```bash
sudo python3 scripts/server_permissions.py
docker compose up -d --build
docker compose logs --tail=50 licenses
```

O serviço da API não expõe portas ao host. O Compose inclui Caddy para HTTPS nas portas 80/443 e um volume persistente para seus certificados. O domínio deve apontar para esse servidor e essas portas precisam estar livres e acessíveis. O volume Docker `license-data` guarda o banco. **Não execute `docker compose down -v` em produção**, pois apaga os volumes.

## HTTPS e proxy confiável

O `Caddyfile` usa o domínio de `ORCAPRIME_PUBLIC_ORIGIN`, emite o certificado TLS e limita o corpo das requisições a 16 KB, inclusive sem Content-Length. Não é necessário instalar Caddy no host. A API confia em cabeçalhos encaminhados somente do IP privado fixo do proxy, `172.30.83.2`. A rede isolada usa `172.30.83.0/24`; se essa faixa já existir na infraestrutura, altere a rede, ambos os IPs e o argumento `--forwarded-allow-ips` de forma consistente.

Verifique `https://SEU_DOMINIO/health`: resposta `{"status":"ok"}`. Acesse `/admin`, informe usuário e senha. A API não tem página pública de documentação nem endpoint administrativo sem autenticação. Como se usa HTTP Basic, fechar a aba pode não limpar as credenciais; utilize um perfil de navegador reservado ao proprietário e encerre a sessão do navegador ao terminar.

Nesta configuração, a aplicação aplica 120 solicitações por minuto por IP real encaminhado pelo proxy confiável, com categorias separadas para administração e clientes. Clientes que compartilham um IP público (NAT) compartilham esse limite. Um 429 é temporário e não revoga o lease já válido no aplicativo. Execute um único worker conforme o Compose; para múltiplas réplicas, substitua o limitador em memória por um limitador compartilhado.

## Gerar e administrar licenças

No painel:

1. Escolha GRÁTIS, PRO ou EMPRESA.
2. Escolha 30, 90, 365 dias ou Permanente.
3. Defina limite de dispositivos e clique em **GERAR LICENÇA**.
4. Copie o código mostrado e entregue ao cliente. O código completo é exibido somente nessa resposta; o servidor conserva um HMAC e uma máscara, não o texto original.
5. Pesquise por ID, máscara, plano ou situação; **Gerenciar** abre detalhes, datas e dispositivos.

A vigência começa na primeira ativação. Licenças permanentes não expiram por tempo, mas podem ser bloqueadas/canceladas. Uma licença ATIVA ainda sem ativação aparece com vencimento “Após ativação”. Para bloquear/desbloquear/cancelar, selecione a situação e salve. “Renovar e ativar” muda para ATIVA e soma dias ao maior valor entre agora e o vencimento anterior; para uma licença ainda não ativada, define o prazo que começará na ativação.

Liberar um dispositivo invalida seu token. A mudança será percebida pelo cliente na próxima validação, ou ao fim do lease vigente. Reativar o mesmo dispositivo não consome vaga adicional e troca seu token. Não reduza o limite abaixo da quantidade de dispositivos ativos: libere os excedentes primeiro.

## Backup e atualização do servidor

Faça backup consistente usando sqlite3.Connection.backup; não copie um banco enquanto há transações sem mecanismo apropriado. Uma alternativa operacional simples é parar o serviço, copiar o volume com ferramenta do servidor e iniciá-lo novamente. Faça também backup privado de `.env` e da chave, preservando permissões. Teste a restauração antes de depender do backup.

Para atualizar código: preserve volume e segredos, substitua os fontes e execute `docker compose up -d --build`. Esta versão não contém migrações para um esquema futuro. Atualizações que alterem esquema exigem plano de migração e backup antes da implantação.
