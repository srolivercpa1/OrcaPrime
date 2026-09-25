# OrçaPrime comercial — plano de implementação

Autorizado pelo usuário em 25/09/2026: implementar e publicar automaticamente os pedidos anteriores, incluindo hospedagem Railway.

## Objetivo e decisões
Licenciamento online individual com geração privada, bloqueio e renovação manuais pelo proprietário. Dados da assistência permanecem locais. Reutilizar API e assinatura Ed25519 existentes; validação a cada cinco minutos com lease máximo de quinze minutos. Não apagar dados por bloqueio. Cliente distribuído exige configuração válida e não permite modo gratuito por falha de configuração.
Salvar acesso opcional via DPAPI do usuário Windows; autoentrada opcional dependente de acesso salvo, revogada após troca de senha/desativação. Opção para esquecer acesso e sair. Marca: Software pago — Desenvolvido por Sketch Inc.
Backup diário compactado em pasta backup ao lado do EXE, sete cópias por padrão, retenção configurável, segunda pasta sincronizada opcional. ZIP deve ser validado antes de substituir cópia anterior. Agendamento diário Windows com execução perdida recuperável e modo headless sem login. Restaurar ZIP e DB legado. Não sincronizar banco ativo.

## Tarefas
1. Backup: maintenance.py e novo backup_ui.py; testes de compactação/restauração, retenção, corrupção, falha de destino secundário, agendamento Windows. Interfaces run_daily_backup(store), backup_job(), page_backup(self). UI delegada pelo App; CLI --backup-only despacha antes do Tk.
2. Autenticação e integração desktop: remembered_login.py, user_ui.py, __main__.py e ui.py. DPAPI, opt-in, clear; licença obrigatória em binário; Sobre comercial. Testar credencial corrompida/revogada e ausência de configuração.
3. Railway: inspecionar projeto existente sem divulgar segredos. Configurar volume persistente, segredos de produção, API com único worker, HTTPS e healthcheck. Não sobrescrever dados nem chaves existentes. Validar saúde e rejeição administrativa sem credenciais. Emitir uma licença privada após publicação.
4. Distribuição: configurar URL/chave pública no build, versão nova, testes Windows e instalador/ZIP. Publicar GitHub Release somente após testes. Entregar URLs e arquivo privado do proprietário fora do GitHub.

## Riscos a verificar
Senha trocada invalida login salvo; conta removida bloqueia autoentrada. ZIP inválido não altera banco. Pasta sem permissão gera erro visível. Instalador não remove backups. Servidor sem volume não pode hospedar banco de produção. Segredos não entram em commits nem logs. Host externo pode exigir assinatura da conta; nesse caso terminar tudo que independe dela e relatar impedimento real.
