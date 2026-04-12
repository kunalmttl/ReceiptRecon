# ==============================================================================
# brand_defense_ai/app/main.py
#
# Flask API service for AI-powered return fraud detection. This service
# uses a multi-stage inspection protocol to analyze product images and
# identify common return fraud techniques.
#
# Author: [Your Name/Team Name]
# Version: 1.0.0 (Refactored for Performance and Robustness)
# ==============================================================================

import os
import json
import base64
import requests
import uuid
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- SETUP AND CONFIGURATION ---

# Load environment variables from the .env file in the project root.
load_dotenv()
app = Flask(__name__)

# Build robust, absolute paths to prevent FileNotFoundError. This code works
# regardless of where the script is executed from.
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir) # Go up one level from /app to /ai_service

# Configure API constants from environment variables.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": os.getenv("YOUR_SITE_URL"),
    "X-Title": os.getenv("YOUR_SITE_NAME"),
}
AI_MODEL_NAME = "google/gemini-2.0-flash-exp:free"

# Load the "Ground Truth" database on startup.
brand_info_path = os.path.join(base_dir, 'reference_data', 'brand_info.json')
try:
    with open(brand_info_path, 'r', encoding='utf-8') as f:
        brand_database = json.load(f)
except FileNotFoundError:
    print(f"FATAL ERROR: brand_info.json not found at {brand_info_path}")
    exit(1)


# --- UTILITY AND CORE API FUNCTIONS ---

def encode_image(image_bytes: bytes) -> str:
    """Encodes raw image bytes into a base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')

def call_vlm_expert(prompt: str, image_parts: list) -> dict:
    """
    Acts as the central communication hub with the AI model.
    Constructs the request payload and sends it to the OpenRouter API.
    """
    data = {
        "model": AI_MODEL_NAME,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] + image_parts}],
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data, timeout=90)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        content_str = response.json()['choices'][0]['message']['content']
        
        # Robustly clean markdown fences from the AI's response before parsing.
        if content_str.startswith("```json"):
            content_str = content_str[7:-3].strip()
        elif content_str.startswith("```"):
            content_str = content_str[3:-3].strip()
            
        return json.loads(content_str)
        
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return {"error": "AI API request failed", "details": str(e)}
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"API Response Parsing Error: {e}")
        return {"error": "Failed to parse AI response", "details": str(e)}


# ==============================================================================
# --- STAGE 1: BRANDING VERIFICATION ---
# ==============================================================================
def execute_branding_check(branding_image_b64: str, brand_info: dict) -> dict:
    """
    Verifies the product's branding and logo.
    Targets "Switcheroo" and knockoff fraud by comparing to official references.
    Passes if EITHER the visual logo OR the extracted text matches.
    """
    logo_path = os.path.join(base_dir, brand_info["reference_logo_path"])
    with open(logo_path, "rb") as f:
        ref_logo_b64 = encode_image(f.read())

    prompt = (
        "You are a Brand Logo Authenticator. Your task is to verify a product's branding from a user's real-world photo (Image 1) "
        "against a clean, official reference logo (Image 2). Your judgment must be precise.\n\n"
        "**Instructions:**\n"
        "1. **Analyze Visuals:** Critically compare the core design elements of the logo symbol in Image 1 to Image 2. "
        "Focus ONLY on the geometric shape, proportions, and alignment. IGNORE differences in color, backgrounds, and lighting.\n"
        "2. **Analyze Text:** Perform OCR on Image 1 to find any text. It is acceptable if no text is found.\n"
        "3. **Return JSON:** Provide your findings STRICTLY as a JSON object with keys: "
        "'visual_match' (boolean: true if the core logo SHAPE is identical) and "
        "'extracted_text' (string: the text found, or an empty string)."
    )
    
    image_parts = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{branding_image_b64}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref_logo_b64}"}}
    ]
    
    analysis = call_vlm_expert(prompt, image_parts)
    if "error" in analysis:
        return {"passed": False, "reason": "AI service failed during branding check.", "details": analysis}

    found_text = analysis.get("extracted_text", "")
    visual_match_passed = analysis.get("visual_match", False)
    text_match_passed = any(b.lower() in found_text.lower() for b in brand_info["brand_text"])
    
    passed = visual_match_passed or text_match_passed

    reason = "Branding authentication passed."
    if not passed: reason = "Branding does not match official references. Suspected knockoff or wrong item."
    elif visual_match_passed and not text_match_passed: reason = "Visual logo matched, no text found. Passed based on symbol."
    elif not visual_match_passed and text_match_passed: reason = "Brand text matched, but visual logo differs. Passed based on text."

    return {
        "passed": passed,
        "reason": reason,
        "details": {"text_check_passed": text_match_passed, "visual_check_passed": visual_match_passed, "found_text": found_text}
    }


# ==============================================================================
# --- STAGE 2: CONDITION VERIFICATION (MULTITHREADED) ---
# ==============================================================================

def inspect_single_angle(img_b64: str, index: int, brand_info: dict) -> tuple:
    """Helper function that inspects a single image for the condition check."""
    prompt = (
        f"You are a Quality Control Inspector reviewing one angle of a returned '{brand_info['product_name']}'. "
        f"A new item is described as: '{brand_info['pristine_description']}'. "
        "Analyze THIS photo for any signs of use: scratches, stains, scuffs, dirt, or damage. "
        "Respond in JSON with keys: 'assessed_condition' ('NEW' or 'USED') and 'condition_notes' (string)."
    )
    image_parts = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]
    analysis = call_vlm_expert(prompt, image_parts)

    if "error" in analysis:
        return (False, f"Angle {index+1}: AI inspection failed.", "ERROR")
    
    condition = analysis.get("assessed_condition", "USED")
    notes = analysis.get("condition_notes", "No specific notes provided.")
    return (condition == "NEW", f"Angle {index+1}: {notes} (Verdict: {condition})", condition)

def execute_condition_check(condition_images_b64: list, brand_info: dict) -> dict:
    """
    Analyzes multiple images of the product's physical condition in parallel.
    Targets "Wardrobing" (rental fraud) and returning used or damaged items.
    """
    individual_results = []
    overall_passed = True
    max_threads = min(4, len(condition_images_b64)) # Use up to 4 threads

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Submit all jobs to the thread pool
        future_to_index = {executor.submit(inspect_single_angle, img, i, brand_info): i for i, img in enumerate(condition_images_b64)}
        
        for future in as_completed(future_to_index):
            try:
                passed, note, status = future.result()
                if not passed: overall_passed = False
                individual_results.append(note)
            except Exception as exc:
                print(f"A condition check thread generated an exception: {exc}")
                overall_passed = False
                individual_results.append(f"Angle check failed: {exc}")
    
    final_reason = "Product condition is consistent with a new item across all angles."
    if not overall_passed: final_reason = "Product failed inspection. Signs of use or damage detected in one or more views."
    
    return {
        "passed": overall_passed,
        "reason": final_reason,
        "details": {"inspected_angles": len(condition_images_b64), "inspection_notes": sorted(individual_results)}
    }


# ==============================================================================
# --- STAGE 3: CONTENTS VERIFICATION ---
# ==============================================================================
def execute_contents_check(contents_image_b64: str, brand_info: dict) -> dict:
    """
    Verifies all expected items and accessories are present in the box.
    Targets "Brick-in-a-Box", "Component Stripping", and missing parts fraud.
    """
    accessory_list = ", ".join(brand_info["expected_accessories"])
    prompt = (
        f"You are an Inventory Inspector verifying package contents for a '{brand_info['product_name']}'. "
        f"The package MUST contain the main product AND all of the following accessories: {accessory_list}. "
        "Analyze the user's photo. Confirm the presence of each required item. "
        "Respond in JSON with boolean keys: 'main_product_present' and 'all_accessories_present'."
    )
    image_parts = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{contents_image_b64}"}}]
    analysis = call_vlm_expert(prompt, image_parts)

    if "error" in analysis:
        return {"passed": False, "reason": "AI service failed during contents check.", "details": analysis}

    product_ok = analysis.get("main_product_present", False)
    accessories_ok = analysis.get("all_accessories_present", False)
    passed = product_ok and accessories_ok

    reason = "All items and accessories are present."
    if not passed:
        reasons = []
        if not product_ok: reasons.append("Main product appears to be missing.")
        if not accessories_ok: reasons.append("One or more required accessories are missing.")
        reason = " ".join(reasons)

    return {
        "passed": passed,
        "reason": reason,
        "details": {"main_product_present": product_ok, "accessories_present": accessories_ok}
    }


# ==============================================================================
# --- MAIN FLASK API ENDPOINT ---
# ==============================================================================
@app.route("/full-inspection", methods=["POST"])
def full_inspection_endpoint():
    """
    Orchestrates the full 3-stage return inspection from a single API call.
    Expects the SKU and all 6 required base64-encoded images.
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

    # --- Aggregate final result ---
    overall_passed = branding_result['passed'] and condition_result['passed'] and contents_result['passed']
    
    final_report = {
        "inspection_id": str(uuid.uuid4()),
        "sku_inspected": sku,
        "overall_passed": overall_passed,
        "stages": {
            "branding_verification": branding_result,
            "condition_verification": condition_result,
            "contents_verification": contents_result
        }
    }
    
    return jsonify(final_report)


# ==============================================================================
# --- STANDALONE TEST RUNNER FOR LOCAL DEVELOPMENT ---
# ==============================================================================
def run_standalone_test():
    """
    Simulates a full API call by loading all test images from a product folder.
    This allows for rapid, local testing without needing an HTTP client.
    """
    print("--- Running Full Standalone Inspection Test Suite ---")
    sku_to_test = "SKU_HELMET_YAM"
    test_product_dir = os.path.join(base_dir, 'test_images', 'prod1')

    def load_image_b64(filename):
        path = os.path.join(test_product_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required test image not found: {path}")
        with open(path, "rb") as f:
            return encode_image(f.read())

    try:
        # Load test images from the specified product test folder.
        brand_info = brand_database[sku_to_test]
        branding_img = load_image_b64("1_branding.jpg")
        condition_imgs = [
            load_image_b64("2a_condition_front.jpg"),
            load_image_b64("2b_condition_side.jpg"),
            load_image_b64("2c_condition_back.jpg"),
            load_image_b64("2d_condition_top.jpg")
        ]
        contents_img = load_image_b64("3_contents.jpg")
        
        # --- Execute each check and print the result ---
        print("\n[1] Executing Branding Check...")
        print(json.dumps(execute_branding_check(branding_img, brand_info), indent=2))

        print("\n[2] Executing Condition Check...")
        print(json.dumps(execute_condition_check(condition_imgs, brand_info), indent=2))
        
        print("\n[3] Executing Contents Check...")
        print(json.dumps(execute_contents_check(contents_img, brand_info), indent=2))

        print("\n--- TEST SUITE COMPLETE ---")

    except FileNotFoundError as e:
        print(f"\n❌ TEST SETUP ERROR: {e}")
    except Exception as e:
        print(f"\n🔥 An unexpected error occurred during the test: {e}")


# ==============================================================================
# --- APPLICATION ENTRY POINT ---
# ==============================================================================
if __name__ == '__main__':
    # Use this to test the logic locally. It requires the 'test_images/prod1/' folder
    # to be set up with all 6 required images.
    # run_standalone_test()
    
    # Use this to run the actual Flask web server for the Node.js backend to call.
    app.run(host='0.0.0.0', port=5002, debug=False)