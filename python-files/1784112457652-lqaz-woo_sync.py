import os
import sys
import configparser
import mysql.connector
from woocommerce import API

# Get the directory where the .exe or script is running
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(base_dir, 'config.ini')

# Load external configuration
config = configparser.ConfigParser()
if not os.path.exists(config_path):
    print(f"Error: Configuration file missing at {config_path}")
    sys.exit(1)

config.read(config_path)

try:
    # Database configuration details
    DB_HOST = config['DATABASE']['host']
    DB_USER = config['DATABASE']['user']
    DB_PASS = config['DATABASE']['password']
    DB_NAME = config['DATABASE']['database']

    # WooCommerce API configuration details
    WOO_URL = config['WOOCOMMERCE']['url']
    WOO_KEY = config['WOOCOMMERCE']['consumer_key']
    WOO_SECRET = config['WOOCOMMERCE']['consumer_secret']
except KeyError as e:
    print(f"Error: Missing configuration key {e}")
    sys.exit(1)

# 1. Connect to local uniCenta DB
try:
    db = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )
    cursor = db.cursor(dictionary=True)
except Exception as e:
    print(f"Database Connection Failed: {e}")
    sys.exit(1)

# 2. Initialize WooCommerce API Client
wcapi = API(
    url=WOO_URL,
    consumer_key=WOO_KEY,
    consumer_secret=WOO_SECRET,
    version="wc/v3",
    timeout=15
)

# 3. Fetch products needing sync
try:
    cursor.execute("SELECT id, reference, name, pricesell FROM products WHERE woocommerce_sync_needed = 1 LIMIT 100")
    changed_products = cursor.fetchall()
except Exception as e:
    print(f"Failed to query products table. Ensure woocommerce_sync_needed column exists. Error: {e}")
    sys.exit(1)

for prod in changed_products:
    sku = prod['reference']
    
    # Check if product exists in WooCommerce via SKU
    try:
        products_found = wcapi.get("products", params={"sku": sku}).json()
    except Exception as e:
        print(f"Failed to reach WooCommerce API: {e}")
        break  # Network might be down, break the loop to retry next interval

    payload = {
        "name": prod['name'],
        "regular_price": str(round(prod['pricesell'], 2)),
        "sku": sku
    }
    
    try:
        if products_found and isinstance(products_found, list) and len(products_found) > 0:
            # Update existing product
            woo_id = products_found[0]['id']
            response = wcapi.put(f"products/{woo_id}", payload)
        else:
            # Create fresh product
            response = wcapi.post("products", payload)
            
        if response.status_code in [200, 201]:
            cursor.execute("UPDATE products SET woocommerce_sync_needed = 0 WHERE id = %s", (prod['id'],))
            db.commit()
            
    except Exception as e:
        print(f"Skipping SKU {sku} due to a processing error: {e}")

cursor.close()
db.close()