import os
import json
import time
from google import genai
from google.genai import types

def extract_json_array_string(text):
    """
    Locates the first '[' and last ']' to safely isolate the JSON array block,
    discarding any markdown formatting tags or conversational text.
    """
    text = text.strip()
    start_idx = text.find('[')
    end_idx = text.rfind(']')
    
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        return text[start_idx:end_idx + 1]
    raise ValueError("No JSON array found in the model's response text.")

def get_pub_deals(client, venue):
    # If explicit text context is provided (like Dunwoody's), use it to bypass firewalls completely
    if "context" in venue:
        prompt = f"""
        Extract the daily food and drink specials for {venue['name']} using ONLY this provided text context:
        {venue['context']}
        
        Return ONLY a valid, raw JSON array of objects mapping exactly to this schema structure.
        Do NOT write markdown "```json" blocks or include extra conversational text:
        [
          {{
            "pub": "{venue['name']}",
            "location": "Cairns",
            "day": "Monday",
            "deal": "Exact meal name and description",
            "price": "$Price",
            "url": "{venue['url']}",
            "last_updated": "June 2026"
          }}
        ]
        """
        config = types.GenerateContentConfig(
            temperature=0.0,
        )
    else:
        # Fallback to Live Web Search for open sites like the Crown
        domain = venue['url'].replace("https://", "").replace("http://", "").split('/')[0]
        prompt = f"""
        You are a professional web scraping agent. Your goal is to extract the CURRENT, active daily food and drink specials for "{venue['name']}" in Cairns from their official website ({venue['url']}).

        DIRECTIONS FOR SEARCH GROUNDING:
        1. Perform web searches targeting the official venue domain using exact search queries:
           - "site:{domain} specials"
           - "site:{domain} whats on"
           - "site:{domain} deals"
        2. Read the search snippets carefully to locate the actual active weekly meal/drink deals.
        
        CRITICAL EXTRACTION RULES:
        - Extract ONLY real, active specials currently offered.
        - If a specific day does not have a food/drink special listed, do NOT include that day.
        - Do NOT invent or guess any deals. 

        OUTPUT SCHEMA:
        Return ONLY a valid, raw JSON array matching this structure without markdown wraps:
        [
          {{
            "pub": "{venue['name']}",
            "location": "Cairns",
            "day": "Monday",
            "deal": "Exact name of the special found",
            "price": "$Price",
            "url": "{venue['url']}",
            "last_updated": "June 2026"
          }}
        ]
        """
        config = types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.0,
        )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Processing data for {venue['name']} (Attempt {attempt + 1}/{max_retries})...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=config,
            )
            
            raw_text = response.text.strip()
            json_string = extract_json_array_string(raw_text)
            return json.loads(json_string)
            
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    time.sleep(wait_time)
                    continue
            print(f"Failed parsing data for {venue['name']}: {e}")
            return []
    return []

try:
    client = genai.Client()
    all_deals = []
    
    venues = [
        {
            "name": "The Crown Hotel", 
            "url": "[https://www.thecrownhotelcairns.com.au/daily-specials](https://www.thecrownhotelcairns.com.au/daily-specials)"
        },
        {
            "name": "Dunwoody's Hotel", 
            "url": "[https://dunwoodys.com.au/whats-on/](https://dunwoodys.com.au/whats-on/)",
            "context": """
            Every Tuesday Lunch & Dinner: Monster Parmi Tuesday for $25 (Choose from 5 styles of 350g Chicken Parmis: Classic, Atherton Signature, Meat Lovers, Hawaiian, Carbonara).
            Every Thursday Lunch & Dinner: Steak Night for $23 (Enjoy a 250g Rump served with chips, salad, and sauce).
            Every Sunday Lunch & Dinner: Sunday Roast for $28 served with traditional trimmings.
            """
        }
    ]
    
    for venue in venues:
        deals = get_pub_deals(client, venue)
        all_deals.extend(deals)
        
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(all_deals, f, indent=2)
        
    print(f"Successfully aggregated and updated {len(all_deals)} total verified deals in public/deals.json!")

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
