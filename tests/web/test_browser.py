"""Opt-in actual-browser tests; CI enables ORCAPRIME_BROWSER_TESTS=1."""
import os
import threading
import time
from pathlib import Path
import pytest

pytestmark=pytest.mark.skipif(os.environ.get('ORCAPRIME_BROWSER_TESTS')!='1',reason='Browser verification is enabled in web CI')

def test_browser_owner_setup(tmp_path):
    import socket
    import uvicorn
    from playwright.sync_api import sync_playwright
    from webapp.api import create_app
    token='browser-installation-code-'+'x'*32
    app=create_app('sqlite:///'+str(tmp_path/'setup.db'),setup_token=token)
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='error'))
    worker=threading.Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True);worker.start()
    for _ in range(100):
        if server.started:break
        time.sleep(.05)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel=os.environ.get('ORCAPRIME_BROWSER_CHANNEL'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':390,'height':844})
            page.goto(f'http://127.0.0.1:{port}')
            page.get_by_role('link',name='Primeiro acesso do proprietário').click()
            page.locator('#setup-form').wait_for(state='visible')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.get_by_label('Código de instalação').fill(token)
            page.get_by_label('Seu e-mail').fill('owner@example.test')
            page.get_by_label('Crie sua senha').fill('Private-password-123')
            page.get_by_role('button',name='Mostrar senha',exact=True).click()
            assert page.locator('[name=password]').get_attribute('type')=='text'
            page.get_by_label('Confirme sua senha').fill('Does-not-match-123')
            page.get_by_role('button',name='Criar conta do proprietário').click()
            page.get_by_text('As senhas não conferem.',exact=True).wait_for()
            page.get_by_label('Confirme sua senha').fill('Private-password-123')
            page.get_by_role('button',name='Criar conta do proprietário').click()
            page.get_by_text('Sua conta foi criada.',exact=False).wait_for()
            assert page.locator('[name=token]').input_value()==''
            page.get_by_role('link',name='Voltar para o login').click()
            page.locator('[name=email]').fill('owner@example.test')
            page.locator('[name=password]').fill('Private-password-123')
            page.get_by_role('button',name='Entrar no OrçaPrime').click()
            page.get_by_role('heading',name='Empresas e licenças',exact=True).wait_for()
            browser.close()
    finally:
        server.should_exit=True;worker.join(timeout=5);sock.close();app.state.engine.dispose()

def test_browser_workflow(tmp_path):
    import uvicorn
    from playwright.sync_api import sync_playwright
    from fastapi.testclient import TestClient
    from webapp.api import create_app
    from webapp.security import bootstrap
    url='sqlite:///'+str(tmp_path/'browser.db')
    bootstrap(url,'owner@example.test','Owner-password-123')
    app=create_app(url)
    owner=TestClient(app);r=owner.post('/api/login',json={'email':'owner@example.test','password':'Owner-password-123'})
    owner.headers['X-CSRF-Token']=r.json()['csrf']
    company=owner.post('/api/companies',json={'name':'OliverTech Soluções','email':'preview@example.test','password':'Preview-only-123','days':30}).json()
    from webapp.db import Record,User
    from webapp.security import hash_password
    with app.state.factory.begin() as db:
        db.add(Record(company_id=company['id'],kind='entries',created=946728000,data={'name':'Entrada antiga','direction':'ENTRADA','amount':10000,'paid':True,'due':''}))
        db.add(Record(company_id=company['id'],kind='entries',data={'name':'Entrada atual','direction':'ENTRADA','amount':20000,'paid':True,'due':''}))
        db.add(User(company_id=company['id'],name='Técnico',email='tech@example.test',password=hash_password('Preview-only-123'),role='TECNICO'))
    import socket
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='error'))
    worker=threading.Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True);worker.start()
    for _ in range(100):
        if server.started:break
        time.sleep(.05)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel=os.environ.get('ORCAPRIME_BROWSER_CHANNEL'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1366,'height':900})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{port}')
            page.get_by_role('heading',name='Acesse sua conta').wait_for()
            folder=Path(os.environ.get('ORCAPRIME_SCREENSHOTS',str(tmp_path)));folder.mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(folder/'orcaprime-login.png'),full_page=True)
            page.locator('[name=email]').fill('preview@example.test');page.locator('[name=password]').fill('Preview-only-123');page.get_by_role('button',name='Entrar no OrçaPrime').click()
            page.get_by_role('heading',name='Visão geral').wait_for()
            left=page.locator('.main-column').bounding_box();right=page.locator('.dashboard aside').bounding_box()
            assert right['x']>=left['x']+left['width']
            page.screenshot(path=str(folder/'orcaprime-painel.png'),full_page=True)
            page.get_by_role('button',name='Cadastrar cliente',exact=True).click()
            page.locator('[name=name]').fill('Cliente de teste <script>');page.locator('[name=phone]').fill('64999999999');page.get_by_role('button',name='Salvar cadastro').click()
            page.locator('dialog').wait_for(state='hidden')
            page.get_by_role('button',name='Nova ordem de serviço',exact=True).click()
            page.locator('[name=customer_id]').select_option(index=1);page.locator('[name=device]').fill('iPhone 13');page.locator('[name=description]').fill('Tela trincada, sem acessórios');page.locator('[name=amount]').fill('250')
            page.get_by_role('button',name='Salvar cadastro').click();page.locator('dialog').wait_for(state='hidden')
            page.get_by_role('button',name='Ordens de serviço',exact=True).click()
            page.get_by_role('button',name='Ver OS').click()
            page.get_by_role('heading',name='Histórico do atendimento').wait_for()
            page.get_by_role('button',name='Editar OS').click()
            page.locator('[name=status]').select_option('EM_ANDAMENTO');page.get_by_role('button',name='Salvar cadastro').click();page.locator('dialog').wait_for(state='hidden')
            page.get_by_role('cell',name='Em andamento',exact=True).wait_for(state='visible')
            page.set_viewport_size({'width':390,'height':844});page.get_by_role('button',name='Abrir menu').click();page.get_by_role('button',name='Início',exact=True).click()
            page.get_by_role('heading',name='Visão geral').wait_for()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(folder/'orcaprime-celular.png'),full_page=True)
            page.set_viewport_size({'width':1366,'height':900})
            page.get_by_role('button',name='Relatórios',exact=True).click()
            page.locator('#from-date').fill('2000-01-01');page.locator('#to-date').fill('2000-12-31')
            page.get_by_role('button',name='Aplicar período').click()
            assert page.locator('#report-count').inner_text()=='1 lançamentos no período'
            assert page.locator('#report-balance').inner_text().replace('\xa0',' ')=='R$ 100,00'
            page.get_by_role('button',name='Clientes',exact=True).click()
            page.get_by_role('button',name='Excluir',exact=True).click()
            page.get_by_text('iPhone 13',exact=False).last.wait_for()
            page.get_by_role('button',name='Cancelar',exact=True).click()
            page.get_by_role('button',name='Sair da conta',exact=True).click()
            page.locator('[name=email]').fill('tech@example.test');page.locator('[name=password]').fill('Preview-only-123');page.get_by_role('button',name='Entrar no OrçaPrime').click()
            page.get_by_role('heading',name='Visão geral').wait_for()
            page.get_by_role('button',name='Clientes',exact=True).click()
            page.get_by_role('heading',name='Clientes',exact=True).wait_for()
            assert page.get_by_role('button',name='Editar',exact=True).count()==0
            assert page.get_by_role('button',name='Novo cliente',exact=True).count()==0
            assert not errors,errors
            browser.close()
    finally:
        server.should_exit=True;worker.join(timeout=5);sock.close()
