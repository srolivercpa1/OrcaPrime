"""Derive stock categories from descriptions without changing inventory records."""
import re
import unicodedata


def folded(value):
    return ''.join(c for c in unicodedata.normalize('NFD',str(value).casefold()) if not unicodedata.combining(c))


_NAMES={
    'bateria':'Bateria','baterias':'Bateria','tela':'Tela','telas':'Tela',
    'conector':'Conector','conectores':'Conector','cabo':'Cabo','cabos':'Cabo',
    'camera':'Câmera','cameras':'Câmera','pelicula':'Película','peliculas':'Película',
    'carregador':'Carregador','carregadores':'Carregador','placa':'Placa','placas':'Placa',
    'botao':'Botão','botoes':'Botão','capinha':'Capinha','capinhas':'Capinha',
    'capa':'Capa','capas':'Capa','microfone':'Microfone','microfones':'Microfone',
    'display':'Display','displays':'Display','flex':'Flex',
}


def category_for(description):
    text=str(description).strip()
    if re.match(r'^alto[\s-]+falantes?\b',folded(text)):return 'Alto-falante'
    match=re.match(r'[\W_]*([^\W\d_]+)',text)
    if not match:return 'Outros'
    word=match.group(1)
    return _NAMES.get(folded(word),word.capitalize())
