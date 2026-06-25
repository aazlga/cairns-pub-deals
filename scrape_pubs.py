import os
import json
import google.generativeai as genai

# Configure the API key
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

try:
    prompt = (
        "Search the web for the current weekly food and drink specials at The Crown Hotel on Shields St in Cairns. "
        "Return ONLY a valid, raw JSON array mapping to this schema with no markdown decoration or extra text: "
        '[{"pub": "The Crown Hotel", "location": "Cairns City", "day": "Monday", "deal": "Steak Night", "price": "$18", "url": "https://www.thecrownhotelcairns.com.au/daily-specials", "last_updated": "Weekly Feed"}]'
    )
    
    print('Invoking Gemini Live Web Grounding...')
    # Using the correct legacy library tool syntax for web search
    res = model.generate_content(prompt, tools='web_search')
    
    # Clean up any accidental markdown code blocks if the model includes them
    cleaned = res.text.strip().replace('```json', '').replace('```', '')
    data = json.loads(cleaned)
    
    # Ensure directory exists and save
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(data, f, indent=2)
        
    print('Successfully updated public/deals.json!')

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
