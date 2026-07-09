from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os

# Loads your local .env file when running on your laptop.
# In Azure, these values can come from App Service settings or Key Vault references.
load_dotenv()

app = FastAPI(title="SEO Intelligence Agent - Howden C&LC website")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY")
SCREAMING_FROG_API_KEY = os.getenv("SCREAMING_FROG_API_KEY")


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
- Keep answers structured with clear priorities and next steps.
"""


def get_fake_response(message: str) -> str:
    """Fallback response if Gemini is not configured or fails."""
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

Demo note: this is sample data. In production this would come from Screaming Frog MCP.
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

Demo note: this is sample data. In production this would come from Semrush MCP.
"""

    if any(word in msg for word in ["traffic", "ga4", "analytics", "gsc", "search console", "clicks", "impressions"]):
        return """
I would use GA4 and Google Search Console connectors for this.

Organic performance summary:

- Organic sessions are down 8% month-on-month.
- Impressions are up 11%, but CTR has dropped from 3.2% to 2.4%.
- The biggest traffic decline is on insurance product landing pages.
- Several pages have strong impressions but weak click-through rates.

Priority opportunities:
1. Rewrite title tags on high-impression pages with low CTR.
2. Improve internal links to pages ranking in positions 6–15.
3. Review landing pages where traffic is stable but quote starts are down.

Demo note: this is sample data. In production this would come from GA4 and Search Console MCP connectors.
"""

    if any(word in msg for word in ["competitor", "compare", "confused", "gocompare", "comparethemarket"]):
        return """
Competitor summary:

Competitors appear stronger in:
1. Guide-based content.
2. Long-tail insurance queries.
3. Local insurance broker searches.
4. FAQ-rich pages.
5. Internal linking to commercial landing pages.

Content gaps:
- Learner driver insurance guide.
- Business insurance by trade.
- Local branch insurance broker pages.
- Claims advice content.
- Policy comparison guides.

Recommended action:
Prioritise content where competitors rank and your site already has a partially relevant page. This is usually faster than building from scratch.

Demo note: this is sample data. In production this would come from Semrush MCP.
"""

    return """
I can help with SEO analysis across technical SEO, keywords, traffic, competitors and content opportunities.

Example questions you can ask:
- What are the biggest technical SEO issues?
- Which keywords should we prioritise?
- Why has organic traffic dropped?
- Where are the biggest competitor gaps?
- Which pages should we optimise first?

Demo note: Gemini is not currently connected, so this fallback response is being used.
"""


def ask_gemini(message: str) -> str:
    """Send the user's question to Gemini and return the answer."""
    if not GEMINI_API_KEY:
        return get_fake_response(message)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
{SYSTEM_PROMPT}

Current tool connection status:
- Gemini API: connected
- Semrush MCP/API key present: {'yes' if SEMRUSH_API_KEY else 'no'}
- Screaming Frog MCP/API key present: {'yes' if SCREAMING_FROG_API_KEY else 'no'}

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
Gemini could not be reached, so the app is using demo fallback mode.

Error detail:
{str(error)}

Fallback answer:
{get_fake_response(message)}
"""


@app.get("/", response_class=HTMLResponse)
def home():
    gemini_status = "Connected" if GEMINI_API_KEY else "Not connected"
    semrush_status = "Key found" if SEMRUSH_API_KEY else "Not connected"
    screaming_frog_status = "Key found" if SCREAMING_FROG_API_KEY else "Not connected"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SEO Intelligence Agent</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f4f7fb;
                color: #1f2937;
            }}
            .container {{
                max-width: 950px;
                margin: 40px auto;
                background: white;
                border-radius: 18px;
                padding: 34px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            }}
            h1 {{
                margin-top: 0;
                color: #003b5c;
                font-size: 34px;
            }}
            .subtitle {{
                color: #64748b;
                margin-bottom: 24px;
                font-size: 17px;
            }}
            .pill-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-bottom: 22px;
            }}
            .pill {{
                background: #eef6f9;
                color: #003b5c;
                padding: 8px 12px;
                border-radius: 999px;
                font-size: 14px;
                border: 1px solid #cfe4ec;
            }}
            #chat {{
                min-height: 380px;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
                padding: 18px;
                background: #fafafa;
                margin-bottom: 16px;
                overflow-y: auto;
            }}
            .message {{
                margin-bottom: 14px;
                padding: 13px 15px;
                border-radius: 12px;
                line-height: 1.55;
                white-space: normal;
            }}
            .user {{
                background: #e0f2fe;
                text-align: right;
            }}
            .bot {{
                background: #ecfdf5;
            }}
            .input-row {{
                display: flex;
                gap: 10px;
            }}
            input {{
                flex: 1;
                padding: 14px;
                border-radius: 10px;
                border: 1px solid #cbd5e1;
                font-size: 16px;
            }}
            button {{
                padding: 14px 20px;
                border: none;
                border-radius: 10px;
                background: #003b5c;
                color: white;
                font-size: 16px;
                cursor: pointer;
            }}
            button:hover {{
                background: #00527d;
            }}
            .status {{
                margin-top: 20px;
                padding: 14px;
                background: #f8fafc;
                border-radius: 10px;
                font-size: 14px;
                color: #475569;
            }}
            .status strong {{
                color: #003b5c;
            }}
            .examples {{
                margin-top: 14px;
                font-size: 14px;
                color: #64748b;
            }}
            .example-btn {{
                display: inline-block;
                margin: 5px 6px 0 0;
                padding: 7px 10px;
                border-radius: 8px;
                background: #f1f5f9;
                cursor: pointer;
                border: 1px solid #e2e8f0;
            }}
            .example-btn:hover {{
                background: #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SEO Intelligence Agent - Howden C&LC</h1>
            <p class="subtitle">
                Local / Azure-ready AI agent demo for SEO analysis, technical audits, keyword opportunities and competitor insights.
            </p>

            <div class="pill-row">
                <span class="pill">Gemini: {gemini_status}</span>
                <span class="pill">Semrush: {semrush_status}</span>
                <span class="pill">Screaming Frog: {screaming_frog_status}</span>
                <span class="pill">MCP Tools: Placeholder</span>
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
                    Hello. Ask me an SEO question. If Gemini is connected, I will use Gemini to answer. MCP tools are still placeholders until the Semrush and Screaming Frog MCP servers are wired in.
                </div>
            </div>

            <div class="input-row">
                <input id="message" placeholder="Example: What are our biggest SEO opportunities?" />
                <button onclick="sendMessage()">Ask</button>
            </div>

            <div class="status">
                <strong>Status:</strong> Gemini is currently <strong>{gemini_status}</strong>. Semrush is <strong>{semrush_status}</strong>. Screaming Frog is <strong>{screaming_frog_status}</strong>. Production credentials should be stored in Azure Key Vault or App Service settings, not in code.
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
    reply = ask_gemini(request.message)
    return {"reply": reply}
