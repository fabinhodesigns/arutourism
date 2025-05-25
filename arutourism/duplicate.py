import os
import django
import shutil
from django.core.files.base import ContentFile
from django.utils.timezone import now

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arutourism.settings')
django.setup()

from accounts.models import Empresa
from django.contrib.auth.models import User

def duplicar_empresa():
    try:
        empresa_original = Empresa.objects.get(id=4)
        usuario = User.objects.get(id=1)
    except Empresa.DoesNotExist:
        print("Empresa com id=4 não existe.")
        return
    except User.DoesNotExist:
        print("Usuário com id=1 não existe.")
        return

    for i in range(10):
        empresa_copy = Empresa(
            nome=f"{empresa_original.nome} - Cópia {i+1}",
            categoria=empresa_original.categoria,
            descricao=empresa_original.descricao,
            endereco=empresa_original.endereco,
            telefone=empresa_original.telefone,
            email=empresa_original.email,
            site=empresa_original.site,
            usuario=usuario,
            data_cadastro=now(),
        )
        
        if empresa_original.imagem:
            original_path = empresa_original.imagem.path
            filename = os.path.basename(original_path)
            new_filename = f"copia_{i+1}_{filename}"
            new_path = os.path.join(os.path.dirname(original_path), new_filename)

            shutil.copyfile(original_path, new_path)

            with open(new_path, 'rb') as f:
                empresa_copy.imagem.save(new_filename, ContentFile(f.read()), save=False)

        empresa_copy.save()
        print(f"Cópia {i+1} criada: {empresa_copy.nome}")

if __name__ == "__main__":
    duplicar_empresa()