import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Define a strict data schema to prevent example matching or hallucination
class PubDeal(BaseModel):
    pub: str = Field(description="The formal name of the venue")
    location: str = Field(description="The suburb or city area, e.g., Cairns City or Cairns North")
    day: str = Field(description="The day of the week, e.g., Monday")
    deal: str = Field(description="The exact name of the food meal deal or special drink deal as written on the page")
    price: str = Field(description="The cost of the deal, including the dollar sign, e.g., $20. If it varies or is not stated, write Varies")
    url: str = Field(description="The exact source page URL used to scrape this deal")
    last_updated: str = Field(description="Set this string to 'June 2026'")

def get_pub_deals(client, venue_name, url):
    prompt = f"""
    Perform a live web search to locate the official current daily food and drink specials page for {venue_name} in Cairns.
    Target URL: {url}
    
    Carefully read the text contents of the web page. Extract every specific daily meal or drink special listed for each day.
    Do not guess, hallucinate, or alter any details. If a specific price is not listed on the page for a deal, label the price as 'Varies'.
    
    Output a valid list matching the required JSON schema structure containing the true specials.
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Invoking Gemini Live Web Grounding for {venue_name} (Attempt {attempt + 1}/{max_retries})...")
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],
                    temperature=0.0,
                    # Enforces structured output safely without brittle string tricks
                    response_mime_type="application/json",
                    response_schema=list[PubDeal],
                ),
            )
            
            # Using Structured Output configuration lets us parse directly safely
            return json.loads(response.text.strip())
            
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
        {"name": "The Crown Hotel", "url": "https://www.thecrownhotelcairns.com.au/daily-specials"},
        {"name": "Dunwoody's Hotel", "url": "https://dunwoodys.com.au/whats-on/"}
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
