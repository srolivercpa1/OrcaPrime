"""Explicit checklist insertion: existing notes are never overwritten."""
TEMPLATES = {
    'celular': ('Estado da tela','Toque','Áudio e microfone','Câmeras','Carregamento'),
    'computador': ('Inicialização','Tela','Teclado','Portas e conexões','Carregamento'),
    'outros': ('Estado físico','Alimentação','Funcionamento'),
}

def append_checklist(current, category):
    if category not in TEMPLATES:
        raise ValueError('Selecione uma categoria de equipamento.')
    title = 'Checklist — ' + category.capitalize()
    if title in current: return current
    template = title + '\n' + '\n'.join('[ ] '+item+': ' for item in TEMPLATES[category])
    return current.rstrip() + '\n\n' + template if current.strip() else template
