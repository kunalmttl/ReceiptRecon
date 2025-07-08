import base64
import os
import json

# ==============================================================================
# Postman Payload Generator for ReceiptRecon
#
# This utility script simulates the payload that the React Native frontend
# sends to the Node.js backend's `/api/orders/.../return` endpoint.
# It gathers 6 test images, encodes them, and structures them into the
# exact format required by the `initiateReturn` controller.
#
# Instructions:
# 1. Place your 6 test images in the `ai_service/test_images/prod1` folder.
# 2. Run this script from the project root (`utils` folder): python generate_payload.py
# 3. Open the generated `postman_full_inspection_payload.json` file.
# 4. Copy the entire contents of that file.
# 5. Paste it into the "Body" -> "raw" (JSON) section of your Postman request.
# ==============================================================================

# --- Configuration ---
# This path is relative to where you RUN the script from (the /utils folder)
TEST_IMAGE_DIR = os.path.join('ai_service', 'test_images', 'prod1')
OUTPUT_FILE = 'postman_full_inspection_payload.json'

# The reason for the return, as entered by the user.
RETURN_REASON = "Item did not fit as expected."
# ---------------------

def encode_image(file_path):
    """Reads an image file and returns its base64 encoded string."""
    try:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"❌ ERROR: Test image not found at '{file_path}'")
        return None

def main():
    """Generates the final JSON payload and writes it to a file."""
    print("--- Generating Postman Request Body for Frontend -> Backend Request ---")
    
    # Define the exact filenames your app expects for a single product test run
    # These must exist inside your TEST_IMAGE_DIR
    image_files = {
        "tagPhoto": ["1_branding.jpg"],
        "photos360": [
            "2a_condition_front.jpg",
            "2b_condition_side.jpg",
            "2c_condition_back.jpg",
            "2d_condition_top.jpg"
        ],
        "accessoryPhotos": ["3_contents.jpg"]
    }
    
    # --- Encode all images and build the nested array structure ---
    try:
        tag_photo_b64 = [encode_image(os.path.join(TEST_IMAGE_DIR, image_files["tagPhoto"][0]))]
        photos360_b64 = [encode_image(os.path.join(TEST_IMAGE_DIR, f)) for f in image_files["photos360"]]
        accessory_photos_b64 = [encode_image(os.path.join(TEST_IMAGE_DIR, image_files["accessoryPhotos"][0]))]
        
        # Check if any image failed to load. The encode_image function returns None on failure.
        # This checks for None in all three lists by concatenating them.
        if any(p is None for p in tag_photo_b64 + photos360_b64 + accessory_photos_b64):
            print("\nAborting: Could not generate payload because one or more required image files were not found.")
            return
    except Exception as e:
        print(f"An error occurred while processing images: {e}")
        return

    # --- Structure the final payload ---
    # This structure exactly matches what your `orderController.js` expects in `req.body`
    payload = {
        "reason": RETURN_REASON,
        "base64_images_encoding": [
            tag_photo_b64,      # This is the [[1]] part
            photos360_b64,      # This is the [[1,2,3,4]] part
            accessory_photos_b64 # This is the final [[1]] part
        ]
    }
    
    # --- Write the payload to the output file ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, OUTPUT_FILE)

    with open(output_path, "w") as out:
        json.dump(payload, out, indent=2)

    print(f"\n✅ Success! Wrote complete payload to '{output_path}'.")
    print("   Open that file, copy its contents, and paste it directly into Postman.")

if __name__ == "__main__":
    main()