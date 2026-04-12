const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');
const orderRoutes = require('./routes/orderRoutes'); 

dotenv.config();

const app = express();

// --- CORS CONFIGURATION ---
// Allows our Vercel frontend and local tools to talk to this Render backend.
app.use(cors({
  origin: '*', // Allow all for now during testing, then lock down
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-user-id']
}));

// --- MIDDLEWARE SETUP ---
app.use(express.json({ limit: '10mb' })); // Body parser for JSON

// --- API ROUTES ---
app.use('/api/orders', orderRoutes); 

// --- TEST ROUTE FOR ROOT URL ---
app.get('/', (req, res) => {
  res.send('Receipt Recon API is running...');
});

// --- HEALTH CHECK FOR WAIT-ON ---
app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});


const PORT = process.env.PORT || 5001;

app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));