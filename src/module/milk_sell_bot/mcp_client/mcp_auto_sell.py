"""
MCP Auto Sale Tools - Order processing and email confirmation
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Add the database module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from core.db.database_manager import SQLDatabaseManager

load_dotenv()

# Initialize MCP server
port = int(os.getenv("AUTO_SALE_MCP_PORT", "9002"))
mcp = FastMCP("AutoSale", port=port)

# Email configuration
EMAIL_USER = os.getenv("EMAIL_USER", "clonefreefire1@gmail.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "stuq kxxy vvaa asws").replace(" ", "")

# Database connection
db_path = os.path.join(os.path.dirname(__file__), '../../../../data/sql/milk_database.db')
db_manager = SQLDatabaseManager(db_path)


def send_email(to: str, subject: str, contents: str) -> bool:
    """Send email using Gmail SMTP."""
    try:
        print(f"[DEBUG] Preparing to send email to {to} with subject: {subject}")
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to
        msg['Subject'] = subject
        
        is_html = '<html>' in contents.lower() or '<body>' in contents.lower()
        msg.attach(MIMEText(contents, 'html' if is_html else 'plain'))
        
        print(f"[DEBUG] Connecting to SMTP server...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        print(f"[DEBUG] Logging in with email: {EMAIL_USER}")
        server.login(EMAIL_USER, EMAIL_PASS)
        print(f"[DEBUG] Sending email...")
        server.sendmail(EMAIL_USER, to, msg.as_string())
        server.quit()
        print(f"[DEBUG] Email sent successfully!")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"[ERROR] SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error sending email: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return False


def get_product_info(product_id: int) -> Optional[Dict[str, Any]]:
    """Get product information from database."""
    try:
        if not db_manager.connection:
            db_manager.connect()
        
        query = """
        SELECT p.*, c.category_name, b.brand_name, b.country_of_origin
        FROM milk_products p
        LEFT JOIN product_categories c ON p.category_id = c.id
        LEFT JOIN milk_brands b ON p.brand_id = b.id
        WHERE p.id = ? AND p.is_active = 1
        """
        
        results = db_manager.fetch_results(query, (product_id,))
        return results[0] if results else None
    except Exception as e:
        print(f"Error getting product info: {e}")
        return None


def calculate_total_price(price_per_unit: float, discount_percent: float, quantity: int) -> Dict[str, float]:
    """Calculate total price with discount."""
    original_total = price_per_unit * quantity
    discount_amount = original_total * (discount_percent / 100)
    final_total = original_total - discount_amount
    
    return {
        "unit_price": price_per_unit,
        "quantity": quantity,
        "original_total": original_total,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "final_total": final_total
    }


def build_order_email(product: Dict[str, Any], quantity: int, pricing: Dict[str, float]) -> str:
    """Build HTML email content for order confirmation."""
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Cảm ơn bạn đã mua hàng!</h2>
            <p>Xin chào,</p>
            <p>Cảm ơn bạn đã đặt hàng tại cửa hàng của chúng tôi. Dưới đây là thông tin đơn hàng của bạn:</p>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #27ae60; margin-top: 0;">Thông tin sản phẩm</h3>
                <p><strong>Tên sản phẩm:</strong> {product.get('product_name', 'N/A')}</p>
                <p><strong>Thương hiệu:</strong> {product.get('brand_name', 'N/A')}</p>
                <p><strong>Danh mục:</strong> {product.get('category_name', 'N/A')}</p>
                <p><strong>Xuất xứ:</strong> {product.get('country_of_origin', 'N/A')}</p>
                <p><strong>Dung tích:</strong> {product.get('package_size_ml', 'N/A')}ml</p>
            </div>
            
            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #27ae60; margin-top: 0;">Thông tin đơn hàng</h3>
                <p><strong>Số lượng:</strong> {quantity}</p>
                <p><strong>Đơn giá:</strong> {pricing['unit_price']:,.0f} VND</p>
                <p><strong>Tổng tiền (chưa giảm):</strong> {pricing['original_total']:,.0f} VND</p>
                <p><strong>Giảm giá:</strong> {pricing['discount_percent']:.0f}% (-{pricing['discount_amount']:,.0f} VND)</p>
                <p style="font-size: 18px; font-weight: bold; color: #e74c3c; margin-top: 15px;">
                    <strong>Tổng thanh toán:</strong> {pricing['final_total']:,.0f} VND
                </p>
            </div>
            
            <p>Chúng tôi sẽ xử lý đơn hàng của bạn trong thời gian sớm nhất. Bạn sẽ nhận được thông báo khi đơn hàng được giao.</p>
            <p>Trân trọng,<br>Đội ngũ bán hàng</p>
        </div>
    </body>
    </html>
    """
    return html


# @mcp.tool()
# async def create_order(email: str, product_id: int, quantity: int) -> str:
#     """
#     Create an order and send confirmation email to customer.
    
#     Args:
#         email: Customer email address
#         product_id: Product ID to purchase
#         quantity: Number of items to purchase
    
#     Returns:
#         Success message or error message
#     """


@mcp.tool()
async def purchase_product(email: str, product_id: int, quantity: int) -> str:
    """
    Purchase a product and send confirmation email to customer.
    Use this tool when customer wants to buy/order/purchase a product.
    
    Args:
        email: Customer email address
        product_id: Product ID to purchase
        quantity: Number of items to purchase

    """

    try:
        # Get product information
        product = get_product_info(product_id)
        if not product:
            return f"Error: Product with ID {product_id} not found or is inactive."
        
        # Check stock
        stock_quantity = product.get('stock_quantity', 0)
        if stock_quantity < quantity:
            return f"Error: Insufficient stock. Available: {stock_quantity}, Requested: {quantity}"
        
        # Calculate pricing
        price_per_unit = float(product.get('price_per_unit', 0))
        discount_percent = float(product.get('discount_percent', 0))
        pricing = calculate_total_price(price_per_unit, discount_percent, quantity)
        
        # Build email content
        email_content = build_order_email(product, quantity, pricing)
        email_subject = f"Xác nhận đơn hàng - {product.get('product_name', 'Sản phẩm')}"
        
        # Send email
        success = send_email(email, email_subject, email_content)
        
        if success:
            return f"Order created successfully! Confirmation email sent to {email}. Total: {pricing['final_total']:,.0f} VND"
        else:
            return f"Error: Failed to send confirmation email to {email}"
            
    except Exception as e:
        return f"Error creating order: {str(e)}"


if __name__ == "__main__":

    
    # Uncomment below to run MCP server
    # print(f"Starting Auto Sale MCP server on port {port}...")
    mcp.run(transport="streamable-http")