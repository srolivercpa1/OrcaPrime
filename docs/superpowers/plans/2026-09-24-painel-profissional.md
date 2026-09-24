# OrçaPrime profissional — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar painel operacional, OS avançadas, impressão centralizada e relatórios na aplicação Windows existente.

**Architecture:** Preservar Tkinter, SQLite e as operações transacionais de `Workshop`. Extrair consultas, painel e controle de documentos em módulos focados, reutilizando geração de PDF e impressão existentes. Integração fiscal terá plano próprio após identificação do emissor.

**Tech Stack:** Python 3.12 no CI Windows, Tkinter/ttk, SQLite, ReportLab, pytest, PyInstaller e Inno Setup; dependências já fixadas nos arquivos requirements.

**Spec:** `docs/superpowers/specs/2026-09-24-painel-profissional.md`

## Global Constraints

- Manter Python, Tkinter/ttk e SQLite. Não introduzir mensalidade nem provedor pago.
- Garantir rolagem e acesso às ações na resolução mínima atual de 920×650, inclusive com escala de tela do Windows.
- Preservar aprovação antes do reparo, congelamento de valores aprovados, consumo transacional de estoque, estornos e identificação de entrega.
- Documentos administrativos permanecem identificados como não fiscais.
- Não criar disparos automáticos de mensagens ao cliente nesta ampliação.
- Credenciais e certificados serão configurados localmente, fora do repositório e dos logs; nunca solicitados em mensagens.
- A tela continuará indicando emissão não configurada enquanto essa etapa não estiver homologada.

## Review Focus

1. Datas vazias ou inválidas em bases antigas: excluir do atraso e sinalizar previsão inválida; teste na tarefa 1.
2. Perfil desativado durante a sessão: nova consulta/ação deve negar acesso; teste na tarefa 1.
3. Mesmo modelo sem serial: histórico não pode afirmar ser o mesmo aparelho; teste na tarefa 3.
4. Impressão interrompida ou sem impressora: nenhum efeito nos dados; teste na tarefa 4.
5. Textos longos, escala de tela e observações internas: controles acessíveis e documentos sem vazamento; testes nas tarefas 2 e 4.

## Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `orcaprime/workshop_queries.py` | Filtros puros, indicadores, histórico e produtividade |
| `orcaprime/workshop.py` | Autorizar consultas e validar prioridade na gravação |
| `orcaprime/dashboard_ui.py` | Cartões, agenda e alertas do painel |
| `orcaprime/widgets.py` | Estilos e componentes visuais compartilhados |
| `orcaprime/ui.py` | Integração do painel, menu e tratamento de permissões |
| `orcaprime/order_templates.py` | Modelos de checklist e inserção sem apagar texto |
| `orcaprime/workshop_ui.py` | Lista filtrada, etapas, formulário e relatórios |
| `orcaprime/document_actions.py` | Geração, prévia e impressão sem mutações de OS |
| `orcaprime/service_documents.py` | Documento de entrega e separação de campos públicos |
| `tests/test_workshop_queries.py` | Regras de consulta e permissões |
| `tests/test_dashboard_ui.py` | Navegação, perfis e geometria do painel |
| `tests/test_order_templates.py` | Preservação de checklists |
| `tests/test_document_actions.py` | Cancelamentos e falhas de impressão |
| `tests/test_service_documents.py` | Conteúdo e formatos dos PDFs |
| `tests/test_workshop_ui.py` | Fluxo integrado de edição e filtros |

## Task 1 — consultas operacionais autorizadas

Interfaces produzidas em `workshop_queries.py`:

```python
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class OrderFilters:
    text: str = ''
    status: str = ''
    technician: str = ''
    priority: str = ''
    deadline: str = ''  # '', 'overdue', 'today', 'undated'

def filter_orders(orders: list[dict], filters: OrderFilters, today: date) -> list[dict]: ...
def summarize_orders(orders: list[dict], today: date) -> dict: ...
def equipment_history(orders: list[dict], customer_id: int, serial: str) -> dict: ...
```

As declarações acima fixam interfaces; os corpos são implementados nesta tarefa. `summarize_orders` retorna `active`, `overdue`, `awaiting_approval`, `ready`, `invalid_dates` e `due_today`. `equipment_history` retorna `scope` (`equipment` ou `customer`) e `orders`.

- [ ] Criar testes com data fixa, inclusive registros antigos:

```python
from datetime import date
from orcaprime.workshop_queries import OrderFilters, filter_orders, summarize_orders

def test_overdue_excludes_closed_and_invalid_dates():
    rows = [dict(id=i, status=s, due_date=d) for i, s, d in [
        (1, 'RECEBIDA', '2026-09-23'), (2, 'ENTREGUE', '2026-09-23'),
        (3, 'CANCELADA', '2026-09-23'), (4, 'RECEBIDA', ''),
        (5, 'RECEBIDA', 'data antiga'), (6, 'RECEBIDA', '2026-09-24')]]
    result = filter_orders(rows, OrderFilters(deadline='overdue'), date(2026, 9, 24))
    assert [r['id'] for r in result] == [1]
    assert summarize_orders(rows, date(2026, 9, 24))['invalid_dates'] == 1
```

- [ ] Rodar `python -m pytest tests/test_workshop_queries.py -q` e confirmar falha pela ausência do módulo.
- [ ] Implementar conjunção dos filtros. Busca usa número, nome do cliente, equipamento e serial, sem pesquisar anexos ou pagamentos. Técnico ignora caixa/espaços externos; prioridade ausente equivale a NORMAL. Datas usam `date.fromisoformat`; valores inválidos não entram em atraso.
- [ ] Adicionar `Workshop.query_orders(filters, today=None)` e `Workshop.dashboard(today=None)`: chamar `_allow('ATENDIMENTO','TECNICO','FINANCEIRO')` antes de consultar. O painel inclui finanças/estoque apenas quando o papel validado é ADMIN ou FINANCEIRO; demais resultados omitem essas chaves. Operações monetárias existentes mantêm permissões.
- [ ] Cobrir usuário desativado com o padrão de `test_disabled_actor_cannot_read`, chamando os dois novos métodos; ambos devem lançar `PermissionError`. Cobrir filtros combinados com prioridade padrão, texto e técnico.
- [ ] Executar testes novos e `tests/test_workshop.py`; confirmar sucesso e registrar commit `feat: adiciona consultas operacionais e indicadores`.

## Task 2 — painel e navegação profissional

Consome `Workshop.dashboard`, `OrderFilters` e `App.safe`. Produz `DashboardPages.page_dashboard(self)` em `dashboard_ui.py`. Integrar como mixin de `App`, removendo a implementação antiga do método.

- [ ] Em `tests/test_dashboard_ui.py`, reutilizar o Store e o App reais. Criar OS com prazo vencido e OS sem prazo; validar a contagem e o clique do cartão pelo filtro recebido em `App.open_orders(filters)`.
- [ ] Implementar `App.open_orders(filters)` guardando filtros iniciais e chamando `navigate('orders')`. O atalho não altera permissões. Testar que perfil técnico não ganha acesso ao painel nem ao financeiro.
- [ ] Construir cartões em grade com duas colunas na largura mínima, agenda em lista rolável e botões acessíveis. Usar dados reais, sem números de demonstração. Zero registros deve mostrar instrução de primeiro atendimento.
- [ ] Organizar menu em Atendimento, Gestão e Configurações, preservando `allowed_pages`. Exibir usuário atual no cabeçalho. Página inicial: dashboard quando permitido, orders caso contrário. Capturar `PermissionError` em `App.safe` e exibir mensagem sem traceback.
- [ ] Criar teste de geometria com `root.geometry('920x650')`, `root.update()` e verificação dos limites dos cartões e ações. Repetir com `root.tk.call('tk', 'scaling', 1.5)` e título de empresa longo. Conferir visualmente screenshots nas duas larguras; usar rolagem onde necessário.
- [ ] Rodar testes de painel e `tests/test_workshop_ui.py`; registrar commit `feat: refina painel e navegacao da assistencia`.

## Task 3 — OS, prioridades, checklists e histórico

Consome `OrderFilters`, `filter_orders`, `equipment_history` e operações existentes de `Workshop`. Produz filtros integrados, visualização por etapas e `append_checklist(current: str, category: str) -> str` em `order_templates.py`.

- [ ] Criar teste de histórico sem serial:

```python
from orcaprime.workshop_queries import equipment_history

def test_blank_serial_is_customer_history():
    rows = [{'id': 1, 'customer_id': 7, 'serial': '', 'model': 'A'},
            {'id': 2, 'customer_id': 8, 'serial': '', 'model': 'A'}]
    result = equipment_history(rows, 7, '')
    assert result['scope'] == 'customer'
    assert [o['id'] for o in result['orders']] == [1]
```

- [ ] Expor prioridade em formulário com valores BAIXA/NORMAL/ALTA/URGENTE. Validar no domínio apenas valores novos informados; leitura de registros antigos preserva dados e normaliza ausência. Testar gravação válida, inválida, edição sem prioridade e OS encerrada.
- [ ] Adicionar filtros por técnico, prioridade e prazo junto aos atuais; botão Limpar; contagem e colunas de técnico/previsão. Compartilhar resultados entre tabela e visualização por etapas. Etapas exibem cartões que abrem o editor; mudanças continuam usando `transition`, sem arrastar e gravar diretamente.
- [ ] Adicionar `tk.Text` para relato, diagnóstico e observações; leitura por `get('1.0','end-1c')`. Comparação de alterações não salvas deve incluir esses campos. Adaptar testes existentes para localizar campos por referências estáveis em vez de índices.
- [ ] Definir modelos: celular (tela, toque, áudio, câmeras, carregamento), computador (inicialização, tela, teclado, portas, carregamento) e outros (estado físico, alimentação, funcionamento). Inserir somente por botão; anexar com separação sem substituir texto existente. Teste:

```python
from orcaprime.order_templates import append_checklist

def test_template_preserves_existing_notes():
    result = append_checklist('Tela trincada na entrada.', 'celular')
    assert result.startswith('Tela trincada na entrada.')
    assert 'Carregamento' in result
```

- [ ] Adicionar acesso ao histórico usando cliente e serial não vazio, com rótulo conforme `scope`. Não permitir alteração silenciosa da OS de origem ao abrir retorno.
- [ ] Rodar testes de consultas, templates, UI e domínio. Verificar que alterações pendentes bloqueiam documentos. Registrar commit `feat: amplia acompanhamento e edicao de ordens`.

## Task 4 — central de impressão e documento de entrega

Consome `export_service_document(order, company, destination, kind='OS', paper='A4')`, `open_document(path)` e `print_document(path, printer)`. Produz `DocumentActions(workshop, company)` com `generate(order_id, destination, kind, paper) -> Path | None` e `send(path, printer) -> None`. `company` é um dicionário, usado como fallback quando não existir snapshot na OS.

- [ ] Criar testes para destino cancelado (`None`), impressora vazia e falha de envio. Comparar `workshop.get_order(order_id)` antes/depois; nenhum pagamento, evento ou situação deve mudar.
- [ ] Implementar `generate`: retornar None para cancelamento; obter OS salva pelo serviço autorizado; gerar por funções existentes. `send` rejeita impressora vazia com `ValueError` e propaga erro operacional para a interface informar.
- [ ] Criar diálogo único de documentos, acessível pela seleção na lista e pelo editor. Disponibilizar prévia, salvar e imprimir com mesmas opções e preferências; bloquear chamada a partir do editor com dados não salvos. Mensagem de sucesso diz envio ao leitor/fila, não impressão física.
- [ ] Acrescentar tipo ENTREGA ao gerador com OS, equipamento, recebedor, data registrada, checklist final e assinatura. Bloquear documento de entrega antes de OS entregue. Manter garantia baseada nos campos registrados.
- [ ] Separar observação interna em campo `internal_notes` validado pelo domínio; manter `notes` como serviços executados/públicos para compatibilidade. Não reinterpretar silenciosamente dados antigos. Excluir `internal_notes` em todos os PDFs. Acrescentar teste com marcador único `SEGREDO_INTERNO_123` e conferir ausência no texto extraído com pypdf.
- [ ] Testar cada documento em A4/58/80 mm com nomes longos e acentos; renderizar e conferir que não há corte ou sobreposição. Etiqueta permanece em 80×40 mm. Verificar política para escolha inconsistente: tipo etiqueta força papel etiqueta; outros tipos não aceitam papel etiqueta.
- [ ] Rodar testes de documentos e fluxo de UI; registrar commit `feat: centraliza impressao e adiciona comprovante de entrega`.

## Task 5 — produtividade e filas de acompanhamento

Produz `productivity(orders: list[dict], start: date, end: date) -> list[dict]` em `workshop_queries.py`, consumida por `Workshop.productivity(start, end)` após `_allow('FINANCEIRO')`. Resultado por técnico: `technician`, `delivered_count`, `delivered_order_ids`. Valores recebidos continuam no relatório financeiro existente, sem atribuir todo pagamento ao período de entrega.

- [ ] Escrever teste com dois eventos SITUACAO→ENTREGUE duplicados para uma OS: contar uma vez pelo primeiro evento válido. Testar limites inclusivos start/end e período invertido, que gera `ValueError`. OS sem evento histórico não deve receber data inventada; sinalizar quantidade sem data separadamente na tela.
- [ ] Filtrar eventos usando `action == 'SITUACAO'`, `target == 'ENTREGUE'` e prefixo de data ISO de `created_at`. Agrupar pelo técnico registrado na OS, com rótulo Sem técnico para vazio; explicar esse critério na tela.
- [ ] Adicionar período ao relatório, contagem entregue por técnico e exportação CSV com o mesmo conjunto. Restringir relatório/CSV a financeiro e administrador, inclusive chamada direta do serviço.
- [ ] Adicionar atalhos acionáveis para aguardando peça, pronta para retirada e retornos (`parent_id` preenchido), reutilizando a lista de OS. Não alterar automaticamente garantia ou prazo ao filtrar.
- [ ] Executar testes de consultas, permissões e relatórios; registrar commit `feat: adiciona produtividade e filas operacionais`.

## Task 6 — regressão, atualização e instalador

- [ ] Atualizar testes de backup para prioridade, `internal_notes` e texto multilinha, verificando valores após restauração. A base armazena esses campos em JSON existente; não criar tabela nem mudar schema sem necessidade demonstrada. Caso haja mudança de schema durante execução, interromper esse caminho e especificar migração/validador antes de aplicar.
- [ ] Rodar `python -m pytest -q` com display disponível para os testes Tkinter. Reportar separadamente testes pulados. Executar `git diff --check` e revisar migração/dados, permissões e mensagens da interface.
- [ ] Atualizar README e manual com filtros, painel, tipos de documentos e limites fiscais. Incrementar `orcaprime/__init__.py` para versão ainda não publicada, depois de consultar tags remotas. Ajustar notas do workflow para descrever somente funcionalidades verificadas.
- [ ] Executar `scripts/build_windows.ps1` no Windows pelo fluxo existente. Conferir jobs de teste, build e abertura do executável; obter instalador e checksum do commit exato. Não declarar teste físico de impressora sem realizá-lo.
- [ ] Publicar seguindo autorização vigente e regras do repositório. Antes de enviar para main, considerar que esse push dispara publicação automática; garantir código revisado e versão correta. Não substituir release existente.
- [ ] Entregar link do instalador verificado, resumo das mudanças e limitações materiais. Em falha de CI, corrigir e executar novamente apenas os gates necessários.

## Frente fiscal separada

Este plano entrega a ampliação local. A especificação fiscal será concluída após cidade/UF, enquadramento e tipos de operação informados pelo usuário. Consultar documentação oficial, selecionar integração sem contratação implícita, especificar credenciais protegidas, idempotência, consulta, autorização, XML e cancelamento. Somente então implementar e homologar transmissão. Até lá, preservar aviso de emissão não configurada e não prometer NF-e funcional.

## Revisão do plano

- Painel/navegação: tarefa 2; OS/histórico/checklists: tarefas 1 e 3.
- Documentos/garantia/prévia/entrega: tarefa 4; gestão/produtividade: tarefa 5.
- Compatibilidade, segurança e entrega Windows: tarefas 1 e 6.
- Fiscal: frente separada com dependência explícita, sem simulação de emissão.
- Método de execução preservado: implementação nesta sessão, conforme plano anterior do projeto. Plano escrito ainda aguarda revisão do usuário; nenhuma tarefa de produto foi executada nesta etapa.
