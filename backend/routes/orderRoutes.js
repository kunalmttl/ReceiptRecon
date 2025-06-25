const express = require('express');
const router = express.Router();
const { getMyOrders, initiateReturn } = require('../controllers/orderController');
const { protect } = require('../middleware/authMiddleware'); 


// @desc   Fetch all orders for a logged-in user
// @route  GET /api/orders
router.route('/').get(protect, getMyOrders);


// @desc   Initiate a return for a specific item in an order
// @route  POST /api/orders/:orderId/items/:itemId/return
router.route('/:orderId/items/:itemId/return').post(protect, initiateReturn);

module.exports = router;