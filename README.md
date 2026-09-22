# OrçaPrime

**Sistema Profissional de Orçamentos** — desenvolvido por **OLIVERTECH SOLUÇÕES**.

Aplicativo Windows em português, com clientes, produtos/serviços, orçamentos, PDF, backup, ativação e API de licenciamento independente.

> **Estado desta entrega:** código-fonte publicado e 36 testes aprovados no Windows do GitHub Actions. O instalador Windows ainda NÃO foi gerado nem validado. Não há EXE neste pacote. O projeto foi publicado em `srolivercpa1/OrcaPrime`. O build Windows parou por falta das Variables ORCAPRIME_LICENSE_URL e ORCAPRIME_PUBLIC_KEY; configure o servidor real de licenças e execute o workflow novamente. Consulte `docs/STATUS_ENTREGA.md`.

## Comece por aqui

1. Leia `LEIA_PRIMEIRO.md`.
2. Implante o servidor privado seguindo `docs/SERVIDOR.md`.
3. Configure a URL e a chave pública no GitHub e envie este projeto conforme `docs/GITHUB_E_BUILD.md`.
4. Execute o workflow. Baixe `OrcaPrime-Windows` em Actions ou publique uma tag `v1.0.0` para gerar a Release.
5. Somente depois de o build passar, distribua `OrcaPrime-Setup.exe` e o checksum.

Repositório oficial: https://github.com/srolivercpa1/OrcaPrime

## Funções implementadas

- Visão geral com quantidade de clientes e orçamentos e valor aprovado.
- Cadastro e edição de clientes, produtos e serviços; pesquisa.
- Orçamentos com cliente, validade, quantidades, preços, desconto, observações e pagamento.
- Edição, duplicação e situações RASCUNHO, ENVIADO, APROVADO e RECUSADO.
- PDF paginado, dados da empresa e espaço para aprovação.
- SQLite local, backup e restauração com cópia prévia.
- Ativação obrigatória, formatação automática, colagem e máscara do código.
- Licenças permanentes ou 30/90/365 dias, planos GRÁTIS/PRO/EMPRESA.
- Painel do proprietário: gerar, pesquisar, alterar plano/limite/vencimento, bloquear, desbloquear, cancelar, renovar, consultar e liberar dispositivos.
- Respostas Ed25519, token protegido por DPAPI no Windows e ausência de chaves privadas no cliente.
- PyInstaller, Inno Setup e GitHub Actions com testes antes da geração do instalador.

Os planos são rótulos comerciais e têm as mesmas funções nesta versão. Não há cobrança automática, integração de pagamentos, emissão de nota fiscal, sincronização entre computadores ou modo offline prolongado.

## Desenvolvimento

Use Python 3.12. No Windows, o instalador oficial do Python inclui Tcl/Tk.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Para abrir a aplicação, prepare `config/client.json` com URL HTTPS e chave pública reais (manual de build), depois:

```powershell
python -m orcaprime
```

Sem configuração válida, o aplicativo informa a pendência e não libera o sistema principal. Não há chave universal nem caminho de demonstração que burle a licença.

## Estrutura

- `orcaprime/`: aplicativo, dados comerciais, PDF e cliente de licença.
- `licensing/`: API, persistência de licenças, autenticação e painel web.
- `tests/`: testes de regras comerciais, assinatura, API, limites e interface.
- `scripts/`: preparação do servidor, configuração pública e build.
- `installer/`: configuração Inno Setup.
- `.github/workflows/`: testes, build e Release.
- `docs/`: operação, implantação, API, plano e estado verificável.

© 2026 Mateus Oliveira — OLIVERTECH SOLUÇÕES. Todos os direitos reservados. Consulte `LICENSE.txt`.
