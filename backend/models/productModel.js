const mongoose = require('mongoose');


const productSchema = mongoose.Schema(
{
        // naam, photo, price, barcode

        name: { type: String, required: true },
        imageUrl: { type: String, required: true },
        price: { type: Number, required: true },
        sku: { type: String, required: true, unique: true },
});


module.exports = mongoose.model('Product', productSchema);

