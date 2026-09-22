# GitHub, executável, instalador e Releases

Repositório único: `git@github.com:srolivercpa1/OrcaPrime.git`.

## Enviar o projeto

O usuário alterou o destino para `srolivercpa1/OrcaPrime`, com acesso de escrita confirmado. Os comandos abaixo também permitem publicação manual. Extraia o ZIP e abra um terminal na pasta que contém README.md, run_app.py e .github.

Para o repositório remoto vazio, após conferir os arquivos:

```bash
git init -b main
git remote add origin git@github.com:srolivercpa1/OrcaPrime.git
git add .
git status
git commit -m "feat: implementa OrcaPrime e licenciamento"
git push -u origin main
```

Se origin já existir, use `git remote set-url origin git@github.com:srolivercpa1/OrcaPrime.git`. Configure sua chave SSH ou use GitHub Desktop autenticado como proprietário. Se o remoto ganhar arquivos antes do envio, faça clone dele e copie os arquivos do pacote para o clone, preservando os existentes e revendo diferenças. Não use `--force`.

**Não envie somente o ZIP para o repositório:** Actions precisa dos arquivos extraídos, especialmente `.github/workflows/build.yml`. Nunca force adicionar arquivos ignorados; revise `git status` antes do commit.

## Configurar o build

Implante o servidor conforme SERVIDOR.md. No GitHub: **Settings → Secrets and variables → Actions → Variables**, cadastre:

- `ORCAPRIME_LICENSE_URL`: domínio HTTPS real do servidor.
- `ORCAPRIME_PUBLIC_KEY`: chave pública Ed25519 em Base64 mostrada pelo setup.

Esses dois valores são públicos. Não coloque chave privada, pepper, senha administrativa ou banco no GitHub. Caso acrescente futuramente credenciais de implantação ou assinatura de código, use **GitHub Secrets**, nunca o código-fonte.

O workflow falha intencionalmente se a configuração estiver ausente ou usar os exemplos. Isso evita entregar um instalador que não possa ativar clientes. Configuração pública muda somente ao reconstruir a distribuição.

Em **Actions → Testes e instalador OrçaPrime → Run workflow**, execute e aguarde. O job test roda no Windows; build depende dele. O script executa os testes novamente, prepara a configuração, gera o ícone, executa PyInstaller, verifica a abertura do processo, executa Inno Setup e calcula SHA-256. Esse teste de abertura verifica processo vivo; a homologação visual e de uso no Windows continua obrigatória.

Após sucesso, baixe **OrcaPrime-Windows** em Artifacts. Conteúdo:

- `OrcaPrime-Setup.exe`
- `OrcaPrime-Setup.exe.sha256`

PyInstaller inclui Python e dependências do cliente; o cliente não instala Python, FastAPI nem o servidor. A distribuição não inclui chaves privadas, banco do proprietário ou `.env`. O instalador é por usuário, cria Menu Iniciar, atalho opcional e desinstalador, e preserva os dados do usuário. Sem certificado de assinatura de código, o Windows pode mostrar fornecedor desconhecido; a entrega não inclui certificado Authenticode.

## Gerar localmente no Windows

Instale Python 3.12 x64 para desenvolvimento e Inno Setup 6. No PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
$env:ORCAPRIME_LICENSE_URL = 'https://SEU_DOMINIO_REAL'
$env:ORCAPRIME_PUBLIC_KEY = 'SUA_CHAVE_PUBLICA_BASE64'
.\scripts\build_windows.ps1
```

Saída em `release\`. Nunca distribua somente o EXE isolado de `dist\OrcaPrime`: o aplicativo precisa da pasta de dependências. Distribua o instalador.

## Publicar nova versão

1. Ajuste a versão em `orcaprime/__init__.py`, texto da UI e `installer/OrcaPrime.iss`.
2. Execute os testes e homologue o Windows.
3. Faça commit e push.
4. Crie uma tag correspondente:

```bash
git tag v1.0.0
git push origin v1.0.0
```

A tag v* dispara testes, build e Release. O job final usa `GITHUB_TOKEN` com permissão contents:write somente para publicar o instalador e checksum. Uma execução falha não publica instalador. O workflow não dispara quando uma Release é criada manualmente sem nova tag: o gatilho implementado é push de tag, além de push em main e execução manual.

Para conferir o arquivo baixado:

```powershell
Get-FileHash .\OrcaPrime-Setup.exe -Algorithm SHA256
```

Compare com o arquivo `.sha256` da mesma Release.
