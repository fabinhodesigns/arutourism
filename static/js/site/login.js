(function () {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;

    const identificadorInput = document.getElementById('id_identificador');
    const passwordInput = document.getElementById('id_password');
    const errIdentificador = document.getElementById('err-identificador');
    const errPassword = document.getElementById('err-password');
    const globalError = document.getElementById('login-error');
    const submitButton = loginForm.querySelector('button[type="submit"]');

    // Função para controlar o estado de loading do botão
    function setButtonLoading(isLoading) {
        if (isLoading) {
            submitButton.disabled = true;
            submitButton.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                <span class="ms-2">Entrando...</span>
            `;
        } else {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Entrar';
        }
    }
    
    // Função para exibir erros nos campos
    function setFieldError(input, errorElement, message) {
        if (message) {
            input.classList.add('is-invalid');
            errorElement.textContent = message;
        } else {
            input.classList.remove('is-invalid');
            errorElement.textContent = '';
        }
    }

    // Função para limpar todos os erros
    function clearAllErrors() {
        setFieldError(identificadorInput, errIdentificador, '');
        setFieldError(passwordInput, errPassword, '');
        globalError.textContent = '';
    }

    // Funções de validação em tempo real
    function validateIdentificador() {
        const value = identificadorInput.value.trim();
        if (!value) {
            setFieldError(identificadorInput, errIdentificador, 'Por favor, informe seu e-mail ou CPF.');
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

    // Adiciona os eventos de validação "on blur"
    identificadorInput.addEventListener('blur', validateIdentificador);
    passwordInput.addEventListener('blur', validatePassword);

    // Evento de submissão do formulário
    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearAllErrors();

        // Roda as validações uma última vez antes de enviar
        const isIdentificadorValid = validateIdentificador();
        const isPasswordValid = validatePassword();

        if (!isIdentificadorValid || !isPasswordValid) {
            return; // Para se algum campo estiver vazio
        }

        setButtonLoading(true);
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

            if (response.ok && data.ok && data.redirect) {
                // Sucesso
                window.location.href = data.redirect;
            } else {
                // Erro retornado pelo backend
                const errorMessage = (data.errors && data.errors.length > 0) ? data.errors[0].message : 'Credenciais inválidas. Tente novamente.';
                globalError.textContent = errorMessage;
                // Destaca os campos para o usuário saber onde corrigir
                identificadorInput.classList.add('is-invalid');
                passwordInput.classList.add('is-invalid');
                setButtonLoading(false);
            }
        } catch (error) {
            console.error('Login request failed:', error);
            globalError.textContent = 'Falha de conexão. Verifique sua internet e tente novamente.';
            setButtonLoading(false);
        }
    });

})();