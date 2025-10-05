document.addEventListener('DOMContentLoaded', function () {
    const qrTagsSelect = document.getElementById('qr-tags');
    const qrCidadeSelect = document.getElementById('qr-cidade');
    const resultArea = document.getElementById('qr-result-area');
    const qrContainer = document.getElementById('qr-code-container');
    const linkInput = document.getElementById('qr-link-input');
    const copyBtn = document.getElementById('qr-copy-btn');
    const downloadBtn = document.getElementById('qr-download-btn');
    const whatsappBtn = document.getElementById('qr-whatsapp-btn');

    let qrCodeInstance = null;

    function generateQRCode() {
        const selectedTags = Array.from(qrTagsSelect.selectedOptions).map(opt => opt.value);
        const selectedCidade = qrCidadeSelect.value;

        if (selectedTags.length === 0 && !selectedCidade) {
            resultArea.classList.remove('active');
            return;
        }

        const baseUrl = new URL(window.location.origin + '/empresas/');
        
        selectedTags.forEach(tagId => baseUrl.searchParams.append('tag', tagId));
        if (selectedCidade) {
            baseUrl.searchParams.set('cidade', selectedCidade);
        }
        
        const finalUrl = baseUrl.href;
        
        linkInput.value = finalUrl;
        
        qrContainer.innerHTML = '';
        qrCodeInstance = new QRCode(qrContainer, {
            text: finalUrl,
            width: 200,
            height: 200,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });

        whatsappBtn.href = `https://api.whatsapp.com/send?text=${encodeURIComponent('Explore estes pontos turísticos: ' + finalUrl)}`;
        
        resultArea.classList.add('active');
    }

    downloadBtn.addEventListener('click', () => {
        const canvas = qrContainer.querySelector('canvas');
        if (canvas) {
            downloadBtn.href = canvas.toDataURL("image/png");
        }
    });
    
    copyBtn.addEventListener('click', () => {
        linkInput.select();
        document.execCommand('copy');
        
        const originalIcon = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="bi bi-check-lg"></i>';
        copyBtn.classList.add('copied');
        
        setTimeout(() => {
            copyBtn.innerHTML = originalIcon;
            copyBtn.classList.remove('copied');
        }, 2000);
    });

    qrTagsSelect.addEventListener('change', generateQRCode);
    qrCidadeSelect.addEventListener('change', generateQRCode);
});