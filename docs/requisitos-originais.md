# 33. PUBLICAÇÃO AUTOMÁTICA NO GITHUB

O projeto completo do **OrçaPrime** deverá ser preparado e publicado no seguinte repositório GitHub já existente:

**Repositório oficial do projeto:**

`git@github.com:mateuscpa2026/or-a-facil.git`

Este deverá ser considerado o **repositório oficial do OrçaPrime**.

Não criar outro repositório sem necessidade. Todo o código-fonte, documentação, testes, configurações de build e workflows deverão ser preparados para funcionar nesse repositório.

O repositório deverá conter:

- Código-fonte completo e organizado.
- Documentação.
- Testes automatizados.
- Arquivos necessários para build no Windows.
- Configuração do PyInstaller.
- Script do Inno Setup.
- GitHub Actions.
- `.gitignore`.
- `.env.example`.
- Documentação do sistema de licenciamento.
- Documentação para geração do instalador.
- Documentação para criação de Releases.

Configurar o Git local, quando necessário, utilizando como origem:

`git remote add origin git@github.com:mateuscpa2026/or-a-facil.git`

Caso o remote `origin` já exista, utilizar:

`git remote set-url origin git@github.com:mateuscpa2026/or-a-facil.git`

Criar GitHub Actions para:

- Executar automaticamente todos os testes.
- Impedir a publicação caso testes obrigatórios falhem.
- Gerar o executável Windows.
- Empacotar as dependências necessárias.
- Gerar o instalador utilizando Inno Setup.
- Calcular o SHA-256 do instalador.
- Criar artefato contendo o instalador.
- Publicar o instalador em Releases quando uma versão/tag for criada.
- Publicar o checksum juntamente com o instalador.

Utilizar **GitHub Secrets** para qualquer segredo, token, senha, credencial ou chave privada.

Nunca armazenar segredos de produção diretamente no código-fonte.

Nome do programa:

**OrçaPrime**

Nome do executável:

`OrcaPrime.exe`

Nome final do instalador:

`OrcaPrime-Setup.exe`

---

# 34. SISTEMA DE LICENÇA E ATIVAÇÃO

O **OrçaPrime** deverá possuir sistema profissional de licença e ativação.

Cada cliente receberá um código exclusivo.

Formato:

`XXXX-XXXX-XXXX-XXXX-XXXX`

Exemplos:

`A2B3-C4D5-E6F7-G8H9-J2K3`

`2345-ABCD-6789-EFGH-2345`

Utilizar somente letras maiúsculas e números.

Sempre que possível, evitar caracteres visualmente ambíguos como:

`O / 0`

`I / 1`

A chave deverá possuir exatamente **5 blocos de 4 caracteres separados por hífen**.

Não utilizar uma única senha universal para todos os clientes.

Cada licença deverá possuir identificador único e ser verificável individualmente pelo servidor de licenciamento.

A geração das licenças deverá utilizar um gerador criptograficamente seguro.

---

# 35. PRIMEIRA EXECUÇÃO

Na primeira execução do programa, apresentar obrigatoriamente:

**ATIVAÇÃO DO ORÇAPRIME**

Campo:

**Código de ativação**

Botão:

**ATIVAR**

Adicionar opção para colar o código.

O campo deverá:

- Converter automaticamente letras para MAIÚSCULAS.
- Adicionar automaticamente os hífens.
- Aceitar somente caracteres permitidos.
- Formatar automaticamente códigos colados.
- Limitar o tamanho ao formato definido.

Exemplo:

`AB23-CD45-EF67-GH89-JK23`

Não permitir acesso ao sistema principal enquanto uma licença obrigatória não estiver validada.

Apresentar mensagens apropriadas para:

- Licença inválida.
- Licença bloqueada.
- Licença expirada.
- Licença cancelada.
- Limite de dispositivos atingido.
- Falha de conexão.
- Servidor de licenciamento indisponível.

---

# 36. EXIBIÇÃO SEGURA DA LICENÇA

Depois da ativação, não mostrar a chave completa.

Exemplo original:

`AB23-CD45-EF67-GH89-JK23`

Exibição protegida:

`AB**-****-****-****-**23`

Mostrar somente os **2 primeiros caracteres e os 2 últimos caracteres**.

Nunca registrar a chave completa desnecessariamente em logs ou mensagens de erro.

---

# 37. VALIDAÇÃO

Não implementar segurança utilizando simplesmente:

`if codigo == "1234-5678-...": liberar_programa()`

Não armazenar uma lista completa de chaves válidas dentro do executável.

Criar uma **API de licenciamento separada**.

Fluxo:

**OrçaPrime**
→ solicitação HTTPS
→ servidor de licenciamento
→ consulta da licença
→ validação
→ resposta autenticada/assinada
→ OrçaPrime verifica a resposta
→ ativação registrada.

Segredos administrativos e chaves privadas deverão permanecer no servidor.

Nunca colocar uma chave privada de produção dentro do executável.

Não enviar ou registrar desnecessariamente dados pessoais do computador.

---

# 38. INFORMAÇÕES DA LICENÇA

Cada licença deverá possuir:

- Código.
- Identificador interno.
- Plano.
- Data de criação.
- Data de ativação.
- Situação.
- Data de expiração, quando aplicável.
- Limite de dispositivos.
- Quantidade de ativações.
- Data da última validação.

Status:

**ATIVA**

**BLOQUEADA**

**EXPIRADA**

**CANCELADA**

Planos:

**GRÁTIS**

**PRO**

**EMPRESA**

---

# 39. LICENÇA PERMANENTE E ASSINATURA

Preparar o sistema para:

**Licença permanente**

e

**Licença por assinatura.**

Períodos:

- 30 dias.
- 90 dias.
- 365 dias.
- Permanente.

A validade deverá ser determinada principalmente pelo servidor.

Não depender exclusivamente do relógio local do computador.

O servidor deverá determinar:

- Status.
- Plano.
- Expiração.
- Bloqueio.
- Cancelamento.
- Limite de dispositivos.

---

# 40. PAINEL ADMINISTRATIVO DE LICENÇAS

Criar separadamente um **Painel Administrativo do OrçaPrime**, protegido e destinado ao proprietário do software.

Permitir:

- Gerar nova licença.
- Pesquisar licença.
- Consultar licença.
- Ativar.
- Bloquear.
- Desbloquear.
- Cancelar.
- Renovar.
- Alterar plano.
- Alterar validade.
- Consultar data de criação.
- Consultar data de ativação.
- Consultar expiração.
- Consultar quantidade de ativações.
- Consultar limite de dispositivos.

Adicionar:

**GERAR LICENÇA**

O gerador deverá produzir automaticamente códigos:

`XXXX-XXXX-XXXX-XXXX-XXXX`

Utilizar geração criptograficamente segura.

Nunca utilizar códigos previsíveis ou sequenciais.

---

# 41. SEGURANÇA DO GITHUB

O projeto ficará no repositório:

`git@github.com:mateuscpa2026/or-a-facil.git`

Nenhuma informação secreta poderá ser publicada nesse repositório.

Não publicar:

- Chaves privadas.
- Tokens.
- Senhas.
- Credenciais do banco de produção.
- Segredos da API.
- Chaves administrativas.
- `.env` real.
- Banco de clientes.
- Banco de licenças de produção.
- Backups privados.

Utilizar:

- Variáveis de ambiente.
- GitHub Secrets.
- Configurações seguras no servidor.

O `.gitignore` deverá impedir o envio acidental de arquivos contendo credenciais.

Fornecer:

`.env.example`

Esse arquivo deverá possuir somente nomes das variáveis e valores fictícios.

---

# 42. INSTALADOR

O instalador deverá instalar:

**OrçaPrime**

Criar:

- Atalho no Menu Iniciar.
- Atalho opcional na Área de Trabalho.
- Desinstalador.
- Ícone do aplicativo.
- Entrada apropriada na lista de aplicativos instalados do Windows.

O cliente não deverá precisar instalar Python.

Todas as dependências necessárias deverão ser incluídas na distribuição.

Executável:

`OrcaPrime.exe`

Instalador:

`OrcaPrime-Setup.exe`

A instalação e a ativação da licença deverão ser tratadas separadamente.

O instalador instala normalmente o aplicativo.

Na primeira execução, o **OrçaPrime** solicita a licença.

---

# 43. RELEASE DO GITHUB

As Releases deverão ser realizadas no repositório:

`git@github.com:mateuscpa2026/or-a-facil.git`

Quando uma nova versão/tag for publicada, o GitHub Actions deverá executar:

**Nova Tag/Release**
→ testes
→ build Windows
→ PyInstaller
→ `OrcaPrime.exe`
→ Inno Setup
→ `OrcaPrime-Setup.exe`
→ cálculo SHA-256
→ artefatos
→ GitHub Release.

Gerar:

`OrcaPrime-Setup.exe`

e:

`OrcaPrime-Setup.exe.sha256`

Publicar ambos na Release correspondente.

Nunca incluir na Release:

- Banco de clientes.
- Banco de licenças.
- `.env`.
- Tokens.
- Senhas.
- Chaves privadas.
- Credenciais administrativas.

---

# 44. RESULTADO OBRIGATÓRIO

A entrega do **OrçaPrime** somente poderá ser considerada completa quando houver:

- Projeto completo.
- Código-fonte organizado.
- Projeto publicado/preparado no repositório `git@github.com:mateuscpa2026/or-a-facil.git`.
- Testes aprovados.
- Executável funcionando.
- `OrcaPrime.exe` funcionando.
- Instalador Windows funcionando.
- `OrcaPrime-Setup.exe` funcionando.
- Cliente sem necessidade de instalar Python.
- Tela de ativação funcionando.
- Formatação automática da licença funcionando.
- Ocultação segura da licença funcionando.
- Sistema de licenciamento funcionando.
- API de licenciamento funcionando.
- Gerador de licenças funcionando.
- Painel administrativo funcionando.
- Licença permanente funcionando.
- Assinaturas funcionando.
- Limite de dispositivos funcionando.
- Segredos fora do código-fonte.
- `.gitignore` configurado.
- `.env.example` criado.
- GitHub Actions executando os testes.
- GitHub Actions gerando o executável.
- Inno Setup gerando o instalador.
- SHA-256 sendo calculado.
- Artefato do instalador disponível.
- Workflow de Release funcionando.
- Documentação de instalação.
- Documentação da API de licenciamento.
- Documentação para geração de novas licenças.
- Documentação para criação de novas versões.
- Release preparada para disponibilizar o instalador.

## IDENTIDADE FINAL DO PROJETO

**Nome comercial:** OrçaPrime

**Descrição:** Sistema Profissional de Orçamentos

**Executável:** `OrcaPrime.exe`

**Instalador:** `OrcaPrime-Setup.exe`

**Repositório oficial:** `git@github.com:mateuscpa2026/or-a-facil.git`

**Tela de ativação:** ATIVAÇÃO DO ORÇAPRIME

**Desenvolvedor:** OLIVERTECH SOLUÇÕES

O nome **OLIVERTECH** poderá aparecer nos créditos, informações do desenvolvedor e documentação, mas não deverá substituir **OrçaPrime** como nome principal do produto.