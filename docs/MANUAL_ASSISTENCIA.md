# Uso da assistência técnica

## Acesso
Na primeira abertura, crie o administrador. Cadastre outros usuários em Usuários. Para trocar de usuário, feche e abra o programa. Administradores gerenciam acessos; atendimento recebe equipamentos; técnicos registram reparos; financeiro cuida de valores e caixa. Operações não autorizadas são bloqueadas.

## OS
Cadastre o cliente primeiro. Em Ordens de serviço, clique Nova OS, preencha equipamento/entrada e salve. As abas separam entrada, diagnóstico/entrega, itens, pagamentos, histórico/anexos e documentos. Alterações não salvas são avisadas ao fechar.

Situações seguem o fluxo: recebida → diagnóstico → aguardando aprovação → em reparo → em testes → pronta → entregue. É possível aguardar peça durante o fluxo. A mudança para reparo exige registrar a aprovação; valores ficam congelados. Para trocar preços depois disso, crie outra OS e mantenha o histórico da anterior.

Adicionar uma peça vinculada ao estoque reduz seu saldo; remover antes da aprovação devolve a peça. Cancelamento devolve peças e exige estornar pagamentos antes. Itens avulsos não movimentam estoque. Utilize a peça cadastrada quando quiser controlar o consumo.

Pagamentos são registrados após aprovação. Podem ser parciais e não exceder o saldo. Estornos exigem justificativa e mantêm os registros originais. Uma entrega com saldo pendente exige autorização do perfil apropriado e justificativa.

## Garantias
Informe dias e condições antes da aprovação. O prazo começa na entrega registrada. Use Retorno em garantia para criar novo atendimento vinculado à OS entregue. A vinculação não reinicia silenciosamente o prazo da OS original; avalie a cobertura do caso e registre o motivo.

## Estoque, caixa e contas
Cadastre peças, custos, preço e mínimo. Faça entrada de estoque com referência à compra e registre ajustes com justificativa. O cadastro do fornecedor não gera movimentação ou conta automaticamente.

Contas a pagar/receber aceitam parcelas mensais com soma preservada. Liquidar uma conta lança o valor no livro-caixa. Recebimentos das OS já entram no livro-caixa; não os registre novamente como entrada manual.

Abertura/fechamento confere apenas dinheiro físico; PIX e cartões aparecem no livro-caixa, mas não são somados ao valor esperado na gaveta. Informe saldo inicial na abertura e dinheiro contado no fechamento. Diferenças exigem justificativa. O livro-caixa aceita registros mesmo quando não há conferência aberta.

## Documentos
Instale o driver da impressora no Windows e associe o formato em Impressoras. Na OS, escolha documento e papel. Exportar e visualizar permite conferir antes de imprimir. Se a impressão direta não funcionar com seu leitor PDF, imprima pelo próprio leitor. Etiquetas usam 80×40 mm; não há corte automático personalizado.

Recibos mostram recebido e saldo. Nota fiscal não está integrada; emita pelo emissor autorizado utilizado pela empresa. Nenhuma impressão local equivale à autorização fiscal.

## Backup
A cópia automática é diária na abertura, na pasta de dados. Faça backups externos regularmente pelo menu Backup e restauração. Fotos/anexos e usuários fazem parte do banco e da cópia. A restauração valida a estrutura e preserva uma cópia anterior. Após restaurar, reabra o programa e utilize a senha existente naquele backup.


## Painel profissional e acompanhamento (2.1)

A Visão geral apresenta quatro indicadores operacionais. Clique em um cartão para abrir as OS correspondentes. O cartão Em andamento exclui entregues e canceladas. A agenda lista previsões válidas; datas antigas inválidas são sinalizadas e não contam como atraso. Indicadores financeiros/estoque do painel só aparecem para administrador e financeiro.

Nas Ordens de serviço, combine situação, técnico, prioridade e prazo com a pesquisa. Em andamento e Retornos são filtros opcionais; Limpar filtros remove todas as restrições. Etapas agrupa as mesmas OS por situação e abre o editor sem modificar o andamento automaticamente.

No editor, use Prioridade para organizar urgências. Os campos de texto aceitam múltiplas linhas. Inserir checklist acrescenta o modelo escolhido preservando anotações anteriores. Observações internas ficam no cadastro e backup, mas não nos PDFs. Serviços executados / observações públicas são impressos na OS, entrega e garantia.

Histórico do equipamento / cliente usa cliente e serial/IMEI. Sem identificador, a janela mostra o histórico do cliente; dois modelos iguais não são considerados automaticamente o mesmo aparelho.

## Central de impressão (2.1)

Selecione uma OS e use Imprimir documentos, ou abra a aba Documentos no editor. Escolha tipo, formato e impressora. Salvar PDF guarda o arquivo; Pré-visualizar abre no leitor; Imprimir envia ao leitor/fila configurados. Salve alterações da OS antes de abrir a central. O comprovante de entrega só é gerado após registrar a entrega.

O tipo ETIQUETA usa exclusivamente papel 80×40 mm e a preferência de impressora de etiquetas. OS, entrada, entrega, recibo e garantia usam A4/58/80 mm. Confira margem/papel no driver real. Envio à fila não comprova saída física do papel.

## Produtividade (2.1)

Em Relatórios, informe início e fim no formato AAAA-MM-DD. O período inclui os dois limites. Cada OS conta uma vez pela primeira entrega registrada em seu histórico, agrupada pelo técnico registrado na OS. Atendimentos sem data de evento válida são sinalizados, sem inventar data. Exportar produtividade CSV aplica novamente o período e as permissões.

A aba Financeiro e estoque contém valores acumulados. Margem orçada não é lucro recebido; as datas de recebimento são independentes das datas de entrega.

## Emissão fiscal

A versão 2.1 não transmite NF-e, NFC-e ou NFS-e. A definição depende da cidade/UF, enquadramento, tipos de operação e emissor da empresa. Nenhum provedor pago foi contratado. Os documentos administrativos do sistema não são notas fiscais autorizadas.
