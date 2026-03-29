const supabase = require('../config/db');
const axios = require('axios'); 
const { v4: uuidv4 } = require('uuid');


// --- CONTROLLER TO GET USER'S ORDER HISTORY ---

const getMyOrders = async (req, res) => 
{
  try 
  {
    const { data: orders, error } = await supabase
      .from('orders')
      .select(`
        *,
        order_items (
          *,
          products (*)
        )
      `)
      .eq('user_id', req.user.id);

    if (error) throw error;
    res.json(orders);
  } 
  catch (error) 
  {
    console.error(`Error in getMyOrders: ${error.message}`);
    res.status(500).json({ message: 'Server Error fetching orders.' });
  }
};



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
    
    const { data: orderItem, error: fetchError } = await supabase
      .from('order_items')
      .select(`
        *,
        orders (id, user_id, purchase_date),
        products (id, name, sku)
      `)
      .eq('id', itemId)
      .eq('order_id', orderId)
      .single();

    if (fetchError || !orderItem) {
      return res.status(404).json({ message: 'Order item not found in the specified order' });
    }

    // Check ownership
    if (orderItem.orders.user_id !== req.user.id) {
       return res.status(403).json({ message: 'You are not authorized to return this item' });
    }
    
    // Check if the item has already been returned
    if (orderItem.return_status && orderItem.return_status !== 'NONE') 
    {
      return res.status(400).json({ success: false, message: 'A return has already been processed for this item.' });
    }

    // Perform the 90-day return window check
    const purchaseDate = new Date(orderItem.orders.purchase_date);
    const currentDate = new Date();
    const ninetyDaysInMs = 90 * 24 * 60 * 60 * 1000;
    if (currentDate - purchaseDate > ninetyDaysInMs) {
      return res.status(403).json({ success: false, message: 'This item is outside the 90-day return window.' });
    }

    // --- 3. ORCHESTRATE THE AI INSPECTION ---

    console.log(`Starting AI inspection for SKU: ${orderItem.products.sku}...`);

    // Prepare the payload for our AI service's `/full-inspection` endpoint
    const aiPayload = 
    {
        sku: orderItem.products.sku, // Use the stable SKU for the AI service
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

      const { error: updateError } = await supabase
        .from('order_items')
        .update({
          return_status: 'APPROVED',
          return_reason: reason,
          inspection_notes: "AI inspection passed all stages.",
          return_initiated_at: new Date(),
          return_id: returnId
        })
        .eq('id', itemId);
      
      if (updateError) throw updateError;
      
      console.log(`Return APPROVED for SKU: ${orderItem.products.sku}`);
      
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

      const { error: updateError } = await supabase
        .from('order_items')
        .update({
          return_status: 'REJECTED',
          return_reason: reason,
          inspection_notes: `AI Rejected: ${rejectionReason}`,
          return_initiated_at: new Date()
        })
        .eq('id', itemId);

      if (updateError) throw updateError;

      console.log(`Return REJECTED for SKU: ${orderItem.products.sku}. Reason: ${rejectionReason}`);

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