# OrçaPrime Web 1.0 — especificação

## Objetivo aprovado
Criar uma versão acessível pelo navegador, inspirada na organização visual da captura do Apex Comércio enviada pelo proprietário. Usar a marca original OrçaPrime e a identificação Desenvolvido por Sketch Inc. O aplicativo Windows continua independente; esta proposta não altera seus dados ou a distribuição existente.

## Experiência visual
Menu lateral fixo no computador: Início, Clientes, Orçamentos, Ordens de serviço, Estoque, Financeiro, Relatórios e Configurações. Acesso destacado para nova OS. Cabeçalho com empresa, perfil e notificações reais. Fundo claro, cartões arredondados, tabelas com cabeçalhos alinhados, estados vazios explicativos e cores da identidade existente do OrçaPrime. Não copiar a marca ou anúncios da referência.

Painel inicial com quantidade e valores de OS, serviços pendentes, aparelhos prontos e resumo financeiro. Coluna direita com ações rápidas e avisos. Em larguras de computador a coluna permanece à direita; em celular o menu vira gaveta e a coluna integra a sequência vertical. Formulários têm rolagem e ações sempre acessíveis. Valores do painel vêm do banco; ausência de dados mostra zero, sem métricas fictícias.

## Arquitetura proposta
Aplicação web própria dentro de um diretório separado do repositório. Backend Python com API; PostgreSQL para empresas, usuários e operações; armazenamento privado de objetos para fotos e documentos. Interface responsiva servida pelo mesmo domínio da API, simplificando sessões e proteção contra requisições indevidas. Reaproveitar regras e geração de documentos do desktop apenas após verificar dependências; não compartilhar o SQLite local pela internet.

Todos os registros operacionais pertencem a uma empresa. A empresa é obtida da sessão autenticada, nunca aceita apenas a partir de um identificador enviado pelo navegador. Consultas, arquivos, alterações e relatórios verificam essa associação no servidor.

## Acessos
Painel da assistência com perfis administrador, atendimento, técnico e financeiro. Permissões verificadas no servidor, inclusive acesso direto à API. Administrador pode criar, editar, revogar e excluir usuários com confirmação, preservando auditoria e pelo menos um administrador ativo. Revogação invalida sessões existentes.

Painel separado do proprietário para cadastrar empresas, definir validade da assinatura, suspender e reativar acesso. Suspensão impede operações da empresa e exibe uma mensagem de contato; não apaga dados. Registrar todas as alterações administrativas. A integração com o servidor de licenças existente precisa preservar o licenciamento Windows.

Senhas armazenadas com hash apropriado; cookies de sessão HttpOnly, Secure em produção e SameSite; proteção CSRF, limitação de tentativas e expiração de sessões. Segredos ficam no ambiente do servidor, sem inclusão no navegador ou no Git. Recuperação de senha depende da configuração do provedor de e-mail.

## Módulos operacionais
Clientes: cadastro completo, pesquisa, histórico e exclusão confirmada. Para compatibilidade com a solicitação anterior, excluir cliente também exclui suas OS; mostrar previamente os registros afetados e manter a consistência financeira e de estoque em transação. Operações financeiras já realizadas exigem política de estorno/preservação de auditoria, sem apagar saldos silenciosamente.

OS: entrada do aparelho, marca/modelo/serial, defeito, checklist, fotos, técnico, prazo, diagnóstico, serviços, peças e pagamentos. Estados em andamento, pronto e entregue, com histórico de datas. Entregues ficam em lista própria. Fotos podem vir da câmera ou do arquivo, com limite de tamanho, validação de conteúdo e URLs temporárias autorizadas.

Orçamentos: itens, totais, aprovação, exclusão confirmada e conversão em OS sem duplicar a operação quando uma requisição for reenviada.

Estoque: categorias, pesquisa, movimentações, consumo e devolução de peças vinculados à OS. Baixa atômica com controle de concorrência.

Financeiro: contas a pagar/receber, recebimentos e caixa; valores decimais e registros auditáveis. Relatórios filtráveis por período.

Documentos: OS e garantia com logo persistente da empresa, PDF e impressão pelo navegador. Emissão fiscal não será apresentada como disponível até a integração com emissor fiscal e a configuração/homologação de cada empresa.

## Operação e migração
HTTPS, banco gerenciado e armazenamento privado. Backup diário comprimido, retenção configurável e cópia fora do servidor principal, com teste de restauração. Não armazenar backups acessíveis por URL pública.

A importação do desktop será explícita, com backup original preservado, validação e relatório de registros importados. Não há sincronização automática bidirecional entre desktop e web nesta primeira versão.

Hospedagem pública depende de selecionar a conta/provedor e configurar domínio e segredos. Autorização prévia do usuário permite preparar a publicação; credenciais e eventuais cobranças não serão presumidas. Não prometer URL operacional antes da verificação do ambiente publicado.

## Entregas verificáveis
1. Base web: banco, empresas, sessões, permissões e painel visual com navegação funcional e dados reais.
2. Atendimento: clientes, OS, fotos, orçamentos e PDFs, com isolamento entre empresas testado.
3. Gestão: estoque, financeiro, relatórios e administração de assinaturas.
4. Produção: backups/restauração, importação, validação responsiva, configuração de hospedagem e verificação do endereço público.

Cada etapa deve incluir testes de autorização, entradas inválidas e erros de rede, além das regras de negócio aplicáveis. O lançamento comercial exige testes de acesso cruzado entre empresas, suspensão de sessões, consistência de operações simultâneas e restauração de backup. A primeira tela visual isolada não constitui o sistema pronto.

## Critérios visuais de aceite
Conferir em 1366 × 768 e 1920 × 1080: ações rápidas à direita, textos legíveis e nenhum botão cortado. Conferir em 390 × 844: navegação acessível, formulários utilizáveis e tabelas com rolagem interna. Comparar o painel com a captura recebida, preservando a marca OrçaPrime.
