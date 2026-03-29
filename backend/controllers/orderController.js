// ==============================================================================
// backend/controllers/orderController.js
//
// Handles order fetching and the multi-stage AI return inspection process.
// Refactored for Supabase (PostgreSQL) and Gemini 2.0 AI Service.
// ==============================================================================

const supabase = require('../config/supabase');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

/**
 * --- CONTROLLER TO GET USER'S ORDER HISTORY ---
 * Fetches orders and their items with product details from Supabase.
 */
const getMyOrders = async (req, res) => {
  try {
    const userId = req.user.id; // From authMiddleware

    // 1. Fetch orders for this user
    const { data: orders, error: ordersError } = await supabase
      .from('orders')
      .select(`
        id,
        purchase_date,
        created_at,
        order_items (
          id,
          quantity,
          price_at_purchase,
          return_status,
          products (
            id,
            name,
            brand,
            price,
            image_url,
            sku
          )
        )
      `)
      .eq('user_id', userId)
      .order('purchase_date', { ascending: false });

    if (ordersError) throw ordersError;

    // 2. Format to match legacy frontend expectations (if needed)
    res.json(orders);
  } catch (error) {
    console.error(`Error in getMyOrders: ${error.message}`);
    res.status(500).json({ message: 'Server Error fetching orders.' });
  }
};

/**
 * --- CORE CONTROLLER FOR THE RETURN PROCESS ---
 * Orchestrates multi-image AI inspection and database status updates.
 */
const initiateReturn = async (req, res) => {
  try {
    const { orderId, itemId } = req.params;
    const { reason, base64_images_encoding } = req.body;

    // 1. Basic Validation
    if (!Array.isArray(base64_images_encoding) || base64_images_encoding.length !== 3) {
      return res.status(400).json({ message: "Invalid image data format. Expected an array of 3 elements." });
    }

    const [tagPhotoArr, photos360Arr, accessoryPhotosArr] = base64_images_encoding;

    // 2. Fetch Order Item and Product details from Supabase
    const { data: orderItem, error: itemError } = await supabase
      .from('order_items')
      .select(`
        id,
        order_id,
        return_status,
        orders ( purchase_date ),
        products ( id, sku, name )
      `)
      .eq('id', itemId)
      .eq('order_id', orderId)
      .single();

    if (itemError || !orderItem) {
      return res.status(404).json({ message: 'Order item not found.' });
    }

    // 3. Return Window Check (90 Days)
    const purchaseDate = new Date(orderItem.orders.purchase_date);
    const currentDate = new Date();
    const ninetyDaysInMs = 90 * 24 * 60 * 60 * 1000;
    
    if (currentDate - purchaseDate > ninetyDaysInMs) {
      return res.status(403).json({ success: false, message: 'This item is outside the 90-day return window.' });
    }

    if (orderItem.return_status !== 'NONE') {
      return res.status(400).json({ success: false, message: 'A return has already been processed for this item.' });
    }

    // 4. Orchestrate AI Inspection
    console.log(`Starting AI inspection for SKU: ${orderItem.products.sku}...`);

    const aiPayload = {
      sku: orderItem.products.sku,
      branding_image_b64: tagPhotoArr[0],
      condition_images_b64: photos360Arr,
      contents_image_b64: accessoryPhotosArr[0],
    };

    const aiResponse = await axios.post(`${process.env.AI_SERVICE_URL}/full-inspection`, aiPayload);
    const { overall_passed, stages } = aiResponse.data;

    // 5. Finalize based on AI decision
    const status = overall_passed ? 'APPROVED' : 'REJECTED';
    const returnId = overall_passed ? uuidv4() : null;
    const inspectionNotes = overall_passed 
      ? "AI inspection passed all stages." 
      : `AI Rejected: ${Object.values(stages).filter(s => !s.passed).map(s => s.reason).join('; ')}`;

    // Update database
    const { error: updateError } = await supabase
      .from('order_items')
      .update({ 
        return_status: status,
        return_id: returnId,
        return_notes: inspectionNotes
      })
      .eq('id', itemId);

    if (updateError) throw updateError;

    if (overall_passed) {
      res.status(200).json({
        success: true,
        message: 'Return Approved. Please show this QR code at the store.',
        qrCodeData: returnId,
        details: stages
      });
    } else {
      res.status(400).json({
        success: false,
        message: `Return Denied. ${inspectionNotes}`,
        details: stages
      });
    }

  } catch (error) {
    console.error("An unexpected error occurred in initiateReturn:", error);
    res.status(500).json({ message: 'Server error during the return process.' });
  }
};

module.exports = { getMyOrders, initiateReturn };