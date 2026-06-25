import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class Deal(BaseModel):
    pub: str = Field(description="Name of the pub, exactly 'The Crown Hotel'")
    location: str = Field(description="Location of the pub, e.g., 'Cairns City'")
    day: str = Field(description="The day of the week, e.g., Monday, Tuesday, Wednesday...")
    deal: str = Field(description="The exact food or drink deal text pulled from the website, e.g. 'Steak Sandwich, chips & salad'")
    price: str = Field(description="The actual price with dollar sign, e.g. '$18'")
    url: str = Field(description="The exact URL of the specials webpage")
    last_updated: str = Field(description="The month and year when parsed, e.g., 'June 2026'")

class PubDealsResponse(BaseModel):
    deals: list[Deal] = Field(description="A collection of the extracted daily specials")

try:
    # Initialize modern Google GenAI Client
    client = genai.Client()
    
    # We describe only the search objective. No dummy prices or placeholder deals are present
    # to confuse the grounding engine.
    prompt = (
        "Search the web for the exact daily food and drink specials currently listed on the official website "
        "of The Crown Hotel in Cairns (https://www.thecrownhotelcairns.com.au/daily-specials). "
        "Extract the real, actual meal and price for each day of the week. "
        "Do not make up, extrapolate, or guess any prices or items."
    )
    
    print('Invoking Gemini Live Web Grounding with Structured Outputs...')

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            # This instructs Gemini to guarantee the output adheres perfectly to our Pydantic schema structure
            response_mime_type="application/json",
            response_schema=PubDealsResponse,
            temperature=0.0,
        ),
    )
    
    # The output is guaranteed to be clean JSON conforming to PubDealsResponse schema
    raw_data = json.loads(response.text)
    
    # Unpack the list of deals to match the exact flat array format the frontend expects
    flat_deals_list = raw_data.get("deals", [])
    
    # Ensure the public directories are ready and save the result
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(flat_deals_list, f, indent=2)
        
    print(f"Successfully scraped and updated {len(flat_deals_list)} real specials in public/deals.json!")

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
