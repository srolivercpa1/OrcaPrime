# OrçaPrime Web 1.0 — Render e Neon

## Objetivo e autorização
Continuar a publicação já autorizada pelo proprietário: aplicação no Render gratuito, PostgreSQL no Neon, mantendo a versão 1.0 e o aplicativo Windows independente. O usuário confirmou a criação das contas e a instalação do Neon. A conexão do Render e a disponibilidade efetiva dos recursos ainda precisam ser verificadas.

## Decisões
- Blueprint com `plan: free`, Docker existente, ramo `feat/orcaprime-web-1.0`, `/health`, sem disco ou banco Render pagos. Usar `RENDER_EXTERNAL_URL` como origem quando `PUBLIC_ORIGIN` estiver ausente.
- Primeiro proprietário cadastrado em `/setup`, mediante código aleatório de 256 bits gerado no ambiente Render, e-mail e senha escolhidos pelo proprietário. O código não entra em URL, logs ou repositório. Cadastro desativado depois do primeiro proprietário, inclusive entre instâncias concorrentes. CLI permanece disponível fora do Render.
- Backup gzip com criptografia autenticada Fernet opcional no comando existente e obrigatória no fluxo de nuvem. Nenhum arquivo intermediário em texto claro. Restauração exige a chave e banco vazio; sessões nunca são restauradas.
- GitHub Actions agenda a cópia diariamente às 06:17 UTC (03:17 em Brasília), fora do serviço Render que pode dormir. Artefatos criptografados com retenção de 14 dias, segredo de conexão de leitura e chave guardados separadamente em Secrets. Executar e testar restauração antes de declarar backup ativo. O workflow precisa estar na branch padrão para agendamento; não alterar a publicação Windows incidentalmente.

## Limites
Gratuidade sujeita às cotas dos provedores. Agendamento do GitHub pode atrasar e em repositórios públicos pode ser desativado após 60 dias sem atividade. Fotos consomem espaço no Neon; backups têm limite de restauração de 512 MiB descomprimidos. Não apresentar a preparação do código como implantação concluída.

## Verificação
Código de instalação inválido, origem cruzada, configuração ausente, cadastro único concorrente, senha com hash, login posterior, backup sem chave, chave errada, arquivo adulterado, restauração de fotos sem sessões e proibição de banco ocupado. CI deve testar PostgreSQL, navegador e início do contêiner.
