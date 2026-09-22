# OrçaPrime Implementation Plan

**Goal:** Implementar aplicativo Windows de orçamentos e licenciamento independente.
**Architecture:** Cliente local SQLite; API FastAPI assinada; painel HTML; build Windows separado.
**Tech Stack:** Python 3.11+, Tkinter, ReportLab, cryptography, FastAPI, PyInstaller, Inno Setup.
**Spec:** ../specs/2026-09-22-orcaprime.md

## Global Constraints
Nome OrçaPrime; executável OrcaPrime.exe; instalador OrcaPrime-Setup.exe; desenvolvedor OLIVERTECH SOLUÇÕES. Nenhum segredo de produção no projeto. Publicação somente no repositório informado. Testes obrigatórios precedem build e Release.

## Review Focus
1. Valores com vírgula, quantidades fracionárias e desconto maior que subtotal.
2. Backup inválido não altera o banco atual.
3. Reenvio concorrente não ultrapassa limite de dispositivos.
4. Resposta adulterada ou de outro dispositivo/nonce nunca libera aplicação.
5. Falha de rede não prolonga licença indefinidamente.

## Etapas e interfaces
- [x] 1. Testes comerciais em tests/test_business.py: total de 2,5 × 10,00 menos 3,00 = 22,00; rejeitar NaN/negativo; CRUD e snapshots; PDF e restauração. Executar pytest (falha esperada: módulos ausentes). Implementar orcaprime/domain.py, storage.py, pdf.py. Interface Store(path), save_customer, save_item, save_quote, get_quote, list_quotes, backup, restore; calculate(items, discount).
- [x] 2. Testes de licenças em tests/test_licensing.py: format_code/mask_code, criação e ativação, limite, revogação, concorrência, autenticação, assinatura. Implementar licensing/service.py, api.py, security.py e orcaprime/license_client.py. API /v1/activate, /v1/validate, /admin/licenses, /admin/licenses/{id}, /admin/licenses/{id}/renew, /admin/licenses/{id}/devices/{id}. Executar suíte até verde.
- [x] 3. Implementar interface orcaprime/ui.py e quote_editor.py consumindo Store e LicenseClient. Tela de ativação impede construção da janela principal antes de verificação. Painel HTML usa endpoints autenticados e textContent para valores. Testar smoke GUI com banco temporário, sem modo de ativação alternativo no produto.
- [x] 4. Configuração pública validada no build; scripts/build_windows.ps1, OrcaPrime.spec, installer/OrcaPrime.iss e .github/workflows/build.yml. Tests -> PyInstaller -> smoke -> Inno -> checksum -> artifact -> tag Release.
- [x] 5. Manual de cliente, API, implantação, geração e publicação. Revisão independente, corrigir achados importantes com regressões. Executar suíte completa e compilar módulos. Entregar ZIP sem segredos, cache ou banco real; registrar gates não executados.

## Execução
Execução nativa nesta sessão, autorizada pelo pedido “quero que você crie tudo”. Decisões e resultados em docs/STATUS_ENTREGA.md. Código e configuração novos em diretório isolado; nenhum arquivo prévio do usuário será sobrescrito.


Estado final: implementação local concluída; gates externos de produção e Windows registrados em docs/STATUS_ENTREGA.md. Não confundir arquivos de build preparados com instalador produzido.
