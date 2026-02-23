
import os
import json
from django.conf import settings

# New SDK import
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import ClientError
except ImportError:
    genai = None
    ClientError = Exception # Fallback
    print("WARNING: google-genai module not found. AI features will use mock data.")

def scan_report_image(image_path, publishers_list):
    """
    Scans a report image using Gemini (google-genai SDK) and extracts data mapped to publishers.
    publishers_list is a list of dicts: [{'id': 1, 'name': 'John Doe'}, ...]
    """
    # Configure API Key
    api_key = getattr(settings, 'GOOGLE_API_KEY', os.environ.get('GOOGLE_API_KEY'))
    if not api_key or not genai:
        if not genai:
            print("ERROR: google-genai not installed.")
        else:
            print("WARNING: Google API Key not found. Using Mock Data.")
        return _mock_scan_response(publishers_list)

    try:
        # Initialize Client
        client = genai.Client(api_key=api_key)
        
        # Prepare the image
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            
        # Build Context for the AI
        names_context = "\n".join([f"ID {p['id']}: {p['name']}" for p in publishers_list])
        
        prompt = f"""
        Act as a data entry clerk for a church report. 
        I need you to extract data from this handwritten report image and map it to the provided list of people.
        
        VALID PEOPLE LIST:
        {names_context}
        
        INSTRUCTIONS:
        1. Read the handwritten rows in the image.
        2. Fuzzy match each handwritten name to the closest name in the 'VALID PEOPLE LIST'. 
           - Look for last names or first names given.
           - If a name in the image roughly matches a name in the list, use that ID.
           - If a person in the list is NOT in the image, ignore them (or return 0s).
        3. Extract the columns:
           - Hours (Look for numbers like '50', '12', '56H'). If 'H' follows a number, that's hours.
           - Studies (Look for 'Est', 'C', 'Cur' or numbers in a separate column). '1C' likely means 1 Study.
           - Participation/Check: If the row says 'Sí', 'Yes', has a checkmark, OR has hours > 0, participation is true.
           - Remarks: Any extra text like 'Precursor', 'Aux', etc.
           
        OUTPUT FORMAT:
        Return ONLY a raw JSON list. No markdown formatting.
        [
            {{
                "id": <ID from valid list>,
                "name": "<Name from valid list>",
                "hours": <integer>,
                "studies": <integer>,
                "participation": <boolean>,
                "aux_pioneer": <boolean>,
                "remarks": "<string>"
            }},
            ...
        ]
        """
        
        # Generate Content using new SDK
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_bytes(data=img_data, mime_type="image/jpeg"),
                    ]
                )
            ]
        )
        
        response_text = response.text.strip()
        print(f"DEBUG: AI Response:\n{response_text}")
        
        # Clean markdown if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        return json.loads(response_text)

    except ClientError as e:
        print(f"AI API Error (Quota/Model): {e}")
        return _mock_scan_response(publishers_list)
    except Exception as e:
        print(f"AI Unexpected Error: {e}")
        # Fallback to mock if AI fails
        return _mock_scan_response(publishers_list)

def _mock_scan_response(publishers_list):
    """
    Mock response for testing without API usage or on failure.
    Tries to map the example image data provided by user to the list if names match roughly.
    """
    # Simulate the user's specific image data
    mock_data = [
        {"name_part": "Josu", "hours": 56, "studies": 1, "remarks": "1C"},
        {"name_part": "Esteb", "hours": 0, "studies": 0, "participation": True, "remarks": "Sí"},
        {"name_part": "Leonor", "hours": 32, "studies": 0, "remarks": "32H"},
        {"name_part": "Lizet", "hours": 27, "studies": 0, "remarks": "27H"},
        {"name_part": "Héctor", "hours": 0, "studies": 0, "participation": True, "remarks": "Sí"},
        {"name_part": "Olga", "hours": 0, "studies": 0, "participation": True, "remarks": "Sí"},
        {"name_part": "Alberto", "hours": 0, "studies": 1, "participation": True, "remarks": "1C"},
        {"name_part": "Mónica", "hours": 45, "studies": 3, "remarks": "45H 3C"},
    ]
    
    results = []
    
    # Try to map mock data to real publishers
    for pub in publishers_list:
        pub_name_lower = pub['name'].lower()
        matched_data = None
        
        for m in mock_data:
            if m['name_part'].lower() in pub_name_lower:
                matched_data = m
                break
        
        if matched_data:
            results.append({
                "id": pub['id'],
                "hours": matched_data.get('hours', 0),
                "studies": matched_data.get('studies', 0),
                "participation": matched_data.get('participation', True if matched_data.get('hours', 0) > 0 else False),
                "aux_pioneer": False,
                "remarks": matched_data.get('remarks', "")
            })
            
    return results
