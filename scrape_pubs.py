import os
import json
from google import genai
from google.genai import types

try:
    # Initialize the modern Gemini Client
    client = genai.Client()
    
    # Simple, direct prompt asking for raw JSON matching your exact array structure
    prompt = (
        "Search the web for the current daily food and drink specials listed on the official website "
        "of The Crown Hotel on Shields St in Cairns. Extract the actual meal and price for each day. "
        "Return ONLY a valid, raw JSON array mapping exactly to this schema structure with no markdown decoration or extra text: "
        '[{"pub": "The Crown Hotel", "location": "Cairns City", "day": "Monday", "deal": "Steak Night", "price": "$18", "url": "https://www.thecrownhotelcairns.com.au/daily-specials", "last_updated": "Weekly Feed"}]'
    )
    
    print('Invoking Gemini Live Web Grounding...')
    
    # Call Gemini 2.5 Flash with search active and temperature 0.0 for deterministic truth
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.0,
        ),
    )
    
    # Clean up standard Markdown code blocks if the model wraps them
    raw_text = response.text.strip()
    cleaned = raw_text.replace('```json', '').replace('```', '').strip()
    
    # Parse the verified JSON string
    data = json.loads(cleaned)
    
    # Save directly to the public directory for Vercel
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(data, f, indent=2)
        
    print('Successfully updated public/deals.json!')

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
