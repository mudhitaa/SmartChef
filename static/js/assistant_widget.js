// assistant_widget.js
document.addEventListener("DOMContentLoaded", function () {
    const root = document.getElementById("sc-assistant-root");
    if (!root) return;

    const toggle = document.getElementById("sc-assistant-toggle");
    const panel = document.getElementById("sc-assistant-panel");
    const closeBtn = document.getElementById("sc-assistant-close");
    const chatContainer = document.getElementById("sc-chat");
    const input = document.getElementById("sc-input");
    const sendBtn = document.getElementById("sc-send");

    // helper to set open/closed classes
    function openWidget() {
        root.classList.add("sc-widget-open");
        root.classList.remove("sc-widget-closed");
        panel.setAttribute("aria-hidden", "false");
        input.focus();
    }
    function closeWidget() {
        root.classList.remove("sc-widget-open");
        root.classList.add("sc-widget-closed");
        panel.setAttribute("aria-hidden", "true");
    }

    toggle.addEventListener("click", () => {
        if (root.classList.contains("sc-widget-open")) closeWidget();
        else openWidget();
    });
    closeBtn.addEventListener("click", closeWidget);

    // Utility: render a message (HTML safe-ish — the backend should send HTML-safe text)
    function renderMessage(role, text) {
        const el = document.createElement("div");
        el.className = "sc-msg " + (role === "user" ? "user" : "bot");
        const bubble = document.createElement("div");
        bubble.className = "bubble";
        // preserve newlines -> <br>
        bubble.innerHTML = text.replace(/\n/g, "<br>");
        el.appendChild(bubble);
        chatContainer.appendChild(el);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // CSRF helper (for Django)
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
    const csrftoken = getCookie('csrftoken');

    // send question to backend
    async function sendQuestion(question) {
        renderMessage("user", question);
        renderMessage("bot", "Thinking\u2026"); // placeholder
        try {
            const res = await fetch("/assistant/ask/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken || ""
                },
                body: JSON.stringify({ question })
            });
            const json = await res.json();
            // remove the "Thinking..." placeholder (last bot message)
            const botPlaceholders = chatContainer.querySelectorAll(".sc-msg.bot");
            if (botPlaceholders.length) {
                botPlaceholders[botPlaceholders.length - 1].remove();
            }
            if (json.answer) {
                renderMessage("bot", json.answer);
            } else {
                renderMessage("bot", "Error: " + (json.error || "Unknown error"));
            }
        } catch (err) {
            // remove placeholder
            const botPlaceholders = chatContainer.querySelectorAll(".sc-msg.bot");
            if (botPlaceholders.length) botPlaceholders[botPlaceholders.length - 1].remove();
            renderMessage("bot", "Network error — is the backend running?");
            console.error(err);
        }
    }

    // send on click
    sendBtn.addEventListener("click", () => {
        const q = input.value.trim();
        if (!q) return;
        input.value = "";
        sendQuestion(q);
    });

    // send on Enter
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            sendBtn.click();
        }
    });

    // Optional: pre-fill greeting
    renderMessage("bot", "Hi! Ask me about recipes, ingredients, substitutions, or cooking methods.");
});
