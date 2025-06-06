def format_price(value):
    """Format price with currency symbol"""
    return f"${value:,.2f}"

def register_filters(app):
    """Register custom filters with Flask app"""
    app.jinja_env.filters['format_price'] = format_price 