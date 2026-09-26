# Notas fiscais e impressão — OrçaPrime 1.0

Atualização de 26/09/2026. A versão visível continua **1.0**; a revisão técnica do instalador é 1.0.3.

## Disponível nesta entrega

- Impressoras: consulta ao Windows sem abrir uma janela do PowerShell.
- Roda do mouse: menu lateral, formulários roláveis e tela de acesso. Listas e campos com rolagem própria conservam seu comportamento.
- Notas fiscais: selecionar o PDF fornecido pelo emissor, visualizar e enviar à impressora selecionada. O arquivo original não é alterado nem arquivado automaticamente.

Abra **Notas fiscais → Selecionar PDF da nota**, escolha a impressora e clique em **Imprimir nota**. Use a impressora e o papel compatíveis com o documento. É necessário um leitor PDF associado no Windows com suporte ao comando de impressão. O envio ao leitor não confirma a impressão física; confira a fila do Windows. A autorização fiscal do arquivo selecionado não é verificada pelo OrçaPrime.

## Integração de emissão ainda necessária

Imprimir um PDF não emite uma nota. Ordens de serviço, garantias e recibos permanecem documentos administrativos. Esta versão não transmite documentos fiscais à prefeitura, ao Sistema Nacional NFS-e ou à SEFAZ.

Para definir a integração precisamos da cidade/UF do estabelecimento, tipo de empresa (MEI ou outro regime) e se emitirá notas de serviços, de mercadorias ou ambas. Dados cadastrais e tributação precisam ser confirmados com o contador. Certificados e senhas devem ser configurados localmente por um fluxo protegido, nunca incluídos no repositório ou enviados no chat.

### Caminho técnico proposto

1. Para serviços, conferir o emissor aplicável ao contribuinte e os parâmetros do município. A documentação nacional prevê consulta de convênio, alíquotas, retenções e benefícios.
2. Preparar o documento fiscal com os dados da empresa, cliente e serviço, validar contra os esquemas vigentes e autenticar/assinar conforme os requisitos da API escolhida.
3. Enviar a DPS ao emissor nacional quando aplicável e guardar o retorno: rejeição explicada ou XML da NFS-e gerada. Usar identificador estável e consulta antes de repetir uma transmissão cujo resultado seja desconhecido, evitando duplicidade.
4. Persistir XML, chave, situação e eventos com rastreabilidade; separar testes e produção. Somente indicar emissão concluída após confirmação do emissor.
5. Obter o DANFSe pela API apropriada e reutilizar o fluxo de impressão. Implementar consulta e cancelamento conforme as regras do emissor.
6. Para mercadorias, implementar separadamente NF-e/NFC-e conforme UF e operação, incluindo credenciamento, certificado e demais requisitos aplicáveis; guardar XML/protocolo autorizado e gerar o documento auxiliar adequado.

Não há integração fiscal paga contratada nem certificado fiscal configurado nesta entrega. Uma integração comercial para vários clientes exige configuração por contribuinte, homologação e manutenção dos leiautes e regras fiscais.

## Fontes oficiais consultadas

- [Documentação atual da NFS-e](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual): manuais, esquemas e anexos vigentes.
- [Manual da API do Emissor Público Nacional](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/manual-contribuintes-emissor-publico-api-sistema-nacional-nfs-e-v1-2-out2025.pdf): parâmetros municipais, DPS, emissão, consultas e eventos.
- [APIs de testes e produção, incluindo DANFSe](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao).
- [Portal Nacional NF-e](https://www.nfe.fazenda.gov.br/portal/): documentação de NF-e/NFC-e e documentos auxiliares.
