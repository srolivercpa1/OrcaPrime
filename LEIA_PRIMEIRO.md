# Entrega do OrçaPrime — leia antes de usar

Este pacote contém o projeto do aplicativo, o servidor de licenças, o painel administrativo, testes e os arquivos para gerar o instalador Windows.

**Ele ainda não contém OrcaPrime.exe nem OrcaPrime-Setup.exe.** A geração e a instalação no Windows não foram realizadas nesta sessão. Não renomeie arquivos Python ou ZIP para `.exe`.

## O que falta para disponibilizar aos clientes

1. **Servidor de licenças:** contratar ou usar um servidor próprio com domínio HTTPS. O código está pronto para implantação, mas não foi hospedado. Veja `docs/SERVIDOR.md`.
2. **GitHub:** o repositório atual é `srolivercpa1/OrcaPrime`, com acesso de escrita confirmado. Acompanhe a execução em Actions. Veja `docs/GITHUB_E_BUILD.md`.
3. **Configuração pública:** cadastrar `ORCAPRIME_LICENSE_URL` e `ORCAPRIME_PUBLIC_KEY` nas Variables do repositório. Nunca colocar a chave privada no GitHub ou no executável.
4. **Build Windows:** executar Actions, aguardar os testes e baixar o instalador gerado.
5. **Homologação:** instalar em Windows 10/11 x64 sem Python, ativar com uma licença de teste, criar orçamento e PDF, fazer backup, restaurar e desinstalar. Repetir bloqueio, renovação e expiração com o servidor real.

## Arquivos importantes

- `README.md`: visão geral e desenvolvimento.
- `docs/MANUAL_USUARIO.md`: utilização do programa.
- `docs/SERVIDOR.md`: implantação e geração de licenças.
- `docs/API.md`: contratos da API e segurança.
- `docs/GITHUB_E_BUILD.md`: publicação, instalador e novas versões.
- `docs/STATUS_ENTREGA.md`: o que foi verificado e o que segue pendente.

O documento original começa no item 33. As funções comerciais ausentes nos itens 1–32 foram definidas nesta implementação e estão descritas na especificação técnica incluída.
