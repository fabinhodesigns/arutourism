(function () {
    const f = document.getElementById('login-form');
    const id = document.getElementById('id_identificador');
    const pw = document.getElementById('id_password');
    const eId = document.getElementById('err-identificador');
    const ePw = document.getElementById('err-password');
    const globalErr = document.getElementById('login-error');

    function setErr(input, el, msg) {
        if (msg) {
            input.classList.add('is-invalid');
            input.setAttribute('aria-invalid', 'true');
            el.textContent = msg;
        } else {
            input.classList.remove('is-invalid');
            input.removeAttribute('aria-invalid');
            el.textContent = '';
        }
    }

    function validateIdentificador() {
        const v = id.value.trim();
        if (!v) { setErr(id, eId, 'Informe e-mail, CPF ou usuário.'); return false; }
        if (v.includes('@')) {
            if (!window.validators.isEmail(v)) { setErr(id, eId, 'E-mail inválido.'); return false; }
        } else if (window.validators.onlyDigits(v).length >= 11) {
            if (!window.validators.isCPF(v)) { setErr(id, eId, 'CPF inválido.'); return false; }
        }
        setErr(id, eId, '');
        return true;
    }
    function validatePassword() {
        if (!pw.value) { setErr(pw, ePw, 'Informe a senha.'); return false; }
        setErr(pw, ePw, ''); return true;
    }

    id.addEventListener('blur', validateIdentificador);
    pw.addEventListener('input', validatePassword);

    f.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        globalErr.textContent = '';
        const ok = validateIdentificador() & validatePassword();
        if (!ok) { (id.classList.contains('is-invalid') ? id : pw).focus(); return; }

        const fd = new FormData(f);
        try {
            const resp = await fetch("{% url 'login' %}", {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: fd
            });
            if (resp.ok) {
                const data = await resp.json();
                if (data.redirect) location.href = data.redirect; return;
            }

            const data = await resp.json();
            if (data.errors) {

                const bad = (arr) => arr.find(e => e.code === 'bad_password');
                const notfound = (arr) => arr.find(e => e.code === 'user_not_found');
                if (bad(data.errors)) setErr(pw, ePw, 'Senha incorreta.');
                if (notfound(data.errors)) setErr(id, eId, 'Usuário não encontrado para o identificador informado.');

                if (!data.errors.length) globalErr.textContent = 'Não foi possível autenticar.';
            } else {
                globalErr.textContent = data.detail || 'Falha no login.';
            }
        } catch (err) {
            globalErr.textContent = 'Falha de conexão. Tente novamente.';
        }
    });
})();
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);
        const csrfToken = getCookie('csrftoken');

        const response = await fetch("{% url 'login' %}", {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData,
        });


        if (response.redirected) {
            window.location.href = response.url;
            return;
        }


        if (!response.ok) {
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const errorLi = doc.querySelector('.alert-danger');

            if (errorLi) {

                let overlay = document.getElementById("message-overlay");
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.id = 'message-overlay';
                    overlay.className = 'message-overlay';
                    overlay.innerHTML = `
                            <div class="message-box">
                                <ul id="message-list"></ul>
                            </div>`;

                    document.getElementById('login-container').prepend(overlay);
                }
                const messageList = overlay.querySelector("#message-list");
                messageList.innerHTML = errorLi.outerHTML;
            }
        }
    });
}