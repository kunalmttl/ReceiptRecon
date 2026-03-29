const mongoose = require('mongoose');
require('./productModel');


const returnInfoSchema = mongoose.Schema(
{
        // return status, return reason, time initiated, unique id for qr code

        status: 
        {
                type: String,
                enum: ['NONE', 'PENDING', 'APPROVED', 'REJECTED'],
                default: 'NONE',
        },
        reason: { type: String },
        returnInitiatedAt: { type: Date },
        returnId: { type: String },
});

const purchasedItemSchema = mongoose.Schema(
{
        product: 
        {
                type: mongoose.Schema.Types.ObjectId,
                required: true,
                ref: 'Product', // Links to the Product model
        },
        quantity: { type: Number, required: true, default: 1 },
        priceAtPurchase: { type: Number, required: true },
        returnInfo: { type: returnInfoSchema, default: () => ({}) },
});

const orderSchema = mongoose.Schema(
  {
        // order = product list + customer + time of purchase
    user: 
    {
        type: mongoose.Schema.Types.ObjectId,
        required: true,
        ref: 'User',
    },
    purchasedItems: [purchasedItemSchema],
    purchaseDate: 
    {
      type: Date,
      default: Date.now,
    },
  },
  { timestamps: true }
);


module.exports = mongoose.model('Order', orderSchema);
