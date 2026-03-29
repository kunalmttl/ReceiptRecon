// ==============================================================================
// backend/controllers/orderController.js
//
// Handles order fetching and the multi-stage AI return inspection process.
// This controller acts as the orchestrator between the frontend, the AI
// service, and the database.
// ==============================================================================

const Order = require('../models/orderModel');
const axios = require('axios'); 
const { v4: uuidv4 } = require('uuid');


// --- CONTROLLER TO GET USER'S ORDER HISTORY ---

const getMyOrders = async (req, res) => 
{
  try 
  {
    const orders = await Order.find({ user: req.user.id }).populate('purchasedItems.product');
    res.json(orders);
  } 
  catch (error) 
  {
    console.error(`Error in getMyOrders: ${error.message}`);
    res.status(500).json({ message: 'Server Error fetching orders.' });
  }
};


// ==============================================================================
// --- CORE CONTROLLER FOR THE RETURN PROCESS ---
// ==============================================================================

const initiateReturn = async (req, res) => 
{ 
  try 
  {
    // --- 1. DATA VALIDATION & EXTRACTION ---

    const { orderId, itemId } = req.params; 
    const { reason, base64_images_encoding } = req.body;

    
    // validation
    if (!Array.isArray(base64_images_encoding) || base64_images_encoding.length !== 3) 
    {
      return res.status(400).json({ message: "Invalid image data format. Expected an array of 3 elements." });
    }
    const [tagPhotoArr, photos360Arr, accessoryPhotosArr] = base64_images_encoding;
    if (photos360Arr.length !== 4) 
    {
       return res.status(400).json({ message: "Invalid image data format. Expected 4 condition photos." });
    }
    
    // --- 2. DATABASE VALIDATION (90-DAY CHECK & ITEM CHECK) ---
    
    const order = await Order.findById(orderId);
    if (!order) {
      return res.status(404).json({ message: 'Order not found' });
    }


    // find the *specific* sub-document ID within the `purchasedItems` array for that order.
    const itemToReturn = order.purchasedItems.find(item => item._id.toString() === itemId);

    if (!itemToReturn) 
    {
      return res.status(404).json({ message: 'This specific product was not found in the specified order.' });
    }

    await order.populate('purchasedItems.product');

    
    // Check if the item has already been returned
    if (itemToReturn.returnInfo && itemToReturn.returnInfo.status !== 'NONE') 
    {
      return res.status(400).json({ success: false, message: 'A return has already been processed for this item.' });
    }

    // Perform the 90-day return window check
    const purchaseDate = order.purchaseDate;
    const currentDate = new Date();
    const ninetyDaysInMs = 90 * 24 * 60 * 60 * 1000;
    if (currentDate - purchaseDate > ninetyDaysInMs) {
      return res.status(403).json({ success: false, message: 'This item is outside the 90-day return window.' });
    }

    // --- 3. ORCHESTRATE THE AI INSPECTION ---

    console.log(`Starting AI inspection for SKU: ${itemToReturn.product.sku}...`);

    // Prepare the payload for our AI service's `/full-inspection` endpoint
    const aiPayload = 
    {
        sku: itemToReturn.product.sku, // Use the stable SKU for the AI service
        branding_image_b64: tagPhotoArr[0], // The first image is for branding
        condition_images_b64: photos360Arr, // The array of 4 condition images
        contents_image_b64: accessoryPhotosArr[0], // The final image is for contents
    };
    
    // Call the deployed Python AI service
    const aiResponse = await axios.post(`${process.env.AI_SERVICE_URL}/full-inspection`, aiPayload);
    
    // Extract the final decision and detailed stages from the AI's response
    const { overall_passed, stages } = aiResponse.data;

    // --- 4. FINALIZE THE RETURN BASED ON AI'S DECISION ---
    
    if (overall_passed) {
      // AI check passed! The return is APPROVED.
      const returnId = uuidv4();

      itemToReturn.returnInfo = 
      {
        status: 'APPROVED',
        reason: reason, // The reason the user provided
        inspectionNotes: "AI inspection passed all stages.", // Add a note for reference
        returnInitiatedAt: new Date(),
        returnId: returnId
      };
      
      await order.save(); // Save the updated order status to the database
      
      console.log(`Return APPROVED for SKU: ${itemToReturn.product.sku}`);
      
      res.status(200).json({ 
          success: true, 
          message: 'Return Approved. Please show this QR code at the store.',
          qrCodeData: returnId,
          details: stages // Optionally pass back the full AI report
      });

    } 
    else 
    {
      // AI check failed! The return is REJECTED.
      // We will save the detailed reasons from the AI for auditing purposes.
      const rejectionReason = [
        stages.branding_verification.passed ? null : stages.branding_verification.reason,
        stages.condition_verification.passed ? null : stages.condition_verification.reason,
        stages.contents_verification.passed ? null : stages.contents_verification.reason
      ].filter(Boolean).join('; '); // Join reasons with a semicolon

      itemToReturn.returnInfo = {
        status: 'REJECTED',
        reason: reason,
        inspectionNotes: `AI Rejected: ${rejectionReason}`, // Save the failure reason
        returnInitiatedAt: new Date(),
        returnId: null // No return ID is generated
      };

      await order.save();

      console.log(`Return REJECTED for SKU: ${itemToReturn.product.sku}. Reason: ${rejectionReason}`);

      res.status(400).json({ 
          success: false, 
          message: `Return Denied. ${rejectionReason}`, // Send a clear reason to the frontend
          details: stages // Send the full report for detailed display if needed
      });
    }

  } catch (error) {
    // This is a robust error handler for unexpected crashes.
    console.error("An unexpected error occurred in initiateReturn:", error);
    // If the error came from the axios call, the response might contain more info
    if (error.response) {
      console.error("Error data from AI service:", error.response.data);
    }
    res.status(500).json({ message: 'Server error during the return process. Please try again later.' });
  }
};


module.exports = { getMyOrders, initiateReturn };