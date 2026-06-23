import os
import json
import google.generativeai as genai

# Initialize Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

all_scraped_deals = []

try:
    # Use Gemini's search capabilities to find the data instead of manual requests
    prompt = """
    Search the live web for the current weekly food and drink specials at 'The Crown Hotel' on Shields St in Cairns. 
    Find their daily deals like Steak nights, Parmy nights, or Happy Hours.

    Return ONLY a raw, valid JSON array matching this exact schema. Do not wrap it in markdown code blocks or add any text.
    [
      {
        "pub": "The Crown Hotel",
        "location": "Cairns City",
        "day": "Monday/Tuesday/Wednesday/Thursday/Friday/Saturday/Sunday/Everyday",
        "deal": "Clean text details of what the meal deal includes",
        "price": "Include explicit dollar amount if stated, e.g. $15, otherwise leave blank",
        "url": "https://www.thecrownhotelcairns.com.au/daily-specials",
        "last_updated": "Weekly Feed"
      }
    ]
    """

    print("Requesting Gemini to search the web...")
    ai_response = model.generate_content(
        prompt,
        tools='google_search_retrieval'
    )
    
    cleaned_json_text = ai_response.text.strip().replace('```json', '').replace('```', '')
    venue_deals = json.loads(cleaned_json_text)
    all_scraped_deals.extend(venue_deals)
    print("Successfully retrieved deals using Gemini Grounding!")

except Exception as e:
    print(f"Error executing Gemini Search: {e}")

# Save output data to the public directory for Vercel deployment
os.makedirs('public', exist_ok=True)
with open('public/deals.json', 'w') as f:
    json.dump(all_scraped_deals, f, indent=2)

print("Workflow complete! public/deals.json updated.")
