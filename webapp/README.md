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

## Hospedagem gratuita: Render + Neon

O arquivo `render.yaml` cria **somente um Web Service gratuito**, sem disco ou PostgreSQL do Render. O banco externo Neon guarda registros, fotos e logotipos. A aplicação continua na versão 1.0. O Render pode suspender o serviço por inatividade; o primeiro acesso pode demorar. As cotas de banco, transferência e execução dos provedores precisam ser acompanhadas.

1. No Neon, utilize o projeto exclusivo do OrçaPrime Web existente ou crie um para uma nova instalação. A configuração Render usa Ohio; mantenha o banco próximo do serviço. Prepare as tabelas com a conta de administração e use uma conexão PostgreSQL com `sslmode=require` de um usuário restrito à aplicação em `DATABASE_URL`.
2. No Render, crie um Blueprint do repositório `srolivercpa1/OrcaPrime`, branch `feat/orcaprime-web-1.0`, arquivo `render.yaml`. Confirme o plano Free. Informe a conexão do Neon em `DATABASE_URL`, somente no campo privado de ambiente.
3. O endereço HTTPS do Render é reconhecido por `RENDER_EXTERNAL_URL`. Para domínio próprio, configure `PUBLIC_ORIGIN` com a origem exata, sem caminho. `/health` deve retornar versão `1.0`.
4. Em Environment do Render, consulte `SETUP_TOKEN`, gerado aleatoriamente. Abra `/setup` no endereço publicado e informe esse código, seu e-mail e sua senha. Não envie o código por chat nem o coloque no endereço da página. Só a primeira conta pode receber o perfil de proprietário.
5. Entre pelo login, cadastre as empresas e seus administradores. Após concluir o primeiro acesso, remova `SETUP_TOKEN` do ambiente. A presença do proprietário já bloqueia novos cadastros, inclusive em reinícios.

O Blueprint desativa atualizações automáticas. Publique novos commits somente após os testes. Não configure `BACKUP_DIR` no Render Free: arquivos locais são temporários e o processo pode dormir.

O Render usa o runtime Python 3.12.15, instala `requirements-web.txt` e inicia a mesma aplicação Uvicorn na porta `$PORT`. O Dockerfile continua disponível para instalações em contêiner. Para criação pela integração Render, use esses comandos do Blueprint e desative auto-deploy; a integração não oferece o campo de health check, portanto confirme `/health` após publicar e configure esse caminho no painel quando disponível.

Na instalação já preparada, `orcaprime_app` tem leitura e escrita somente nas seis tabelas `web_*`; `orcaprime_backup` tem somente leitura e não acessa `web_sessions`. Ambos são criados inicialmente com `NOLOGIN`: habilite `LOGIN` com senhas aleatórias fortes apenas ao configurar as variáveis privadas da hospedagem e do backup. Use a conexão com pool para a aplicação e a conexão direta para o backup. Não conceda acesso ao esquema `neon_auth` nem coloque a senha do proprietário do banco no serviço. Alterações futuras no esquema devem ser aplicadas separadamente com a conta de administração; o usuário da aplicação não cria tabelas.

### Backup diário externo e criptografado

`.github/workflows/web-backup.yml` prepara execução diária às **03:17 de Brasília**, independente da aplicação estar acordada. Cada snapshot inclui banco, fotos e logotipos, exclui sessões e é comprimido com gzip e criptografado com Fernet antes de qualquer gravação. Artefatos têm retenção de 14 dias. O nome e horário do arquivo ficam visíveis; o conteúdo exige a chave privada.

**Para ativar:**

- Crie um usuário PostgreSQL exclusivo de backup com `CONNECT`, `USAGE` no schema e `SELECT` nas tabelas `web_*`. O comando de backup não cria tabelas. Não reutilize a credencial de backup para restaurar.
- Configure o GitHub Secret `ORCAPRIME_BACKUP_DATABASE_URL` com essa conexão e `ORCAPRIME_BACKUP_ENCRYPTION_KEY` com uma chave Fernet gerada por `Fernet.generate_key()`. Guarde uma segunda cópia da chave em seu gerenciador de senhas; perder a chave impede restauração. Nunca grave a chave no código, em artefatos ou nos logs.
- Coloque o workflow de backup na **branch padrão** para habilitar o agendamento; ele lê o código da branch web. Faça essa integração isoladamente, preservando o fluxo de publicação do aplicativo Windows.
- Execute manualmente o workflow e valide uma restauração em banco descartável antes de considerar o backup ativo. Confirme o histórico de execuções e habilite as notificações de falha na sua conta GitHub. Em repositórios públicos, agendamentos podem ser desativados após 60 dias sem atividade; o GitHub também pode atrasar execuções. Não há garantia de horário exato.

Para cópia criptografada manual, configure `DATABASE_URL` e `BACKUP_ENCRYPTION_KEY` em ambiente privado e execute:

```bash
python -m webapp.cli backup --encrypted --directory backup
```

Para restaurar, baixe e extraia o artefato, configure `DATABASE_URL` apontando para um banco **vazio**, forneça a mesma `BACKUP_ENCRYPTION_KEY` e execute:

```bash
python -m webapp.cli restore --file backup/orcaprime-web-AAAAMMDD-HHMMSS-micros.json.gz.enc
```

Chave incorreta, adulteração e destino ocupado são recusados. O limite é 512 MiB de JSON descomprimido por snapshot; fotos consomem boa parte desse espaço. Backups existentes `.json.gz` continuam compatíveis com a restauração sem chave. O comando sem `--encrypted` continua destinado a cópias locais privadas, nunca ao envio para artefatos públicos.

A presença desses arquivos no repositório **não significa que contas, banco, site ou agendamento já foram provisionados**. A publicação só termina após confirmar acesso às contas, endereço público e recuperação de um backup real.

Referências: [Blueprint Render](https://render.com/docs/blueprint-spec), [limites gratuitos Render](https://render.com/docs/free), [variáveis Render](https://render.com/docs/environment-variables), [agendamento GitHub](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [Fernet](https://cryptography.io/en/stable/fernet/).
