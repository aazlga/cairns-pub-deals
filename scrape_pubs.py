import os
import json
from google import genai
from google.genai import types

try:
    # The new client automatically picks up GEMINI_API_KEY from os.environ
    client = genai.Client()
    
  prompt = (
        "Search the web for the exact current daily food specials listed on the official website for The Crown Hotel in Cairns (https://www.thecrownhotelcairns.com.au/daily-specials). "
        "Extract the actual meal and price for each day of the week from the text. Do not make up or guess any prices. "
        "Return ONLY a valid, raw JSON array mapping exactly to this schema structure with no markdown decoration, no ```json tags, and no extra text: "
        '[{"pub": "The Crown Hotel", "location": "Cairns City", "day": "Monday", "deal": "Actual Deal Text Here", "price": "$Actual Price", "url": "[https://www.thecrownhotelcairns.com.au/daily-specials](https://www.thecrownhotelcairns.com.au/daily-specials)", "last_updated": "June 2026"}]'
    )
    
    print('Invoking Gemini Live Web Grounding...')
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.0,  # Forces deterministic, accurate output from the search results
        ),
    )
    
    # Clean up any accidental markdown code blocks if the model includes them
    cleaned = response.text.strip().replace('```json', '').replace('```', '')
    data = json.loads(cleaned)
    
    # Ensure directory exists and save
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(data, f, indent=2)
        
    print('Successfully updated public/deals.json!')

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
