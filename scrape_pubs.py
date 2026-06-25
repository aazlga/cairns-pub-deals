import os
import json
from google import genai
from google.genai import types

try:
    # 1. Initialize the modern client
    client = genai.Client()
    
    # 2. Define a clean, direct prompt using simple string concatenation to avoid formatting errors
    prompt = (
        "Search the web for the current daily food and drink specials listed on the official website "
        "of The Crown Hotel on Shields St in Cairns. Extract the actual meal and price for each day. "
        "Return ONLY a valid, raw JSON array mapping exactly to this schema structure with no markdown decoration or extra text: "
        '[{"pub": "The Crown Hotel", "location": "Cairns City", "day": "Monday", "deal": "Steak Night", "price": "$18", "url": "https://www.thecrownhotelcairns.com.au/daily-specials", "last_updated": "Weekly Feed"}]'
    )
    
    print('Invoking Gemini Live Web Grounding...')
    
    # 3. Call the model with live web search enabled
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.0
        ),
    )
    
    # 4. Strip away any potential markdown wrappers safely
    raw_text = response.text.strip()
    cleaned = raw_text.replace('```json', '').replace('```', '').strip()
    
    # 5. Parse and save
    data = json.loads(cleaned)
    
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(data, f, indent=2)
        
    print('Successfully updated public/deals.json!')

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
