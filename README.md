<div align="center">

# 🛡️ ReceiptRecon

### AI-Powered Verification to Eliminate Return Fraud

ReceiptRecon is a sophisticated, full-stack application designed to combat the multi-billion dollar problem of retail return fraud. By leveraging a multi-stage, AI-powered "digital inspection" protocol, our system intelligently verifies product returns in real-time, protecting sellers from scams while providing a fair and transparent process for legitimate customers.
`This Repository is for the backend of the project.`
</div>

---

### 🚀 Project Vision & Teamwork

**The Problem:** Return fraud costs retailers like Walmart over **$100 billion annually**. Scammers have developed numerous techniques—from returning used "wardrobed" items and old-for-new "switcheroos" to missing components and counterfeit products. This erodes trust and creates significant, often unrecoverable, losses for sellers.

**Our Solution:** We engineered ReceiptRecon as a robust defense. Instead of relying on a single photo, our application guides the user through a comprehensive, three-stage digital inspection. This process gathers specific visual evidence for our AI to analyze, creating an irrefutable case for or against the return's legitimacy.

**Team Synergy:** This project was a collaborative effort, mirroring a professional development environment:
*   **Frontend (React Native):** Intuitive, guided camera UI that captures all necessary images seamlessly.
*   **Backend (Node.js):** The orchestration layer, managing business logic, database interactions, and communication between the frontend and AI.
*   **AI Service (Python):** The intelligent core, built to analyze visual data and provide expert judgment on product authenticity and condition.

---

### 🧰 Tech Stack & Architecture

This project is built as a modern microservices architecture to ensure scalability and separation of concerns.

**`Frontend:`**  
<br />
<img align="left" alt="React Native" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/react/react-original.svg"/>
<img align="left" alt="TypeScript" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/typescript/typescript-original.svg"/>
<br />
<br />

**`Backend (Orchestrator):`**  
<br />
<img align="left" alt="Node.js" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/nodejs/nodejs-original-wordmark.svg" />
<img align="left" alt="Express.js" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/express/express-original.svg"/>
<img align="left" alt="Axios" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/axios/axios-plain-wordmark.svg"/>
<br />
<br />

**`AI Service:`**  
<br />
<img align="left" alt="Python" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg"/>
<img align="left" alt="Flask" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/flask/flask-original.svg"/>
<img align="left" alt="Google" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/google/google-original.svg"/>
<br />
<br />

**`Database & Deployment:`**  
<br />
<img align="left" alt="MongoDB" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/mongodb/mongodb-original-wordmark.svg" />
<img align="left" alt="Git" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/git/git-original.svg"/>
<img align="left" alt="GitHub" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/github/github-original.svg"/>
<br />

---

### 🏛️ System Architecture

The system operates as three distinct services communicating via REST APIs:

    [React Native App]
          |
     (1) Sends all 6 images
          v
    [receiptrecon-backend-node]
          |
     (2) Validates & calls AI service
          v
    [receiptrecon-backend-flask]
          |
     (3) Performs 3-stage AI analysis via Google Gemini
          |
     (4) Returns report
          v
    [receiptrecon-backend-node]
          |
     (5) Updates MongoDB Atlas
          v
    [MongoDB Atlas]
          |
     (6) Sends Approve/Reject decision
          v
    [React Native App]


---

### 🛠️ Installation

To get this project running locally, you need to set up the two backend services and the utility scripts.

**Prerequisites:**
*   Node.js (v18 or later)
*   Python (v3.10 or later)
*   Git

**1. Clone the Repository:**
```bash
git clone https://github.com/kunalmttl/ReceiptRecon.git
cd ReceiptRecon
```

**2. Set-up the backend (Node.js):**
```bash
cd backend
npm install

# Create a .env file and add your MongoDB connection string and AI service URL:
# MONGO_URI=your_mongodb_atlas_uri
# AI_SERVICE_URL=http://localhost:5000
```

**3. Set-up the AI service (python):**
```bash
cd ai_service
python -m venv venv
# Activate the virtual environment
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

# Create a .env file and add your OpenRouter key:
# OPENROUTER_API_KEY=your_openrouter_api_key
# YOUR_SITE_URL=http://localhost:3000
# YOUR_SITE_NAME=ReceiptRecon```
```

**4. Set Up the Utility Scripts:**
```bash
cd utils
python -m venv .venv
# Activate the virtual environment
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

---

### 🏃 Usage

This project consists of two separate backend services that must be running in parallel to function correctly. The frontend (React Native) application makes requests *only* to the Node.js backend.

**Terminal 1: Start the AI Service**

Navigate to the `ai_service` directory and run the Flask application. Make sure its dedicated virtual environment is activated first.

```bash
# Navigate to the AI service folder
cd ai_service

# Activate its virtual environment (example for Windows)
.\venv\Scripts\activate

# Run the server
python app/main.py

# The AI service will now be running on http://localhost:5000
```

**Terminal 2: Start the Node.js Backend**

In a new terminal, navigate to the `backend` directory and start the Express server using `nodemon` for live reloading.

```bash
# Navigate to the backend folder
cd backend

# Run the server
nodemon server.js

# The Node.js backend will now be running on http://localhost:5001
```


Your React Native application should be configured to send its API requests to the Node.js backend URL. For production, use the URLs provided by Render for each service.

---

### ✅ Testing

A robust testing workflow is set up to ensure end-to-end reliability without needing a fully built frontend. All testing utility scripts are located in the `/utils` directory.

**1. Populate the Database**

To fill your MongoDB database with a fresh set of realistic test orders and products, run the seeder script. This script will clear the existing `orders` and `products` collections before adding new data.

```bash
# Navigate to the utilities folder
cd utils

# Activate its virtual environment (example for Mac/Linux)
source .venv/bin/activate

# Run the population script
python populate_db.py
```
After running, your MongoDB Atlas cluster will be seeded with 10 orders (8 recent, 2 old).

**2. Generate a Postman Payload**

Our main endpoint requires a complex JSON body with 6 base64-encoded images. The `generate_payload.py` script automates this.

```bash
# Navigate to the utilities folder if you aren't already there
cd utils

# Make sure the venv is active
# Run the payload generator
python generate_payload.py
```
This will create a file named `postman_full_inspection_payload.json` inside the `utils` folder.

**3. Test the Full Inspection Endpoint with Postman**

*   **Method:** `POST`
*   **URL:** `https://receiptrecon-backendnode.onrender.com/api/orders/{orderId}/items/{productId}/return`
    *   *For local testing, use:* `http://localhost:5001/api/orders/{orderId}/items/{productId}/return`
    *   Replace `{orderId}` and `{productId}` with valid IDs from your database.
*   **Headers:**
    *   `Content-Type`: `application/json`
    *   `x-user-id`: `653fb13ec7a3a9b9a647329f` (or another valid user ID)
*   **Body:**
    1.  Open the `postman_full_inspection_payload.json` file.
    2.  Copy its entire contents.
    3.  In Postman, select the `Body` tab, choose `raw`, and set the type to `JSON`.
    4.  Paste the copied JSON into the text area.
    5.  Click "Send".


---

### 📜 License

This project is created for the purpose of the Walmart Sparkathon and is licensed under the **MIT License**.

This means you are free to:
*   **Use:** Use the code for any purpose, including commercial projects.
*   **Modify:** Make changes and adapt it to your needs.
*   **Distribute:** Share the code with others.

The only requirement is that the original copyright and permission notice are included in any substantial portion of the software. For more details, see the `LICENSE` file in the repository.
