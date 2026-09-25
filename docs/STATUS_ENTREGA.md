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
