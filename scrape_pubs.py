import os
import json
from google import genai
from google.genai import types

try:
    # The new client automatically picks up GEMINI_API_KEY from os.environ
    client = genai.Client()
    
    prompt = (
        "Search the web for the current weekly food and drink specials at The Crown Hotel on Shields St in Cairns. "
        "Return ONLY a valid, raw JSON array mapping to this schema with no markdown decoration or extra text: "
        '[{"pub": "The Crown Hotel", "location": "Cairns City", "day": "Monday", "deal": "Steak Night", "price": "$18", "url": "https://www.thecrownhotelcairns.com.au/daily-specials", "last_updated": "Weekly Feed"}]'
    )
    
    print('Invoking Gemini Live Web Grounding...')
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],  # This turns on live web search
            temperature=0.0
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
