# Estado verificável da entrega — 22/09/2026

## Resultado

**Projeto-fonte implementado e testado localmente. A entrega operacional completa exigida no item 44 ainda NÃO foi atingida.** Não foram produzidos `OrcaPrime.exe` ou `OrcaPrime-Setup.exe`, não houve publicação no GitHub e o servidor não foi implantado.

## Evidências desta sessão

- Repositório oficial consultado: `mateuscpa2026/orca-facil`; tamanho informado 0, branch padrão main, `pull=true`, `push=false`.
- Ambiente de implementação: Linux, Python 3.12.14.
- Suíte final executada com display virtual Xvfb: **36 testes aprovados, 0 falhas, 0 testes ignorados**.
- Inclui telas principais, preservação de edição durante bloqueio, controles do editor visíveis na janela mínima, valores, PDF longo, backup inválido, duplicação histórica, assinatura e nonce, expiração, renovação, limite concorrente, autenticação e limitação por IP do proxy confiável.
- `python -m compileall -q orcaprime licensing scripts`: aprovado.
- `node --check licensing/admin.js`: aprovado.
- Capturas reais da aplicação no display Linux em `docs/imagens/`; dados de clientes são fictícios. As fontes de substituição do Linux não representam a renderização final do Segoe UI no Windows.
- PDF de exemplo gerado pelo próprio módulo em `docs/imagens/orcamento-exemplo.pdf`.
- Dois avisos de depreciação em dependências de teste Starlette/httpx/anyio; não são falhas. Atualização dessas dependências deve passar pela suíte antes de alterar os pins.

## Cobertura do documento recebido

| Item | Implementação | Estado |
|---|---|---|
| 33 | Estrutura, testes, build, Inno, workflow, ignore, exemplo de ambiente e documentação | Preparados; publicação bloqueada por falta de escrita |
| 34 | Código exclusivo, 5 × 4, alfabeto sem O/I/0/1, secrets e HMAC | Testado |
| 35 | Tela obrigatória, colagem, formatação e mensagens | Testado localmente |
| 36 | Máscara somente 2 primeiros/2 últimos; código não persiste no cliente | Testado |
| 37 | API separada, HTTPS, Ed25519, nonce, token e validação | Testado em integração local; produção pendente |
| 38 | Metadados, planos, status, datas e dispositivos | Implementado e testado |
| 39 | Permanência, 30/90/365, tempo do servidor | Testado |
| 40 | Painel HTML autenticado e operações administrativas | API testada; navegador em produção pendente |
| 41 | Segredos excluídos e configuração pública separada | Revisado |
| 42 | Especificação PyInstaller e Inno Setup | Preparada; build/instalação Windows pendentes |
| 43 | Testes → build → instalador → SHA-256 → artifact → Release em tag | Configurado; GitHub Actions ainda não executado |
| 44 | Conjunto de critérios operacionais | NÃO concluído, devido aos gates abaixo |

## Gates externos pendentes

1. Permissão de escrita/autenticação do proprietário para publicar no repositório oficial.
2. Servidor com domínio HTTPS, Docker, persistência e segredos provisionados pelo proprietário.
3. Configuração das Variables públicas de build no GitHub.
4. Execução bem-sucedida do GitHub Actions em Windows.
5. Teste do instalador em Windows 10/11 x64 sem Python: atalhos, primeira abertura, DPAPI, ativação real, PDF, backup e desinstalação.
6. Validação de operação do Docker/Caddy e do painel com TLS em produção. Docker não está disponível neste ambiente.

## Revisão independente e correções

Uma revisão separada encontrou seis problemas importantes. Correções aplicadas:

- Validar estrutura e conteúdo do backup antes de substituir o banco; regressão cobre preservação dos dados.
- Fornecer ajuste restrito da chave para UID 10001, automático quando o setup roda como root e explícito por `server_permissions.py` nos demais casos. A configuração completa do container continua pendente de implantação.
- Ocultar e preservar telas e editores durante bloqueio; reativação os restaura sem liberar ações enquanto a licença está inválida.
- Serializar solicitações pela interface, descartar callbacks de telas anteriores e manter polling mesmo quando um callback falha.
- Duplicar usando o snapshot da proposta original quando o cliente não é trocado.
- Proxy Caddy em IP fixo confiável; limitar por IP encaminhado por ele; tratar 429 como falha temporária sem prolongar nem revogar o lease existente.

A inspeção visual também encontrou falta de espaço para os controles inferiores do editor. O layout passou a reservar o rodapé antes de expandir a tabela, com teste na janela mínima.

## Decisões de escopo

Os itens 1–32 não foram recebidos. O pedido para criar tudo autorizou definir funções comerciais coerentes: clientes, catálogo, orçamentos, PDF, empresa e backup. Não foram inventadas integrações fiscais, pagamentos automáticos ou sincronização. Todos os planos têm as mesmas funções; definir diferenças comerciais exigirá uma nova regra de produto. Os dados comerciais permanecem locais. Licenciamento requer internet na abertura e revalidação periódica, com lease máximo de 15 minutos.

Não houve criação de outro repositório, hospedagem, uso de credenciais inventadas ou publicação de segredos. O pacote ZIP contém código e documentação, não um instalador.

## Atualização de destino

O usuário corrigiu o destino para `git@github.com:mateuscpa2026/orca-facil.git`. Remote local e documentação atualizados. A API confirmou o mesmo ID de repositório (1381500936), agora com nome orca-facil, ainda vazio. Conta conectada: srolivercpa1; proprietário: mateuscpa2026; push=false. Publicação e Release não realizadas. Não há configuração local de URL/chave pública de produção.

## Novo repositório autorizado

Destino atualizado pelo usuário: https://github.com/srolivercpa1/OrcaPrime . A conexão confirmou push=true e admin=true. Projeto preparado para publicação nesse destino. O histórico de falhas de acesso acima refere-se aos repositórios anteriores. Build Windows e implantação permanecem pendentes até execução verificada.
