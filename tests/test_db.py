import pandas as pd
from src.core.db.database_manager import SQLDatabaseManager

database = SQLDatabaseManager("data/sql/milk_database.db")
print("Database Manager initialized.")

# Connect to the database (will create if not exists)
database.connect()
print("Database connected and tables created successfully!")

def check_and_migrate_schema():
    """Check schema and migrate if missing columns"""
    
    # Check all tables for missing columns
    tables_to_check = {
        'product_categories': ['id', 'category_name', 'description', 'image_url', 'created_at', 'updated_at'],
        'milk_brands': ['id', 'brand_name', 'country_of_origin', 'description', 'market_position', 'is_premium', 'logo_url', 'created_at', 'updated_at'],
        'milk_products': ['id', 'product_name', 'sku', 'category_id', 'brand_id', 'package_size_ml', 'age_range_from', 'age_range_to', 'price_per_unit', 'discount_percent', 'stock_quantity', 'description', 'main_ingredients', 'image_url', 'is_active', 'created_at', 'updated_at']
    }
    
    schema_correct = True
    
    for table_name, expected_columns in tables_to_check.items():
        try:
            schema = database.fetch_results(f"PRAGMA table_info({table_name})")
            current_columns = [col['name'] for col in schema]
            
            print(f"\n {table_name}:")
            print(f"   Expected: {len(expected_columns)} columns")
            print(f"   Current:  {len(current_columns)} columns")
            
            missing_columns = [col for col in expected_columns if col not in current_columns]
            
            if missing_columns:
                print(f"Missing columns: {missing_columns}")
                schema_correct = False
            else:
                print(f"All columns present")

        except Exception as e:
            print(f"Error checking {table_name}: {e}")
            schema_correct = False
    
    if not schema_correct:
        print(f"\nSchema incorrect, need to recreate database...")
        return False
    else:
        print(f"\nDatabase schema correct!")
        return True
    
def force_recreate_database():
    """Force recreate database with correct schema"""
    print("\nRECREATING DATABASE...")
    
    try:
        # Disconnect current
        database.disconnect()
        
        # Delete database file
        import os
        if os.path.exists(database.connection_string):
            os.remove(database.connection_string)
            print("Old database file removed")

        # Reconnect - will create new database with correct schema
        database.connect()
        print("New database created with correct schema")
        
        # Verify schema again
        return check_and_migrate_schema()
        
    except Exception as e:
        print(f"Error recreating database: {e}")
        return False

# Run schema check
try:
    schema_ok = check_and_migrate_schema()
    
    if not schema_ok:
        print("\nNeed to recreate database to have correct schema...")
        recreate_success = force_recreate_database()
        
        if recreate_success:
            print("Database recreated successfully!")
        else:
            print("Failed to recreate database properly")

except Exception as e:
    print(f"Error during schema check: {e}")
    print("Forcing database recreation...")
    force_recreate_database()

def populate_data_from_csv(database, df):
    """
    Populate database from CSV data
    Map columns from CSV to database tables
    Ensure all fields are fully populated
    """

    # Dictionary to track unique categories and brands created
    categories_created = {}
    brands_created = {}

    print("Starting data population...")

    for index, row in df.iterrows():
        try:
            # 1. Create category if not exists
            category_key = (row['category_id'], row['category_name'])
            if category_key not in categories_created:
                category_id = database.create_product_category(
                    category_name=row['category_name'],
                    description=row['category_description'],
                    image_url=None  # Not available in CSV, set to None
                )
                categories_created[category_key] = category_id
                print(f"✓ Created category: {row['category_name']} (ID: {category_id})")
            else:
                category_id = categories_created[category_key]

            # 2. Create brand if not exists
            brand_key = (row['brand_id'], row['brand_name'])
            if brand_key not in brands_created:
                brand_id = database.create_milk_brand(
                    brand_name=row['brand_name'],
                    country_of_origin=row['country_of_origin'],
                    description=None,  # Not available in CSV
                    market_position=None,  # Not available in CSV
                    is_premium=bool(row['is_premium']),
                    logo_url=None  # Not available in CSV
                )
                brands_created[brand_key] = brand_id
                print(f"✓ Created brand: {row['brand_name']} (ID: {brand_id})")
            else:
                brand_id = brands_created[brand_key]

            # 3. Create product with all fields
            product_id = database.create_milk_product(
                product_name=row['product_name'],
                sku=row['sku'],
                category_id=category_id,
                brand_id=brand_id,
                package_size_ml=int(row['package_size_ml']),
                age_range_from=int(row['age_range_from']),
                age_range_to=int(row['age_range_to']),
                price_per_unit=float(row['price_per_unit']),
                discount_percent=int(row['discount_percent']),
                stock_quantity=int(row['stock_quantity']),
                description=row['product_description'],
                main_ingredients=row['main_ingredients'],
                image_url=None,  # Not available in CSV, set to None
                is_active=True  # Default is active
            )
            print(f"Created product: {row['product_name']} (ID: {product_id})")
            
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            print(f"   Row data: {row.to_dict()}")
            continue

    print(f"\nCompleted! Created:")
    print(f"   - {len(categories_created)} categories")
    print(f"   - {len(brands_created)} brands") 
    print(f"   - {len(df)} products")

# Load CSV data
df = pd.read_csv("data/csv/milk_consultation.csv")
populate_data_from_csv(database, df)

# Check data has been populated successfully
print("=== CHECK DATA ===")

# Check categories
categories = database.get_product_categories()
print(f"\nProduct Categories ({len(categories)}):")
for cat in categories:
    print(f"   {cat['id']}: {cat['category_name']}")

# Check brands
brands = database.get_milk_brands()
print(f"\nMilk Brands ({len(brands)}):")
for brand in brands:
    print(f"   {brand['id']}: {brand['brand_name']} ({brand['country_of_origin']})")

# Check products with JOIN
products = database.get_milk_products()
print(f"\nMilk Products ({len(products)}):")
for product in products[:5]:
    print(f"   {product['id']}: {product['product_name']}")
    print(f"      Brand: {product['brand_name']}, Category: {product['category_name']}")
    print(f"      Price: {product['price_per_unit']:,.0f} VNĐ, Stock: {product['stock_quantity']}")

if len(products) > 5:
    print(f"   ... and {len(products) - 5} other products")

    # Check database schema to ensure all fields are created
print("=== CHECK DATABASE SCHEMA ===")

def check_table_schema(table_name):
    """Check schema of a table"""
    query = f"PRAGMA table_info({table_name})"
    schema_info = database.fetch_results(query)
    
    print(f"\nTable: {table_name}")
    print("   Fields:")
    for field in schema_info:
        nullable = "NULL" if field['notnull'] == 0 else "NOT NULL"
        default = f"DEFAULT {field['dflt_value']}" if field['dflt_value'] else ""
        print(f"     {field['name']} ({field['type']}) {nullable} {default}")
    
    return schema_info

# Check schema of all tables
product_categories_schema = check_table_schema('product_categories')
milk_brands_schema = check_table_schema('milk_brands')  
milk_products_schema = check_table_schema('milk_products')

# Check foreign keys
print(f"\nForeign Keys:")
fk_info = database.fetch_results("PRAGMA foreign_key_list(milk_products)")
for fk in fk_info:
    print(f"   {fk['from']} → {fk['table']}.{fk['to']}")