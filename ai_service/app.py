from flask import Flask, request, jsonify

# For the hackathon, we don't need a real AI model yet.
# We will simulate its response. This allows us to test the full flow.

app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    # Get the data from the Node.js backend
    data = request.get_json()
    
    # Print it to the terminal so we can see what we received
    print(f"Received data for prediction: {data}")

    # Check if we got the data we expect
    if not data or 'expected_product_id' not in data or 'image_data' not in data:
        return jsonify({"error": "Missing data"}), 400

    # --- HACKATHON SIMULATION ---
    # In a real project, you would load your TensorFlow model here and
    # classify the image_data. For now, we will just pretend it's always a match.
    # This lets you test the Node.js "happy path".
    is_match = True 
    
    print(f"Prediction result: {'Match' if is_match else 'No Match'}")

    # Send the result back to the Node.js backend
    return jsonify({"match": is_match})


if __name__ == "__main__":
    # This tells Flask to listen on all available network interfaces (0.0.0.0)
    # which includes both 127.0.0.1 (IPv4) and ::1 (IPv6)
    app.run(host='0.0.0.0', port=5000, debug=True)
