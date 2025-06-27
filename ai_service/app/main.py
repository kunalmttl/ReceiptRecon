# ==============================================================================
# brand_defense_ai/app/main.py
#
# Flask API service for AI-powered return fraud detection.
# This service accepts multiple images of a returned product and performs
# a three-stage verification using a Vision-Language Model (VLM).
#
# Stages:
# 1. Branding Verification: Checks logo and OCR text against references.
# 2. Condition Analysis: Inspects multiple angles for wear, damage, or use.
# 3. Contents Inspection: Verifies all expected components are present.
# ==============================================================================


import os
import json
import base64
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import uuid

##   --- SETUP AND CONFIGURATION ---


load_dotenv()
app = Flask(__name__)

#* --- Path Configuration: Makes file paths robust and independent of CWD ---

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

#* --- API Configuration for OpenRouter ---

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": os.getenv("YOUR_SITE_URL"),
    "X-Title": os.getenv("YOUR_SITE_NAME"),
}

#* Define the exact model to be used for all calls.

AI_MODEL_NAME = "google/gemini-2.0-flash-exp:free"

#* --- Load Ground Truth Database ---

brand_info_path = os.path.join(base_dir, 'reference_data', 'brand_info.json')
with open(brand_info_path, 'r') as f:
    brand_database = json.load(f)


##      --- UTILITY FUNCTIONS ---


def encode_image(image_bytes: bytes) -> str:
    """Encodes raw image bytes into a base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')

def call_vlm_expert(prompt: str, image_parts: list) -> dict:
    """
    Acts as the central communication hub with the AI model.
    Constructs the request payload and sends it to the OpenRouter API.

    Args:
        prompt: The specific instructions for the AI expert role.
        image_parts: A list of image data formatted for the API.

    Returns:
        A dictionary parsed from the AI's JSON response.
    """
    data = {
        "model": AI_MODEL_NAME,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] + image_parts}],
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data, timeout=90)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        # Robustly clean the response before parsing
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return json.loads(content)
        
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return {"error": "API request failed", "details": str(e)}
    except (json.JSONDecodeError, KeyError) as e:
        print(f"API Response Parsing Error: {e}")
        return {"error": "Failed to parse AI response", "details": str(e)}


## ==============================================================================
##                  --- CORE VERIFICATION LOGIC ---
## ==============================================================================


def execute_branding_check(branding_image_b64: str, brand_info: dict) -> dict:
    """
    Stage 1: Verifies the product's branding and logo.
    Targets "Switcheroo" and knockoff fraud.
    """
    logo_path = os.path.join(base_dir, brand_info["reference_logo_path"])
    with open(logo_path, "rb") as f:
        ref_logo_b64 = encode_image(f.read())

    prompt = (
        "You are a meticulous Brand Authenticator. Your task is to verify a product's branding from a user's photo (Image 1) "
        "against an official reference logo (Image 2). Your analysis must be precise. "
        "First, perform OCR on Image 1 to extract all text. "
        "Second, visually compare the logo's font, style, shape, and alignment in Image 1 against Image 2. "
        "The match must be exact. Any deviation in style or text constitutes a failure. "
        "Return your findings as a JSON object with two keys: 'extracted_text' (string) and 'visual_match' (boolean)."
    )
    
    image_parts = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{branding_image_b64}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref_logo_b64}"}}
    ]
    
    analysis = call_vlm_expert(prompt, image_parts)
    if "error" in analysis: return {"passed": False, "reason": "AI service failed during branding check.", "details": analysis}
    
    text = analysis.get("extracted_text", "")
    visual = analysis.get("visual_match", False)
    text_match = any(b.lower() in text.lower() for b in brand_info["brand_text"])
    
    passed = text_match and visual
    reason = "Branding authentication passed." if passed else "Branding does not match official references. Suspected knockoff or wrong item."

    return {
        "passed": passed,
        "reason": reason,
        "details": 
        {
            "text_check_passed": text_match,
            "visual_check_passed": visual,
            "found_text": text
        }
    }

def execute_condition_check(condition_images_b64: list, brand_info: dict) -> dict:
    """
    Stage 2: Analyzes the product's physical condition from multiple angles.
    Targets "Wardrobing" (rental fraud) and returning used/damaged items.
    """
    prompt = (
        f"You are a strict Quality Control Inspector. You are examining a returned '{brand_info['product_name']}'. "
        f"The only acceptable condition is brand new, described as: '{brand_info['pristine_description']}'. "
        "Analyze the following series of images which show the product from multiple angles. Synthesize your findings across ALL images. "
        "Report any and all signs of use, including but not limited to: scratches, stains, wrinkles, scuffs, dirt, or physical damage. "
        "Based on your complete analysis, conclude if the item's overall condition is 'NEW' or 'USED'. "
        "Return your findings as a JSON object with two keys: 'assessed_condition' ('NEW' or 'USED') and 'condition_notes' (string detailing all flaws found)."
    )

    image_parts = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}} for img_b64 in condition_images_b64]
    
    analysis = call_vlm_expert(prompt, image_parts)
    if "error" in analysis: return {"passed": False, "reason": "AI service failed during condition check.", "details": analysis}

    condition = analysis.get("assessed_condition", "USED")
    passed = condition == "NEW"
    reason = "Product condition is consistent with a new item." if passed else f"Product failed inspection. Signs of use detected: {analysis.get('condition_notes', 'N/A')}"
    
    return 
    {
        "passed": passed,
        "reason": reason,
        "details": 
        {
            "condition": condition,
            "notes": analysis.get("condition_notes", "")
        }
    }

def execute_contents_check(contents_image_b64: str, brand_info: dict) -> dict:
    """
    Stage 3: Verifies all expected items and accessories are present.
    Targets "Brick-in-a-Box", "Component Stripping", and missing parts fraud.
    """
    accessory_list = ", ".join(brand_info["expected_accessories"])
    prompt = (
        f"You are a diligent Inventory Inspector verifying a return package for a '{brand_info['product_name']}'. "
        f"The package must contain the main product itself AND all of the following accessories: {accessory_list}. "
        "Analyze the user's photo showing all items laid out. Confirm the presence of each required item. "
        "Return your findings as a JSON object with two boolean keys: 'main_product_present' and 'all_accessories_present'."
    )
    
    image_parts = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{contents_image_b64}"}}]

    analysis = call_vlm_expert(prompt, image_parts)
    if "error" in analysis: return {"passed": False, "reason": "AI service failed during contents check.", "details": analysis}

    product_ok = analysis.get("main_product_present", False)
    accessories_ok = analysis.get("all_accessories_present", False)
    passed = product_ok and accessories_ok

    reason = "All items and accessories are present."
    if not passed:
        reasons = []
        if not product_ok: reasons.append("Main product is missing.")
        if not accessories_ok: reasons.append("One or more required accessories are missing.")
        reason = " ".join(reasons)

    return {
        "passed": passed,
        "reason": reason,
        "details": {
            "main_product_present": product_ok,
            "accessories_present": accessories_ok
        }
    }


## ==============================================================================
##                       --- MAIN API ENDPOINT ---
## ==============================================================================


@app.route("/full-inspection", methods=["POST"])
def full_inspection_endpoint():
    """
    Orchestrates the full 3-stage return inspection from a single API call.
    Expects a payload with the SKU and all 6 required images.
    """
    data = request.get_json()
    required_keys = ['sku', 'branding_image_b64', 'condition_images_b64', 'contents_image_b64']
    if not all(k in data for k in required_keys):
        return jsonify({"error": "Missing one or more required keys.", "required": required_keys}), 400
        
    sku = data['sku']
    if sku not in brand_database:
        return jsonify({"error": f"SKU '{sku}' not found in reference database."}), 404
    brand_info = brand_database[sku]

    # --- Execute all three verification stages ---
    branding_result = execute_branding_check(data['branding_image_b64'], brand_info)
    condition_result = execute_condition_check(data['condition_images_b64'], brand_info)
    contents_result = execute_contents_check(data['contents_image_b64'], brand_info)

    # --- Aggregate results and make a final decision ---
    overall_passed = branding_result['passed'] and condition_result['passed'] and contents_result['passed']
    
    final_report = {
        "inspection_id": str(uuid.uuid4()), # Generates a standard unique ID
        "sku_inspected": sku,
        "overall_passed": overall_passed,
        "stages": {
            "branding_verification": branding_result,
            "condition_verification": condition_result,
            "contents_verification": contents_result
        }
    }
    
    return jsonify(final_report)




## ==============================================================================
##               --- STANDALONE TEST RUNNER ---
## ==============================================================================



def run_standalone_test():
    """
    Simulates a full API call to the '/full-inspection' endpoint.
    Loads all 6 required images from the test folder for a single product.
    """
    print("--- Running Full Standalone Inspection Test ---")
    sku_to_test = "SKU_IRON_BD"
    
    # Define the directory where test images for one product are stored
    test_product_dir = os.path.join(base_dir, 'test_images', 'prod1')
    
    # Helper to load an image and check for existence
    def load_image_b64(filename):
        path = os.path.join(test_product_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required test image not found: {path}")
        with open(path, "rb") as f:
            return encode_image(f.read())

    try:
        # Prepare the payload just like the frontend would
        payload = {
            "sku": sku_to_test,
            "branding_image_b64": load_image_b64("1_branding.jpg"),
            "condition_images_b64": [
                load_image_b64("2a_condition_front.jpg"),
                load_image_b64("2b_condition_side.jpg"),
                load_image_b64("2c_condition_back.jpg"),
                load_image_b64("2d_condition_top.jpg")
            ],
            "contents_image_b64": load_image_b64("3_contents.jpg")
        }
        
        # Simulate a request to our own endpoint logic for a unified test
        # We can't use `requests` here as the server isn't running in the same thread.
        # So we directly call the functions that the endpoint would call.
        brand_info = brand_database[payload["sku"]]
        
        print("\n[1] Executing Branding Check...")
        branding_res = execute_branding_check(payload["branding_image_b64"], brand_info)
        print(json.dumps(branding_res, indent=2))

        print("\n[2] Executing Condition Check...")
        condition_res = execute_condition_check(payload["condition_images_b64"], brand_info)
        print(json.dumps(condition_res, indent=2))
        
        print("\n[3] Executing Contents Check...")
        contents_res = execute_contents_check(payload["contents_image_b64"], brand_info)
        print(json.dumps(contents_res, indent=2))

        print("\n--- TEST COMPLETE ---")

    except FileNotFoundError as e:
        print(f"\n❌ TEST SETUP ERROR: {e}")
    except Exception as e:
        print(f"\n🔥 An unexpected error occurred during the test: {e}")


if __name__ == '__main__':
    # Use this to test the logic locally without starting a web server.
    # It requires you to create the folder test_images/prod1/ and place 6 images in it.
    run_standalone_test()
    
    # Use this to run the actual web server that the Node.js backend will call.
    # app.run(host='0.0.0.0', port=5000)