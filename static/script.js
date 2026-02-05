document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const status = document.getElementById('status');
    const progressBar = document.getElementById('progressBar');
    const submitBtn = document.querySelector('.btn-primary');

    if (!file) {
        status.textContent = ' Veuillez sélectionner un fichier';
        status.className = 'status error';
        return;
    }

    // Validation du type de fichier
    const validExtensions = ['.csv', '.xlsx', '.xls', '.json', '.xml'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
        status.textContent = ' Format de fichier non supporté';
        status.className = 'status error';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        // Afficher l'état de chargement
        status.textContent = ' Traitement en cours...';
        status.className = 'status loading';
        progressBar.classList.remove('hidden');
        submitBtn.disabled = true;

        const response = await fetch('/clean', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            // Télécharger le fichier
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'cleaned_' + file.name;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            status.textContent = ' Fichier nettoyé avec succès !';
            status.className = 'status success';
            fileInput.value = '';
        } else {
            const error = await response.text();
            status.textContent = ' Erreur : ' + error;
            status.className = 'status error';
        }
    } catch (error) {
        status.textContent = ' Erreur : ' + error.message;
        status.className = 'status error';
    } finally {
        progressBar.classList.add('hidden');
        submitBtn.disabled = false;
    }
});

// Afficher le nom du fichier sélectionné
document.getElementById('fileInput').addEventListener('change', function(e) {
    const fileName = this.files[0]?.name;
    if (fileName) {
        const label = document.querySelector('label[for="fileInput"]');
        label.textContent = `Fichier sélectionné : ${fileName}`;
    }
});
