
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Union


class SQLDatabaseManager:
    def __init__(self, connection_string: str = "data/sql/milk_database.db"):
        self.connection_string = connection_string
        self.connection = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """Establish a database connection"""
        try:
            self.connection = sqlite3.connect(self.connection_string)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access to rows
            self.logger.info(f"Connected to database: {self.connection_string}")
            self._create_tables()
        except sqlite3.Error as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise

    def disconnect(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Database connection closed")

    def _create_tables(self):
        """Create database tables based on DBML schema (only if they don't exist)"""
        # Check if tables already exist to avoid unnecessary work
        try:
            if self.connection:
                cursor = self.connection.cursor()
                # Check if main table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='milk_products'
                """)
                if cursor.fetchone():
                    # Tables already exist, skip creation
                    return
                
                # Tables don't exist, create them
                tables_sql = [
                    """
                    CREATE TABLE IF NOT EXISTS product_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category_name TEXT NOT NULL,
                        description TEXT,
                        image_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS milk_brands (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        brand_name TEXT NOT NULL,
                        country_of_origin TEXT,
                        description TEXT,
                        market_position TEXT,
                        is_premium BOOLEAN DEFAULT 0,
                        logo_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS milk_products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_name TEXT NOT NULL,
                        sku TEXT UNIQUE,
                        category_id INTEGER,
                        brand_id INTEGER,
                        package_size_ml INTEGER,
                        age_range_from INTEGER,
                        age_range_to INTEGER,
                        price_per_unit DECIMAL(10,2),
                        discount_percent INTEGER DEFAULT 0,
                        stock_quantity INTEGER DEFAULT 0,
                        description TEXT,
                        main_ingredients TEXT,
                        image_url TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (category_id) REFERENCES product_categories (id),
                        FOREIGN KEY (brand_id) REFERENCES milk_brands (id)
                    )
                    """
                ]
                
                for sql in tables_sql:
                    cursor.execute(sql)
                
                # Create indexes for better query performance
                indexes_sql = [
                    # Indexes for milk_products table
                    "CREATE INDEX IF NOT EXISTS idx_products_name ON milk_products(product_name)",
                    "CREATE INDEX IF NOT EXISTS idx_products_active ON milk_products(is_active)",
                    "CREATE INDEX IF NOT EXISTS idx_products_brand ON milk_products(brand_id)",
                    "CREATE INDEX IF NOT EXISTS idx_products_category ON milk_products(category_id)",
                    "CREATE INDEX IF NOT EXISTS idx_products_price ON milk_products(price_per_unit)",
                    "CREATE INDEX IF NOT EXISTS idx_products_stock ON milk_products(stock_quantity)",
                    "CREATE INDEX IF NOT EXISTS idx_products_age_range ON milk_products(age_range_from, age_range_to)",
                    # Composite index for common queries
                    "CREATE INDEX IF NOT EXISTS idx_products_active_price ON milk_products(is_active, price_per_unit)",
                    
                    # Indexes for milk_brands table
                    "CREATE INDEX IF NOT EXISTS idx_brands_name ON milk_brands(brand_name)",
                    "CREATE INDEX IF NOT EXISTS idx_brands_country ON milk_brands(country_of_origin)",
                    "CREATE INDEX IF NOT EXISTS idx_brands_premium ON milk_brands(is_premium)",
                    
                    # Indexes for product_categories table
                    "CREATE INDEX IF NOT EXISTS idx_categories_name ON product_categories(category_name)",
                ]
                
                for sql in indexes_sql:
                    cursor.execute(sql)
                
                self.connection.commit()
                self.logger.info("Database tables and indexes created successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating tables: {e}")
            raise

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[int]:
        """Execute a SQL query (INSERT, UPDATE, DELETE)"""
        if not self.connection:
            raise ConnectionError("Database not connected")
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            self.logger.error(f"Error executing query: {e}")
            self.connection.rollback()
            raise

    def fetch_results(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Fetch results from a SQL query (SELECT)"""
        if not self.connection:
            raise ConnectionError("Database not connected")
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Error fetching results: {e}")
            raise

    # CRUD Operations for Product Categories
    def create_product_category(self, category_name: str, description: Optional[str] = None, 
                              image_url: Optional[str] = None) -> Optional[int]:
        """Create a new product category"""
        query = """
        INSERT INTO product_categories (category_name, description, image_url)
        VALUES (?, ?, ?)
        """
        return self.execute_query(query, (category_name, description, image_url))

    def get_product_categories(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get product categories"""
        if category_id:
            query = "SELECT * FROM product_categories WHERE id = ?"
            return self.fetch_results(query, (category_id,))
        else:
            query = "SELECT * FROM product_categories ORDER BY category_name"
            return self.fetch_results(query)

    def update_product_category(self, category_id: int, category_name: Optional[str] = None, 
                              description: Optional[str] = None, image_url: Optional[str] = None) -> None:
        """Update a product category"""
        updates = []
        params = []
        
        if category_name is not None:
            updates.append("category_name = ?")
            params.append(category_name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if image_url is not None:
            updates.append("image_url = ?")
            params.append(image_url)
        
        if not updates:
            return
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(category_id)
        
        query = f"UPDATE product_categories SET {', '.join(updates)} WHERE id = ?"
        self.execute_query(query, tuple(params))

    def delete_product_category(self, category_id: int) -> None:
        """Delete a product category"""
        query = "DELETE FROM product_categories WHERE id = ?"
        self.execute_query(query, (category_id,))

    # CRUD Operations for Milk Brands
    def create_milk_brand(self, brand_name: str, country_of_origin: Optional[str] = None, 
                         description: Optional[str] = None, market_position: Optional[str] = None,
                         is_premium: bool = False, logo_url: Optional[str] = None) -> Optional[int]:
        """Create a new milk brand"""
        query = """
        INSERT INTO milk_brands (brand_name, country_of_origin, description, 
                               market_position, is_premium, logo_url)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_query(query, (brand_name, country_of_origin, description,
                                        market_position, is_premium, logo_url))

    def get_milk_brands(self, brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get milk brands"""
        if brand_id:
            query = "SELECT * FROM milk_brands WHERE id = ?"
            return self.fetch_results(query, (brand_id,))
        else:
            query = "SELECT * FROM milk_brands ORDER BY brand_name"
            return self.fetch_results(query)

    def update_milk_brand(self, brand_id: int, **kwargs) -> None:
        """Update a milk brand"""
        updates = []
        params = []
        
        allowed_fields = ['brand_name', 'country_of_origin', 'description', 
                         'market_position', 'is_premium', 'logo_url']
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return
            
        params.append(brand_id)
        query = f"UPDATE milk_brands SET {', '.join(updates)} WHERE id = ?"
        self.execute_query(query, tuple(params))

    def delete_milk_brand(self, brand_id: int) -> None:
        """Delete a milk brand"""
        query = "DELETE FROM milk_brands WHERE id = ?"
        self.execute_query(query, (brand_id,))

    # CRUD Operations for Milk Products
    def create_milk_product(self, product_name: str, sku: Optional[str] = None, 
                           category_id: Optional[int] = None, brand_id: Optional[int] = None, 
                           package_size_ml: Optional[int] = None, age_range_from: Optional[int] = None, 
                           age_range_to: Optional[int] = None, price_per_unit: Optional[float] = None, 
                           discount_percent: int = 0, stock_quantity: int = 0, 
                           description: Optional[str] = None, main_ingredients: Optional[str] = None, 
                           image_url: Optional[str] = None, is_active: bool = True) -> Optional[int]:
        """Create a new milk product"""
        query = """
        INSERT INTO milk_products (product_name, sku, category_id, brand_id, 
                                 package_size_ml, age_range_from, age_range_to,
                                 price_per_unit, discount_percent, stock_quantity,
                                 description, main_ingredients, image_url, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_query(query, (product_name, sku, category_id, brand_id,
                                        package_size_ml, age_range_from, age_range_to,
                                        price_per_unit, discount_percent, stock_quantity,
                                        description, main_ingredients, image_url, is_active))

    def get_milk_products(self, product_id: Optional[int] = None, category_id: Optional[int] = None,
                         brand_id: Optional[int] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get milk products with optional filters"""
        query = """
        SELECT p.*, c.category_name, b.brand_name 
        FROM milk_products p
        LEFT JOIN product_categories c ON p.category_id = c.id
        LEFT JOIN milk_brands b ON p.brand_id = b.id
        """
        
        conditions = []
        params = []
        
        if product_id:
            conditions.append("p.id = ?")
            params.append(product_id)
        if category_id:
            conditions.append("p.category_id = ?")
            params.append(category_id)
        if brand_id:
            conditions.append("p.brand_id = ?")
            params.append(brand_id)
        if is_active is not None:
            conditions.append("p.is_active = ?")
            params.append(is_active)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY p.product_name"
        
        return self.fetch_results(query, tuple(params) if params else None)

    def update_milk_product(self, product_id: int, **kwargs) -> None:
        """Update a milk product"""
        updates = []
        params = []
        
        allowed_fields = ['product_name', 'sku', 'category_id', 'brand_id',
                         'package_size_ml', 'age_range_from', 'age_range_to',
                         'price_per_unit', 'discount_percent', 'stock_quantity',
                         'description', 'main_ingredients', 'image_url', 'is_active']
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(product_id)
        
        query = f"UPDATE milk_products SET {', '.join(updates)} WHERE id = ?"
        self.execute_query(query, tuple(params))

    def delete_milk_product(self, product_id: int) -> None:
        """Delete a milk product"""
        query = "DELETE FROM milk_products WHERE id = ?"
        self.execute_query(query, (product_id,))

    def update_stock_quantity(self, product_id: int, quantity_change: int) -> None:
        """Update stock quantity by adding/subtracting a value"""
        query = """
        UPDATE milk_products 
        SET stock_quantity = stock_quantity + ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
        """
        self.execute_query(query, (quantity_change, product_id))

    def get_low_stock_products(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Get products with low stock"""
        query = """
        SELECT p.*, c.category_name, b.brand_name 
        FROM milk_products p
        LEFT JOIN product_categories c ON p.category_id = c.id
        LEFT JOIN milk_brands b ON p.brand_id = b.id
        WHERE p.stock_quantity <= ? AND p.is_active = 1
        ORDER BY p.stock_quantity ASC
        """
        return self.fetch_results(query, (threshold,))

class VectorDatabaseManager:
    def __init__(self, vector_store_config):
        self.vector_store_config = vector_store_config
        self.connection = None

    def connect(self):
        # Logic to establish a connection to the vector database
        pass

    def disconnect(self):
        # Logic to close the vector database connection
        pass

    def insert_vector(self, vector_data):
        # Logic to insert vector data into the database
        pass

    def query_vectors(self, query_vector, top_k=10):
        # Logic to query similar vectors from the database
        pass