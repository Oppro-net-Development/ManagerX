const API_BASE = "http://127.0.0.1:3002/api";

// Hilfsfunktion: Token holen
const getToken = () => localStorage.getItem('discord_token');
const getRefreshToken = () => localStorage.getItem('discord_refresh_token');

// Token-Status prüfen
function checkTokenStatus() {
    const token = getToken();
    const refreshToken = getRefreshToken();
    console.log("🔍 Token-Status:");
    console.log("  - Access Token:", token ? "Vorhanden (" + token.substring(0, 10) + "...)" : "Nicht vorhanden");
    console.log("  - Refresh Token:", refreshToken ? "Vorhanden (" + refreshToken.substring(0, 10) + "...)" : "Nicht vorhanden");
    return { hasToken: !!token, hasRefreshToken: !!refreshToken };
}

// Debug-Funktion global verfügbar machen
window.checkTokenStatus = checkTokenStatus;

async function refreshToken() {
    const refreshToken = getRefreshToken();
    console.log("🔑 Refresh-Token vorhanden:", refreshToken ? "Ja" : "Nein");
    if (!refreshToken) {
        throw new Error("Kein Refresh-Token verfügbar");
    }
    
    const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
    });
    console.log("🔄 Refresh-API Response Status:", response.status);
    
    if (!response.ok) {
        const errorText = await response.text();
        console.error("❌ Refresh-API Fehler:", errorText);
        throw new Error("Token-Refresh fehlgeschlagen");
    }
    
    const data = await response.json();
    console.log("✅ Neuer Token erhalten:", data.access_token ? "Ja" : "Nein");
    localStorage.setItem('discord_token', data.access_token);
    if (data.refresh_token) {
        localStorage.setItem('discord_refresh_token', data.refresh_token);
    }
    return data.access_token;
}

// --- API FETCH HELPER (vereinfacht - bei 401 zur Login-Seite) ---
async function apiFetch(url, options = {}) {
    const token = getToken();
    if (!token) {
        console.log("❌ Kein Token gefunden - Weiterleitung zur Login-Seite");
        window.location.href = 'index.html';
        throw new Error("Kein Token gefunden");
    }
    
    // Authorization header für alle Requests
    const headers = { ...options.headers, "Authorization": `Bearer ${token}` };
    
    let res = await fetch(url, { ...options, headers });
    
    // Wenn 401, direkt zur Login-Seite (kein Refresh mehr)
    if (res.status === 401) {
        console.log("🔄 Token abgelaufen - Weiterleitung zur Login-Seite");
        // Tokens löschen
        localStorage.removeItem('discord_token');
        localStorage.removeItem('discord_refresh_token');
        localStorage.removeItem('user_info');
        // Zur Login-Seite mit Hinweis
        window.location.href = 'index.html?logged_out=true';
        throw new Error("Token abgelaufen");
    }
    
    return res;
}

document.addEventListener('DOMContentLoaded', async () => {
    const params = new URLSearchParams(window.location.search);
    const guildId = params.get('id');
    const path = window.location.pathname;

    console.log("ManagerX JS geladen auf:", path);

    // --- Seite: dashboard.html ---
    if (path.includes('dashboard.html')) {
        console.log("Lade Server-Liste");
        await loadGuilds();
    }

    // --- Seite: tempvc.html ---
    if (path.includes('tempvc.html')) {
        if (!guildId) return window.location.href = '../dashboard.html';
        
        console.log("Initialisiere TempVC Modul für Guild:", guildId);
        loadTempVCModule(guildId);

        const form = document.getElementById('tempvc-form');
        if (form) {
            form.onsubmit = async (e) => {
                e.preventDefault();
                await saveTempVC(guildId);
            };
        }
    }

    // --- Seite: welcome.html ---
    if (path.includes('welcome.html')) {
        if (!guildId) return window.location.href = '../dashboard.html';
        
        console.log("Initialisiere Welcome Modul für Guild:", guildId);
        loadWelcomeModule(guildId);

        const form = document.getElementById('welcome-form');
        if (form) {
            form.onsubmit = async (e) => {
                e.preventDefault();
                await saveWelcome(guildId);
            };
        }
    }

    // --- Seite: levelsystem.html ---
    if (path.includes('levelsystem.html')) {
        if (!guildId) return window.location.href = '../dashboard.html';
        
        console.log("Initialisiere Levelsystem Modul für Guild:", guildId);
        loadLevelsystemModule(guildId);

        const form = document.getElementById('levelsystem-form');
        if (form) {
            form.onsubmit = async (e) => {
                e.preventDefault();
                await saveLevelsystem(guildId);
            };
        }
    }
});

// --- FUNKTION: Speichern (Ungekürzt) ---
async function saveTempVC(guildId) {
    console.log("Speichervorgang für Guild ausgelöst:", guildId);

    const payload = {
        creator_channel_id: document.getElementById('creator_channel_id').value,
        category_id: document.getElementById('category_id').value,
        auto_delete_time: parseInt(document.getElementById('auto_delete_time').value) || 0,
        ui_enabled: document.getElementById('ui_enabled').checked,
        ui_prefix: document.getElementById('ui_prefix').value || "🔧"
    };

    try {
        const response = await apiFetch(`${API_BASE}/guild/${guildId}/tempvc`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            alert("✅ Erfolg: " + (data.message || "Gespeichert!"));
        } else {
            if (response.status === 403 && data.detail && data.detail.includes("deaktiviert")) {
                alert("❌ Dieses Feature ist in der Bot-Config deaktiviert.");
                return;
            }
            alert("❌ Fehler: " + (data.detail || "Unbekannter Fehler"));
        }
    } catch (error) {
        console.error("Netzwerkfehler beim Speichern:", error);
        alert("❌ Netzwerkfehler: Backend unter http://127.0.0.1:3002 erreichbar?");
    }
}

// --- FUNKTION: Laden ---
async function loadTempVCModule(guildId) {
    try {
        const res = await apiFetch(`${API_BASE}/guild/${guildId}/tempvc`);
        if (!res.ok) {
            if (res.status === 403) {
                const errorData = await res.json();
                if (errorData.detail && errorData.detail.includes("deaktiviert")) {
                    alert("❌ Dieses Feature ist in der Bot-Config deaktiviert.");
                    window.location.href = `../guild.html?id=${guildId}`;
                    return;
                }
            }
            throw new Error("Laden fehlgeschlagen: " + (await res.text()));
        }
        
        const data = await res.json();
        
        // Lade Kanäle für Dropdowns
        await loadChannels(guildId);
        
        // Felder befüllen
        document.getElementById('creator_channel_id').value = data.creator_channel_id || "";
        document.getElementById('category_id').value = data.category_id || "";
        document.getElementById('auto_delete_time').value = data.auto_delete_time || 0;
        document.getElementById('ui_enabled').checked = data.ui_enabled || false;
        document.getElementById('ui_prefix').value = data.ui_prefix || "🔧";
    } catch (err) {
        console.error("Fehler beim Laden der Daten:", err);
        alert("❌ Fehler beim Laden: " + err.message);
    }
}

// --- FUNKTION: Kanäle laden ---
async function loadChannels(guildId) {
    try {
        const res = await apiFetch(`${API_BASE}/guild/${guildId}/channels`);
        if (!res.ok) {
            const errorText = await res.text();
            throw new Error(`Kanäle laden fehlgeschlagen (${res.status}): ${errorText}`);
        }
        
        const data = await res.json();
        const channels = data.channels;
        
        // Creator Channel Dropdown (Voice-Kanäle, type 2)
        const creatorSelect = document.getElementById('creator_channel_id');
        if (creatorSelect) {
            creatorSelect.innerHTML = '<option value="">-- Wähle einen Voice-Channel --</option>';
            channels.filter(ch => ch.type === 2).forEach(ch => {
                const option = document.createElement('option');
                option.value = ch.id;
                option.textContent = ch.name;
                creatorSelect.appendChild(option);
            });
        }
        
        // Kategorie Dropdown (Kategorien, type 4)
        const categorySelect = document.getElementById('category_id');
        if (categorySelect) {
            categorySelect.innerHTML = '<option value="">-- Wähle eine Kategorie --</option>';
            channels.filter(ch => ch.type === 4).forEach(ch => {
                const option = document.createElement('option');
                option.value = ch.id;
                option.textContent = ch.name;
                categorySelect.appendChild(option);
            });
        }

        // Level Up Channel Dropdown (Text-Kanäle, type 0)
        const levelSelect = document.getElementById('level_up_channel');
        if (levelSelect) {
            levelSelect.innerHTML = '<option value="">-- Wähle einen Text-Channel --</option>';
            channels.filter(ch => ch.type === 0).forEach(ch => {
                const option = document.createElement('option');
                option.value = ch.id;
                option.textContent = ch.name;
                levelSelect.appendChild(option);
            });
        }
    } catch (err) {
        console.error("Fehler beim Laden der Kanäle:", err);
        alert("❌ Kanäle konnten nicht geladen werden: " + err.message);
    }
}

// --- FUNKTION: Welcome laden ---
async function loadWelcomeModule(guildId) {
    try {
        const res = await apiFetch(`${API_BASE}/guild/${guildId}/welcome`);
        if (!res.ok) {
            if (res.status === 403) {
                const errorData = await res.json();
                if (errorData.detail && errorData.detail.includes("deaktiviert")) {
                    alert("❌ Dieses Feature ist in der Bot-Config deaktiviert.");
                    window.location.href = `../guild.html?id=${guildId}`;
                    return;
                }
            }
            throw new Error("Laden fehlgeschlagen: " + (await res.text()));
        }
        
        const data = await res.json();
        
        // Lade Kanäle für Dropdowns
        await loadChannels(guildId);
        
        // Felder befüllen
        document.getElementById('channel_id').value = data.channel_id || "";
        document.getElementById('welcome_message').value = data.welcome_message || "";
        document.getElementById('enabled').checked = data.enabled || false;
        document.getElementById('embed_enabled').checked = data.embed_enabled || false;
        document.getElementById('embed_color').value = data.embed_color || "#00ff00";
        document.getElementById('embed_title').value = data.embed_title || "";
        document.getElementById('embed_description').value = data.embed_description || "";
        document.getElementById('embed_thumbnail').checked = data.embed_thumbnail || false;
        document.getElementById('embed_footer').value = data.embed_footer || "";
        document.getElementById('ping_user').checked = data.ping_user || false;
        document.getElementById('delete_after').value = data.delete_after || 0;
    } catch (err) {
        console.error("Fehler beim Laden der Welcome-Daten:", err);
        alert("❌ Fehler beim Laden: " + err.message);
    }
}

// --- FUNKTION: Levelsystem laden ---
async function loadLevelsystemModule(guildId) {
    try {
        const res = await apiFetch(`${API_BASE}/guild/${guildId}/levelsystem`);
        if (!res.ok) {
            if (res.status === 403) {
                const errorData = await res.json();
                if (errorData.detail && errorData.detail.includes("deaktiviert")) {
                    alert("❌ Dieses Feature ist in der Bot-Config deaktiviert.");
                    window.location.href = `../guild.html?id=${guildId}`;
                    return;
                }
            }
            throw new Error("Laden fehlgeschlagen: " + (await res.text()));
        }
        
        const data = await res.json();
        
        // Lade Kanäle für Dropdowns
        await loadChannels(guildId);
        
        // Felder befüllen
        document.getElementById('levelsystem_enabled').checked = data.levelsystem_enabled || false;
        document.getElementById('min_xp').value = data.min_xp || 10;
        document.getElementById('max_xp').value = data.max_xp || 20;
        document.getElementById('xp_cooldown').value = data.xp_cooldown || 30;
        document.getElementById('level_up_channel').value = data.level_up_channel || "";
        document.getElementById('prestige_enabled').checked = data.prestige_enabled || false;
        document.getElementById('prestige_min_level').value = data.prestige_min_level || 50;
    } catch (err) {
        console.error("Fehler beim Laden der Levelsystem-Daten:", err);
        alert("❌ Fehler beim Laden: " + err.message);
    }
}

// --- FUNKTION: Levelsystem speichern ---
async function saveLevelsystem(guildId) {
    console.log("Speichervorgang für Levelsystem ausgelöst:", guildId);

    const payload = {
        levelsystem_enabled: document.getElementById('levelsystem_enabled').checked,
        min_xp: parseInt(document.getElementById('min_xp').value) || 10,
        max_xp: parseInt(document.getElementById('max_xp').value) || 20,
        xp_cooldown: parseInt(document.getElementById('xp_cooldown').value) || 30,
        level_up_channel: document.getElementById('level_up_channel').value,
        prestige_enabled: document.getElementById('prestige_enabled').checked,
        prestige_min_level: parseInt(document.getElementById('prestige_min_level').value) || 50
    };

    try {
        const response = await apiFetch(`${API_BASE}/guild/${guildId}/levelsystem`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            alert("✅ Erfolg: " + (data.message || "Gespeichert!"));
        } else {
            if (response.status === 403 && data.detail && data.detail.includes("deaktiviert")) {
                alert("❌ Dieses Feature ist in der Bot-Config deaktiviert.");
                return;
            }
            alert("❌ Fehler: " + (data.detail || "Unbekannter Fehler"));
        }
    } catch (error) {
        console.error("Netzwerkfehler beim Speichern:", error);
        alert("❌ Netzwerkfehler: Backend unter http://127.0.0.1:3002 erreichbar?");
    }
}

// --- FUNKTION: Server-Liste laden ---
async function loadGuilds() {
    try {
        const res = await apiFetch(`${API_BASE}/user/guilds`);
        if (!res.ok) throw new Error("Server laden fehlgeschlagen");
        
        const guilds = await res.json();
        const guildList = document.getElementById('guild-list');
        
        if (guilds.length === 0) {
            guildList.innerHTML = '<p>Keine Server mit Admin-Rechten gefunden.</p>';
            return;
        }
        
        guildList.innerHTML = '';
        guilds.forEach(guild => {
            const guildCard = document.createElement('div');
            guildCard.className = 'guild-card';
            guildCard.innerHTML = `
                <img src="https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png" alt="${guild.name}" onerror="this.src='https://via.placeholder.com/64x64?text=?';">
                <h3>${guild.name}</h3>
                <a href="guild.html?id=${guild.id}" class="btn">Verwalten</a>
            `;
            guildList.appendChild(guildCard);
        });
    } catch (err) {
        console.error("Fehler beim Laden der Server:", err);
        document.getElementById('guild-list').innerHTML = '<p>❌ Fehler beim Laden der Server.</p>';
    }
}

// --- FUNKTION: Guild-Details laden (für guild.html) ---
async function fetchGuildDetails(guildId) {
    const token = getToken();
    try {
        // Hole Guild-Info von Discord API über unseren Endpoint
        const res = await fetch(`${API_BASE}/user/guilds?token=${token}`);
        if (!res.ok) throw new Error("Guild-Details laden fehlgeschlagen");
        
        const guilds = await res.json();
        const guild = guilds.find(g => g.id == guildId);
        
        if (guild) {
            document.getElementById('guild-icon').src = `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png`;
            document.getElementById('guild-icon').onerror = () => this.src = 'https://via.placeholder.com/64x64?text=?';
            document.getElementById('guild-name').textContent = guild.name;
        } else {
            document.getElementById('guild-name').textContent = 'Server nicht gefunden';
        }
    } catch (err) {
        console.error("Fehler beim Laden der Guild-Details:", err);
        document.getElementById('guild-name').textContent = 'Fehler beim Laden';
    }
}

// --- FUNKTION: Welcome speichern ---
async function saveWelcome(guildId) {
    console.log("Speichervorgang für Welcome ausgelöst:", guildId);

    const payload = {
        channel_id: document.getElementById('channel_id').value,
        welcome_message: document.getElementById('welcome_message').value,
        enabled: document.getElementById('enabled').checked,
        embed_enabled: document.getElementById('embed_enabled').checked,
        embed_color: document.getElementById('embed_color').value,
        embed_title: document.getElementById('embed_title').value,
        embed_description: document.getElementById('embed_description').value,
        embed_thumbnail: document.getElementById('embed_thumbnail').checked,
        embed_footer: document.getElementById('embed_footer').value,
        ping_user: document.getElementById('ping_user').checked,
        delete_after: parseInt(document.getElementById('delete_after').value) || 0
    };

    try {
        const response = await apiFetch(`${API_BASE}/guild/${guildId}/welcome`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            alert("✅ Erfolg: " + (data.message || "Gespeichert!"));
        } else {
            if (response.status === 403 && data.detail && data.detail.includes("deaktiviert")) {
                alert("❌ Dieses Feature ist in der Bot-Config deaktiviert.");
                return;
            }
            alert("❌ Fehler: " + (data.detail || "Unbekannter Fehler"));
        }
    } catch (error) {
        console.error("Netzwerkfehler beim Speichern:", error);
        alert("❌ Netzwerkfehler: Backend unter http://127.0.0.1:3002 erreichbar?");
    }
}

// --- FUNKTION: Bot-Stats laden (für index.html) ---
async function loadBotStats() {
    try {
        const response = await fetch(`${API_BASE}/managerx/stats`);
        const data = await response.json();
        
        document.getElementById('server-count').textContent = data.stats?.server_count || '0';
        document.getElementById('user-count').textContent = data.stats?.user_count || '0';
        document.getElementById('bot-ping').textContent = data.bot_info?.latency ? data.bot_info.latency + 'ms' : '--ms';
        document.getElementById('bot-status').textContent = data.bot_info?.status || 'Offline';
        
        console.log("✅ Bot-Stats erfolgreich geladen");
    } catch (error) {
        console.error('❌ Fehler beim Laden der Bot-Stats:', error);
        // Bei Fehler Standardwerte setzen
        document.getElementById('server-count').textContent = '--';
        document.getElementById('user-count').textContent = '--';
        document.getElementById('bot-ping').textContent = '--ms';
        document.getElementById('bot-status').textContent = 'Offline';
    }
}