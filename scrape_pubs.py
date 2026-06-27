import os
import json
import time
import re
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

def get_pub_deals(client, venue_name, url):
    # Extract the domain to perform clean site-restricted grounding searches
    domain = url.replace("https://", "").replace("http://", "").split('/')[0]
    
    prompt = f"""
    You are a professional web scraping agent. Your goal is to extract the CURRENT, active daily food and drink specials for "{venue_name}" in Cairns from their official website presence ({url}).

    DIRECTIONS FOR SEARCH GROUNDING:
    1. Perform web searches targeting the official venue domain using exact search queries:
       - "site:{domain} specials"
       - "site:{domain} whats on"
       - "site:{domain} deals"
       - "site:{domain} Monday" (and other days of the week to look up specific event pages)
    2. Read the search snippets carefully to locate the actual active weekly meal/drink deals.
    
    CRITICAL EXTRACTION RULES:
    - Extract ONLY real, active specials currently offered.
    - If a specific day of the week (Monday through Sunday) does not have a food or drink special explicitly listed, do NOT include that day in the output.
    - Do NOT invent, guess, or extrapolate any deals. If you cannot verify a deal for a day, skip that day completely.
    - If you find a valid special but no price is mentioned, set the price field to "Varies" or "Free" (if applicable).

    OUTPUT SCHEMA:
    Return ONLY a valid, raw JSON array of objects mapping to this exact schema structure. 
    Do NOT include any conversational introduction, backticks, or write markdown "```json" blocks around it:
    [
      {{
        "pub": "{venue_name}",
        "location": "Cairns",
        "day": "Day of the week (e.g., Monday)",
        "deal": "Exact name of the special / description found",
        "price": "Price found (e.g., $20 or Varies or Free)",
        "url": "{url}",
        "last_updated": "June 2026"
      }}
    ]
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Scraping {venue_name} dynamically (Attempt {attempt + 1}/{max_retries})...")
            
            # Using Gemini with Search Grounding enabled (with response_schema omitted to bypass tool conflicts)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],
                    temperature=0.0,
                ),
            )
            
            raw_text = response.text.strip()
            
            # Clean and isolate the JSON block from any markdown decoration
            json_string = extract_json_array_string(raw_text)
            parsed_data = json.loads(json_string)
            
            print(f"Successfully parsed {len(parsed_data)} deals for {venue_name}!")
            return parsed_data
            
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
        {
            "name": "The Crown Hotel", 
            "url": "[https://www.thecrownhotelcairns.com.au/daily-specials](https://www.thecrownhotelcairns.com.au/daily-specials)"
        },
        {
            "name": "Dunwoody's Hotel", 
            "url": "[https://dunwoodys.com.au/whats-on/](https://dunwoodys.com.au/whats-on/)"
        }
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
