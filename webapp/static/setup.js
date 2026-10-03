'use strict';
const form=document.querySelector('#setup-form');
const status=document.querySelector('#setup-status');
const error=document.querySelector('#setup-error');
async function checkInstallation(){
  try{
    const response=await fetch('/api/setup');
    if(!response.ok)throw new Error('Não foi possível verificar a instalação. Atualize a página para tentar novamente.');
    const state=await response.json();
    form.hidden=!state.available;
    status.textContent=state.available?'Informe o código exclusivo da instalação e escolha os dados da sua conta.':'A configuração inicial está encerrada ou indisponível. Entre pelo login ou contate o responsável pela instalação.';
  }catch(e){status.textContent=e.message}
}
document.querySelector('#show-password').onclick=()=>{
  const input=form.elements.password;
  input.type=input.type==='password'?'text':'password';
  document.querySelector('#show-password').setAttribute('aria-label',input.type==='password'?'Mostrar senha':'Ocultar senha');
};
form.onsubmit=async e=>{
  e.preventDefault();error.textContent='';
  if(form.elements.password.value!==form.elements.confirm.value){error.textContent='As senhas não conferem.';return}
  const button=e.submitter;button.disabled=true;
  try{
    const response=await fetch('/api/setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:form.elements.token.value,email:form.elements.email.value,password:form.elements.password.value})});
    const result=await response.json();
    if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:'Confira os campos e tente novamente.');
    form.reset();form.hidden=true;
    status.textContent='Sua conta foi criada. Entre pelo login com o e-mail e a senha que você escolheu.';
  }catch(e){error.textContent=e.message}
  finally{button.disabled=false}
};
checkInstallation();
