function useExample(text) {
    const input = document.getElementById("message");
    input.value = text;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById("message");
    const chat = document.getElementById("chat");
    const message = input.value.trim();

    if (!message) return;

    chat.insertAdjacentHTML(
        "beforeend",
        `<div class="message user">${escapeHtml(message)}</div>`
    );

    input.value = "";

    const thinkingId = `thinking-${Date.now()}`;

    chat.insertAdjacentHTML(
        "beforeend",
        `<div id="${thinkingId}" class="message bot"><em>Thinking...</em></div>`
    );

    chat.scrollTop = chat.scrollHeight;

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        document.getElementById(thinkingId)?.remove();

        const renderedReply =
            typeof marked !== "undefined"
                ? marked.parse(data.reply || "")
                : escapeHtml(data.reply || "").replaceAll("\n", "<br>");

        chat.insertAdjacentHTML(
            "beforeend",
            `<div class="message bot">${renderedReply}</div>`
        );

        chat.scrollTop = chat.scrollHeight;

    } catch (error) {

        document.getElementById(thinkingId)?.remove();

        chat.insertAdjacentHTML(
            "beforeend",
            `<div class="message bot">
                The request failed: ${escapeHtml(String(error))}
            </div>`
        );
    }
}

function escapeHtml(text) {

    return text
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {

    document
        .getElementById("message")
        .addEventListener("keydown", function (e) {

            if (e.key === "Enter") {
                sendMessage();
            }

        });

});
