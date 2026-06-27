import os
import json
import time
import re
import urllib.request
import urllib.error
from google import genai
from google.genai import types

def extract_json_array_string(text):
    """
    Locates the first '[' and last ']' to safely isolate the JSON array block,
    discarding any markdown formatting tags or conversational text.
    """
    text = text.strip()
    start_idx = text.find('[')
    end_idx = text.rfind(']')
    
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        return text[start_idx:end_idx + 1]
    raise ValueError("No JSON array found in the model's response text.")

def clean_target_url(url):
    """
    Saves the scraper from breaking if Markdown URLs like [URL](URL) slip in.
    Extracts the clean, plain URL string.
    """
    match = re.search(r'https?://[^\s\)]+', url)
    if match:
        return match.group(0).strip()
    return url.strip()

def clean_html(html_content):
    """
    Strips script tags, style tags, and HTML tags to produce clean, 
    highly dense webpage text for Gemini to parse.
    """
    # Remove scripts and style blocks
    html_content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html_content, flags=re.I)
    html_content = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html_content, flags=re.I)
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Consolidate whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_webpage_text(url):
    """
    Attempts to fetch the raw webpage and return clean text content.
    Returns None if blocked or failed.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        req = urllib.request.Request
