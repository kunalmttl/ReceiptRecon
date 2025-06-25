const express = require('express');
const dotenv = require('dotenv');
const connectDB = require('./config/db');


dotenv.config();


connectDB();

const app = express();


// test route
app.get('/', (req, res) => 
{
  res.send('Receipt Recon API is running...');
});


const PORT = process.env.PORT || 5001;

app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));