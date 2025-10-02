// Em static/js/site/gerenciar_tags.js

document.addEventListener('DOMContentLoaded', function () {
    const childrenModal = document.getElementById('childrenModal');
    if (!childrenModal) return; // Garante que o script não quebre em outras páginas

    // Evento disparado quando o modal de subcategorias vai ser aberto
    childrenModal.addEventListener('show.bs.modal', function (event) {
        // Pega o botão que acionou o modal
        const button = event.relatedTarget; 
        
        // Extrai os dados dos atributos data-* do botão
        const parentId = button.dataset.parentId;
        const parentName = button.dataset.parentName;
        const childrenIds = button.dataset.childrenIds.split(',').filter(id => id);

        // Encontra os elementos do modal para atualizar
        const modalTitle = childrenModal.querySelector('.modal-title');
        const modalParentName = childrenModal.querySelector('#modal-parent-name');
        const modalParentIdInput = childrenModal.querySelector('#modal-parent-id');
        
        // Atualiza o conteúdo do modal com os dados da tag clicada
        modalTitle.textContent = `Subcategorias de "${parentName}"`;
        modalParentName.textContent = parentName;
        modalParentIdInput.value = parentId;

        // Limpa e marca os checkboxes corretos
        const allCheckboxes = childrenModal.querySelectorAll('input[name="children"]');
        allCheckboxes.forEach(checkbox => {
            // Desmarca e habilita todos para começar do zero
            checkbox.checked = false;
            checkbox.disabled = false;
            
            // Se o ID deste checkbox está na lista de filhos, marca ele
            if (childrenIds.includes(checkbox.value)) {
                checkbox.checked = true;
            }
            
            // Desabilita o checkbox da própria categoria pai (não pode ser filho de si mesmo)
            if (checkbox.value === parentId) {
                checkbox.disabled = true;
            }
        });
    });
});