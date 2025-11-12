from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
import os
import sys
import sqlite3

# Add the database module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from core.db.database_manager import SQLDatabaseManager

# Initialize MCP server
mcp = FastMCP("Simplified Milk Database Tools", port=9000)

# Database connection
db_path = os.path.join(os.path.dirname(__file__), '../../../../data/sql/milk_database.db')
db_manager = SQLDatabaseManager(db_path)

def ensure_connection():
    """Ensure database connection is active (lazy connection - only connect when needed)"""
    if not db_manager.connection:
        db_manager.connect()

# ============================================================================
# Business Logic Functions (defined first, without decorators)
# ============================================================================

async def _find_products(search_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Simple product search - finds products by name, brand, or description.
    
    Args:
        search_text: What to search for (product name, brand, or keyword)
        limit: How many results to return (max 20)
    
    Returns:
        List of matching products with basic info
    """
    ensure_connection()
    limit = min(limit, 20)  # Cap at 20 results
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, c.category_name,
           p.price_per_unit, p.package_size_ml, p.age_range_from, p.age_range_to,
           p.discount_percent, p.stock_quantity
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE (p.product_name LIKE ? OR b.brand_name LIKE ? OR p.description LIKE ?)
    AND p.is_active = 1
    ORDER BY p.product_name
    LIMIT ?
    """
    
    search_param = f"%{search_text}%"
    return db_manager.fetch_results(query, (search_param, search_param, search_param, limit))

async def _products_by_price(min_price: float, max_price: float) -> List[Dict[str, Any]]:
    """
    Find products within a price range.
    
    Args:
        min_price: Minimum price (VND)
        max_price: Maximum price (VND)
    
    Returns:
        Products in the price range, sorted by price
    """
    ensure_connection()
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, c.category_name,
           p.price_per_unit, p.package_size_ml, p.discount_percent, p.stock_quantity
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE p.price_per_unit BETWEEN ? AND ? AND p.is_active = 1
    ORDER BY p.price_per_unit ASC
    LIMIT 15
    """
    
    return db_manager.fetch_results(query, (min_price, max_price))

async def _products_for_age(child_age_months: int) -> List[Dict[str, Any]]:
    """
    Find products suitable for a child's age.
    
    Args:
        child_age_months: Child's age in months
    
    Returns:
        Products suitable for this age, sorted by price
    """
    ensure_connection()
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, c.category_name,
           p.price_per_unit, p.package_size_ml, p.age_range_from, p.age_range_to,
           p.discount_percent, p.stock_quantity
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE ? BETWEEN p.age_range_from AND p.age_range_to 
    AND p.is_active = 1
    ORDER BY p.price_per_unit ASC
    LIMIT 15
    """
    
    return db_manager.fetch_results(query, (child_age_months,))

async def _get_product_info(product_id: int) -> Dict[str, Any]:
    """
    Get complete information about a specific product.
    
    Args:
        product_id: The product ID
    
    Returns:
        Complete product details
    """
    ensure_connection()
    
    query = """
    SELECT p.*, c.category_name, b.brand_name, b.country_of_origin, b.is_premium
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE p.id = ?
    """
    
    results = db_manager.fetch_results(query, (product_id,))
    return results[0] if results else {}

async def _discounted_products() -> List[Dict[str, Any]]:
    """
    Get products currently on discount.
    
    Returns:
        Products with discounts, sorted by discount percentage
    """
    ensure_connection()
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, c.category_name,
           p.price_per_unit, p.discount_percent, p.stock_quantity,
           ROUND(p.price_per_unit / (1 - p.discount_percent/100.0), 2) as original_price
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE p.discount_percent > 0 AND p.is_active = 1
    ORDER BY p.discount_percent DESC
    LIMIT 15
    """
    
    return db_manager.fetch_results(query)

async def _list_brands() -> List[Dict[str, Any]]:
    """
    Get all available milk brands with detailed information.
    
    Returns:
        List of all brands with product count, country of origin, and premium status
    """
    ensure_connection()
    
    query = """
    SELECT b.id, b.brand_name, b.country_of_origin, b.description, 
           b.market_position, b.is_premium, b.logo_url,
           COUNT(p.id) as product_count,
           MIN(p.price_per_unit) as min_price,
           MAX(p.price_per_unit) as max_price,
           ROUND(AVG(p.price_per_unit), 2) as avg_price
    FROM milk_brands b
    LEFT JOIN milk_products p ON b.id = p.brand_id AND p.is_active = 1
    GROUP BY b.id, b.brand_name, b.country_of_origin, b.description, 
             b.market_position, b.is_premium, b.logo_url
    ORDER BY b.brand_name
    """
    
    return db_manager.fetch_results(query)

async def _list_categories() -> List[Dict[str, Any]]:
    """
    Get all product categories (các loại sữa) with detailed information.
    
    Returns:
        List of all categories with product counts, price ranges, and descriptions
    """
    ensure_connection()
    
    query = """
    SELECT c.id, c.category_name, c.description, c.image_url,
           COUNT(p.id) as product_count,
           MIN(p.price_per_unit) as min_price,
           MAX(p.price_per_unit) as max_price,
           ROUND(AVG(p.price_per_unit), 2) as avg_price
    FROM product_categories c
    LEFT JOIN milk_products p ON c.id = p.category_id AND p.is_active = 1
    GROUP BY c.id, c.category_name, c.description, c.image_url
    ORDER BY c.category_name
    """
    
    return db_manager.fetch_results(query)

async def _products_by_brand(brand_name: str) -> List[Dict[str, Any]]:
    """
    Get all products from a specific brand.
    
    Args:
        brand_name: Name of the brand (partial match works)
    
    Returns:
        All products from the brand
    """
    ensure_connection()
    
    query = """
    SELECT p.id, p.product_name, c.category_name, p.price_per_unit,
           p.package_size_ml, p.age_range_from, p.age_range_to, p.discount_percent, p.stock_quantity
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE b.brand_name LIKE ? AND p.is_active = 1
    ORDER BY p.product_name
    """
    
    return db_manager.fetch_results(query, (f"%{brand_name}%",))

async def _products_by_category(category_name: str) -> List[Dict[str, Any]]:
    """
    Get all products in a specific category.
    
    Args:
        category_name: Name of the category (partial match works)
    
    Returns:
        All products in the category
    """
    ensure_connection()
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, p.price_per_unit,
           p.package_size_ml, p.age_range_from, p.age_range_to, p.discount_percent, p.stock_quantity
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE c.category_name LIKE ? AND p.is_active = 1
    ORDER BY p.price_per_unit ASC
    """
    
    return db_manager.fetch_results(query, (f"%{category_name}%",))

async def _cheapest_products(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get the cheapest products available. Returns products sorted by price from LOWEST to HIGHEST.
    The FIRST item in the result is the CHEAPEST product.
    
    Args:
        limit: How many products to return (default: 10, max: 20)
    
    Returns:
        List of cheapest products sorted by price (ASCENDING - lowest first).
        Each product includes: id, product_name, brand_name, category_name, price_per_unit, stock_quantity.
        IMPORTANT: The first product (index 0) is the CHEAPEST one.
    """
    ensure_connection()
    limit = min(limit, 20)
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, c.category_name,
           p.price_per_unit, p.package_size_ml, p.discount_percent, p.stock_quantity
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE p.is_active = 1 
    AND p.price_per_unit IS NOT NULL 
    AND p.price_per_unit > 0
    ORDER BY p.price_per_unit ASC
    LIMIT ?
    """
    
    return db_manager.fetch_results(query, (limit,))

async def _premium_products(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get premium/high-end products.
    
    Args:
        limit: How many products to return
    
    Returns:
        Premium products from premium brands
    """
    ensure_connection()
    limit = min(limit, 20)
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, c.category_name,
           p.price_per_unit, p.package_size_ml, b.country_of_origin, p.stock_quantity
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE b.is_premium = 1 AND p.is_active = 1
    ORDER BY p.price_per_unit DESC
    LIMIT ?
    """
    
    return db_manager.fetch_results(query, (limit,))

async def _list_countries() -> List[Dict[str, Any]]:
    """
    Get all countries of origin (các nhà cung cấp/nước xuất xứ) with product information.
    
    Returns:
        List of all countries with brand count, product count, and price ranges
    """
    ensure_connection()
    
    query = """
    SELECT b.country_of_origin,
           COUNT(DISTINCT b.id) as brand_count,
           COUNT(p.id) as product_count,
           MIN(p.price_per_unit) as min_price,
           MAX(p.price_per_unit) as max_price,
           ROUND(AVG(p.price_per_unit), 2) as avg_price
    FROM milk_brands b
    LEFT JOIN milk_products p ON b.id = p.brand_id AND p.is_active = 1
    GROUP BY b.country_of_origin
    ORDER BY product_count DESC, b.country_of_origin
    """
    
    return db_manager.fetch_results(query)

async def _list_price_ranges() -> List[Dict[str, Any]]:
    """
    Get available price ranges (các mức giá) with product counts.
    Divides products into price brackets: 0-100k, 100k-200k, 200k-300k, 300k-500k, 500k-1000k, 1000k+
    
    Returns:
        List of price ranges with product counts and price statistics
    """
    ensure_connection()
    
    query = """
    SELECT 
        CASE 
            WHEN price_per_unit < 100000 THEN '0-100k'
            WHEN price_per_unit < 200000 THEN '100k-200k'
            WHEN price_per_unit < 300000 THEN '200k-300k'
            WHEN price_per_unit < 500000 THEN '300k-500k'
            WHEN price_per_unit < 1000000 THEN '500k-1000k'
            ELSE '1000k+'
        END as price_range,
        MIN(price_per_unit) as min_price,
        MAX(price_per_unit) as max_price,
        COUNT(*) as product_count,
        ROUND(AVG(price_per_unit), 2) as avg_price
    FROM milk_products
    WHERE is_active = 1
    GROUP BY 
        CASE 
            WHEN price_per_unit < 100000 THEN '0-100k'
            WHEN price_per_unit < 200000 THEN '100k-200k'
            WHEN price_per_unit < 300000 THEN '200k-300k'
            WHEN price_per_unit < 500000 THEN '300k-500k'
            WHEN price_per_unit < 1000000 THEN '500k-1000k'
            ELSE '1000k+'
        END
    ORDER BY min_price
    """
    
    return db_manager.fetch_results(query)

async def _products_by_country(country_name: str) -> List[Dict[str, Any]]:
    """
    Get all products from a specific country of origin (nước xuất xứ).
    
    Args:
        country_name: Name of the country (partial match works, e.g., "Mỹ", "Hà Lan", "Việt Nam")
    
    Returns:
        All products from brands in the specified country
    """
    ensure_connection()
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, c.category_name,
           p.price_per_unit, p.package_size_ml, p.age_range_from, p.age_range_to,
           p.discount_percent, b.country_of_origin, p.stock_quantity
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE b.country_of_origin LIKE ? AND p.is_active = 1
    ORDER BY p.price_per_unit ASC
    LIMIT 50
    """
    
    return db_manager.fetch_results(query, (f"%{country_name}%",))

async def _products_by_price_range(price_range: str) -> List[Dict[str, Any]]:
    """
    Get products in a specific price range bracket.
    
    Args:
        price_range: Price range bracket. Options: "0-100k", "100k-200k", "200k-300k", 
                     "300k-500k", "500k-1000k", "1000k+"
    
    Returns:
        Products in the specified price range
    """
    ensure_connection()
    
    # Parse price range
    ranges = {
        "0-100k": (0, 100000),
        "100k-200k": (100000, 200000),
        "200k-300k": (200000, 300000),
        "300k-500k": (300000, 500000),
        "500k-1000k": (500000, 1000000),
        "1000k+": (1000000, 999999999)
    }
    
    if price_range not in ranges:
        return []
    
    min_price, max_price = ranges[price_range]
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, c.category_name,
           p.price_per_unit, p.package_size_ml, p.age_range_from, p.age_range_to,
           p.discount_percent, p.stock_quantity
    FROM milk_products p
    LEFT JOIN product_categories c ON p.category_id = c.id
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE p.price_per_unit >= ? AND p.price_per_unit < ? AND p.is_active = 1
    ORDER BY p.price_per_unit ASC
    LIMIT 50
    """
    
    return db_manager.fetch_results(query, (min_price, max_price))

async def _database_stats() -> Dict[str, Any]:
    """
    Get basic statistics about the database.
    
    Returns:
        Summary statistics of products, brands, and categories
    """
    ensure_connection()
    
    stats = {}
    
    # Basic counts
    stats['total_products'] = db_manager.fetch_results("SELECT COUNT(*) as count FROM milk_products WHERE is_active = 1")[0]['count']
    stats['total_brands'] = db_manager.fetch_results("SELECT COUNT(*) as count FROM milk_brands")[0]['count']
    stats['total_categories'] = db_manager.fetch_results("SELECT COUNT(*) as count FROM product_categories")[0]['count']
    
    # Countries count
    countries_result = db_manager.fetch_results("SELECT COUNT(DISTINCT country_of_origin) as count FROM milk_brands WHERE country_of_origin IS NOT NULL AND country_of_origin != ''")
    stats['total_countries'] = countries_result[0]['count'] if countries_result else 0
    
    # Price info
    price_info = db_manager.fetch_results("""
        SELECT MIN(price_per_unit) as min_price, 
               MAX(price_per_unit) as max_price,
               ROUND(AVG(price_per_unit), 2) as avg_price
        FROM milk_products WHERE is_active = 1
    """)[0]
    stats.update(price_info)
    
    # Discount info
    stats['products_on_discount'] = db_manager.fetch_results(
        "SELECT COUNT(*) as count FROM milk_products WHERE discount_percent > 0 AND is_active = 1"
    )[0]['count']
    
    return stats

async def _check_stock_quantity(product_id: int) -> Dict[str, Any]:
    """
    Check current stock quantity of a product.
    
    Args:
        product_id: ID of the product to check
    
    Returns:
        Product info and stock status
    """
    ensure_connection()
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, p.stock_quantity,
           CASE WHEN p.stock_quantity > 0 THEN 'In Stock' ELSE 'Out of Stock' END as status
    FROM milk_products p
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE p.id = ? AND p.is_active = 1
    """
    
    results = db_manager.fetch_results(query, (product_id,))
    return results[0] if results else {"error": "Product not found"}

async def _products_in_stock(limit: int = 15) -> List[Dict[str, Any]]:
    """
    Get list of products currently in stock.
    
    Args:
        limit: Number of products to return (max 50)
    
    Returns:
        List of available products
    """
    ensure_connection()
    limit = min(limit, 50)
    
    query = """
    SELECT p.id, p.product_name, b.brand_name, p.price_per_unit,
           p.stock_quantity, p.discount_percent
    FROM milk_products p
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE p.stock_quantity > 0 AND p.is_active = 1
    ORDER BY p.stock_quantity DESC
    LIMIT ?
    """
    
    return db_manager.fetch_results(query, (limit,))

async def _get_stock_by_product_name(product_name: str) -> Dict[str, Any]:
    """
    Get stock quantity of a product by its name. Use this when customer asks about stock quantity.
    This tool searches for products by name and returns stock information.
    
    Args:
        product_name: Product name to search for (can be partial match, e.g., "TH true MILK", "sữa tươi")
    
    Returns:
        Dictionary with product info and stock quantity. Format:
        {
            "product_id": int,
            "product_name": str,
            "brand_name": str,
            "stock_quantity": int,
            "status": str ("In Stock" or "Out of Stock"),
            "price_per_unit": float
        }
        If product not found, returns {"error": "Product not found"}
    """
    ensure_connection()
    
    query = """
    SELECT p.id as product_id, p.product_name, b.brand_name, 
           p.stock_quantity, p.price_per_unit,
           CASE WHEN p.stock_quantity > 0 THEN 'In Stock' ELSE 'Out of Stock' END as status
    FROM milk_products p
    LEFT JOIN milk_brands b ON p.brand_id = b.id
    WHERE p.product_name LIKE ? 
    AND p.is_active = 1
    ORDER BY 
        CASE 
            WHEN p.product_name = ? THEN 1
            WHEN p.product_name LIKE ? THEN 2
            ELSE 3
        END,
        p.product_name
    LIMIT 1
    """
    
    # Try exact match first, then partial match
    search_param = f"%{product_name}%"
    exact_param = product_name.strip()
    starts_with_param = f"{exact_param}%"
    
    results = db_manager.fetch_results(
        query, 
        (search_param, exact_param, starts_with_param)
    )
    
    if results:
        return results[0]
    else:
        return {"error": f"Product '{product_name}' not found"}

# ============================================================================
# MCP Tool Registration (wrap business logic functions with @mcp.tool())
# ============================================================================

@mcp.tool()
async def find_products(search_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Simple product search - finds products by name, brand, or description."""
    return await _find_products(search_text, limit)

@mcp.tool()
async def products_by_price(min_price: float, max_price: float) -> List[Dict[str, Any]]:
    """Find products within a price range."""
    return await _products_by_price(min_price, max_price)

@mcp.tool()
async def products_for_age(child_age_months: int) -> List[Dict[str, Any]]:
    """Find products suitable for a child's age."""
    return await _products_for_age(child_age_months)

@mcp.tool()
async def get_product_info(product_id: int) -> Dict[str, Any]:
    """Get complete information about a specific product."""
    return await _get_product_info(product_id)

@mcp.tool()
async def discounted_products() -> List[Dict[str, Any]]:
    """Get products currently on discount."""
    return await _discounted_products()

@mcp.tool()
async def list_brands() -> List[Dict[str, Any]]:
    """Get all available milk brands with detailed information."""
    return await _list_brands()

@mcp.tool()
async def list_categories() -> List[Dict[str, Any]]:
    """Get all product categories (các loại sữa) with detailed information."""
    return await _list_categories()

@mcp.tool()
async def products_by_brand(brand_name: str) -> List[Dict[str, Any]]:
    """Get all products from a specific brand."""
    return await _products_by_brand(brand_name)

@mcp.tool()
async def products_by_category(category_name: str) -> List[Dict[str, Any]]:
    """Get all products in a specific category."""
    return await _products_by_category(category_name)

@mcp.tool()
async def cheapest_products(limit: int = 10) -> List[Dict[str, Any]]:
    """Get the cheapest products available. Returns products sorted by price from LOWEST to HIGHEST."""
    return await _cheapest_products(limit)

@mcp.tool()
async def premium_products(limit: int = 10) -> List[Dict[str, Any]]:
    """Get premium/high-end products."""
    return await _premium_products(limit)

@mcp.tool()
async def list_countries() -> List[Dict[str, Any]]:
    """Get all countries of origin (các nhà cung cấp/nước xuất xứ) with product information."""
    return await _list_countries()

@mcp.tool()
async def list_price_ranges() -> List[Dict[str, Any]]:
    """Get available price ranges (các mức giá) with product counts."""
    return await _list_price_ranges()

@mcp.tool()
async def products_by_country(country_name: str) -> List[Dict[str, Any]]:
    """Get all products from a specific country of origin (nước xuất xứ)."""
    return await _products_by_country(country_name)

@mcp.tool()
async def products_by_price_range(price_range: str) -> List[Dict[str, Any]]:
    """Get products in a specific price range bracket."""
    return await _products_by_price_range(price_range)

@mcp.tool()
async def database_stats() -> Dict[str, Any]:
    """Get basic statistics about the database."""
    return await _database_stats()

@mcp.tool()
async def check_stock_quantity(product_id: int) -> Dict[str, Any]:
    """Check current stock quantity of a product."""
    return await _check_stock_quantity(product_id)

@mcp.tool()
async def products_in_stock(limit: int = 15) -> List[Dict[str, Any]]:
    """Get list of products currently in stock."""
    return await _products_in_stock(limit)

@mcp.tool()
async def get_stock_by_product_name(product_name: str) -> Dict[str, Any]:
    """Get stock quantity of a product by its name. Use this when customer asks about stock quantity."""
    return await _get_stock_by_product_name(product_name)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
