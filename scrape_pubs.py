import os
import json
import time
from google import genai
from google.genai import types

def get_pub_deals(client, venue_name, url):
    prompt = f"""
    You are a professional web scraping agent. Your goal is to extract the CURRENT, active daily food and drink specials for "{venue_name}" in Cairns from their official website presence ({url}).

    DIRECTIONS:
    1. Perform web searches targeting the official venue domain to discover active dining special pages.
    2. Read search snippets carefully to locate the active weekly meal/drink deals.
    3. Match the data to the required output schema structure exactly.
    
    CRITICAL EXTRACTION RULES:
    - Extract ONLY real, active food and drink specials currently offered.
    - If a specific day of the week does not have a clear deal listed, skip that day completely.
    - Do NOT invent or extrapolate prices. If a valid special lacks a price, use "Varies".
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Scraping {venue_name} with strict JSON config (Attempt {attempt + 1}/{max_retries})...")
            
            # Legacy structure passing explicit JSON formatting configs directly to the model call
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            
            raw_text = response.text.strip()
            parsed_data = json.loads(raw_text)
            
            print(f"Successfully parsed {len(parsed_data)} structured deals for {venue_name}!")
            return parsed_data
            
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"Server busy. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            print(f"Failed parsing structured schema data for {venue_name}: {e}")
            return []
    return []

try:
    client = genai.Client()
    all_deals = []
    
    venues = [
        {
            "name": "The Crown Hotel", 
            "url": "https://www.thecrownhotelcairns.com.au/daily-specials"
        },
        {
            "name": "Dunwoody's Hotel", 
            "url": "https://dunwoodys.com.au/whats-on/"
        }
    ]
    
    for venue in venues:
        deals = get_pub_deals(client, venue["name"], venue["url"])
        all_deals.extend(deals)
        
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(all_deals, f, indent=2)
        
    print(f"Successfully aggregated {len(all_deals)} total verified deals in public/deals.json!")

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
