# core/templatetags/user_extras.py
from django import template

register = template.Library()

@register.filter
def display_name(user):
    """
    Retorna um nome curto para exibir no header:
    - user.first_name
    - primeiro nome de user.perfil.full_name
    - user.username
    """
    try:
        name = (getattr(user, "first_name", "") or "").strip()
        if not name:
            # tenta pegar o primeiro nome do full_name do perfil
            full = ""
            try:
                perfil = getattr(user, "perfil", None)
                full = (getattr(perfil, "full_name", "") or "").strip()
            except Exception:
                full = ""
            if full:
                name = full.split()[0].strip()
        if not name:
            name = getattr(user, "username", "").strip() or "Usuário"
        return name
    except Exception:
        return "Usuário"
