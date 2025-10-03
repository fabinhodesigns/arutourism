// js/site/register.js
(function () {
    const form = document.getElementById('register-form');
    if (!form) return;

    // Mapeamento de campos e elementos de erro
    const fields = {
        fullName: { input: document.getElementById('id_full_name'), errorEl: document.getElementById('err-full_name') },
        username: { input: document.getElementById('id_username'), errorEl: document.getElementById('err-username') },
        email: { input: document.getElementById('id_email'), errorEl: document.getElementById('err-email') },
        cpfCnpj: { input: document.getElementById('id_cpf_cnpj'), errorEl: document.getElementById('err-cpf_cnpj'), label: document.getElementById('cpf_cnpj_label') },
        password: { input: document.getElementById('id_password1'), errorEl: document.getElementById('err-password1') },
        password2: { input: document.getElementById('id_password2'), errorEl: document.getElementById('err-password2') },
    };
    const globalError = document.getElementById('register-error');
    const docTypeRadios = document.querySelectorAll('input[name="document_type"]');

    // Funções de máscara simples
    const masks = {
        cpf: value => value.replace(/\D/g, '').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2'),
        cnpj: value => value.replace(/\D/g, '').replace(/^(\d{2})(\d)/, '$1.$2').replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3').replace(/\.(\d{3})(\d)/, '.$1/$2').replace(/(\d{4})(\d)/, '$1-$2')
    };

    let currentMask = 'cpf'; // Padrão

    function applyMask(e) {
        const input = e.target;
        const value = input.value;
        const maxLength = currentMask === 'cpf' ? 14 : 18;
        
        input.value = masks[currentMask](value);
        if (input.value.length > maxLength) {
            input.value = input.value.slice(0, maxLength);
        }
    }

    // Função auxiliar de validação e exibição de erro
    function setFieldError(field, message) {
        if (message) {
            field.input.classList.add('is-invalid');
            field.errorEl.textContent = message;
        } else {
            field.input.classList.remove('is-invalid');
            field.errorEl.textContent = '';
        }
    }

    // Funções de validação específicas
    function validateFullName() {
        const value = fields.fullName.input.value.trim();
        if (!value) { setFieldError(fields.fullName, 'O nome completo é obrigatório.'); return false; }
        if (value.split(' ').length < 2) { setFieldError(fields.fullName, 'Por favor, insira nome e sobrenome.'); return false; }
        setFieldError(fields.fullName, '');
        return true;
    }
    function validateUsername() {
        const value = fields.username.input.value.trim();
        if (!value) { setFieldError(fields.username, 'O nome de usuário é obrigatório.'); return false; }
        if (!/^[a-zA-Z0-9_]+$/.test(value)) { setFieldError(fields.username, 'Use apenas letras, números e underscore (_).'); return false; }
        setFieldError(fields.username, '');
        return true;
    }
    function validateEmail() {
        const value = fields.email.input.value.trim();
        if (!value) { setFieldError(fields.email, 'O e-mail é obrigatório.'); return false; }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) { setFieldError(fields.email, 'Insira um e-mail válido.'); return false; }
        setFieldError(fields.email, '');
        return true;
    }
    function validateCpfCnpj() {
        const value = fields.cpfCnpj.input.value.replace(/\D/g, '');
        if (!value) { setFieldError(fields.cpfCnpj, 'O documento é obrigatório.'); return false; }
        if (currentMask === 'cpf' && value.length !== 11) { setFieldError(fields.cpfCnpj, 'CPF inválido. Deve ter 11 dígitos.'); return false; }
        if (currentMask === 'cnpj' && value.length !== 14) { setFieldError(fields.cpfCnpj, 'CNPJ inválido. Deve ter 14 dígitos.'); return false; }
        setFieldError(fields.cpfCnpj, '');
        return true;
    }
    function validatePasswords() {
        const pass1 = fields.password.input.value;
        const pass2 = fields.password2.input.value;
        let isValid = true;
        if (pass1.length < 8) {
            setFieldError(fields.password, 'A senha deve ter no mínimo 8 caracteres.');
            isValid = false;
        } else {
            setFieldError(fields.password, '');
        }
        if (pass1 !== pass2) {
            setFieldError(fields.password2, 'As senhas não coincidem.');
            isValid = false;
        } else {
            setFieldError(fields.password2, '');
        }
        return isValid;
    }

    // Event listeners
    docTypeRadios.forEach(radio => {
        radio.addEventListener('change', e => {
            currentMask = e.target.value;
            fields.cpfCnpj.label.textContent = currentMask.toUpperCase();
            fields.cpfCnpj.input.value = ''; // Limpa o campo ao trocar
            fields.cpfCnpj.input.placeholder = currentMask === 'cpf' ? '000.000.000-00' : '00.000.000/0000-00';
            validateCpfCnpj();
        });
    });

    fields.cpfCnpj.input.addEventListener('input', applyMask);
    fields.fullName.input.addEventListener('blur', validateFullName);
    fields.username.input.addEventListener('blur', validateUsername);
    fields.email.input.addEventListener('blur', validateEmail);
    fields.cpfCnpj.input.addEventListener('blur', validateCpfCnpj);
    fields.password.input.addEventListener('input', validatePasswords);
    fields.password2.input.addEventListener('input', validatePasswords);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        globalError.textContent = '';

        // Executa todas as validações
        const validations = [
            validateFullName(),
            validateUsername(),
            validateEmail(),
            validateCpfCnpj(),
            validatePasswords()
        ];

        if (validations.some(v => !v)) {
            return; // Interrompe se alguma validação falhar
        }

        const formData = new FormData(form);
        
        try {
            const response = await fetch(REGISTER_URL, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });

            const data = await response.json();

            if (response.ok && data.redirect) {
                window.location.href = data.redirect;
            } else if (data.errors) {
                // Exibe erros retornados pelo backend nos campos correspondentes
                Object.entries(data.errors).forEach(([fieldName, messages]) => {
                    const fieldKey = fieldName === 'password1' ? 'password' : fieldName;
                    if (fields[fieldKey]) {
                        setFieldError(fields[fieldKey], messages[0]);
                    }
                });
            } else {
                globalError.textContent = data.detail || 'Ocorreu um erro. Tente novamente.';
            }

        } catch (error) {
            globalError.textContent = 'Falha de conexão. Tente novamente mais tarde.';
        }
    });

})();