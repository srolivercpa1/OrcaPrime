# OrçaPrime 1.0 — Premium R2

Identidade visual baseada nas três referências fornecidas: painel azul-marinho/azul elétrico, logo original no aplicativo e no ícone Windows, login e cadastro com campos e botões arredondados. Tema aplicado às abas de serviço, tabelas, formulários, histórico e observações.

Painel responsivo com indicadores, ações rápidas, agenda ligada às OS e resumo dos prazos de hoje. Atalhos preservam as permissões de cada perfil. Layout adapta a coluna lateral e os cartões em janelas menores.

A versão exibida permanece 1.0. A identificação `v1.0-premium-r2` preserva os releases anteriores. A mudança visual não reverte dados nem remove funções. O login continua exigindo senha; não foi adicionado armazenamento de senha nem entrada automática.

Distribuição: instalador Windows e ZIP portátil com executável, runtime e dependências. Extraia o ZIP inteiro antes de abrir o EXE. Ambos usam a mesma pasta de dados em `%LOCALAPPDATA%\OrcaPrime`.

Validação: testes automatizados com interface gráfica, inspeção de painel/login/cadastro/editor de OS e revisão independente. Publicação condicionada aos testes Windows, compilação e verificação de abertura do executável.

Impressão física depende do equipamento do usuário. Emissão fiscal continua não configurada.

## Correção visual R2

Banner estático reutilizado da referência fornecida, proporções de cabeçalho e navegação ajustadas, superfícies arredondadas nos cartões, painéis, botões, abas e campos. O desenho adapta-se ao tamanho da janela.

Novo ícone: `orcaprime-premium-r2.ico`. O instalador aplica esse arquivo explicitamente aos atalhos e usa a mesma identidade de barra de tarefas do aplicativo. A compilação verifica os bytes dos ícones embutidos no EXE. A revisão do instalador é 1.0.1; a identificação visual permanece 1.0.

100 testes locais aprovados. A instalação anterior não precisa ser removida; feche o aplicativo e instale a revisão no mesmo local, preservando o banco. Atalhos fixados manualmente antes da atualização podem precisar ser fixados novamente.

## Versão 1.0 Comercial — revisão do instalador 1.0.2

- Identidade: Software pago — Desenvolvido por Sketch Inc. Novo ícone transparente fornecido pelo proprietário em 25/09/2026; aplicado a EXE, janela, instalador e atalhos.
- Licenciamento online obrigatório na distribuição: servidor Railway, códigos individuais, validade e bloqueio/renovação pelo proprietário. Nenhuma senha administrativa ou chave privada entra no instalador/repositório. O aplicativo consulta a licença a cada cinco minutos; sem conexão, o prazo de validação é de até quinze minutos. Ao expirar/bloquear, o acesso é suspenso sem apagar o banco.
- Versões anteriores offline continuam offline: o controle passa a valer após instalar esta distribuição comercial.
- Salvar meus dados e entrar automaticamente são opcionais. Credenciais protegidas por DPAPI no Windows atual; redefinir senha/desativar conta invalida o acesso salvo. Menu Esquecer acesso e sair remove as credenciais.
- Backup ZIP validado na pasta `backup` ao lado do EXE. Mantém sete versões diárias por padrão, configurável de 1 a 365. A cópia do mesmo dia pode ser atualizada manualmente ou pelo agendamento.
- O instalador registra uma tarefa do usuário atual para 18h e ao entrar no Windows. Requer computador ligado e sessão desse usuário; executa atrasos quando possível. O programa também verifica o backup ao abrir. A desinstalação retira a tarefa, preservando dados e cópias.
- A versão portátil faz backup ao abrir; o agendamento é configurado pelo instalador.
- Segunda pasta opcional: selecionar uma pasta já sincronizada por OneDrive/Google Drive. A aplicação confirma a cópia local; a sincronização depende do cliente de nuvem, conexão e espaço disponível. Não é integração direta com a API de nuvem.
- Backups não incluem a senha administrativa do servidor, suas chaves privadas ou o token DPAPI de ativação. A restauração dos dados requer a licença do computador de destino. Use pasta privada para cópias dos dados da assistência.
- A hospedagem é um serviço contratado na conta do proprietário, com cobrança conforme o plano Railway. Não há integração de cobrança automática: bloqueio e renovação são manuais no painel.
