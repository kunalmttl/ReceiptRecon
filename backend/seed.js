const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');
const fs = require('fs');
const path = require('path');

dotenv.config({ path: path.join(__dirname, '.env') });

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

// Path to brand_info.json relative to the `backend` folder
const brandInfoPath = path.join(__dirname, '..', 'ai_service', 'reference_data', 'brand_info.json');

async function seed() {
  console.log('🌱 Seeding database with brand data...');

  // 1. Check if brand_info.json exists
  if (!fs.existsSync(brandInfoPath)) {
    console.error(`❌ brand_info.json not found at: ${brandInfoPath}`);
    return;
  }

  const brandInfo = JSON.parse(fs.readFileSync(brandInfoPath, 'utf8'));

  // 2. Prepare test user
  const testUserId = '00000000-0000-0000-0000-000000123456'; 
  
  const { data: profile, error: profileErr } = await supabase
    .from('profiles')
    .upsert({ 
      id: testUserId, 
      name: 'Kunal Test User', 
      email: 'kunal@test.com' 
    })
    .select();

  if (profileErr) {
    console.error('Error seeding profile:', profileErr.message);
  } else {
    console.log('✅ Profile seeded');
  }

  // 3. Prepare products from brand_info.json
  const productsToSeed = [];
  
  // Mapping of category keywords to high-res images for better visuals
  const imgMap = {
    'SAMSUNG': 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&q=80&w=800',
    'NOBERO': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&q=80&w=800',
    'LG': 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&q=80&w=800',
    'BEYOUNG': 'https://images.unsplash.com/photo-1576566582414-74737c356191?auto=format&fit=crop&q=80&w=800',
    'THE NORTH FACE': 'https://images.unsplash.com/photo-1578932750294-f500ad43fddb?auto=format&fit=crop&q=80&w=800',
    'adidas': 'https://images.unsplash.com/photo-1587563871167-1ee9c731aefb?auto=format&fit=crop&q=80&w=800',
    'YAMAHA': 'https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&q=80&w=800'
  };

  const prices = {
    'SKU_SAMSUNG_A73': 499,
    'SKU_NOBERO_TSHIRT': 25,
    'SKU_LG_FRIDGE': 1200,
    'SKU_BEYOUNG_TSHIRT': 20,
    'SKU_TNF_TSHIRT': 45,
    'SKU_ADIDAS_SHOES': 85,
    'SKU_HELMET_YAM': 150
  };

  for (const [sku, details] of Object.entries(brandInfo)) {
    const brand = details.brand_text[0];
    productsToSeed.push({
      sku: sku,
      name: details.product_name,
      brand: brand,
      image_url: imgMap[brand] || 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&q=80&w=800',
      price: prices[sku] || 100,
      description: details.pristine_description,
      accessories: details.expected_accessories,
      category: sku.includes('TSHIRT') ? 'Apparel' : sku.includes('SHOES') ? 'Footwear' : sku.includes('SAMSUNG') ? 'Electronics' : 'Appliances'
    });
  }

  // Seeding initial products
  const { data: dbProducts, error: prodErr } = await supabase
    .from('products')
    .upsert(productsToSeed, { onConflict: 'sku' })
    .select();

  if (prodErr) {
    console.error('Error seeding products:', prodErr.message);
  } else {
    console.log(`✅ ${dbProducts.length} Products seeded`);
  }

  // 4. Create one order for each product to make the app look "alive"
  if (dbProducts && dbProducts.length > 0) {
    console.log('📦 Seeding orders and user history...');
    
    for (const p of dbProducts) {
      const { data: order, error: orderErr } = await supabase
        .from('orders')
        .insert({ 
          user_id: testUserId,
          purchase_date: new Date(Date.now() - Math.floor(Math.random() * 30) * 86400000).toISOString()
        })
        .select();

      if (orderErr) {
        console.error(`Error seeding order for product ${p.name}:`, orderErr.message);
        continue;
      }

      await supabase.from('order_items').insert({
        order_id: order[0].id,
        product_id: p.id,
        quantity: 1,
        price_at_purchase: p.price,
        return_status: 'NONE'
      });
    }
  }

  console.log('✨ Seeding complete! Database is now full of premium brand data.');
}

seed();
