import os
import json
from google import genai
from google.genai import types

def get_pub_deals(client, venue_name, url):
    prompt = f"""
    Search the web for the exact daily food and drink specials currently listed on the official website 
    for {venue_name} in Cairns ({url}). 
    
    Extract the real, actual meal item and price for each day of the week. 
    Do not make up or guess any prices. If a day has no specified deal, skip it.
    
    Return ONLY a valid, raw JSON array mapping exactly to this schema structure with no markdown decoration, no ```json tags, and no extra text:
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
    
    print(f"Invoking Gemini Live Web Grounding for {venue_name}...")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.0,
        ),
    )
    
    # Clean standard Markdown code blocks
    raw_text = response.text.strip()
    cleaned = raw_text.replace('```json', '').replace('```', '').strip()
    
    try:
        return json.loads(cleaned)
    except Exception as parse_error:
        print(f"Failed parsing data for {venue_name}: {parse_error}")
        return []

try:
    # Initialize modern client
    client = genai.Client()
    all_deals = []
    
    # Map out our venues
    venues = [
        {"name": "The Crown Hotel", "url": "[https://www.thecrownhotelcairns.com.au/daily-specials](https://www.thecrownhotelcairns.com.au/daily-specials)"},
        {"name": "Dunwoody's Hotel", "url": "[https://dunwoodys.com.au/whats-on/](https://dunwoodys.com.au/whats-on/)"}
    ]
    
    # Step through each venue and aggregate the payloads
    for venue in venues:
        deals = get_pub_deals(client, venue["name"], venue["url"])
        all_deals.extend(deals)
        
    # Write the unified dataset back to public directory
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(all_deals, f, indent=2)
        
    print(f"Successfully aggregated and updated {len(all_deals)} total deals in public/deals.json!")

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
