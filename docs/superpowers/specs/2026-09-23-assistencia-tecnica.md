# OrçaPrime Assistência — projeto da ampliação

Estado: proposta técnica para a próxima versão. As funções descritas aqui ainda não estão implementadas no instalador v1.0.0.

## Objetivo e decisões

Atender uma assistência técnica desde o recebimento do equipamento até a entrega, recebimento financeiro e eventual retorno em garantia. O usuário pediu sistema completo, impressora comum e de documentos fiscais, OS e garantias. O aplicativo deve continuar gratuito, sem licença online e sem hospedagem paga.

A base será o aplicativo Windows existente. Clientes, catálogo e orçamentos atuais serão preservados. A opção inicial de implantação é uma loja em um computador, com vários usuários locais. Essa é uma hipótese de projeto, não uma limitação informada pelo usuário. Uso simultâneo em vários computadores exige uma implantação própria com serviço de banco de dados; não compartilhar o arquivo SQLite em uma pasta de rede.

Alternativas consideradas: aplicação web hospedada introduz operação e possível custo recorrente; aplicação nova descartaria a base existente. Ampliar o desktop atual preserva a instalação gratuita e os dados.

## Fluxo principal

1. Localizar/cadastrar cliente e equipamento.
2. Abrir OS numerada com defeito relatado, estado físico, acessórios, checklist e fotos.
3. Imprimir comprovante de entrada e etiqueta de identificação.
4. Registrar diagnóstico, serviços, peças, prazo previsto e orçamento.
5. Registrar aprovação ou recusa com data, responsável, canal e observação.
6. Executar reparo, registrar peças consumidas, responsável e testes de saída.
7. Registrar pagamentos e saldo; emitir recibo identificado como não fiscal.
8. Entregar equipamento com identificação do recebedor, comprovante e termo de garantia.
9. Vincular eventual retorno à OS e preservar todo o histórico anterior.

## Módulos e regras

| Módulo | Entrega planejada |
|---|---|
| Clientes | Pessoa física/jurídica, contatos, endereço, pesquisa e histórico financeiro/técnico |
| Equipamentos | Categoria, fabricante, modelo, serial/IMEI opcional, cliente e histórico de atendimentos |
| Ordens de serviço | Numeração única, prioridade, técnico, prazo, checklist, fotos, observações internas e públicas |
| Andamento | Recebida, diagnóstico, aguardando aprovação, aguardando peça, em reparo, em testes, pronta, entregue e cancelada |
| Orçamentos | Peças e mão de obra separadas, desconto, versões, aprovação e conversão vinculada à OS |
| Estoque | Fornecedores, compras/entradas, consumo por OS, devoluções, ajustes justificados e alerta de estoque mínimo |
| Financeiro | Caixa, abertura/fechamento, entradas/saídas, formas de pagamento, parcelas e contas a pagar/receber |
| Garantias | Termos configuráveis por item/serviço, data inicial registrada na entrega e retornos vinculados |
| Impressão | OS, orçamento, entrada, retirada, recibo, garantia, etiquetas e relatórios |
| Relatórios | OS por situação/técnico, prazos, recebimentos, pendências, estoque e custos/resultado por serviço |
| Usuários | Administrador, atendimento, técnico e financeiro, permissões verificadas nas operações |
| Segurança operacional | Histórico de alterações, backups automáticos, restauração verificada e atualização sem perda de dados |

## Integridade e operações críticas

- Valores monetários em centavos; quantidades decimais validadas. Sem cálculos financeiros em ponto flutuante.
- Status mudam por operações explícitas com registro de usuário, data, origem e destino. Cancelar não apaga histórico.
- Consumo de peça e movimento de estoque são gravados na mesma transação. Uma repetição de clique não duplica consumo.
- Ajustes e devoluções geram movimentos compensatórios. Bloquear saldo negativo por padrão.
- Um recebimento quita apenas o valor registrado, podendo ser parcial. Estorno vincula o recebimento original; não se apaga lançamento financeiro.
- Separar valor orçado, aprovado, recebido e saldo. Proibir recebimento acima do saldo sem operação específica de crédito.
- Documentos emitidos preservam os dados de cliente, empresa, itens, valores e termos daquele momento.
- Entrega exige identificação e checklist final; saldo pendente exige autorização do perfil competente e justificativa.
- Retorno em garantia é novo atendimento vinculado à origem. Não alterar a OS original nem reiniciar prazos silenciosamente.
- Não presumir um prazo jurídico universal de garantia: termos e prazos comerciais precisam ser configurados para a operação.

## Impressoras e documentos

Listar impressoras instaladas no Windows, escolher dispositivo por tipo de documento e salvar tamanho do papel. Oferecer pré-visualização, PDF e impressão em A4, 58 mm e 80 mm. Etiquetas terão dimensões configuráveis. A instalação do driver continua sendo feita pelo instalador oficial do fabricante/Windows; não instalar drivers genéricos sem conhecer o equipamento.

Impressão deve preservar acentos, margens, quebra de páginas e totais. Impressora ausente ou falha na fila não altera o estado da OS nem marca entrega. Registrar envio para a fila sem alegar que o papel foi efetivamente impresso.

Compatibilidade física, corte de papel e comandos específicos dependem da marca/modelo. PDF é a alternativa quando não houver driver compatível. Não prometer compatibilidade com toda impressora antes do teste físico.

## Nota fiscal: integração pendente de definição

O pedido de sistema completo inclui o objetivo de emissão fiscal, mas a integração ainda não está definida. É necessário identificar cidade/UF, atividade/documentos emitidos e enquadramento da empresa antes de escolher o emissor e verificar seus requisitos oficiais. Não solicitar certificados ou credenciais em mensagens comuns.

Planejar módulo separado de emissão, consulta de situação, cancelamento quando aplicável e armazenamento de documentos/protocolos. A operação local da assistência continuará disponível quando a integração fiscal estiver indisponível. Reenvios precisam consultar a situação anterior e impedir duplicidade.

Não incluir provedor pago sem autorização. Não chamar recibo ou PDF gerado localmente de nota fiscal autorizada. Até a integração ser configurada e testada, apresentar a emissão fiscal como indisponível, sem simular sucesso.

## Arquitetura e migração

Separar interface, regras de negócio, persistência, impressão e relatórios em módulos. Usar migrações versionadas para acrescentar tabelas de equipamentos, OS, itens de OS, eventos, anexos, fornecedores, movimentos de estoque, caixa, títulos, pagamentos, garantias, usuários e auditoria.

Aplicar chaves estrangeiras, índices de pesquisa, restrições de unicidade e transações. Guardar anexos em pasta gerenciada por identificadores, sem depender do arquivo original do usuário. Não guardar senha/PIN de desbloqueio do equipamento por padrão.

Antes da primeira migração, fazer backup consistente e verificar integridade. Em erro, manter a base original disponível. O validador atual aceita apenas schema 1 e deverá passar a validar explicitamente cada versão suportada; não basta acrescentar tabelas ao banco.

Backup da nova edição inclui banco, anexos e configuração necessária, com manifesto e hashes. Restaurar primeiro em área temporária, validar formato/caminhos/conteúdo e só então substituir os dados. Preservar cópia anterior. Backups locais não protegem contra perda do computador; permitir destino externo escolhido pelo usuário.

Permissões locais protegem operações na aplicação, mas não devem ser apresentadas como proteção contra um administrador do Windows com acesso ao banco. Senhas de usuários são armazenadas como hashes com salt, nunca texto puro.

## Etapas de implementação

1. Migrações, preservação dos dados, equipamentos, OS, eventos e documentos de entrada/saída.
2. Orçamento integrado, aprovação, estoque transacional, fornecedores e custos.
3. Caixa, contas, pagamentos, estornos, garantias e relatórios.
4. Usuários/permissões, auditoria, anexos, backups completos e impressão configurável.
5. Integração fiscal conforme definição da empresa e validação em ambiente adequado.
6. Testes integrados no Windows, atualização sobre v1.0.0 e nova Release com instalador e checksum.

Essas etapas são partes do mesmo objetivo. Uma entrega parcial deverá ser identificada como parcial, nunca como sistema completo.

## Critérios de aceitação

- Atualizar uma base v1.0.0 sem perder clientes, catálogo, orçamentos ou PDFs já salvos.
- Completar recebimento, aprovação, consumo de peça, reparo, pagamento, entrega e retorno em garantia.
- Provar rollback em falha e ausência de duplicação em consumo, pagamento e numeração.
- Provar permissões em operações, inclusive por chamadas diretas às regras de negócio.
- Validar restauração com anexos e rejeitar backup corrompido antes de alterar a base atual.
- Conferir documentos A4/58/80 mm com textos longos, acentos, múltiplas páginas e totais.
- Testar impressora indisponível; comprovar que OS e pagamentos permanecem intactos.
- Gerar instalador Windows que abre sem internet e sem cadastro em serviços externos.
- Só declarar emissão fiscal funcional após teste e confirmação de resposta real do emissor escolhido.

## Informação necessária para fechar a parte fiscal

Cidade e estado da assistência. Marca/modelo da impressora e enquadramento da empresa serão solicitados quando a integração correspondente for configurada.
