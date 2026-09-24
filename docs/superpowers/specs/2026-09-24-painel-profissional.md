# OrçaPrime — painel profissional e operação avançada

Estado: escopo aprovado na conversa; especificação escrita para revisão. Não representa funcionalidades já entregues.

## Objetivo e continuidade

Evoluir o aplicativo Windows gratuito e local da assistência técnica, preservando clientes, OS, estoque, pagamentos, usuários e backups. Base examinada: commit 5013008b31fb19e24d10640472a5ca1b0874d63f. Manter Python, Tkinter/ttk e SQLite. Não introduzir mensalidade nem provedor pago.

O usuário aprovou painel profissional, OS avançadas, central de impressão, acompanhamento da assistência e módulo fiscal. A integração fiscal depende ainda da cidade/UF, enquadramento e documentos efetivamente emitidos pela empresa. Essa dependência não bloqueia as melhorias locais.

## Diagnóstico da base

- `ui.py` tem painel de orçamentos com três indicadores; usuários autenticados entram na lista de OS.
- `workshop_ui.py` oferece pesquisa e situação, mas não filtros por técnico, prioridade e prazo. O campo de prioridade já existe no domínio e não aparece no formulário.
- Checklists atuais são texto livre. O editor concentra entrada, diagnóstico, itens, pagamentos, histórico, anexos e documentos em abas.
- Impressões A4, 58/80 mm e etiquetas já existem em `service_documents.py`. Reutilizar essas funções e as preferências de impressora.
- A tela fiscal atual não transmite documentos. A especificação anterior já condiciona essa integração à identificação da empresa.

## 1. Painel e navegação

Paleta azul-marinho, verde-petróleo, fundo claro e cartões brancos; tipografia Segoe UI, hierarquia consistente e espaçamento uniforme. Manter contraste e destacar situações também por texto, sem depender apenas de cor.

Painel inicial para os perfis autorizados: OS em andamento, atrasadas, aguardando aprovação e prontas para retirada. Atrasadas são OS não entregues/não canceladas com previsão anterior à data local; sem previsão não significa atraso. Indicadores financeiros ficam restritos aos perfis financeiro e administrador.

Cartões abrem listas filtradas. Exibir agenda de prazos, alertas de estoque aos perfis autorizados e atalhos para nova OS, clientes e impressão. Técnico continua entrando em suas áreas permitidas. Não ampliar permissões por meio dos atalhos.

Organizar menu em Atendimento, Gestão e Configurações. Garantir rolagem e acesso às ações na resolução mínima atual de 920×650, inclusive com escala de tela do Windows.

## 2. Ordens de serviço

Filtros combináveis por texto, situação, técnico, prioridade e prazo: todas, atrasadas, hoje e sem previsão. Botão para limpar filtros e contagem dos resultados. Prioridades: baixa, normal, alta e urgente. Registros antigos sem prioridade aparecem como normal, sem regravar todo o banco.

Lista apresenta número, cliente, equipamento, técnico, prioridade, previsão e situação. Valores financeiros respeitam permissões. Oferecer visualização por etapas além da tabela, usando as mesmas regras de transição do domínio; não alterar situação diretamente pela interface.

Formulário expõe prioridade e campos de texto multilinha para relato, diagnóstico e observações. Modelos de checklist por categoria — celular, computador e outros — podem ser inseridos mediante ação explícita, preservando texto existente. O resultado aplicado fica na OS, independente de alterações futuras no modelo.

Histórico do equipamento usa cliente e serial/IMEI não vazio como correspondência exata. Quando não houver identificador, mostrar histórico do cliente, sem afirmar que atendimentos de modelos iguais são do mesmo aparelho. Retornos permanecem vinculados à OS original.

Preservar aprovação antes do reparo, congelamento de valores aprovados, consumo transacional de estoque, estornos e identificação de entrega. Salvar alterações antes de emitir documentos; informar quando houver edição não salva.

## 3. Central de documentos

Na lista e no editor da OS, disponibilizar entrada, OS, entrega, recibo, garantia e etiqueta. Seleção de papel e impressora, abrir prévia no leitor PDF, salvar PDF e enviar para impressão. A prévia deve corresponder aos dados salvos usados na impressão.

Termo de garantia identifica empresa, cliente, equipamento, OS, entrega, prazo e condições registrados. Não inventar prazo de garantia nem misturar observações internas com texto destinado ao cliente. Documentos administrativos permanecem identificados como não fiscais.

Impressora ausente, cancelamento da escolha de arquivo ou erro no leitor não alteram OS, pagamentos ou estoque. Informar envio à fila sem alegar impressão física. Usar drivers instalados no Windows; validação física depende do equipamento disponível.

## 4. Gestão e relatórios

Listas acionáveis de OS aguardando peça, retiradas pendentes e retornos. Relatório de produtividade por técnico e período usa eventos registrados de conclusão/entrega, com definição explícita da data considerada. Separar quantidade entregue, valor recebido e saldo; não tratar orçamento aprovado como receita recebida.

Reutilizar caixa e estoque existentes. Relatórios e exportações aplicam as mesmas permissões que a interface. Não criar disparos automáticos de mensagens ao cliente nesta ampliação.

## 5. Fiscal: etapa dependente de definição

A aplicação local continua operando sem conexão. Antes de implementar transmissão, identificar cidade/UF, enquadramento, venda de produtos versus prestação de serviços e emissor disponível. Consultar documentação oficial vigente para escolher NF-e/NFC-e/NFS-e aplicável e confirmar requisitos e eventuais custos. Nenhuma contratação está autorizada.

Após essa definição, detalhar um adaptador separado para emissão, consulta e cancelamento, retenção de XML/protocolos e documento auxiliar. A identidade local do pedido deve impedir reenvios duplicados; timeout exige consulta antes de nova transmissão. Autorização só pode ser mostrada após resposta verificável do emissor. Cancelamento fiscal não estorna automaticamente a OS.

Credenciais e certificados serão configurados localmente, fora do repositório e dos logs; nunca solicitados em mensagens. A estratégia de proteção, backup e renovação depende do emissor e será especificada antes de armazená-los. A tela continuará indicando emissão não configurada enquanto essa etapa não estiver homologada.

## Organização técnica

Extrair consultas e indicadores para módulo próprio, com filtros testáveis sem interface. Separar painel, documentos e componentes visuais para evitar aumentar os arquivos monolíticos. Reutilizar `Workshop` como fronteira de autorização e transações, e `service_documents.py` como gerador.

Adicionar apenas campos necessários com compatibilidade para dados antigos. Se forem criadas tabelas, usar migração versionada, atualizar validador de backup e validar restauração. Não copiar nem compartilhar SQLite em rede como solução multiusuário.

## Verificação e entrega

1. Testar filtros combinados, limites de data, prioridade ausente e histórico sem serial.
2. Verificar perfis por chamadas diretas e por navegação/atalhos.
3. Testar migração, preservação de dados e restauração; rodar regressões de estoque, aprovação e pagamentos.
4. Conferir visualmente painel e editor em resolução mínima e maior; validar rolagem, foco e legibilidade.
5. Renderizar documentos A4/58/80 mm com acentos e textos longos; verificar paginação, totais e ausência de dados internos.
6. Testar impressora ausente e falhas de envio sem efeitos nos dados.
7. Gerar e verificar instalador no fluxo Windows existente, publicando resultado e limites reais de homologação.

A entrega local pode ser publicada separadamente da fiscal, identificando claramente a emissão pendente. O projeto completo só será declarado concluído após integração fiscal definida e homologada. Esta especificação não promete instalador novo antes da implementação e verificação.
