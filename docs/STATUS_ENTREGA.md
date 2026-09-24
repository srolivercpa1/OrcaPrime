# Estado da entrega — OrçaPrime 2.1

Implementados: painel operacional, filtros de OS, prioridades, visualização por etapas, checklists, histórico de equipamento/cliente, observações internas, central de impressão com comprovante de entrega e produtividade por período. Dados e operações da versão 2.0 preservados.

Validação local: 96 testes passaram com interface gráfica virtual, incluindo regressão de restauração de backups anteriores, permissões, datas inválidas, filtros, documentos e acesso aos botões em resolução mínima. Existe um aviso de depreciação da dependência Starlette/httpx na API legada; não é falha de teste.

Os PDFs foram gerados em A4/58/80 mm e etiquetas para conferência. Impressão física depende de teste no equipamento do usuário. O instalador Windows é entregue somente após aprovação dos testes e build no GitHub Actions.

Emissão de NF-e/NFC-e/NFS-e não configurada. Depende dos dados da empresa, definição do emissor e homologação. Nenhuma emissão foi simulada.
