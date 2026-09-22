# Manual do OrçaPrime

## Instalação e ativação

Após receber o instalador gerado e homologado, execute `OrcaPrime-Setup.exe`. A instalação é por usuário e não exige instalar Python. O atalho da Área de Trabalho é opcional. Abra o programa e cole o código enviado pelo fornecedor; clique em **ATIVAR**. São cinco blocos de quatro caracteres. Letras são convertidas para maiúsculas; hífens são inseridos automaticamente. Os caracteres O, I, 0 e 1 não fazem parte do alfabeto.

É necessário acesso à internet em toda abertura. O programa também valida a licença durante o uso. Se houver falha de rede durante uma sessão já validada, ela permanece disponível apenas até o fim da autorização atual (no máximo 15 minutos desde a última validação). Bloqueio, cancelamento ou expiração impedem a continuidade. Ao bloquear o acesso, a tela de ativação oculta as edições abertas; elas são restauradas após a validação, enquanto o programa permanecer aberto. Encerrar o programa descarta alterações não salvas, com confirmação quando há uma edição aberta. Salve com frequência.

Em **Minha licença**, o código aparece apenas com os dois primeiros e os dois últimos caracteres. Para trocar a licença, use **Trocar código de ativação**. A instalação do aplicativo não ativa uma licença automaticamente.

## Fluxo de trabalho

1. Em **Minha empresa**, cadastre nome, documento, telefone, e-mail, endereço e condições de pagamento padrão.
2. Em **Clientes**, clique em **Novo**, preencha o nome e os dados de contato e salve. Use a busca para localizar um cadastro e **Editar selecionado** para alterá-lo.
3. Em **Produtos e serviços**, cadastre itens frequentes, tipo, unidade e preço. É permitido criar itens livres diretamente no orçamento.
4. Em **Orçamentos**, clique em **Novo**, escolha o cliente e informe a validade no formato DD/MM/AAAA.
5. Escolha um item do catálogo ou escreva uma descrição. Informe quantidade, unidade e preço, e clique em **Adicionar**. Para corrigir uma linha, remova-a e adicione a versão corrigida.
6. Informe desconto em reais, pagamento e observações. O desconto não pode superar o subtotal. Clique em **Salvar orçamento**.
7. Selecione o orçamento e clique em **Exportar PDF**. Escolha onde salvar; envie o PDF ao cliente pelo canal de sua preferência.
8. Atualize a situação para ENVIADO, APROVADO ou RECUSADO conforme o andamento.

Preços usam reais, com vírgula decimal; quantidades podem ser fracionárias. Preços unitários são arredondados a centavos antes da multiplicação. Não informe `R$` dentro de campos numéricos. O orçamento guarda uma cópia dos dados do cliente, preservando o histórico quando o cadastro muda. Os dados da sua própria empresa no PDF são os atuais.

**Duplicar** cria outro orçamento, com novo número e situação RASCUNHO; revise cliente e validade antes de salvar. Não existe exclusão definitiva de orçamentos nesta versão; use as situações para organizar o histórico.

## Backup

Em **Backup e restauração**, escolha **Criar backup** e guarde o arquivo `.db` fora do computador. Ele inclui clientes, catálogo, empresa e orçamentos. Não inclui a ativação. Trate o backup como arquivo privado.

Para recuperar, escolha **Restaurar backup** e confirme a substituição. O sistema valida o arquivo antes de restaurar e cria automaticamente um arquivo `antes-restauracao-*.db` junto do banco atual. Use apenas backups de confiança. A restauração de dados não transfere a licença de outro computador.

Dados padrão no Windows: `%LOCALAPPDATA%\OrcaPrime`. A desinstalação preserva essa pasta para evitar perda acidental. Excluir manualmente a identidade de instalação exige nova ativação; o proprietário pode liberar a ativação antiga pelo painel.

## Limites da versão

O PDF é um orçamento comercial, não um documento fiscal. Cada computador guarda seus próprios dados. Os planos GRÁTIS, PRO e EMPRESA não restringem funcionalidades nesta versão. Não há cobrança recorrente automática: o proprietário renova as licenças pelo painel.
