(function () {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;

    const identificadorInput = document.getElementById('id_identificador');
    const passwordInput = document.getElementById('id_password');
    const errIdentificador = document.getElementById('err-identificador');
    const errPassword = document.getElementById('err-password');
    const globalError = document.getElementById('login-error');
    
    const validators = window.validators || {};

    function setFieldError(input, errorElement, message) {
        if (message) {
            input.classList.add('is-invalid');
            input.setAttribute('aria-invalid', 'true');
            errorElement.textContent = message;
            // Garante que o feedback seja visível
            errorElement.style.display = 'block'; 
        } else {
            input.classList.remove('is-invalid');
            input.removeAttribute('aria-invalid');
            errorElement.textContent = '';
            errorElement.style.display = 'none';
        }
    }

    function validateIdentificador() {
        const value = identificadorInput.value.trim();
        if (!value) {
            setFieldError(identificadorInput, errIdentificador, 'Por favor, informe seu e-mail ou CPF.');
            return false;
        }
        if (value.includes('@') && validators.isEmail && !validators.isEmail(value)) {
            setFieldError(identificadorInput, errIdentificador, 'O e-mail informado é inválido.');
            return false;
        }
        if (!value.includes('@') && validators.isCPF && !validators.isCPF(value)) {
             setFieldError(identificadorInput, errIdentificador, 'O CPF informado é inválido.');
             return false;
        }
        setFieldError(identificadorInput, errIdentificador, '');
        return true;
    }

    function validatePassword() {
        if (!passwordInput.value) {
            setFieldError(passwordInput, errPassword, 'Por favor, informe sua senha.');
            return false;
        }
        setFieldError(passwordInput, errPassword, '');
        return true;
    }

    identificadorInput.addEventListener('blur', validateIdentificador);
    passwordInput.addEventListener('input', () => {
        if (passwordInput.classList.contains('is-invalid')) {
            validatePassword();
        }
    });

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        globalError.textContent = '';
        setFieldError(passwordInput, errPassword, ''); // Limpa erro da senha antes de revalidar

        const isIdentificadorValid = validateIdentificador();
        const isPasswordValid = validatePassword();

        if (!isIdentificadorValid || !isPasswordValid) {
            (identificadorInput.classList.contains('is-invalid') ? identificadorInput : passwordInput).focus();
            return;
        }

        const formData = new FormData(loginForm);

        try {
            const response = await fetch(LOGIN_URL, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            } else {
                if (data.errors) {
                    // Verifica se há um erro específico para identificador
                    if (data.errors.user_not_found) {
                        setFieldError(identificadorInput, errIdentificador, data.errors.user_not_found);
                        identificadorInput.focus();
                    }
                    // Verifica se há um erro específico para senha
                    if (data.errors.bad_password) {
                        setFieldError(passwordInput, errPassword, data.errors.bad_password);
                        passwordInput.focus();
                    }
                     // Se houver outros erros não específicos de campo, mostre globalmente
                    if (Object.keys(data.errors).length === 0 || (!data.errors.user_not_found && !data.errors.bad_password)) {
                         globalError.textContent = data.detail || 'Não foi possível autenticar. Verifique suas credenciais.';
                         globalError.style.display = 'block';
                    }
                } else {
                    globalError.textContent = data.detail || 'Falha no login. Tente novamente mais tarde.';
                    globalError.style.display = 'block';
                }
            }
        } catch (error) {
            console.error('Login request failed:', error);
            globalError.textContent = 'Falha de conexão. Verifique sua internet e tente novamente.';
            globalError.style.display = 'block';
        }
    });

})();