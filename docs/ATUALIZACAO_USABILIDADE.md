# OrçaPrime 1.0 — Usabilidade e fotos

Atualização de 28/09/2026, instalador revisão 1.0.4. A versão exibida continua 1.0.

- Janela principal maximizada ao entrar no aplicativo.
- Cadastro de clientes com formulário rolável e botões fixos no rodapé.
- Nova OS adaptada ao tamanho da tela; comandos em duas colunas, sem depender de rolar para salvar.
- Botão **+ Novo cliente** na entrada da OS: cria e seleciona o cliente sem perder o preenchimento, inclusive no primeiro atendimento de uma base sem clientes.
- Área de histórico e anexos rolável, com pré-visualização de imagens.
- Botão **Adicionar fotos** disponível na OS: permite selecionar até 20 imagens de uma vez; em uma OS nova, primeiro salva os dados válidos. Fotos ficam vinculadas à OS e entram no backup do banco.
- Cópias de fotos em JPEG, até 1920 pixels no maior lado e qualidade 85; limite de entrada de 25 MB/25 megapixels por foto. Arquivos originais permanecem intactos. JPG, PNG, WEBP e BMP são aceitos; outros arquivos continuam disponíveis em **Adicionar foto / anexo**.
- Consulta das impressoras e preparação das fotos fora da fila da interface. O backup inicial ocorre em segundo plano após o login. Falhas de cópia continuam sendo informadas.
- Busca na lista de clientes/produtos filtra os dados carregados, sem consultar novamente o banco a cada letra digitada.

Enquanto as fotos são importadas, o programa solicita aguardar antes de fechar a OS ou sair, para evitar uma importação interrompida. Cada arquivo tem resultado individual; uma foto inválida não impede salvar as demais.

O desempenho em bases grandes, unidades de rede e drivers de impressora depende do computador e do ambiente. Esta revisão trata as operações bloqueantes identificadas; não representa uma garantia de eliminar qualquer travamento externo.
