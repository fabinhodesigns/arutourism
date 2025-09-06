# core/utils/cpf.py
from __future__ import annotations
import re, time, hashlib, random
from django.db import transaction, IntegrityError

def only_digits(s: str | None) -> str:
    return re.sub(r"\D", "", s or "")

def is_valid_cpf(cpf: str) -> bool:
    cpf = only_digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    def _dv(digs: list[int], start: int) -> int:
        s = sum(n * w for n, w in zip(digs, range(start, 1, -1)))
        r = s % 11
        return 0 if r < 2 else 11 - r
    nums = [int(c) for c in cpf[:9]]
    d1 = _dv(nums, 10)
    d2 = _dv(nums + [d1], 11)
    return cpf[-2:] == f"{d1}{d2}"

def generate_cpf() -> str:
    """Gera CPF válido (11 dígitos). Evita sequências repetidas."""
    for _ in range(50):
        # entropia: hash(time + random)
        seed = f"{random.random()}|{time.time_ns()}"
        h = hashlib.sha256(seed.encode()).hexdigest()
        nine = "".join(str(int(h[i], 16) % 10) for i in range(9))
        if len(set(nine)) == 1:  # evita 000000000 etc
            continue
        nums = [int(c) for c in nine]
        def _dv(digs, start):
            s = sum(n * w for n, w in zip(digs, range(start, 1, -1)))
            r = s % 11
            return 0 if r < 2 else 11 - r
        d1 = _dv(nums, 10)
        d2 = _dv(nums + [d1], 11)
        cpf = nine + str(d1) + str(d2)
        if is_valid_cpf(cpf):
            return cpf
    raise RuntimeError("Falha ao gerar CPF válido")

def generate_unique_cpf(model_cls, field_name: str = "cpf_cnpj") -> str:
    """Gera CPF válido que não exista no banco (tolerante a corrida)."""
    from django.db.models import Q
    for _ in range(100):
        cpf = generate_cpf()
        exists = model_cls.objects.filter(**{field_name: cpf}).exists()
        if not exists:
            return cpf
    raise RuntimeError("Não consegui gerar CPF único (muitas tentativas)")
