import os
import json
import urllib.request
import google.generativeai as genai

# 1. Initialize Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Define the exact daily specials endpoint for The Crown Hotel
URLS_TO_TRACK = {
    "The Crown Hotel": "https://www.thecrownhotelcairns.com.au/daily-specials"
}

all_scraped_deals = []

for venue_name, url in URLS_TO_TRACK.items():
    try:
        # Fetch webpage text securely
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            raw_html = response.read().decode('utf-8', errors='ignore')
        
        # Strip code bloat to optimize token usage
        lines = [line.strip() for line in raw_html.split('\n') if line.strip()]
        clean_text = " ".join(lines)[:25000]

        # 3. Prompt Gemini to map data perfectly to your frontend layout
        prompt = f"""
        You are a data extraction bot for a local restaurant app. 
        Analyze the following webpage content from "{venue_name}" and extract any weekly food or drink specials (e.g., Steak Night, Schnitzel deals, Trivia meal deals, Happy Hours).
        
        Return ONLY a raw, valid JSON array matching this exact schema. Do not wrap it in markdown code blocks or add any introductory or concluding text.
        [
          {{
            "pub": "{venue_name}",
            "location": "Cairns City",
            "day": "Monday/Tuesday/Wednesday/Thursday/Friday/Saturday/Sunday/Everyday",
            "deal": "Clean text details of what the meal deal includes (excluding the price if price is listed separately)",
            "price": "Include explicit dollar amount if stated, e.g. $15, otherwise leave blank",
            "url": "{url}",
            "last_updated": "Weekly Feed"
          }}
        ]

        Webpage Content:
        {clean_text}
        """

        ai_response = model.generate_content(prompt)
        
        # Ensure raw text string cleans out any accidental markdown triple-backticks
        cleaned_json_text = ai_response.text.strip().replace('```json', '').replace('```', '')
        venue_deals = json.loads(cleaned_json_text)
        
        all_scraped_deals.extend(venue_deals)
        print(f"Successfully processed {venue_name}")

    except Exception as e:
        print(f"Error processing {venue_name}: {e}")

# 4. Save to the public directory for Vercel deployment
os.makedirs('public', exist_ok=True)
with open('public/deals.json', 'w') as f:
    json.dump(all_scraped_deals, f, indent=2)

print("Scrape complete! public/deals.json updated.")
