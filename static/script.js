let currentToken = null;

function resetControls() {
    document.getElementById('showBtn').disabled = true;
    document.getElementById('downloadBtn').disabled = true;
    document.getElementById('formatSelect').disabled = true;
    document.getElementById('statsSection').classList.add('hidden');
    document.getElementById('previewSection').classList.add('hidden');
    document.getElementById('statsList').innerHTML = '';
    document.getElementById('preview').innerHTML = '';
    currentToken = null;
}

async function performClean() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const status = document.getElementById('status');
    const progressBar = document.getElementById('progressBar');
    const cleanBtn = document.getElementById('cleanBtn');

    if (!file) {
        status.textContent = ' Veuillez sélectionner un fichier';
        status.className = 'status error';
        return;
    }

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
        status.textContent = ' Traitement en cours...';
        status.className = 'status loading';
        progressBar.classList.remove('hidden');
        cleanBtn.disabled = true;

        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (response.ok && data.token) {
            currentToken = data.token;
            displayStats(data.stats);
            document.getElementById('preview').innerHTML = data.preview;        
            document.getElementById('statsSection').classList.remove('hidden'); 
            document.getElementById('previewSection').classList.remove('hidden');
            document.getElementById('showBtn').disabled = false;
            document.getElementById('downloadBtn').disabled = false;
            document.getElementById('formatSelect').disabled = false;
            status.textContent = ' Traitement terminé';
            status.className = 'status success';
            // réinitialiser le sélecteur de fichier pour permettre un nouveau chargement
            fileInput.value = '';
            const label = document.querySelector('label[for="fileInput"]');     
            if (label) label.textContent = 'Sélectionnez un fichier :';
        } else {
            status.textContent = ' Erreur : ' + (data.error || 'Réponse invalide');
            status.className = 'status error';
        }
    } catch (error) {
        status.textContent = ' Erreur : ' + error.message;
        status.className = 'status error';
    } finally {
        progressBar.classList.add('hidden');
        cleanBtn.disabled = false;
    }
}

document.getElementById('cleanBtn').addEventListener('click', function(e) {     
    e.preventDefault();
    resetControls();
    performClean();
});

document.getElementById('showBtn').addEventListener('click', function() {       
    document.getElementById('previewSection').classList.remove('hidden');       
    document.getElementById('preview').scrollIntoView({behavior:'smooth'});     
});

document.getElementById('downloadBtn').addEventListener('click', function() {   
    if (!currentToken) return;
    const fmt = document.getElementById('formatSelect').value;
    window.open(`/download/${currentToken}?format=${fmt}`, '_blank');
});

function displayStats(stats) {
    const container = document.getElementById('statsList');
    container.innerHTML = '';
    const labels = {
        columns: 'Nombre de colonnes',
        rows_before: 'Lignes avant traitement',
        rows_after: 'Lignes après traitement',
        missing_values_before: 'Valeurs manquantes (avant)',
        missing_values_after: 'Valeurs manquantes (après)',
        missing_removed: 'Valeurs manquantes traitées',
        duplicates_removed: 'Doublons supprimés',
        outliers_removed: 'Valeurs aberrantes supprimées',
        normalized_columns: 'Colonnes normalisées',
        quality_score: 'Score de qualité'
    };

    const table = document.createElement('table');
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    ['Élément', 'Valeur'].forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    for (const [key, value] of Object.entries(stats)) {
        const row = document.createElement('tr');
        const label = labels[key] || key.replace(/_/g, ' ');
        const td1 = document.createElement('td');
        td1.textContent = label;
        const td2 = document.createElement('td');
        td2.textContent = value;
        row.appendChild(td1);
        row.appendChild(td2);
        tbody.appendChild(row);
    }
    table.appendChild(tbody);
    container.appendChild(table);
}

// Afficher le nom du fichier sélectionné
document.getElementById('fileInput').addEventListener('change', function(e) {   
    const fileName = this.files[0]?.name;
    if (fileName) {
        const label = document.querySelector('label[for="fileInput"]');
        label.textContent = `Fichier sélectionné : ${fileName}`;
    }
});

// navigation active link en fonction du défilement
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('nav a');
    let current = '';
    document.querySelectorAll('section, .card').forEach(sec => {
        const top = sec.offsetTop - 80;
        if (pageYOffset >= top) {
            current = sec.getAttribute('id');
        }
    });
    sections.forEach(a => {
        a.classList.toggle('active', a.getAttribute('href') === '#' + current); 
    });
});

// smooth scroll for nav links
document.querySelectorAll('nav a').forEach(a => {
    a.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));       
        if (target) target.scrollIntoView({behavior: 'smooth'});
    });
});
