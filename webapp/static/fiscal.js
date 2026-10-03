'use strict';
const fiscalLabels = {
  legal_name:'Razão social', trade_name:'Nome fantasia', cnpj:'CNPJ',
  state_registration:'Inscrição estadual', municipal_registration:'Inscrição municipal',
  tax_regime:'Regime tributário (CRT)', street:'Logradouro', number:'Número',
  complement:'Complemento', district:'Bairro', city:'Município', state:'UF',
  municipality_code:'Código IBGE do município', postal_code:'CEP',
  environment:'Ambiente', series:'Série da NF-e', next_number:'Próximo número da NF-e'
};

function fiscalField(key, values, options) {
  const limits = {legal_name:160,trade_name:160,cnpj:18,state_registration:30,municipal_registration:30,
    street:160,number:30,complement:100,district:100,city:100,municipality_code:7,postal_code:9};
  const value = values[key] ?? '';
  const control = options ? `<select name="${key}" aria-labelledby="fiscal-label-${key}">${options.map(([id,label]) => `<option value="${esc(id)}" ${String(value) === id ? 'selected' : ''}>${esc(label)}</option>`).join('')}</select>`
    : `<input name="${key}" aria-labelledby="fiscal-label-${key}" value="${esc(value)}" ${['series','next_number'].includes(key) ? `type="number" min="${key === 'series' ? 0 : 1}" max="${key === 'series' ? 999 : 999999999}" step="1" required` : `type="text" maxlength="${limits[key]}"`} ${['municipality_code','postal_code'].includes(key) ? 'inputmode="numeric"' : ''}>`;
  return `<label class="field"><span id="fiscal-label-${key}">${fiscalLabels[key]}</span>${control}</label>`;
}

function fiscalStatus(data) {
  return `<div class="fiscal-status"><div>${icon(data.profile_complete ? 'check' : 'file')}<strong>${data.profile_complete ? 'Cadastro fiscal preenchido' : 'Complete seu cadastro fiscal'}</strong></div><span class="badge ${data.profile_complete ? 'PRONTO' : 'PENDENTE'}">${data.profile_complete ? 'Dados salvos' : 'Cadastro pendente'}</span></div>
    <p class="subtitle">${data.profile_complete ? 'Os dados estão salvos. A emissão será habilitada após conectar e validar a integração fiscal.' : 'Você pode salvar aos poucos. Faltam: ' + data.missing_fields.map(key => fiscalLabels[key]).join(', ') + '.'}</p>`;
}

async function fiscal() {
  const data = await api('/fiscal');
  if (page !== 'fiscal') return;
  const s = data.settings;
  const fields = keys => keys.map(key => fiscalField(key,s)).join('');
  const states = 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split(' ');
  $('#content').innerHTML = heading('Notas fiscais','Organize o cadastro fiscal e as preferências de NF-e da sua empresa.') + `
    <div class="fiscal-layout"><form id="fiscal-form">
      <section class="card fiscal-card"><div class="section-title"><h2>${icon('file')}Dados do emitente</h2><span class="badge">NF-e · modelo 55</span></div>
        <div class="form-grid">${fields(['legal_name','trade_name','cnpj','state_registration','municipal_registration'])}
          ${fiscalField('tax_regime',s,[['','Selecione'],['1','1 · Simples Nacional'],['2','2 · Simples Nacional, excesso de sublimite'],['3','3 · Regime normal'],['4','4 · MEI']])}</div>
        <p class="field-hint">Informe os dados do estabelecimento. Confirme o regime e as inscrições aplicáveis com a contabilidade.</p>
      </section>
      <section class="card fiscal-card"><div class="section-title"><h2>${icon('home')}Endereço fiscal</h2></div>
        <div class="form-grid">${fields(['postal_code','street','number','complement','district','city'])}
          ${fiscalField('state',s,[['','Selecione'],...states.map(state=>[state,state])])}${fields(['municipality_code'])}</div>
        <p class="field-hint">O código IBGE tem 7 dígitos e deve corresponder ao município do estabelecimento.</p>
      </section>
      <section class="card fiscal-card"><div class="section-title"><h2>${icon('settings')}Preferências de emissão</h2></div>
        <div class="form-grid">${fiscalField('environment',s,[['homologation','Homologação · testes'],['production','Produção · documentos fiscais']])}${fields(['series','next_number'])}</div>
        <p class="field-hint">Confira a série e a numeração já utilizadas antes de iniciar. Escolher Produção não ativa a emissão. Documentos de homologação não têm valor fiscal.</p>
      </section>
      <div class="fiscal-save"><div class="error" id="fiscal-error" role="alert"></div><div class="fiscal-save-row"><span class="muted">Configuração exclusiva desta empresa</span><button class="primary" type="submit">${icon('check')}Salvar dados fiscais</button></div></div>
    </form><aside class="fiscal-summary">
      <section class="card fiscal-card" id="fiscal-status" aria-live="polite">${fiscalStatus(data)}</section>
      <section class="card fiscal-card"><div class="section-title"><h2>${icon('shield')}Integração fiscal</h2></div><span class="badge PENDENTE">Não conectada</span>
        <p class="field-hint">Para emitir pelo OrçaPrime, ainda é necessário conectar o serviço de emissão, configurar o certificado digital e validar o credenciamento da empresa.</p>
        <p class="field-hint">A emissão e a impressão do DANFE serão disponibilizadas após essa integração. OS e garantias continuam disponíveis no atendimento.</p>
        <a class="link" href="https://www.nfe.fazenda.gov.br/portal/" target="_blank" rel="noopener noreferrer">Portal nacional da NF-e ↗</a>
      </section>
      <section class="notice"><strong>Nota de serviço (NFS-e)</strong><br>A NFS-e utiliza uma integração própria. Confirme com sua contabilidade o documento aplicável a cada operação.<br><a class="link" href="https://www.gov.br/nfse/pt-br" target="_blank" rel="noopener noreferrer">Portal nacional da NFS-e ↗</a></section>
    </aside></div>`;
  const form = $('#fiscal-form');
  const error = $('#fiscal-error');
  const status = $('#fiscal-status');
  form.onsubmit = async event => {
    event.preventDefault();
    const button = event.submitter;
    const body = Object.fromEntries(new FormData(form));
    body.series = Number(body.series); body.next_number = Number(body.next_number);
    button.disabled = true; error.textContent = '';
    try {
      const saved = await api('/fiscal',{method:'PUT',body});
      if (!form.isConnected) return;
      for (const [key,value] of Object.entries(saved.settings)) form.elements.namedItem(key).value = value;
      status.innerHTML = fiscalStatus(saved);
      toast('Dados fiscais salvos.');
    } catch (err) { error.textContent = err.message + ' Confira também o CNPJ, o CEP e o código IBGE da UF selecionada.'; }
    finally { button.disabled = false; }
  };
}
