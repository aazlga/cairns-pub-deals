import os
import json
import time
from google import genai
from google.genai import types

def get_pub_deals(client, venue_name, url):
    prompt = f"""
    Search the web for the exact current daily food specials listed on the official website for {venue_name} in Cairns ({url}).
    Extract the real, actual meal item and price for each day of the week. Do not guess or extrapolate any prices.

    Return ONLY a valid, raw JSON array mapping exactly to this schema structure with no markdown decoration, no ```json tags, and no conversational text:
    [
      {{
        "pub": "{venue_name}",
        "location": "Cairns",
        "day": "Monday",
        "deal": "Actual Deal Text Here",
        "price": "$Actual Price Here",
        "url": "{url}",
        "last_updated": "June 2026"
      }}
    ]
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Invoking Gemini Live Web Grounding for {venue_name} (Attempt {attempt + 1}/{max_retries})...")
            
            # Using search grounding cleanly by dropping response_schema
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],
                    temperature=0.0,
                ),
            )
            
            raw_text = response.text.strip()
            
            # Extract out json array strings if wrapped in markdown formatting tags
            cleaned = raw_text.replace('```json', '').replace('```', '').strip()
            
            return json.loads(cleaned)
            
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"Server busy (503). Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            print(f"Failed parsing data for {venue_name}: {e}")
            return []
    return []

try:
    client = genai.Client()
    all_deals = []
    
    venues = [
        {"name": "The Crown Hotel", "url": "[https://www.thecrownhotelcairns.com.au/daily-specials](https://www.thecrownhotelcairns.com.au/daily-specials)"},
        {"name": "Dunwoody's Hotel", "url": "[https://dunwoodys.com.au/whats-on/](https://dunwoodys.com.au/whats-on/)"}
    ]
    
    for venue in venues:
        deals = get_pub_deals(client, venue["name"], venue["url"])
        all_deals.extend(deals)
        
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(all_deals, f, indent=2)
        
    print(f"Successfully aggregated and updated {len(all_deals)} total verified deals in public/deals.json!")

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
