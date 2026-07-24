"""
File: server/services/flashcard_generator.py
Description: Passes reading text into Groq cloud AI models and reads the reply.
"""

import json

try:
    from .groq_client import query_groq_ai
except ImportError:
    from groq_client import query_groq_ai

def generate_flashcards(text):
    """
    Asks the Groq cloud model to read textbook text and distill it into structural list data.
    """
    # Safety checker: Stop execution early if our extraction string is empty space
    if not text.strip():
        return []
    
    # Instruct the chatbot to act like a strict code engine rather than an emotional assistant
    system_instructions = (
        "You are an expert academic tutor. Your job is to read the provided text "
        "and extract the most important definitions, concepts, or formulas to make flashcards.\n\n" 
        "CRITICAL RULE: You must reply ONLY with a valid JSON array of objects. "
        "Each object must use exactly these keys: 'front' and 'back'. Do not include any extra conversational text.\n" 
        "Example:\n"
        "[\n"
        "  {\"front\": \"Question/Term\", \"back\": \"Answer/Definition\"}\n"
        "]"
    )

    # Package our template directives and scraped textbook string into a single message packet
    full_prompt = f"{system_instructions}\n\nStudy Material Text:\n{text}"

    try:
        # Transmit prompt over web sockets to our Groq hardware api wrapper
        ai_raw_response = query_groq_ai(full_prompt)

        # Catch instances where network firewalls or rate limits return error alerts
        if "Error" in ai_raw_response:
            return []
        
        # json.loads converts a static text string looking like a list back into a real python list array
        flashcards_list = json.loads(ai_raw_response)
        return flashcards_list
    
    except Exception as error:
        # Catches JSON formatting errors safely without crashing the backend system
        print(f"Failed to generate or parse flashcards: {str(error)}")
        return []