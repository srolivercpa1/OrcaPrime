# OrçaPrime — especificação de implementação

Produto Windows para pequenos negócios criarem orçamentos, desenvolvido por OLIVERTECH SOLUÇÕES. Repositório exclusivo: git@github.com:srolivercpa1/OrcaPrime.git. Requisitos recebidos: itens 33–44 em requisitos-originais.md. Os itens 1–32 não foram fornecidos; as funções abaixo são decisões de implementação, não transcrição de requisitos ausentes.

## Arquitetura
Aplicativo Python 3.11+ com Tkinter/ttk e SQLite por usuário, PDF com ReportLab; servidor independente FastAPI, SQLite transacional, respostas Ed25519; painel web administrativo. Instalador Inno Setup com PyInstaller, Windows 10/11 x64. Preferido a um sistema web integral porque o pedido exige executável e armazenamento local; preferido a um servidor por cliente porque separa os dados comerciais do licenciamento.

## Fluxos comerciais
Cadastro e edição de clientes (nome, documento, telefone, email, endereço) e catálogo (produto/serviço, descrição, unidade, preço). Orçamentos numerados, itens livres ou do catálogo, quantidade decimal, preço em reais, desconto fixo, validade, condições, observações, status RASCUNHO/ENVIADO/APROVADO/RECUSADO. Duplicação e edição preservam dados históricos do cliente e dos itens. Arredondamento monetário decimal por linha, total não negativo. PDF paginado com empresa, cliente, itens, total e condições. Busca, painel de totais e contagens. Backup consistente e restauração validada com cópia de segurança prévia. Dados ficam no perfil do Windows, nunca na pasta de instalação.

## Licenças
Formato cinco blocos de quatro caracteres, alfabeto sem O/0/I/1, geração secrets. Exibição AB**-****-****-****-**23. Servidor mantém apenas HMAC do código, máscara e metadados; código completo mostrado somente ao criar. Planos GRATIS/PRO/EMPRESA, todos com mesmas funções nesta versão, sem regras comerciais inventadas. Vigência 30/90/365 dias a partir da primeira ativação ou permanente. Renovação soma período ao maior valor entre agora e vencimento. Estados ATIVA/BLOQUEADA/EXPIRADA/CANCELADA. Ativação idempotente por identificador aleatório persistente da instalação, sem coletar hardware. Reinstalar/apagar dados pode consumir outro dispositivo; proprietário pode liberar um dispositivo pelo painel.

Cliente exige internet na ativação e em toda abertura; revalida a cada 5 minutos com lease de 15 minutos medido por relógio monotônico. Indisponibilidade na abertura não libera acesso. Durante sessão já validada, falha de rede permite apenas o restante do lease; revogação bloqueia na próxima resposta. Não há modo offline prolongado. Resposta assinada vinculada ao dispositivo, licença, nonce de cada pedido e horário do servidor. Renovação usa token aleatório de dispositivo, armazenado com DPAPI no Windows; chave completa não persiste. Chave pública e URL HTTPS são fixadas no build. Configuração pública não permite troca do verificador na interface.

## Administração e implantação
Painel exige autenticação HTTP Basic por HTTPS, senha armazenada como hash scrypt, proteção de origem nas mutações, cabeçalhos restritivos, limitação de requisições. Criar/buscar/editar/renovar/bloquear/desbloquear/cancelar e liberar dispositivos. Não incluir servidor/chaves privadas/bancos no executável. Servidor precisa de domínio HTTPS, volume persistente e segredos provisionados pelo proprietário. Nenhum segredo real é entregue.

## Verificação e critérios de entrega
Testes de valores, cadastros, PDF, backup, ativação, expiração, revogação, limite concorrente, adulteração, nonce, autenticação. Smoke test da tela em display virtual e Windows no CI. Workflow testa antes do build, gera instalador, SHA-256 e publica tag v*. Instalador cria atalhos e desinstalador, preserva dados do usuário. Instalação não depende de Python no cliente.

## Restrições constatadas
Em 22/09/2026 a conexão GitHub reporta push=false; repositório vazio. Ambiente local Linux sem Wine/Windows. Portanto publicação, build Windows e instalação real são gates pendentes; não declarar executável ou implantação funcionando sem evidência. Entregar código preparado, testes verificáveis e instruções concretas, com status explícito.
