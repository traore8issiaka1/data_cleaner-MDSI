let cleanedFileId = null;
let cleanedFileName = 'cleaned_data';

const authSection = document.getElementById('authSection');
const appSection = document.getElementById('appSection');
const authUsername = document.getElementById('authUsername');
const authPassword = document.getElementById('authPassword');
const loginBtn = document.getElementById('loginBtn');
const registerBtn = document.getElementById('registerBtn');
const logoutBtn = document.getElementById('logoutBtn');
const authStatus = document.getElementById('authStatus');
const userBadge = document.getElementById('userBadge');

const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const missingSelectElem = document.getElementById('missingSelect');
const constGroup = document.getElementById('constGroup');
const constInput = document.getElementById('constInput');

const status = document.getElementById('status');
const progressBar = document.getElementById('progressBar');
const cleanBtn = document.getElementById('cleanBtn');
const showBtn = document.getElementById('showBtn');
const downloadGroup = document.getElementById('downloadGroup');
const downloadBtn = document.getElementById('downloadBtn');
const formatSelect = document.getElementById('formatSelect');

const statsSection = document.getElementById('statsSection');
const statsGrid = document.getElementById('statsGrid');
const qualityScoreValue = document.getElementById('qualityScoreValue');
const qualityFill = document.getElementById('qualityFill');

const previewSection = document.getElementById('previewSection');
const previewMeta = document.getElementById('previewMeta');
const previewTable = document.getElementById('previewTable');

const historyMeta = document.getElementById('historyMeta');
const historyTable = document.getElementById('historyTable');

function setStatus(type, message) {
    status.textContent = message;
    status.className = `status ${type}`;
}

function setAuthStatus(type, message) {
    authStatus.textContent = message;
    authStatus.className = `status ${type}`;
}

async function apiJson(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        }
    });
    let payload = {};
    try {
        payload = await response.json();
    } catch (_e) {
        payload = {};
    }
    if (!response.ok) {
        throw new Error(payload.error || 'Erreur serveur');
    }
    return payload;
}

function resetResultViews() {
    showBtn.disabled = true;
    downloadGroup.classList.add('hidden');
    statsSection.classList.add('hidden');
    previewSection.classList.add('hidden');
    previewTable.innerHTML = '';
    previewMeta.textContent = '';
    statsGrid.innerHTML = '';
    qualityScoreValue.textContent = '0%';
    qualityFill.style.width = '0%';
}

function renderStatCard(title, value, accentClass) {
    const card = document.createElement('div');
    card.className = `stat-card ${accentClass}`;

    const cardTitle = document.createElement('span');
    cardTitle.className = 'stat-title';
    cardTitle.textContent = title;

    const cardValue = document.createElement('strong');
    cardValue.className = 'stat-value';
    cardValue.textContent = String(value);

    card.appendChild(cardTitle);
    card.appendChild(cardValue);
    return card;
}

function renderStats(stats) {
    statsGrid.innerHTML = '';

    const entries = [
        ['Colonnes', stats.columns ?? '-', 'accent-main'],
        ['Valeurs manquantes traitees', stats.missing_removed ?? '-', 'accent-warn'],
        ['Doublons supprimes', stats.duplicates_removed ?? '-', 'accent-main'],
        ['Valeurs aberrantes supprimees', stats.outliers_removed ?? '-', 'accent-warn'],
        ['Colonnes normalisees', stats.normalized_columns ?? '-', 'accent-main'],
        ['Lignes (avant -> apres)', `${stats.rows_before ?? '-'} -> ${stats.rows_after ?? '-'}`, 'accent-neutral']
    ];

    entries.forEach(([label, value, accent]) => {
        statsGrid.appendChild(renderStatCard(label, value, accent));
    });

    const score = Number(stats.quality_score ?? 0);
    const safeScore = Math.max(0, Math.min(100, score));
    qualityScoreValue.textContent = `${safeScore.toFixed(2)}%`;
    qualityFill.style.width = `${safeScore}%`;

    statsSection.classList.remove('hidden');
}

function renderPreview(columns, rows, rowsPreview, rowsTotal) {
    previewTable.innerHTML = '';

    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    columns.forEach((col) => {
        const th = document.createElement('th');
        th.textContent = col;
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);

    const tbody = document.createElement('tbody');
    rows.forEach((row) => {
        const tr = document.createElement('tr');
        row.forEach((cell) => {
            const td = document.createElement('td');
            td.textContent = cell;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });

    previewTable.appendChild(thead);
    previewTable.appendChild(tbody);

    previewMeta.textContent = `Affichage de ${rowsPreview} ligne(s) sur ${rowsTotal}.`;
    previewSection.classList.remove('hidden');
}

function renderHistory(items) {
    historyTable.innerHTML = '';
    if (!items.length) {
        historyMeta.textContent = 'Aucun traitement enregistre pour le moment.';
        return;
    }

    historyMeta.textContent = `${items.length} traitement(s) enregistre(s).`;

    const columns = ['Date', 'Fichier source', 'Fichier nettoye', 'Colonnes', 'Valeurs manquantes', 'Doublons', 'Aberrantes', 'Score'];

    const thead = document.createElement('thead');
    const hr = document.createElement('tr');
    columns.forEach((label) => {
        const th = document.createElement('th');
        th.textContent = label;
        hr.appendChild(th);
    });
    thead.appendChild(hr);

    const tbody = document.createElement('tbody');
    items.forEach((item) => {
        const tr = document.createElement('tr');
        const stats = item.stats || {};

        const cells = [
            item.created_at,
            item.original_filename,
            item.cleaned_filename,
            stats.columns ?? '-',
            stats.missing_removed ?? '-',
            stats.duplicates_removed ?? '-',
            stats.outliers_removed ?? '-',
            `${Number(stats.quality_score ?? 0).toFixed(2)}%`
        ];

        cells.forEach((cell) => {
            const td = document.createElement('td');
            td.textContent = String(cell);
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });

    historyTable.appendChild(thead);
    historyTable.appendChild(tbody);
}

function setAuthenticatedUI(authenticated, username = '') {
    if (authenticated) {
        authSection.classList.add('hidden');
        appSection.classList.remove('hidden');
        userBadge.textContent = `Connecte: ${username}`;
        userBadge.classList.remove('hidden');
        logoutBtn.classList.remove('hidden');
    } else {
        authSection.classList.remove('hidden');
        appSection.classList.add('hidden');
        userBadge.classList.add('hidden');
        logoutBtn.classList.add('hidden');
        cleanedFileId = null;
        resetResultViews();
        historyTable.innerHTML = '';
        historyMeta.textContent = '';
    }
}

async function loadHistory() {
    try {
        const payload = await apiJson('/history');
        renderHistory(payload.items || []);
    } catch (error) {
        historyMeta.textContent = `Erreur historique: ${error.message}`;
    }
}

async function checkAuth() {
    try {
        const me = await apiJson('/auth/me', { headers: {} });
        if (me.authenticated) {
            setAuthenticatedUI(true, me.username || '');
            await loadHistory();
            return;
        }
        setAuthenticatedUI(false);
    } catch (_error) {
        setAuthenticatedUI(false);
    }
}

loginBtn.addEventListener('click', async function () {
    const username = authUsername.value.trim();
    const password = authPassword.value;
    try {
        const payload = await apiJson('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        setAuthStatus('success', payload.message || 'Connexion reussie');
        setAuthenticatedUI(true, payload.username || username);
        await loadHistory();
    } catch (error) {
        setAuthStatus('error', error.message);
    }
});

registerBtn.addEventListener('click', async function () {
    const username = authUsername.value.trim();
    const password = authPassword.value;
    try {
        const payload = await apiJson('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        setAuthStatus('success', payload.message || 'Inscription reussie');
        setAuthenticatedUI(true, payload.username || username);
        await loadHistory();
    } catch (error) {
        setAuthStatus('error', error.message);
    }
});

logoutBtn.addEventListener('click', async function () {
    try {
        await apiJson('/auth/logout', { method: 'POST' });
    } catch (_e) {
        // Keep logout UX even if server answered with error.
    }
    setAuthenticatedUI(false);
    setAuthStatus('loading', 'Vous etes deconnecte.');
});

missingSelectElem.addEventListener('change', function () {
    if (this.value === 'const') {
        constGroup.classList.remove('hidden');
    } else {
        constGroup.classList.add('hidden');
    }
});

uploadForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
        setStatus('error', 'Veuillez selectionner un fichier');
        return;
    }

    const validExtensions = ['.csv', '.xlsx', '.xls', '.json', '.xml'];
    const fileExtension = `.${file.name.split('.').pop().toLowerCase()}`;
    if (!validExtensions.includes(fileExtension)) {
        setStatus('error', 'Format de fichier non supporte');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const strategy = missingSelectElem.value;
    if (strategy === 'const') {
        formData.append('missing_strategy', `const:${constInput.value}`);
    } else {
        formData.append('missing_strategy', strategy);
    }

    try {
        setStatus('loading', 'Nettoyage en cours...');
        progressBar.classList.remove('hidden');
        cleanBtn.disabled = true;
        cleanedFileId = null;
        resetResultViews();

        const response = await fetch('/clean', {
            method: 'POST',
            body: formData
        });

        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.error || 'Erreur inconnue');
        }

        cleanedFileId = payload.file_id;
        cleanedFileName = payload.default_filename || `cleaned_${file.name}`;

        renderStats(payload.stats || {});
        showBtn.disabled = false;
        downloadGroup.classList.remove('hidden');
        await loadHistory();

        setStatus('success', 'Nettoyage termine. Vous pouvez afficher puis telecharger le fichier traite.');
    } catch (error) {
        setStatus('error', `Erreur : ${error.message}`);
    } finally {
        progressBar.classList.add('hidden');
        cleanBtn.disabled = false;
    }
});

showBtn.addEventListener('click', async function () {
    if (!cleanedFileId) {
        setStatus('error', 'Aucun fichier traite disponible. Lancez d abord le nettoyage.');
        return;
    }

    try {
        showBtn.disabled = true;
        setStatus('loading', 'Chargement de l apercu...');

        const response = await fetch(`/preview/${cleanedFileId}?limit=20`);
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.error || 'Erreur de recuperation de l apercu');
        }

        renderPreview(payload.columns || [], payload.rows || [], payload.rows_preview || 0, payload.rows_total || 0);
        setStatus('success', 'Apercu charge.');
    } catch (error) {
        setStatus('error', `Erreur : ${error.message}`);
    } finally {
        showBtn.disabled = false;
    }
});

downloadBtn.addEventListener('click', async function () {
    if (!cleanedFileId) {
        setStatus('error', 'Aucun fichier traite disponible. Lancez d abord le nettoyage.');
        return;
    }

    try {
        downloadBtn.disabled = true;
        const format = formatSelect.value;

        const response = await fetch(`/download/${cleanedFileId}?format=${encodeURIComponent(format)}`);
        if (!response.ok) {
            const payload = await response.json();
            throw new Error(payload.error || 'Echec du telechargement');
        }

        const blob = await response.blob();
        const extension = format === 'xls' ? 'xlsx' : format;
        const baseName = cleanedFileName.replace(/\.[^.]+$/, '');
        const downloadName = `${baseName}.${extension}`;

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = downloadName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        setStatus('success', 'Telechargement termine.');
    } catch (error) {
        setStatus('error', `Erreur : ${error.message}`);
    } finally {
        downloadBtn.disabled = false;
    }
});

fileInput.addEventListener('change', function () {
    const fileName = this.files[0]?.name;
    const label = document.querySelector('label[for="fileInput"]');
    label.textContent = fileName ? `Fichier selectionne : ${fileName}` : 'Selectionnez un fichier :';

    cleanedFileId = null;
    resetResultViews();
    setStatus('loading', 'Fichier charge. Lancez le nettoyage.');
});

resetResultViews();
checkAuth();
