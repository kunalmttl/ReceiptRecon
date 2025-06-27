import os
import json
import base64
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv


# --- SETUP AND CONFIGURATION ---
load_dotenv()
app = Flask(__name__)

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)


# Load config from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": os.getenv("YOUR_SITE_URL"),
    "X-Title": os.getenv("YOUR_SITE_NAME"),
}

# Load reference "database"
brand_info_path = os.path.join(base_dir, 'reference_data', 'brand_info.json')
with open(brand_info_path, 'r') as f:
    brand_database = json.load(f)


# Helper function
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# --- Central API Caller ---
def call_gemini_vision(prompt, image_parts):
    data = {
        "model": "google/gemini-2.0-flash-exp:free", # Using the exact model you specified
        "messages": [
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text", 
                        "text": prompt
                    }] + image_parts
            }],
        "response_format": {"type": "json_object"}
    }
    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=data,
            timeout=60 # Add a timeout to prevent hanging indefinitely
        )
        response.raise_for_status()

        raw_response_data = response.json()

        print("--- RAW API RESPONSE FROM OPENROUTER ---")
        print(json.dumps(raw_response_data, indent=2))
        print("----------------------------------------")

        # The content from the API is a JSON string, so we need to parse it twice.
        api_response_str = raw_response_data['choices'][0]['message']['content']
        
        if api_response_str.startswith("```json"):
            api_response_str = api_response_str[7:-3].strip() # Remove ```json and ```
        elif api_response_str.startswith("```"):
             api_response_str = api_response_str[3:-3].strip() # Remove ```

        return json.loads(api_response_str)
    
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenRouter: {e}")

        if e.response:
            print(f"Response Body: {e.response.text}")
        return {"error": str(e), "passed": False}
    
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}")
        print(f"Received non-JSON content from API: '{api_response_str}'")
        return {"error": "Failed to parse AI response", "raw_content": api_response_str, "passed": False}


# --- STAGE 1: BRANDING VERIFICATION ---
def verify_branding(user_image_b64, brand_info):
    logo_path = os.path.join(base_dir, brand_info["reference_logo_path"])

    with open(logo_path, "rb") as f:
        ref_logo_b64 = encode_image(f.read())

    
    prompt = (
        "Act as a brand authenticator. Image 1 is a user's photo. Image 2 is the official logo. "
        "Analyze Image 1 for text and visual elements. Compare it to Image 2. "
        "Respond in JSON with keys: 'extracted_text' (string) and 'visual_match' (boolean)."
    )
    
    image_parts = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{user_image_b64}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref_logo_b64}"}}
    ]
    
    analysis = call_gemini_vision(prompt, image_parts)
    if "error" in analysis: return analysis
    
    text = analysis.get("extracted_text", "")
    visual = analysis.get("visual_match", False)
    text_match = any(b.lower() in text.lower() for b in brand_info["brand_text"])
    
    return {
        "passed": text_match and visual,
        "details": {
            "text_check": {"passed": text_match, "found": text},
            "visual_check": {"passed": visual}
        }
    }

# --- STAGE 2: CONDITION VERIFICATION ---
def verify_condition(user_image_b64, brand_info):
    prompt = (
        f"You are a quality inspector reviewing a '{brand_info['product_name']}'. "
        "The expected new condition is '{brand_info['description']}'. "
        "Analyze the user's photo for signs of use: scratches, stains, dirt, scuffs, or damage. "
        "Respond in JSON with keys: 'assessed_condition' ('NEW' or 'USED') and 'condition_notes' (string describing findings)."
    )
    image_parts = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{user_image_b64}"}}]
    
    analysis = call_gemini_vision(prompt, image_parts)
    if "error" in analysis: return analysis
    
    condition = analysis.get("assessed_condition", "USED")
    return {
        "passed": condition == "NEW",
        "details": {
            "condition": condition,
            "notes": analysis.get("condition_notes", "")
        }
    }

# --- STAGE 3: CONTENTS VERIFICATION ---
def verify_box_contents(user_image_b64, brand_info):
    accessory_list = ", ".join(brand_info["expected_accessories"])
    prompt = (
        f"You are an inventory inspector. For '{brand_info['product_name']}', you expect to see the main product and these accessories: {accessory_list}. "
        "Look at the user's photo showing all items from the box. "
        "Respond in JSON with boolean keys: 'main_product_present' and 'all_accessories_present'."
    )
    image_parts = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{user_image_b64}"}}]
    
    analysis = call_gemini_vision(prompt, image_parts)
    if "error" in analysis: return analysis
    
    product_ok = analysis.get("main_product_present", False)
    accessories_ok = analysis.get("all_accessories_present", False)

    return {
        "passed": product_ok and accessories_ok,
        "details": {
            "main_product_check": {"present": product_ok},
            "accessories_check": {"present": accessories_ok}
        }
    }

# --- THE MAIN FLASK API ENDPOINT ---
@app.route("/inspect", methods=["POST"])
def inspect_endpoint():
    data = request.get_json()
    if not all(k in data for k in ['sku', 'image_b64', 'check_type']):
        return jsonify({"error": "Missing sku, image_b64, or check_type"}), 400
    
    sku, image_b64, check_type = data['sku'], data['image_b64'], data['check_type']
    
    if sku not in brand_database:
        return jsonify({"error": f"SKU not found: {sku}"}), 404
        
    brand_info = brand_database[sku]
    
    result = {}
    if check_type == 'branding':
        result = verify_branding(image_b64, brand_info)
    elif check_type == 'condition':
        result = verify_condition(image_b64, brand_info)
    elif check_type == 'contents':
        result = verify_box_contents(image_b64, brand_info)
    else:
        return jsonify({"error": f"Invalid check_type: {check_type}"}), 400
        
    return jsonify(result)

# --- STANDALONE TEST BLOCK ---
def run_standalone_test():
    """Allows testing one function without starting the server."""
    print("--- Running Standalone Verification Test ---")
    sku_to_test = "SKU_IRON_BD"
    image_to_test = "test_images/pressa.jpg"
    brand_info = brand_database[sku_to_test]
    
    print(f"Testing Stage 1: Branding for {sku_to_test}")
    with open(image_to_test, "rb") as f:
        image_b64 = encode_image(f.read())
    
    brandResult = verify_branding(image_b64, brand_info)
    print(json.dumps(brandResult, indent=2))
    
    condResult = verify_condition(image_b64, brand_info)
    print(json.dumps(condResult, indent=2))
    
    boxResult = verify_box_contents(image_b64, brand_info)
    print(json.dumps(boxResult, indent=2))

if __name__ == '__main__':
    # To test a single function:
    run_standalone_test()
    
    # To run the full web server:
    # app.run(host='0.0.0.0', port=5000, debug=True)