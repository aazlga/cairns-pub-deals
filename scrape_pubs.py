import os
import json
from google import genai
from google.genai import types

try:
    # Initialize the modern Gemini Client
    client = genai.Client()
    
    # Using a single triple-quoted string to avoid indentation and line-wrap bugs
    prompt = """
Search the web for the exact current daily food specials listed on the official website for The Crown Hotel in Cairns (https://www.thecrownhotelcairns.com.au/daily-specials).

Extract the actual meal and price for each day of the week. Do not make up or guess any prices.

Return ONLY a valid, raw JSON array mapping exactly to this schema structure with no markdown decoration, no ```json tags, and no extra text:
[
  {
    "pub": "The Crown Hotel",
    "location": "Cairns City",
    "day": "Monday",
    "deal": "Actual Deal Text Here",
    "price": "$Actual Price Here",
    "url": "[https://www.thecrownhotelcairns.com.au/daily-specials](https://www.thecrownhotelcairns.com.au/daily-specials)",
    "last_updated": "June 2026"
  }
]
"""
    
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
