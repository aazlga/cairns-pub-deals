import os
import json
from google import genai
from google.genai import types

try:
    # Initialize the modern Gemini Client (automatically pulls GEMINI_API_KEY from environment)
    client = genai.Client()
    
    # We describe the target structure directly in the prompt since we cannot use a response_schema with search
    prompt = (
        "Search the web for the exact daily food and drink specials currently listed on the official website "
        "of The Crown Hotel in Cairns (https://www.thecrownhotelcairns.com.au/daily-specials). "
        "Extract the real, actual meal and price for each day of the week. "
        "Do not make up, extrapolate, or guess any prices or items. "
        "Return ONLY a valid, raw JSON array mapping exactly to this schema structure with no conversational text: "
        '[\n'
        '  {\n'
        '    "pub": "The Crown Hotel",\n'
        '    "location": "Cairns City",\n'
        '    "day": "Monday",\n'
        '    "deal": "Actual Deal Text Here",\n'
        '    "price": "$Actual Price Here",\n'
        '    "url": "https://www.thecrownhotelcairns.com.au/daily-specials",\n'
        '    "last_updated": "June 2026"\n'
        '  }\n'
        ']'
    )
    
    print('Invoking Gemini Live Web Grounding...')
    
    # Call Gemini 2.5 Flash with search active, but without the restricted JSON format schema
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.0,
        ),
    )
    
    # Robustly isolate and extract the JSON array from the response text
    raw_text = response.text.strip()
    
    # Handle standard Markdown code block encapsulation if the model provides it
    if "```" in raw_text:
        parts = raw_text.split("```")
        cleaned_text = ""
        for part in parts:
            part_stripped = part.strip()
            if part_stripped.startswith("json"):
                cleaned_text = part_stripped[4:].strip()
                break
            elif part_stripped.startswith("[") or part_stripped.startswith("{"):
                cleaned_text = part_stripped
                break
        if not cleaned_text:
            cleaned_text = parts[1].strip() if len(parts) > 1 else raw_text
    else:
        cleaned_text = raw_text

    # Parse the text to verify it's valid JSON
    data = json.loads(cleaned_text)
    
    # Output the structured data to your public folder for Vercel deployment
    os.makedirs('public', exist_ok=True)
    with open('public/deals.json', 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Successfully scraped and updated {len(data)} real specials in public/deals.json!")

except Exception as e:
    print(f'Failed execution: {e}')
    exit(1)
