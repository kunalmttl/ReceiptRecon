const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');
const supabase = require('./config/db');
const orderRoutes = require('./routes/orderRoutes'); 

dotenv.config();

const app = express();


// --- MIDDLEWARE SETUP ---
app.use(cors({
  origin: process.env.FRONTEND_URL || '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-user-id']
}));
app.use(express.json({ limit: '10mb' })); // Body parser for JSON

// --- API ROUTES ---
app.use('/api/orders', orderRoutes); 

// --- TEST ROUTE FOR ROOT URL ---
app.get('/', (req, res) => {
  res.send('Receipt Recon API is running...');
});

// Health check for wait-on
app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});


const PORT = process.env.PORT || 5001;

app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));