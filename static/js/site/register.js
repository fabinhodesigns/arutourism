// ARQUIVO: js/site/register.js (VERSÃO FINAL COM CORREÇÃO DE ERROS)

(function () {
    const form = document.getElementById('register-form');
    if (!form) return;

    const fields = {
        full_name: { input: document.getElementById('id_full_name'), errorEl: document.getElementById('err-full_name') },
        username: { input: document.getElementById('id_username'), errorEl: document.getElementById('err-username') },
        email: { input: document.getElementById('id_email'), errorEl: document.getElementById('err-email') },
        cpf_cnpj: { input: document.getElementById('id_cpf_cnpj'), errorEl: document.getElementById('err-cpf_cnpj'), label: document.getElementById('cpf_cnpj_label') },
        password1: { input: document.getElementById('id_password1'), errorEl: document.getElementById('err-password1') },
        password2: { input: document.getElementById('id_password2'), errorEl: document.getElementById('err-password2') },
    };
    const globalError = document.getElementById('register-error');
    const docTypeRadios = document.querySelectorAll('input[name="document_type"]');
    const submitButton = form.querySelector('button[type="submit"]');

    const masks = {
        cpf: value => value.replace(/\D/g, '').slice(0, 11).replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2'),
        cnpj: value => value.replace(/\D/g, '').slice(0, 14).replace(/^(\d{2})(\d)/, '$1.$2').replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3').replace(/\.(\d{3})(\d)/, '.$1/$2').replace(/(\d{4})(\d)/, '$1-$2')
    };
    let currentMask = 'cpf';

    function applyMask(e) { e.target.value = masks[currentMask](e.target.value); }

    function setButtonLoading(isLoading) {
        if (isLoading) {
            submitButton.disabled = true;
            submitButton.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span><span class="ms-2">Cadastrando...</span>`;
        } else {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Cadastrar';
        }
    }

    function setFieldError(field, message) {
        if (!field || !field.input || !field.errorEl) return;
        if (message) {
            field.input.classList.add('is-invalid');
            field.errorEl.innerHTML = message;
        } else {
            field.input.classList.remove('is-invalid');
            field.errorEl.innerHTML = '';
        }
    }

    function clearAllErrors() {
        Object.values(fields).forEach(field => setFieldError(field, ''));
        globalError.textContent = '';
    }

    // Funções de validação em tempo real (mantidas do seu código original)
    function validateFullName() { const value = fields.full_name.input.value.trim(); if (!value) { setFieldError(fields.full_name, 'O nome completo é obrigatório.'); return false; } if (value.split(' ').length < 2) { setFieldError(fields.full_name, 'Por favor, insira nome e sobrenome.'); return false; } setFieldError(fields.full_name, ''); return true; }
    function validateUsername() { const value = fields.username.input.value.trim(); if (!value) { setFieldError(fields.username, 'O nome de usuário é obrigatório.'); return false; } if (!/^[a-zA-Z0-9_]+$/.test(value)) { setFieldError(fields.username, 'Use apenas letras, números e underscore (_).'); return false; } setFieldError(fields.username, ''); return true; }
    function validateEmail() { const value = fields.email.input.value.trim(); if (!value) { setFieldError(fields.email, 'O e-mail é obrigatório.'); return false; } if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) { setFieldError(fields.email, 'Insira um e-mail válido.'); return false; } setFieldError(fields.email, ''); return true; }
    function validateCpfCnpj() { const value = fields.cpf_cnpj.input.value.replace(/\D/g, ''); if (!value) { setFieldError(fields.cpf_cnpj, 'O documento é obrigatório.'); return false; } if (currentMask === 'cpf' && value.length !== 11) { setFieldError(fields.cpf_cnpj, 'CPF inválido. Deve ter 11 dígitos.'); return false; } if (currentMask === 'cnpj' && value.length !== 14) { setFieldError(fields.cpf_cnpj, 'CNPJ inválido. Deve ter 14 dígitos.'); return false; } setFieldError(fields.cpf_cnpj, ''); return true; }
    function validatePasswords() { const pass1 = fields.password1.input.value; const pass2 = fields.password2.input.value; let isValid = true; if (pass1.length < 8) { setFieldError(fields.password1, 'A senha deve ter no mínimo 8 caracteres.'); isValid = false; } else { setFieldError(fields.password1, ''); } if (pass1 !== pass2) { setFieldError(fields.password2, 'As senhas não coincidem.'); isValid = false; } else { if (isValid) setFieldError(fields.password2, ''); } return isValid; }

    // Event Listeners (mantidos do seu código original)
    if (docTypeRadios.length > 0) { docTypeRadios.forEach(radio => { radio.addEventListener('change', e => { currentMask = e.target.value; fields.cpf_cnpj.label.textContent = currentMask.toUpperCase(); fields.cpf_cnpj.input.value = ''; fields.cpf_cnpj.input.placeholder = currentMask === 'cpf' ? '000.000.000-00' : '00.000.000/0000-00'; validateCpfCnpj(); }); }); }
    fields.cpf_cnpj.input.addEventListener('input', applyMask);
    fields.full_name.input.addEventListener('blur', validateFullName);
    fields.username.input.addEventListener('blur', validateUsername);
    fields.email.input.addEventListener('blur', validateEmail);
    fields.cpf_cnpj.input.addEventListener('blur', validateCpfCnpj);
    fields.password1.input.addEventListener('input', validatePasswords);
    fields.password2.input.addEventListener('input', validatePasswords);

    // Evento de submissão do formulário
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAllErrors();

        const validations = [validateFullName(), validateUsername(), validateEmail(), validateCpfCnpj(), validatePasswords()];
        if (validations.some(v => !v)) return;

        setButtonLoading(true);
        const formData = new FormData(form);

        try {
            const response = await fetch(REGISTER_URL, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': formData.get('csrfmiddlewaretoken') }
            });

            const data = await response.json();
            setButtonLoading(false);

            if (response.ok && data.ok && data.redirect) {
                window.location.href = data.redirect;
            } else if (data.errors) {
                Object.entries(data.errors).forEach(([fieldName, messages]) => {
                    // Mapeamento robusto para encontrar o campo correto no objeto `fields`
                    const fieldKey = Object.keys(fields).find(key => fields[key].input.name === fieldName);
                    const field = fields[fieldKey];

                    if (field) {
                        setFieldError(field, messages[0]);
                    } else if (fieldName === '__all__') {
                        globalError.innerHTML = messages[0];
                    }
                });
                const firstInvalidField = form.querySelector('.is-invalid');
                if (firstInvalidField) firstInvalidField.focus();
            } else {
                globalError.textContent = data.detail || 'Ocorreu um erro desconhecido. Tente novamente.';
            }
        } catch (error) {
            console.error('Register request failed:', error);
            globalError.textContent = 'Falha de conexão. Tente novamente mais tarde.';
            setButtonLoading(false);
        }
    });

})();