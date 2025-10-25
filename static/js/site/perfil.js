(function () {
  const file = document.querySelector('input[name="avatar"]');
  const prev = document.getElementById('avatar-preview');
  if (file && prev) {
    file.addEventListener('change', function () {
      const f = this.files && this.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = e => prev.src = e.target.result;
      reader.readAsDataURL(f);
    });
  }

  document.querySelectorAll('button[data-toggle="pw"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.previousElementSibling;
      if (!input) return;
      const isText = input.getAttribute('type') === 'text';
      input.setAttribute('type', isText ? 'password' : 'text');
      btn.innerHTML = isText ? '<i class="bi bi-eye" aria-hidden="true"></i>'
        : '<i class="bi bi-eye-slash" aria-hidden="true"></i>';
    });
  });

  function fmtCpfCnpj(v) {
    v = (v || '').toString().replace(/\D/g, '');
    if (v.length === 11) {
      return v.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
    } else if (v.length === 14) {
      return v.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
    }
    return v;
  }

  const cpfRo = document.getElementById('cpf_ro');
  if (cpfRo) cpfRo.value = fmtCpfCnpj(cpfRo.value);

  document.querySelectorAll('[data-documento]').forEach(span => {
    const raw = span.getAttribute('data-documento') || '';
    span.textContent = fmtCpfCnpj(raw) || '—';
  });

  const cpfInput = document.getElementById('id_cpf_cnpj');
  if (cpfInput) {
    cpfInput.addEventListener('input', function () {
      let v = this.value.replace(/\D/g, '').slice(0, 11);
      if (v.length > 9) v = v.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, '$1.$2.$3-$4');
      else if (v.length > 6) v = v.replace(/(\d{3})(\d{3})(\d{0,3})/, '$1.$2.$3');
      else if (v.length > 3) v = v.replace(/(\d{3})(\d{0,3})/, '$1.$2');
      this.value = v;
    });
  }
})();