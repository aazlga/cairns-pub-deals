prompt = f"""
Analyze the following webpage content from "{venue_name}" and extract any weekly food or drink specials.

Return ONLY a raw, valid JSON array matching this exact schema. Do not wrap it in markdown code blocks.
[
  {{
    "pub": "{venue_name}",
    "location": "Cairns City", 
    "day": "Monday/Tuesday/Wednesday/Thursday/Friday/Saturday/Sunday",
    "deal": "Clean text details of what the meal deal is",
    "price": "Include explicit dollar amount if stated, e.g. $15, otherwise leave blank",
    "url": "{url}",
    "last_updated": "Monday Morning"
  }}
]

Webpage Content:
{clean_text}
"""
