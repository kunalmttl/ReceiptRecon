import os
from pymongo import MongoClient
from bson.objectid import ObjectId
import random
from datetime import datetime, timedelta
from faker import Faker


# --- CONFIGURATION ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://tanishqs1403:gx8AiuhHwZwNoi1p@cluster0-walmart.1bltqtc.mongodb.net/dummyDB?retryWrites=true&w=majority")
DB_NAME = "dummyDB"
# The hardcoded User ID for Tanishq
USER_ID = ObjectId("653fb13ec7a3a9b9a647329f") 

fake = Faker()

# Define a list of realistic, fraud-prone product templates
PRODUCT_TEMPLATES = [
    {"name": "Pro-Grade 20V Power Drill", "sku": "SKU_DRILL_PRO20", "price": 89.99, "category": "Tools"},
    {"name": "Athletic Works Men's Hoodie, Gray", "sku": "SKU_HOODIE_AWG", "price": 24.50, "category": "Apparel"},
    {"name": "onn. Wireless Bluetooth Headphones", "sku": "SKU_HEADPHONES_ONN", "price": 49.88, "category": "Electronics"},
    {"name": "LEGO Star Wars Millennium Falcon Set", "sku": "SKU_LEGO_FALCON", "price": 169.99, "category": "Toys"},
    {"name": "Gourmet 12-Piece Knife Set", "sku": "SKU_KNIFE_SET_12", "price": 75.00, "category": "Home Goods"},
    {"name": "Designer-Style Throw Pillow (2-pack)", "sku": "SKU_PILLOW_DSGN", "price": 35.00, "category": "Home Goods"},
    {"name": "Spalding NBA Official Game Ball", "sku": "SKU_BASKETBALL_NBA", "price": 39.97, "category": "Sporting Goods"},
    {"name": "4K Ultra HD Streaming Device", "sku": "SKU_STREAM_4K", "price": 49.99, "category": "Electronics"},
    {"name": "Luxury Bath Towel Set (6-Piece)", "sku": "SKU_TOWEL_SET_6", "price": 54.99, "category": "Home Goods"},
    {"name": "Mainstays Classic Steam Iron", "sku": "SKU_IRON_MS", "price": 19.99, "category": "Home Goods"}
]

# To create orders older than 90 day return window limit.

def create_old_orders(db, all_products):
    """Creates 2 orders with purchase dates in January 2024."""
    print("\nCreating 2 old orders from January 2024...")
    
    orders_to_insert = []
    old_start_date = datetime(2025, 1, 1) # Set the base date to Jan 1st, 2024
    
    for _ in range(2):
        num_items = random.randint(1, 2)
        products_in_order = random.sample(all_products, num_items)
        
        purchased_items_list = []
        for product in products_in_order:
            purchased_items_list.append({
                "_id": ObjectId(),
                "product": product["_id"],
                "quantity": 1,
                "priceAtPurchase": product["price"],
                "returnInfo": { "status": "NONE" }
            })
            
        new_order = {
            "user": USER_ID,
            # Set the date to be a random day in January 2024
            "purchaseDate": old_start_date + timedelta(days=random.randint(0, 30)), 
            "purchasedItems": purchased_items_list
        }
        orders_to_insert.append(new_order)
        
    db.orders.insert_many(orders_to_insert)
    print(f"Inserted {len(orders_to_insert)} old orders.")




def populate_database():
    """Clears and populates the database with realistic test data."""
    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # --- STEP 1: CLEAR OLD DATA ---
    # We clear the collections to avoid duplicates when re-running the script
    db.products.delete_many({})
    db.orders.delete_many({})
    print("Cleared existing products and orders.")
    
    # --- STEP 2: CREATE AND INSERT PRODUCTS ---
    # Create product documents from our templates
    products_to_insert = []
    for template in PRODUCT_TEMPLATES:
        products_to_insert.append({
            "_id": ObjectId(),
            "name": template["name"],
            "imageUrl": f"/images/{template['sku'].lower()}.jpg",
            "price": template["price"],
            "sku": template["sku"]
        })
    
    db.products.insert_many(products_to_insert)
    # Fetch the newly created products so we have their IDs for the orders
    all_products = list(db.products.find({}))
    print(f"Inserted {len(all_products)} products into the database.")
    
    # --- STEP 3: CREATE AND INSERT ORDERS ---
    orders_to_insert = []
    
    # Generate dates for the last month (May 2025)
    start_date = datetime(2025, 5, 1)
    
    # Let's create 8 diverse orders
    for i in range(8):
        # Each order has between 1 and 4 unique items
        num_items = random.randint(1, 4)
        # Use random.sample to pick unique products for this order
        products_in_order = random.sample(all_products, num_items)
        
        purchased_items_list = []
        for product in products_in_order:
            purchased_items_list.append({
                "_id": ObjectId(), # Each sub-document gets its own ID
                "product": product["_id"], # Reference the product's ID
                "quantity": 1, # Keep quantity 1 for simplicity
                "priceAtPurchase": product["price"],
                "returnInfo": { "status": "NONE" }
            })
            
        # Create the full order object
        new_order = {
            "user": USER_ID,
            "purchaseDate": start_date + timedelta(days=random.randint(0, 30)),
            "purchasedItems": purchased_items_list
        }
        orders_to_insert.append(new_order)
        
    db.orders.insert_many(orders_to_insert)
    print(f"Inserted {len(orders_to_insert)} new orders for user 'Tanishq'.")
    
    create_old_orders(db, all_products)


    print("\nDatabase population complete!")
    client.close()

if __name__ == "__main__":
    populate_database()