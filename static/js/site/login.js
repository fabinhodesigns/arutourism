(function () {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;

    const fields = {
        identificador: {
            input: document.getElementById('id_identificador'),
            errorEl: document.getElementById('err-identificador')
        },
        password: {
            input: document.getElementById('id_password'),
            errorEl: document.getElementById('err-password')
        }
    };
    const globalError = document.getElementById('login-error');
    const submitButton = loginForm.querySelector('button[type="submit"]');

    function setButtonLoading(isLoading) {
        if (isLoading) {
            submitButton.disabled = true;
            submitButton.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span><span class="ms-2">Entrando...</span>`;
        } else {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Entrar';
        }
    }
    
    function setFieldError(field, message) {
        if (!field || !field.input || !field.errorEl) return;
        if (message) {
            field.input.classList.add('is-invalid');
            field.errorEl.textContent = message;
        } else {
            field.input.classList.remove('is-invalid');
            field.errorEl.textContent = '';
        }
    }

    function clearAllErrors() {
        Object.values(fields).forEach(field => setFieldError(field, ''));
        globalError.textContent = '';
    }

    fields.identificador.input.addEventListener('blur', () => {
        if (!fields.identificador.input.value.trim()) {
            setFieldError(fields.identificador, 'Este campo é obrigatório.');
        } else {
            setFieldError(fields.identificador, '');
        }
    });
    fields.password.input.addEventListener('blur', () => {
        if (!fields.password.input.value) {
            setFieldError(fields.password, 'Este campo é obrigatório.');
        } else {
            setFieldError(fields.password, '');
        }
    });

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearAllErrors();

        let isFormValid = true;
        Object.entries(fields).forEach(([key, field]) => {
            if (!field.input.value.trim()) {
                setFieldError(field, 'Este campo é obrigatório.');
                isFormValid = false;
            }
        });
        if (!isFormValid) return;

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
            setButtonLoading(false);

            if (response.ok && data.ok && data.redirect) {
                window.location.href = data.redirect;
            } else if (data.errors) {
                Object.entries(data.errors).forEach(([fieldName, messages]) => {
                    const message = messages[0]; 
                    if (fields[fieldName]) {
                        setFieldError(fields[fieldName], message);
                    } else if (fieldName === '__all__') {
                        globalError.textContent = message;
                        fields.identificador.input.classList.add('is-invalid');
                        fields.password.input.classList.add('is-invalid');
                    }
                });
            } else {
                globalError.textContent = 'Ocorreu um erro inesperado. Tente novamente.';
            }
        } catch (error) {
            console.error('Login request failed:', error);
            globalError.textContent = 'Falha de conexão. Verifique sua internet e tente novamente.';
            setButtonLoading(false);
        }
    });
})();