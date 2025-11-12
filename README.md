# 🥛 Milk Sell Bot - AI-Powered E-commerce Chatbot

An intelligent conversational AI system for milk product sales with real-time inventory management, order processing, and email confirmation capabilities.

## 🚀 Features

### Core Capabilities
- **🔍 Smart Product Search**: Natural language product discovery by name, brand, category, and specifications
- **💰 Price Intelligence**: Dynamic pricing queries, discount detection, and price range filtering  
- **👶 Age-Based Recommendations**: Intelligent product suggestions based on child's age (0-36+ months)
- **📦 Real-time Inventory**: Live stock quantity checking and availability updates
- **🛒 Order Management**: Seamless order placement with automated email confirmations
- **💬 Conversational Memory**: Context-aware conversations with persistent chat history

### Technical Features
- **MCP (Model Context Protocol) Architecture**: Modular tool system for extensible functionality
- **Multi-threading Support**: Thread-safe database operations with concurrent request handling
- **Web Interface**: Modern Gradio-based UI with real-time chat capabilities
- **Email Integration**: SMTP-based order confirmation system
- **SQLite Database**: Efficient local data storage with optimized queries

## 🏗️ Architecture

```
autosell-chatbot/
├── src/
│   ├── core/
│   │   ├── agent/           # AI agent and MCP client
│   │   ├── db/              # Database management
│   │   └── memory/          # Conversation memory
│   ├── module/
│   │   └── milk_sell_bot/
│   │       ├── mcp_client/  # MCP servers
│   │       ├── prompts/     # System prompts
│   │       ├── main.py      # CLI interface
│   │       └── gradio_app.py # Web interface
│   └── utils/               # Utilities and loaders
├── data/sql/                # SQLite database
└── start_all.py            # Service orchestrator
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- SQLite3
- Gmail account (for email notifications)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd autosell-chatbot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Configuration**
Create `.env` file in the root directory:
```env
EMAIL_USER=your-gmail@gmail.com
EMAIL_PASS=your-app-password
AUTO_SALE_MCP_PORT=9002
```

4. **Database Setup**
Ensure your SQLite database is placed at:
```
data/sql/milk_database.db
```

## 🚀 Quick Start

### Option 1: All Services (Recommended)
```bash
python start_all.py
```
This starts all required services automatically.

### Option 2: Individual Services
Run each service in separate terminals:

```bash
# Terminal 1: Search Tools MCP Server
python src/module/milk_sell_bot/mcp_client/search_tools.py

# Terminal 2: Auto Sale MCP Server  
python src/module/milk_sell_bot/mcp_client/mcp_auto_sale.py

# Terminal 3: Web Interface
python src/module/milk_sell_bot/gradio_app.py
```

### Option 3: CLI Interface
```bash
python src/module/milk_sell_bot/main.py
```

## 🌐 Access Points

- **Web Interface**: http://localhost:7123
- **Search Tools API**: http://localhost:9000
- **Order Processing API**: http://localhost:9002

## 💬 Usage Examples

### Product Search
```
"What milk products do you have?"
"Show me products from TH True Milk"
"Find products between 30k and 50k VND"
```

### Age-Based Recommendations
```
"What milk is suitable for 12 month old baby?"
"Show products for newborn"
```

### Stock Management
```
"How much stock of Cô Gái Hà Lan?"
"What products are in stock?"
```

### Order Placement
```
"I want to buy TH true MILK, 3 units, email: customer@email.com"
"Order Vinamilk, quantity 2, my email is test@gmail.com"
```

### Price Queries
```
"What's the cheapest milk?"
"Show products on discount"
"Products from Vietnam under 100k"
```

## 🔧 Configuration

### System Prompts
Customize AI behavior by editing:
```
src/module/milk_sell_bot/prompts/sql_query.j2
```

### Database Schema
The system expects these main tables:
- `milk_products`: Product catalog with pricing and inventory
- `milk_brands`: Brand information and origin
- `product_categories`: Product categorization
- Relationships via foreign keys

### Email Configuration
Configure SMTP settings in `.env`:
- Use Gmail App Passwords for authentication
- Ensure 2FA is enabled on your Gmail account

## 🛡️ Security Considerations

- **Environment Variables**: Never commit `.env` files
- **Email Credentials**: Use Gmail App Passwords, not regular passwords
- **Database Access**: SQLite file should have appropriate permissions
- **Port Security**: Consider firewall rules for production deployment

## 🧪 Development

### Adding New Tools
1. Create new MCP tool functions in `mcp_client/`
2. Register with `@mcp.tool()` decorator
3. Update agent initialization to include new tools

### Database Extensions
1. Modify schema in SQLite database
2. Update corresponding query functions
3. Test with sample data

### UI Customization
- Modify Gradio interface in `gradio_app.py`
- Update CSS styling and themes
- Add new interactive components

## 🐛 Troubleshooting

### Common Issues

**MCP Connection Failed**
```bash
# Check if servers are running
netstat -an | grep :9000
netstat -an | grep :9002
```

**SQLite Thread Errors**
- Ensure thread-safe database connections
- Check thread-local storage implementation

**Email Send Failures**
- Verify Gmail App Password
- Check SMTP settings and firewall

**Memory Issues**
- Monitor conversation history size
- Implement memory cleanup if needed

### Debug Mode
Enable detailed logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Database Schema

### Core Tables
- **milk_products**: id, product_name, brand_id, category_id, price_per_unit, package_size_ml, age_range_from, age_range_to, discount_percent, stock_quantity, is_active
- **milk_brands**: id, brand_name, country_of_origin, description, market_position, is_premium, logo_url
- **product_categories**: id, category_name, description, image_url

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## 📝 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) for modular tool architecture
- UI powered by [Gradio](https://gradio.app/) for interactive web interface
- Email functionality via Python's built-in SMTP library

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed description

---

**Made with ❤️ for intelligent e-commerce solutions**