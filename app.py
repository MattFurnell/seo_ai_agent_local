from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from semrush_client import ask_semrush
from screamingfrog_client import ask_screaming_frog
import os

load_dotenv()

app = FastAPI(title="SEO Intelligence Agent - Howden C&LC website")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY")
SEMRUSH_MCP_URL = os.getenv(
    "SEMRUSH_MCP_URL",
    "https://mcp.semrush.com/v1/mcp",
)

# Screaming Frog does not use an API key here.
# The app connects to the HTTP MCP URL exposed by the licensed SEO Spider app.
SCREAMING_FROG_MCP_URL = os.getenv("SCREAMING_FROG_MCP_URL")


class ChatRequest(BaseModel):
    message: str


SYSTEM_PROMPT = """
You are an SEO Intelligence Agent for Howden C&LC.

Your job is to help with:
- Technical SEO analysis
- Keyword opportunities
- Competitor research
- Content gaps
- GA4 / Search Console style analysis
- Prioritised SEO recommendations

Important rules:
- Be practical and business-focused.
- Explain findings clearly for SEO and marketing users.
- If live tool data is not connected, say what tool would be needed.
- Do not pretend you have live Semrush, Screaming Frog, GA4 or GSC data unless it has been supplied.
- Semrush questions are handled through the live Semrush MCP connection.
- Screaming Frog crawl and technical-audit questions are handled through the live Screaming Frog MCP connection.
- Keep answers structured with clear priorities and next steps.
"""


def get_fake_response(message: str) -> str:
    msg = message.lower()

    if any(word in msg for word in ["technical", "crawl", "screaming frog", "broken", "404", "h1", "title"]):
        return """
Technical SEO analysis requires the Screaming Frog MCP connection.

Please make sure:
1. Screaming Frog SEO Spider is open.
2. Its MCP server is enabled.
3. SCREAMING_FROG_MCP_URL is present in the .env file.
4. The requested website URL is included in your question.
"""

    if any(word in msg for word in ["keyword", "semrush", "ranking", "rankings", "content gap", "search volume"]):
        return """
Keyword and competitor analysis requires the Semrush MCP connection.

Please make sure:
1. SEMRUSH_API_KEY is present in the .env file.
2. SEMRUSH_MCP_URL is present in the .env file.
3. Your Semrush account has the required API access.
"""

    return """
I can help with SEO analysis across technical SEO, keywords, traffic, competitors and content opportunities.

Example questions:
- Use Screaming Frog to crawl https://example.com and find broken internal links.
- Use Semrush to find keyword opportunities for young driver insurance.
- Explain canonical tags in plain English.
"""


def ask_gemini(message: str) -> str:
    if not GEMINI_API_KEY:
        return get_fake_response(message)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
{SYSTEM_PROMPT}

Current tool connection status:
- Gemini API: connected
- Semrush MCP configured: {'yes' if SEMRUSH_API_KEY and SEMRUSH_MCP_URL else 'no'}
- Screaming Frog MCP configured: {'yes' if SCREAMING_FROG_MCP_URL else 'no'}

User question:
{message}
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        return response.text or "Gemini returned an empty response."

    except Exception as error:
        return f"""
Gemini could not be reached.

Error detail:
{str(error)}

Fallback answer:
{get_fake_response(message)}
"""


@app.get("/", response_class=HTMLResponse)
def home():
    gemini_status = "Connected" if GEMINI_API_KEY else "Not connected"
    semrush_status = "Configured" if SEMRUSH_API_KEY and SEMRUSH_MCP_URL else "Not connected"
    screaming_frog_status = "Configured" if SCREAMING_FROG_MCP_URL else "Not connected"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SEO Intelligence Agent</title>
        <style>
            body {{ margin: 0; font-family: Arial, sans-serif; background: #f4f7fb; color: #1f2937; }}
            .container {{ max-width: 950px; margin: 40px auto; background: white; border-radius: 18px; padding: 34px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }}
            h1 {{ margin-top: 0; color: #003b5c; font-size: 34px; }}
            .subtitle {{ color: #64748b; margin-bottom: 24px; font-size: 17px; }}
            .pill-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 22px; }}
            .pill {{ background: #eef6f9; color: #003b5c; padding: 8px 12px; border-radius: 999px; font-size: 14px; border: 1px solid #cfe4ec; }}
            #chat {{ min-height: 380px; border: 1px solid #e5e7eb; border-radius: 14px; padding: 18px; background: #fafafa; margin-bottom: 16px; overflow-y: auto; }}
            .message {{ margin-bottom: 14px; padding: 13px 15px; border-radius: 12px; line-height: 1.55; white-space: normal; }}
            .user {{ background: #e0f2fe; text-align: right; }}
            .bot {{ background: #ecfdf5; }}
            .input-row {{ display: flex; gap: 10px; }}
            input {{ flex: 1; padding: 14px; border-radius: 10px; border: 1px solid #cbd5e1; font-size: 16px; }}
            button {{ padding: 14px 20px; border: none; border-radius: 10px; background: #003b5c; color: white; font-size: 16px; cursor: pointer; }}
            button:hover {{ background: #00527d; }}
            .status {{ margin-top: 20px; padding: 14px; background: #f8fafc; border-radius: 10px; font-size: 14px; color: #475569; }}
            .status strong {{ color: #003b5c; }}
            .examples {{ margin-top: 14px; font-size: 14px; color: #64748b; }}
            .example-btn {{ display: inline-block; margin: 5px 6px 0 0; padding: 7px 10px; border-radius: 8px; background: #f1f5f9; cursor: pointer; border: 1px solid #e2e8f0; }}
            .example-btn:hover {{ background: #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SEO Intelligence Agent - Howden C&LC</h1>
            <p class="subtitle">Local / Azure-ready AI agent for Semrush analysis and Screaming Frog technical crawls.</p>

            <div class="pill-row">
                <span class="pill">Gemini: {gemini_status}</span>
                <span class="pill">Semrush MCP: {semrush_status}</span>
                <span class="pill">Screaming Frog MCP: {screaming_frog_status}</span>
            </div>

            <div class="examples">
                Try:
                <span class="example-btn" onclick="useExample('Use Screaming Frog to crawl https://example.com and find broken internal links.')">Technical crawl</span>
                <span class="example-btn" onclick="useExample('Use Semrush to find keyword opportunities for young driver insurance in the UK.')">Keyword opportunities</span>
                <span class="example-btn" onclick="useExample('Use Semrush to find the top organic competitors for howdeninsurance.co.uk in the UK.')">Competitor research</span>
            </div>

            <br></br>

            <div id="chat">
                <div class="message bot">
                    Hello. Semrush questions use the live Semrush MCP connection. Crawl and technical-audit questions use the live Screaming Frog MCP connection.
                </div>
            </div>

            <div class="input-row">
                <input id="message" placeholder="Example: Crawl https://example.com and identify broken internal links." />
                <button onclick="sendMessage()">Ask</button>
            </div>

            <div class="status">
                <strong>Status:</strong>
                Gemini is <strong>{gemini_status}</strong>.
                Semrush MCP is <strong>{semrush_status}</strong>.
                Screaming Frog MCP is <strong>{screaming_frog_status}</strong>.
                Screaming Frog must be open with its MCP server enabled.
            </div>
        </div>

        <script>
            function useExample(text) {{
                document.getElementById("message").value = text;
                sendMessage();
            }}

            async function sendMessage() {{
                const input = document.getElementById("message");
                const chat = document.getElementById("chat");
                const message = input.value.trim();

                if (!message) return;

                chat.innerHTML += `<div class="message user">${{message}}</div>`;
                input.value = "";
                chat.innerHTML += `<div class="message bot"><em>Thinking...</em></div>`;
                chat.scrollTop = chat.scrollHeight;

                try {{
                    const response = await fetch("/chat", {{
                        method: "POST",
                        headers: {{"Content-Type": "application/json"}},
                        body: JSON.stringify({{message}})
                    }});

                    const data = await response.json();

                    const thinkingMessages = chat.querySelectorAll(".bot em");
                    if (thinkingMessages.length > 0) {{
                        thinkingMessages[thinkingMessages.length - 1].parentElement.remove();
                    }}

                    chat.innerHTML += `<div class="message bot">${{data.reply.replaceAll("\n", "<br>")}}</div>`;
                    chat.scrollTop = chat.scrollHeight;
                }} catch (error) {{
                    const thinkingMessages = chat.querySelectorAll(".bot em");
                    if (thinkingMessages.length > 0) {{
                        thinkingMessages[thinkingMessages.length - 1].parentElement.remove();
                    }}

                    chat.innerHTML += `<div class="message bot">The request failed: ${{error}}</div>`;
                }}
            }}

            document.getElementById("message").addEventListener("keydown", function(e) {{
                if (e.key === "Enter") sendMessage();
            }});
        </script>
    </body>
    </html>
    """


@app.post("/chat")
async def chat(request: ChatRequest):
    message = request.message.strip()
    message_lower = message.lower()

    screaming_frog_terms = [
        "screaming frog",
        "crawl",
        "technical audit",
        "technical seo audit",
        "broken link",
        "broken links",
        "internal link",
        "internal links",
        "404",
        "4xx",
        "5xx",
        "missing title",
        "duplicate title",
        "missing h1",
        "duplicate h1",
        "missing meta description",
        "duplicate meta description",
        "redirect chain",
        "redirect chains",
        "canonical issue",
        "canonical issues",
        "orphan page",
        "orphan pages",
    ]

    semrush_terms = [
        "semrush",
        "keyword",
        "keywords",
        "ranking",
        "rankings",
        "search volume",
        "keyword difficulty",
        "competitor",
        "competitors",
        "organic search",
        "backlink",
        "backlinks",
        "domain overview",
        "traffic estimate",
        "content gap",
    ]

    try:
        if SCREAMING_FROG_MCP_URL and any(term in message_lower for term in screaming_frog_terms):
            reply = await ask_screaming_frog(message)

        elif SEMRUSH_API_KEY and SEMRUSH_MCP_URL and any(term in message_lower for term in semrush_terms):
            reply = await ask_semrush(message)

        else:
            reply = ask_gemini(message)

        return {"reply": reply}

    except Exception as error:
        return {"reply": f"The request could not be completed. Error detail: {error}"}
