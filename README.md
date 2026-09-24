# OrçaPrime Assistência 2.1

Aplicativo gratuito para Windows, com dados locais e sem licença online ou mensalidade.

[Baixar a última versão](https://github.com/srolivercpa1/OrcaPrime/releases/latest)

## Novidades da versão 2.1

- Painel operacional com OS em andamento, atrasadas, aguardando aprovação e prontas para retirada; cartões abrem as listas correspondentes.
- Filtros combinados por cliente/equipamento, situação, técnico, prioridade e prazo; visualização em tabela ou por etapas.
- Prioridades baixa/normal/alta/urgente, campos multilinha e checklists de celular/computador/outros sem substituir anotações existentes.
- Histórico por cliente e serial/IMEI; sem serial, o sistema identifica o resultado como histórico do cliente.
- Central de impressão acessível pela lista ou pelo editor: OS, entrada, entrega, recibo, garantia e etiquetas, com prévia no leitor PDF.
- Observações internas separadas dos serviços executados públicos; dados internos não aparecem nos PDFs.
- Produtividade por técnico e período, baseada no primeiro evento de entrega, com exportação CSV.
- Compatibilidade de restauração com backups anteriores, sem apagar os dados existentes.

## Recursos

- Clientes, catálogo e orçamentos em PDF preservados da versão 1.
- Ordens de serviço com equipamento, marca, modelo, série, acessórios, diagnóstico, técnico, previsão, checklists e histórico.
- Peças e mão de obra na OS; aprovação registrada antes do reparo e congelamento dos valores aprovados.
- Estoque com entradas, saídas, ajustes, consumo por OS e devolução no cancelamento.
- Fornecedores, contas a pagar/receber, parcelas mensais, recebimentos parciais, estornos e livro-caixa.
- Abertura e conferência do caixa em dinheiro, separada de PIX e outros meios.
- Entrega com recebedor/checklist e retornos vinculados à OS original; garantia configurável por OS.
- Fotos e anexos armazenados no banco, incluídos nos backups.
- PDFs de OS, entrada, recibo e garantia em A4/58/80 mm; etiquetas de 80×40 mm.
- Seleção de impressoras instaladas no Windows; exportação e abertura em leitor PDF.
- Relatórios e exportação CSV; perfis administrador, atendimento, técnico e financeiro.
- Backup automático na abertura (até sete cópias diárias locais), backup manual e restauração validada.

## Primeiro uso

1. Instale `OrcaPrime-Setup.exe`.
2. Crie seu usuário administrador e uma senha de pelo menos 10 caracteres. Este acesso é local, sem cadastro online.
3. Cadastre a empresa e os clientes. Adicione peças e registre o saldo inicial do estoque.
4. Abra uma OS e preencha a entrada. Salve antes de adicionar itens, pagamentos ou anexos.
5. Passe por diagnóstico e aprovação. Para iniciar reparo, registre quem aprovou e por qual canal.
6. Registre recebimentos, testes de saída e recebedor antes de entregar.

## Impressão e limites atuais

O driver deve ser instalado pelo Windows ou pelo fabricante. A impressão direta de PDF depende de leitor com suporte ao comando Windows `printto`; se indisponível, exporte/abra o PDF e imprima pelo leitor. O envio ao leitor/fila não comprova impressão física. Corte automático e comandos específicos de impressoras não são implementados. Teste papel e margens no seu modelo.

**Não emite NF-e, NFC-e ou NFS-e nesta versão.** A tela fiscal informa que não está configurada. OS, recibos e PDFs não são documentos fiscais autorizados. A integração fiscal depende da definição do emissor e dos dados da empresa.

Destina-se ao uso local em um computador. Não compartilhe o arquivo SQLite diretamente em uma pasta de rede para acesso simultâneo. Prazos de garantia são configurados pela assistência; não representam orientação jurídica. Senhas/PINs de desbloqueio de aparelhos não devem ser guardados nas observações.

## Atualização e segurança dos dados

A atualização usa a mesma pasta de dados `%LOCALAPPDATA%\OrcaPrime`. Novas tabelas são adicionadas sem apagar clientes/orçamentos existentes. Na primeira abertura há configuração de acesso local. Faça também um backup manual em dispositivo externo antes de atualizar. Backups no mesmo computador não protegem contra perda do equipamento.

Depois de restaurar um backup, o programa fecha para reabrir com os usuários e permissões restaurados. Guarde a senha administrativa. Permissões do aplicativo não substituem a proteção da conta Windows e não impedem um administrador do computador de acessar o banco.

## Desenvolvimento

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m orcaprime
```

Windows: `scripts/build_windows.ps1` testa, empacota com PyInstaller, verifica abertura, compila com Inno Setup e calcula SHA-256. GitHub Actions publica uma Release após aprovação desses passos. O pacote não exige Python instalado no computador do cliente.

Os módulos de licenciamento antigos permanecem como histórico técnico e não são utilizados na inicialização gratuita.
