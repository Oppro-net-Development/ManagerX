// Funktion zur Formatierung von Zahlen (z.B. 1500 -> 1.5k)
function formatNumber(num) {
    if (num >= 1000) {
        return (num / 1000).toFixed(1).replace('.0', '') + "k";
    }
    return num;
}

// Funktion für die Hochzähl-Animation
function animateValue(id, start, end, duration, suffix = "+") {
    const obj = document.getElementById(id);
    if (!obj) return;
    
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const current = Math.floor(progress * (end - start) + start);
        
        obj.innerHTML = formatNumber(current) + suffix;
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Hauptfunktion zum Abrufen der Daten
async function fetchLiveStats() {
    // Hier deine neue URL einfügen
    const API_ENDPOINT = "http://127.0.0.1:3002/api/managerx/stats";

    try {
        const response = await fetch(API_ENDPOINT);
        if (!response.ok) throw new Error("API Offline");
        
        const data = await response.json();

        // 1. Server & User Animation
        animateValue("server-count", 0, data.stats.server_count, 1200, "+");
        animateValue("user-count", 0, data.stats.user_count, 1200, "+");

        // 2. Ping-Anzeige & Farbe
        const pingElement = document.getElementById('bot-ping');
        const ping = Math.round(data.bot_info.latency);
        pingElement.innerText = ping + "ms";

        if (ping < 80) pingElement.style.color = "#00ff88"; 
        else if (ping < 180) pingElement.style.color = "#ffbb00"; 
        else pingElement.style.color = "#ff4444";

        // 3. Status Anzeige
        const statusElement = document.getElementById('bot-status');
        statusElement.innerText = "Online";
        statusElement.style.color = "#00ff88";

    } catch (error) {
        console.error("Dashboard-Fehler:", error);
        document.getElementById('bot-status').innerText = "Offline";
        document.getElementById('bot-status').style.color = "#ff4444";
        document.getElementById('bot-ping').innerText = "---";
        document.getElementById('bot-ping').style.color = "#fff";
    }
}

// Initialer Start und Intervall
document.addEventListener('DOMContentLoaded', () => {
    fetchLiveStats();
    setInterval(fetchLiveStats, 60000);
});