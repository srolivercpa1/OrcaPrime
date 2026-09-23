# OrçaPrime — gratuito e offline

Esta edição funciona sem internet, servidor ou código de ativação. Os dados ficam no computador.

Baixe `OrcaPrime-Setup.exe` na [última Release](https://github.com/srolivercpa1/OrcaPrime/releases/latest). O instalador é publicado automaticamente após os testes e a compilação no Windows.

Clientes, produtos, orçamentos, PDF e backups continuam disponíveis. Faça backups regularmente para proteger seus dados. Não é necessário Railway nem configurar variáveis de licença para gerar o instalador.

## Desenvolvimento

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m orcaprime
```

No Windows, execute `scripts/build_windows.ps1` para compilar com PyInstaller e Inno Setup 6.

Os módulos de licenciamento e os documentos antigos ficam preservados como histórico técnico; não são exigidos pela edição gratuita.
