const Order = require('../models/orderModel');
const axios = require('axios'); 
const { v4: uuidv4 } = require('uuid');


// controller to get all orders

const getMyOrders = async (req, res) => {
  try {
    const orders = await Order.find({ user: req.user.id }).populate(
      'purchasedItems.product'
    );
    res.json(orders);
  } catch (error) {
    console.error(`Error in getMyOrders: ${error.message}`);
    res.status(500).json({ message: 'Server Error' });
  }
};


// flowchart

const initiateReturn = async (req, res) => 
{
        // get data from user request 
        
  const { orderId, itemId } = req.params;
  const { reason, image_data } = req.body; 

  try 
  {
    const order = await Order.findById(orderId);

    if (!order) 
    {
      return res.status(404).json({ message: 'Order not found' });
    }

    const itemToReturn = order.purchasedItems.find(item => item._id.toString() === itemId);

    if (!itemToReturn) 
    {
      return res.status(404).json({ message: 'Item not found in this order' });
    }

    // check 90 days limit
    const purchaseDate = order.purchaseDate;
    const currentDate = new Date();
    const ninetyDaysInMs = 90 * 24 * 60 * 60 * 1000; // 90 days in milliseconds

    if (currentDate - purchaseDate > ninetyDaysInMs) 
    {
      // It's past the 90-day limit. Reject the request immediately.
      return res.status(403).json({ // 403 Forbidden is a good status code here
        success: false,
        message: 'This item is outside the 90-day return window.',
      });
    }

    
  // ================================================================
  // HACKATHON/DEVELOPMENT NOTE: AI Service Simulation
  // We are temporarily disabling the real call to the Python service.
  // We will pretend the AI check is always successful.
  // REMEMBER to uncomment this section when the real AI service is ready!
  // ================================================================

  /*
    // Step 1: AI DOES ITS WORKS
    const aiResponse = await axios.post( `${process.env.AI_SERVICE_URL}/predict`,        // The URL of your Python AI service 
    {   
        expected_product_id: itemToReturn.product.toString(),
        image_data: image_data,
    });

    const { match } = aiResponse.data;
    */

    const match = true;

    // Step 2: CHECK IF GOOD PRODUCT
    if (match) 
    {
      // It's a match! Proceed with return logic.
      const returnId = uuidv4(); // Generate a unique ID for the QR code

      // Step 3: SAVE REASON FOR RETURN & GENERATE QR CODE
      itemToReturn.returnInfo = 
      {
        status: 'APPROVED',
        reason: reason,
        returnInitiatedAt: new Date(),
        returnId: returnId
      };
      
      await order.save();
      
      res.status(200).json({ 
          success: true, 
          message: 'Return Approved. Show this QR code at the store.',
          qrCodeData: returnId 
      });

    } else 
    {
      // It's NOT a match ("Not good condition" / fraud attempt)
      itemToReturn.returnInfo.status = 'REJECTED';
      await order.save();

      res.status(400).json(
      { 
          success: false, 
          message: 'Product could not be verified. Please see an associate for help.' 
      });
    }
  } 
  catch (error) 
  {
    console.error(error);
    res.status(500).json({ message: 'Server error during return process' });
  }
};


module.exports = { getMyOrders, initiateReturn };