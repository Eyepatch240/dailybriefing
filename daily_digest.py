import os
import feedparser
import trafilatura
import google.generativeai as genai
from datetime import datetime
from jinja2 import Template

# --- CONFIGURATION ---
# Add your RSS feeds here
RSS_FEEDS = [

    "https://news.ycombinator.com/rss",  
    
    "https://astralcodexten.substack.com/feed",  
    "https://aella.substack.com/feed",           
    "https://feeds.feedburner.com/marginalrevolution/feed", 
    
    "https://www.lesswrong.com/feed.xml?view=curated-rss", 
    
    "https://www.indiehackers.com/feed", 
    
    "https://spacenews.com/feed/",       
    
    "https://www.politico.eu/feed/",     
    "https://www.euractiv.com/feed/"     
]

# Define what you care about
USER_INTERESTS = """
I am looking for high-signal content. My specific interests are:

1. HARD TECH & AI: LLMs, agents, code, open-source models, and technical breakthroughs.
2. THE FUTURE: Transhumanism, longevity, biohacking, and space colonization (SpaceX, Starship, Mars).
3. BUSINESS: Bootstrapped startups, indie hacking, SaaS metrics, interesting VC-backed companies.
4. SOCIOLOGY & DATA: Unconventional social studies, evolutionary psychology, prediction markets, and contrarian takes on society.
5. GEOPOLITICS: Specifically European strategic autonomy, EU defense, and macro-political shifts in Europe. 

EXCLUDE: Generic gadget reviews (iPhone rumors), celebrity gossip, sports, partisan US domestic politics (unless it affects global tech), and crypto shitcoins (unless technical blockchain innovation).
"""

# Setup Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-pro')

def get_headlines():
    print("Fetching RSS feeds...")
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]: # Increased to 15 per feed
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get('summary', '')[:500] # Truncate summary
                })
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    return articles

def filter_articles(articles):
    print("Filtering articles with LLM...")
    # We send the list to Gemini and ask it to pick the best URLs
    prompt = f"""
    Here is a list of news headlines:
    {articles}

    Based on these user interests: "{USER_INTERESTS}"
    
    Select the TOP 13-15 most relevant and promising articles (err on the side of more, not fewer).
    Return ONLY a raw JSON list of their URLs, nothing else. 
    Example: ["url1", "url2", "url3"]
    Respond ONLY with that JSON list. No markdown formatting or commentary.
    """
    
    response = model.generate_content(prompt)
    try:
        # Clean up code blocks if the LLM adds them
        text = response.text.replace("```json", "").replace("```", "").strip()
        import json
        selected_urls = json.loads(text)
        return selected_urls
    except Exception as e:
        print(f"Error parsing LLM selection ({e}). Fallback to first 8.")
        return [a['link'] for a in articles[:8]]

def scrape_content(urls):
    print("Scraping full content...")
    full_texts = []
    for url in urls:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        if text:
            full_texts.append(f"SOURCE URL: {url}\nCONTENT:\n{text}\n---")
    return "\n".join(full_texts)

def generate_digest(content_text):
    print("Writing the digest...")
    prompt = f"""
    You are a professional news editor.
    Here is the full text of several articles:
    
    {content_text}

    Task:
    1. Categorize each article by topic (e.g., Tech, Politics, Science).
    2. Write a curated, concise, and high-signal daily news digest. Use clear, readable language—avoid hype or filler.
    3. For each story, provide a substantive summary suitable for a sophisticated and time-constrained reader.
    4. At the end of each section, include the provided "SOURCE URL" as a clickable Markdown link: [Read full article](url).
    5. Use minimalist Markdown formatting—headings, short paragraph blocks, bullet points where useful. Avoid emojis, exclamation marks, and unnecessary flourishes.
    """

    response = model.generate_content(prompt)
    return response.text

def save_html(markdown_content):
    html_template = """
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>Daily Briefing - {{ date }}</title>
        <style>
            :root {
                color-scheme: dark;
            }
            body {
                background: #15171a;
                color: #e9e9ec;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 42px 18px 72px 18px;
                font-size: 1.08rem;
                line-height: 1.85; /* Increased for easier reading */
            }
            h1, h2, h3, h4 {
                color: #e4e8ee;
                font-weight: 600;
                letter-spacing: -0.02em;
                margin-bottom: 0.92em;
                margin-top: 2.1em;
            }
            h1 {
                font-size: 1.85rem;
                margin-top: 0.2em;
                margin-bottom: 0.6em;
                border-bottom: 1px solid #22242b;
                padding-bottom: 0.35em;
            }
            h2 {
                font-size: 1.29rem;
                margin-top: 2.5em;
                margin-bottom: 0.64em;
            }
            /* Article Card Style (optional, minimalist) */
            .article-block {
                margin-bottom: 2.7em;
                margin-top: 2.7em;
                padding: 1.3em 1.1em;
                background: #191c21;
                border-radius: 9px;
                border: 1px solid #23252c;
            }
            hr {
                border: none;
                border-top: 1px solid #23252d;
                margin: 2.8em 0 2.3em;
            }
            a {
                color: #99c6ff;
                text-decoration: underline;
                transition: color 0.15s;
            }
            a:hover {
                color: #6aaeff;
            }
            code, pre {
                background: #1e2228;
                color: #c2c7cf;
                border-radius: 3px;
                padding: 0.17em 0.33em;
            }
            p {
                margin-bottom: 1.38em;
                margin-top: 0.4em; /* For space between body and heading */
            }
            ul {
                margin-top: 0.6em;
                margin-bottom: 1.2em;
                padding-left: 1.3em;
            }
            li {
                margin-bottom: 0.5em;
            }
        </style>
    </head>
    <body>
        <h1>Daily Briefing <span style=\"color:#686d79;font-weight:300;font-size:0.92em;\">{{ date }}</span></h1>
        <hr>
        <div>{{ content }}</div>
    </body>
    </html>
    """
    
    import markdown
    html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code', 'codehilite'])
    
    t = Template(html_template)
    final_html = t.render(date=datetime.now().strftime("%Y-%m-%d"), content=html_content)
    
    # Save to index.html so GitHub Pages serves it
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    all_articles = get_headlines()
    selected_urls = filter_articles(all_articles)
    full_content = scrape_content(selected_urls)
    digest = generate_digest(full_content)
    save_html(digest)
    print("Done! index.html generated.")
