const express = require('express');
const dotenv = require('dotenv');
const orderRoutes = require('./routes/orderRoutes'); 

dotenv.config();

const app = express();

// --- MIDDLEWARE SETUP ---
app.use(express.json({ limit: '10mb' })); // Body parser for JSON

// --- API ROUTES ---
app.use('/api/orders', orderRoutes); 

// --- TEST ROUTE FOR ROOT URL ---
app.get('/', (req, res) => {
  res.send('Receipt Recon API is running...');
});


const PORT = process.env.PORT || 5001;

app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));