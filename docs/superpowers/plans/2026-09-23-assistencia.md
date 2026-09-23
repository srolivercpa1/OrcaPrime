# Implementação da assistência técnica

Objetivo autorizado: ampliar o desktop gratuito, preservar dados e publicar instalador. Execução nesta sessão, sem serviço pago. Emissão fiscal depende de configuração externa ainda não fornecida; não simular autorização fiscal.

1. Banco e regras (`workshop.py`): tabelas adicionais, OS, itens, estoque transacional, pagamentos/estornos, garantias, eventos e anexos no próprio banco. Manter tabelas atuais para compatibilidade e migrar/restaurar com validação. Testar criação, saldo, duplicidade, rollback e backup.
2. Interface (`workshop_ui.py`): painel de OS, editor em abas, cadastros, peças, estoque, caixa, contas, garantias, relatórios, usuários e configurações de impressão. Integrar navegação existente sem quebrar orçamentos.
3. Documentos (`service_documents.py`): PDF A4/58/80mm e etiquetas; seleção de impressora Windows e envio com tratamento de erro. Não afirmar impressão física sem confirmação.
4. Usuários: senha com hash, login inicial configurável, papéis e auditoria. Aplicar autorização nas operações de dados.
5. Integração: backup completo, migração validada, documentação clara de recursos e limitações; testes Windows e release versionada.

Critério final: completar fluxo real de OS com estoque e financeiro, backup/restauração, documentos e instalador testado. Funcionalidade fiscal não implementada deve aparecer explicitamente como não configurada. Compatibilidade da impressora física depende do driver/modelo.
