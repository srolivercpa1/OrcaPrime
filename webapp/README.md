# OrçaPrime Web 1.0

Versão web independente, com layout inspirado na referência do Apex e identidade OrçaPrime. Desenvolvido por Sketch Inc.

## Implementado
- Login com senha protegida por hash, cookie HttpOnly e opção manter conectado; troca de senha encerra sessões.
- Empresas independentes, painel do proprietário para criar, bloquear, reativar e renovar assinaturas.
- Usuários com perfis, revogação e exclusão; proteção do próprio administrador.
- Painel com totais reais, menu lateral, formulários arredondados, rolagem e adaptação a celular.
- Clientes, orçamentos, aprovação/conversão em OS, exclusão confirmada.
- OS com estado de entrada, acessórios, técnico, prazo, diagnóstico, serviço executado, histórico e lista de entregues.
- Fotos privadas em JPEG otimizado, logo persistente e PDFs de OS/garantia.
- Estoque por categoria, consumo de peças idempotente e devolução na exclusão de OS não entregue.
- Contas a pagar/receber, pagamento confirmado, saldo e exportação CSV. Pagamentos confirmados são preservados; estorne com lançamento inverso.
- Auditoria e backups diários GZIP, retenção de 14 arquivos e restauração por comando.

## Publicação
A tentativa de criar um projeto Railway em 01/10/2026 foi bloqueada pelo limite de recursos do plano gratuito. Nenhuma URL pública foi publicada e nenhum serviço existente foi alterado.

O pacote está preparado para um servidor com Docker e domínio apontado para ele:

1. Baixe o código desta branch e copie `.env.web.example` para `.env.web`.
2. Defina seu domínio e uma senha de banco aleatória (use caracteres alfanuméricos para evitar problemas na URL de conexão).
3. Execute `docker compose --env-file .env.web -f compose.web.yml up -d --build`.
4. Crie o proprietário, sem senha padrão: `docker compose --env-file .env.web -f compose.web.yml exec web python -m webapp.cli init`.
5. Abra `https://SEU_DOMINIO`, entre com o proprietário e crie a primeira empresa em **Empresas e licenças**. O e-mail/senha informados nessa criação são o acesso inicial do administrador da empresa.
6. Entre como empresa para cadastrar funcionários, clientes e atendimentos. Troque a senha inicial pelo menu **Alterar minha senha**.

Em Railway ou outra plataforma: criar PostgreSQL com disco persistente, usar `webapp/Dockerfile`, configurar `DATABASE_URL`, `PUBLIC_ORIGIN` e volume para `BACKUP_DIR`, porta 8080, healthcheck `/health`. Executar `python -m webapp.cli init` no terminal privado do serviço. Nunca colocar senhas no Git. Usar uma instância/worker enquanto o limitador de login é local ao processo.

## Desenvolvimento local

```sh
python -m pip install -r requirements-web.txt
export DATABASE_URL=sqlite:///orcaprime-web-local.db
export PUBLIC_ORIGIN=http://127.0.0.1:8080
python -m webapp.cli init
python -m uvicorn webapp.server:application --factory --host 127.0.0.1 --port 8080
```
SQLite é apenas para desenvolvimento. Em produção o servidor exige HTTPS e PostgreSQL. Não usar banco local como armazenamento de produção concorrente.

## Backup e recuperação

O processo, com BACKUP_DIR configurado, produz um snapshot GZIP ao iniciar e depois uma vez por dia UTC. Fotos e logotipos estão incluídos. Não restaura sessões antigas. Dados são privados e não há rota de download pública. O volume é persistente no Compose, mas uma cópia no mesmo servidor não protege contra perda do servidor: configure adicionalmente backup do provedor ou cópia externa privada.

Backup manual: `python -m webapp.cli backup --directory /data/backup`.
Restauração: pare o serviço, configure DATABASE_URL para um banco vazio e execute `python -m webapp.cli restore --file caminho.json.gz`. O comando recusa sobrescrever um banco que contenha registros. Teste a recuperação antes de operar comercialmente.

## Limites desta entrega

Esta versão implementa o fluxo básico descrito acima; não é uma cópia de todas as funções comerciais do Apex. Ainda não inclui PDV de vendas, emissão fiscal, cobrança automática, integração WhatsApp, recuperação de senha por e-mail, migração do banco Windows, sincronização desktop/web ou armazenamento externo de fotos. Relatórios financeiros têm filtro pela data de cadastro e exportação do período; gráficos históricos estão pendentes. Orçamentos e OS têm um valor total informado e consumo de peças separado; não há composição detalhada de mão de obra/itens no orçamento. Imprimir o PDF abre o diálogo do navegador/leitor e depende da impressora local.

O bloqueio de assinatura desativa o acesso da empresa e invalida as sessões, sem apagar os dados. Exclusão de cliente também remove suas OS, fotos e orçamentos. Serviços já entregues mantêm a baixa de estoque; serviços não entregues devolvem as peças. Lançamentos financeiros independentes continuam preservados.

## Validação

`python -m pip install -r requirements-dev.txt -r requirements-web.txt`
`python -m pytest -q`

A CI web testa também PostgreSQL, instala o navegador de teste e verifica navegação, cadastro, alinhamento à direita no computador e rolagem no celular. Artefatos de imagem permitem inspecionar o resultado.
