// static/js/validators.js
window.validators = (function(){
  function onlyDigits(s){ return (s||'').replace(/\D/g,''); }

  function isEmail(s){
    // simples e suficiente pro cliente; servidor valida de novo
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test((s||'').trim());
  }

  function isCPF(cpf){
    cpf = onlyDigits(cpf);
    if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
    let calc = (slice)=>{
      let sum = 0, weight = slice.length + 1;
      for (let n of slice){ sum += parseInt(n,10) * weight--; }
      let d = (sum * 10) % 11; return d === 10 ? 0 : d;
    };
    const d1 = calc(cpf.slice(0,9));
    const d2 = calc(cpf.slice(0,10));
    return d1 === parseInt(cpf[9],10) && d2 === parseInt(cpf[10],10);
  }

  function passwordScore(pw){
    if (!pw) return 0;
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
    if (/\d/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    return Math.min(score, 4);
  }

  return { onlyDigits, isEmail, isCPF, passwordScore };
})();
