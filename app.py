from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os

# Load local environment variables from a .env file when running locally.
# In Azure, these values would usually come from App Service settings or Key Vault.
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-2.5-flash"

client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="SEO Intelligence Agent - Howden C&LC website")


class ChatRequest(BaseModel):
    message: str


def get_fake_response(message: str) -> str:
    """Fallback response used when no Gemini API key is available."""
    msg = message.lower()

    if any(word in msg for word in ["technical", "crawl", "screaming frog", "broken", "404", "h1", "title"]):
        return """
Technical SEO findings:

1. 42 pages have missing or duplicate H1 tags.
2. 18 URLs return 4xx status codes.
3. 73 pages have title tags over 60 characters.
4. 26 pages have missing meta descriptions.
5. 11 pages appear to be thin-content pages.

Recommended priority:
High: Fix 4xx errors and duplicate titles first.
Medium: Rewrite missing meta descriptions on commercial landing pages.
Low: Review thin-content pages after higher-impact fixes.

Demo note: this is sample data. Gemini is not currently connected because GEMINI_API_KEY is missing.
"""

    if any(word in msg for word in ["keyword", "semrush", "ranking", "rankings", "content gap", "search volume"]):
        return """
Here are some keyword opportunities:

1. "young driver insurance" — 2,400 monthly searches — current position 14.
2. "temporary car insurance" — 8,100 monthly searches — current position 11.
3. "business van insurance" — 1,900 monthly searches — current position 18.
4. "home insurance broker" — 720 monthly searches — current position 9.
5. "landlord insurance quote" — 1,300 monthly searches — current position 16.

Recommended action:
Focus on keywords ranking between positions 8–20 where a page already exists. These are likely quicker wins than creating brand-new content.

Demo note: this is sample data. Gemini is not currently connected because GEMINI_API_KEY is missing.
"""

    return """
I can help with SEO analysis across technical SEO, keywords, traffic, competitors and content opportunities.

Example questions you can ask:
- What are the biggest technical SEO issues?
- Which keywords should we prioritise?
- Why has organic traffic dropped?
- Where are the biggest competitor gaps?
- Which pages should we optimise first?

Demo note: this version is using fallback sample data because GEMINI_API_KEY is missing.
"""


def ask_gemini(message: str) -> str:
    """Send the user's message to Gemini and return a natural-language answer."""
    if not GEMINI_API_KEY:
        return get_fake_response(message)

    client = genai.Client(api_key=GEMINI_API_KEY)

    system_context = """
You are an SEO Intelligence Agent for Howden C&LC.
You help with technical SEO, keyword research, competitor analysis, content opportunities, GA4/GSC interpretation, and SEO prioritisation.

Important rules:
- Be clear and practical.
- Explain recommendations in plain English.
- If live tool/API data is not available in the prompt, say that you would normally use the relevant MCP connector.
- Do not pretend to have live Semrush, Screaming Frog, GA4, or Google Search Console data unless it has been provided.
- When making recommendations, prioritise actions by likely business impact.
"""

    prompt = f"{system_context}\n\nUser question:\n{message}"

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text or "Gemini returned an empty response."
    except Exception as error:
        return f"Gemini connection error: {error}"


@app.get("/", response_class=HTMLResponse)
def home():
    gemini_status = "Connected" if GEMINI_API_KEY else "Not connected"
    data_status = "Gemini Enabled" if GEMINI_API_KEY else "Fallback Demo Data"

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
            <p class="subtitle">Local AI agent demo for SEO analysis, technical audits, keyword opportunities and competitor insights.</p>

            <div class="pill-row">
                <span class="pill">App: Live</span>
                <span class="pill">Gemini: {gemini_status}</span>
                <span class="pill">Mode: {data_status}</span>
                <span class="pill">Semrush MCP: Next step</span>
                <span class="pill">Screaming Frog MCP: Next step</span>
            </div>

            <div class="examples">
                Try:
                <span class="example-btn" onclick="useExample('What are the biggest technical SEO issues?')">Technical SEO issues</span>
                <span class="example-btn" onclick="useExample('Which keywords should we prioritise?')">Keyword opportunities</span>
                <span class="example-btn" onclick="useExample('Why has organic traffic dropped?')">Traffic drop</span>
                <span class="example-btn" onclick="useExample('Where are the biggest competitor gaps?')">Competitor gaps</span>
            </div>

            <br></br>

            <div id="chat">
                <div class="message bot">
                    Hello. Ask me an SEO question. If Gemini is connected, I will use Gemini to answer. MCP tools such as Semrush and Screaming Frog can be connected next.
                </div>
            </div>

            <div class="input-row">
                <input id="message" placeholder="Example: What are our biggest SEO opportunities?" />
                <button onclick="sendMessage()">Ask</button>
            </div>

            <div class="status">
                <strong>Local demo:</strong> Gemini status is <strong>{gemini_status}</strong>. API keys should be stored in your local .env file and not committed to GitHub.
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

                const response = await fetch("/chat", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{message}})
                }});

                const data = await response.json();

                chat.innerHTML += `<div class="message bot">${{data.reply.replaceAll("\\n", "<br>")}}</div>`;
                chat.scrollTop = chat.scrollHeight;
            }}

            document.getElementById("message").addEventListener("keydown", function(e) {{
                if (e.key === "Enter") sendMessage();
            }});
        </script>
    </body>
    </html>
    """


@app.post("/chat")
def chat(request: ChatRequest):

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=request.message,
    )
    return {
        "reply": response.text
        }