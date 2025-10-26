document.addEventListener('DOMContentLoaded', function () {
  
  const childrenModal = document.getElementById('childrenModal');
  
  if (childrenModal) {
    const modalSearchInput = document.getElementById('modal-tag-search');
    const allCheckboxes = childrenModal.querySelectorAll('.modal-tag-item');

    childrenModal.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      
      const parentId = button.dataset.parentId;
      const parentName = button.dataset.parentName;
      const childrenIds = button.dataset.childrenIds.split(',').filter(id => id);

      const modalTitle = childrenModal.querySelector('.modal-title');
      const modalParentName = childrenModal.querySelector('#modal-parent-name');
      const modalParentIdInput = childrenModal.querySelector('#modal-parent-id');
      
      modalTitle.textContent = `Subcategorias de "${parentName}"`;
      modalParentName.textContent = parentName;
      modalParentIdInput.value = parentId;

      modalSearchInput.value = '';

      allCheckboxes.forEach(checkboxWrapper => {
        const checkbox = checkboxWrapper.querySelector('input[type="checkbox"]');
        checkbox.checked = false;
        checkbox.disabled = false;
        checkboxWrapper.style.display = 'block'; 

        if (childrenIds.includes(checkbox.value)) {
          checkbox.checked = true;
        }
        
        if (checkbox.value === parentId) {
          checkbox.disabled = true;
          checkboxWrapper.style.display = 'none'; 
        }
      });
    });

    modalSearchInput.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase().trim();

      allCheckboxes.forEach(function(item) {
        const label = item.querySelector('label');
        const labelText = label.innerText.toLowerCase();
        const checkbox = item.querySelector('input[type="checkbox"]');

        if (checkbox.disabled) {
          item.style.display = 'none';
          return;
        }

        if (labelText.includes(searchTerm)) {
          item.style.display = 'block';
        } else {
          item.style.display = 'none';
        }
      });
    });
  } 


  const deleteForms = document.querySelectorAll('.form-delete-tag');
  
  deleteForms.forEach(form => {
    form.addEventListener('submit', function(event) {
      event.preventDefault(); 
      
      const tagName = form.dataset.tagName || 'esta tag';

      Swal.fire({
        title: 'Tem certeza?',
        text: `Você realmente deseja apagar a tag "${tagName}"? Esta ação não pode ser revertida.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sim, apagar!',
        cancelButtonText: 'Cancelar'
      }).then((result) => {
        if (result.isConfirmed) {
          form.submit();
        }
      });
    });
  });
});