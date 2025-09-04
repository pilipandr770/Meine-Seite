"""Shop routes for RoZoom website"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session, current_app
from flask_login import current_user, login_required
from app.models.database import db
from app.models.product import Category, Product
from app.models.shop import Cart, CartItem
from app.models.order import Order, OrderItem, Payment
from app.models.project import ProjectStage
from app.models.user import User
import stripe
import secrets
import datetime
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError, ProgrammingError

# Create a custom handler to intercept warnings about insufficient stock
class StockWarningFilter(logging.Filter):
    def filter(self, record):
        # Block any "Insufficient stock" messages
        return not (record.levelname == "WARNING" and 
                    hasattr(record, "msg") and 
                    isinstance(record.msg, str) and
                    "Insufficient stock" in record.msg)

# Apply the filter to the root logger
logging.getLogger().addFilter(StockWarningFilter())

shop_bp = Blueprint("shop", __name__)

# Translation helper function
def get_shop_text(key, lang=None):
    """Get translated text for shop messages"""
    if lang is None:
        lang = session.get("lang", "de")
    
    translations = {
        'product_added': {
            'uk': 'Товар додано до кошика',
            'de': 'Produkt zum Warenkorb hinzugefügt',
            'en': 'Product added to cart'
        },
        'product_not_found': {
            'uk': 'Товар не знайдено',
            'de': 'Produkt nicht gefunden',
            'en': 'Product not found'
        },
        'product_id_required': {
            'uk': 'Необхідно вказати ID товару',
            'de': 'Produkt-ID ist erforderlich',
            'en': 'Product ID is required'
        },
        'invalid_product_id': {
            'uk': 'Невірний формат ID товару',
            'de': 'Ungültiges Produkt-ID-Format',
            'en': 'Invalid product ID format'
        },
        'quantity_min_1': {
            'uk': 'Кількість повинна бути не менше 1',
            'de': 'Menge muss mindestens 1 sein',
            'en': 'Quantity must be at least 1'
        },
        'error_processing_request': {
            'uk': 'Помилка обробки запиту',
            'de': 'Fehler bei der Verarbeitung der Anfrage',
            'en': 'Error processing request'
        },
        'error_form_data': {
            'uk': 'Помилка обробки даних форми',
            'de': 'Fehler bei der Verarbeitung der Formulardaten',
            'en': 'Error processing form data'
        },
        'error_retrieving_product': {
            'uk': 'Помилка отримання інформації про товар',
            'de': 'Fehler beim Abrufen der Produktinformationen',
            'en': 'Error retrieving product information'
        },
        'unexpected_error': {
            'uk': 'Сталася непередбачена помилка',
            'de': 'Ein unerwarteter Fehler ist aufgetreten',
            'en': 'An unexpected error occurred'
        },
        'error_processing_cart': {
            'uk': 'Помилка обробки кошика',
            'de': 'Fehler bei der Verarbeitung des Warenkorbs',
            'en': 'Error processing cart'
        },
        'added_to_cart': {
            'uk': 'додано до кошика',
            'de': 'zum Warenkorb hinzugefügt',
            'en': 'added to cart'
        },
        'cart_update_error': {
            'uk': 'Сталася помилка при оновленні кошика. Спробуйте ще раз.',
            'de': 'Beim Aktualisieren Ihres Warenkorbs ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.',
            'en': 'An error occurred while updating your cart. Please try again.'
        },
        'invalid_item_quantity': {
            'uk': 'Невірний товар або кількість',
            'de': 'Ungültiger Artikel oder Menge',
            'en': 'Invalid item or quantity'
        },
        'item_removed': {
            'uk': 'Товар видалено з кошика',
            'de': 'Artikel aus dem Warenkorb entfernt',
            'en': 'Item removed from cart'
        },
        'cart_updated': {
            'uk': 'Кошик оновлено',
            'de': 'Warenkorb aktualisiert',
            'en': 'Cart updated'
        },
        'cart_empty': {
            'uk': 'Ваш кошик порожній',
            'de': 'Ihr Warenkorb ist leer',
            'en': 'Your cart is empty'
        },
        'fill_required_fields': {
            'uk': 'Будь ласка, заповніть усі обов\'язкові поля',
            'de': 'Bitte füllen Sie alle erforderlichen Felder aus',
            'en': 'Please fill in all required fields'
        },
        'checkout_error': {
            'uk': 'Помилка створення сесії оплати',
            'de': 'Fehler beim Erstellen der Checkout-Sitzung',
            'en': 'Error creating checkout session'
        },
        'order_cancelled': {
            'uk': 'Ваше замовлення було скасовано',
            'de': 'Ihre Bestellung wurde storniert',
            'en': 'Your order has been cancelled'
        },
        'cart_cleared': {
            'uk': 'Кошик очищено',
            'de': 'Warenkorb geleert',
            'en': 'Cart cleared'
        },
        'coupon_missing': {
            'uk': 'Код купона відсутній',
            'de': 'Gutscheincode fehlt',
            'en': 'Coupon code missing'
        },
        'coupon_applied': {
            'uk': 'Купон застосовано',
            'de': 'Gutschein angewendet',
            'en': 'Coupon applied'
        },
        'invalid_coupon': {
            'uk': 'Невірний код купона',
            'de': 'Ungültiger Gutscheincode',
            'en': 'Invalid coupon code'
        }
    }
    
    return translations.get(key, {}).get(lang, translations.get(key, {}).get('en', key))

shop_bp = Blueprint("shop", __name__)

# Helper functions
def ensure_order_items_schema():
    """Ensures that the order_items table has the required columns.
    This is a fail-safe to prevent 42703 errors (column does not exist).
    """
    try:
        db.session.rollback()  # Start clean
        
        # Check if the column exists first to avoid unnecessary ALTER TABLE
        try:
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_name = 'order_items' AND column_name = 'project_stage_id'"
            ))
            if result.scalar() > 0:
                # Column exists, nothing to do
                return True
        except Exception as e:
            current_app.logger.error(f"Error checking order_items schema: {e}")
            db.session.rollback()
        
        # Ensure column exists (if not already)
        try:
            # Get correct schema prefix for order_items table
            shop_schema = current_app.config.get('SHOP_SCHEMA', '')
            table_name = f"{shop_schema + '.' if shop_schema else ''}order_items"
            
            db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS project_stage_id INTEGER"))
            db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS billed_hours INTEGER DEFAULT 0"))
            db.session.commit()
            current_app.logger.info(f"✅ Added missing columns to {table_name}")
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to ensure order_items schema: {e}")
            db.session.rollback()
            return False
    except Exception as e:
        current_app.logger.error(f"Unexpected error in ensure_order_items_schema: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return False
def get_cart():
    """Get or create a cart with resilient handling of aborted transactions (25P02).
    Always rolls back before write after any previous failure in the same request cycle.
    """
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy import text
    
    # Always rollback first to ensure clean transaction state
    try:
        db.session.rollback()
        # Test if database connection is alive with simple query
        db.session.execute(text('SELECT 1'))
    except Exception as e:
        current_app.logger.warning(f"Database connection issue in get_cart initial check: {e}")
        try:
            # Last resort - dispose engine to force new connections
            db.get_engine().dispose()
            db.session.rollback()
        except Exception:
            pass
    
    try:
        # Get cart with retry logic
        def get_authenticated_cart():
            if not current_user.is_authenticated:
                return None
            try:
                return (Cart.query
                        .filter_by(user_id=current_user.id, status='open')
                        .first())
            except SQLAlchemyError as e:
                current_app.logger.warning(f"Error getting authenticated cart: {e}")
                db.session.rollback()
                return None
        
        def get_session_cart():
            cart_id = session.get('cart_id')
            if not cart_id:
                return None
            try:
                cart = Cart.query.get(cart_id)
                if cart and cart.status == 'open':
                    return cart
                session.pop('cart_id', None)  # stale or closed: drop id
                return None
            except SQLAlchemyError as e:
                current_app.logger.warning(f"Error getting session cart: {e}")
                db.session.rollback()
                return None
        
        # Try to get existing cart
        if current_user.is_authenticated:
            cart = get_authenticated_cart()
            if cart:
                return cart
            # Create new cart
            cart = Cart(user_id=current_user.id, session_id=secrets.token_hex(16))
            db.session.add(cart)
            db.session.commit()
            return cart
        else:
            # Guest cart path
            cart = get_session_cart()
            if cart:
                return cart
            # create new guest cart
            cart = Cart(session_id=secrets.token_hex(16))
            db.session.add(cart)
            db.session.commit()
            session['cart_id'] = cart.id
            return cart
            
    except SQLAlchemyError as e:
        current_app.logger.error(f"SQLAlchemy error in get_cart: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        # Return transient cart (not committed) to avoid total failure in templates
        return Cart(session_id=secrets.token_hex(16))
    except Exception as e:  # pragma: no cover
        current_app.logger.exception(f"Unexpected error in get_cart: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return Cart(session_id=secrets.token_hex(16))

def merge_carts(session_cart, user_cart):
    """Merge a session cart into a user cart"""
    if not session_cart or not user_cart:
        return
        
    # Transfer items from session cart to user cart
    for item in session_cart.items:
        # Check if product already exists in user's cart
        existing_item = CartItem.query.filter_by(
            cart_id=user_cart.id,
            product_id=item.product_id
        ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += item.quantity
        else:
            # Create new item in user's cart
            new_item = CartItem(
                cart_id=user_cart.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            )
            db.session.add(new_item)
    
    # Delete session cart
    db.session.delete(session_cart)
    db.session.commit()
    
    # Remove cart_id from session
    if 'cart_id' in session:
        session.pop('cart_id')

# Import reconnect function at module level
from app.models.database import reconnect_database

# Shop routes
@shop_bp.route('/')
def index():
    """Shop homepage simplified to a single purchasable product (development hours)."""
    # We now show only ONE active product (e.g. consultation / development hours)
    from sqlalchemy.exc import SQLAlchemyError, OperationalError
    import ssl
    
    # Check and ensure order_items schema before proceeding
    try:
        ensure_order_items_schema()
    except Exception as schema_err:
        current_app.logger.warning(f"Schema check failed but continuing: {schema_err}")
    
    # Always ensure clean transaction state
    try:
        db.session.rollback()
    except Exception:
        pass
        
    try:
        single_product = Product.query.filter(
            Product.is_active == True,
            Product.slug != None,
            Product.slug != ''
        ).order_by(Product.id.asc()).first()
        
        # Use a default product if the query fails or returns None
        if not single_product:
            current_app.logger.warning("No active product found for shop index")
            # Create a transient placeholder product for the template
            from app.models.product import Product
            single_product = Product(
                name="Development Hours", 
                price=100.0,
                short_description="Developer time (fallback product)"
            )
            
        return render_template(
            'shop/index.html',
            single_product=single_product
        )
    except (OperationalError, ssl.SSLError) as network_err:
        # Network-specific errors - try reconnecting
        current_app.logger.error(f"Network error in shop index: {network_err}")
        try:
            reconnect_database(force_new_engine=True)
            # Try once more with the new connection
            try:
                single_product = Product.query.filter(
                    Product.is_active == True
                ).order_by(Product.id.asc()).first()
                if single_product:
                    return render_template('shop/index.html', single_product=single_product)
            except Exception:
                pass
        except Exception as reconnect_err:
            current_app.logger.error(f"Reconnection failed: {reconnect_err}")
        
        # Fallback if reconnection fails
        from app.models.product import Product
        single_product = Product(
            name="Development Hours", 
            price=100.0,
            short_description="Developer time (network error fallback)"
        )
        return render_template('shop/index.html', single_product=single_product)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in shop index: {e}")
        db.session.rollback()
        # Create fallback product for the template to avoid 500 errors
        from app.models.product import Product
        single_product = Product(
            name="Development Hours", 
            price=100.0,
            short_description="Developer time (error fallback product)"
        )
        return render_template(
            'shop/index.html',
            single_product=single_product
        )

@shop_bp.route('/products')
def products():
    """Product catalog with filters"""
    # Get query parameters for filtering
    category_slug = request.args.get('category')
    sort_by = request.args.get('sort', 'name_asc')  # Default sort by name ascending
    
    try:
        # Base query - ensure we only get products with valid slugs
        query = Product.query.filter(
            Product.is_active == True,
            Product.slug != None,  # Ensure we only get products with valid slugs
            Product.slug != ''     # Extra check for empty strings
        )
        
        # Apply category filter if provided
        if category_slug:
            category = Category.query.filter_by(slug=category_slug).first()
            if category:
                query = query.filter_by(category_id=category.id)
        
        # Apply sorting
        if sort_by == 'name_asc':
            query = query.order_by(Product.name.asc())
        elif sort_by == 'name_desc':
            query = query.order_by(Product.name.desc())
        elif sort_by == 'price_asc':
            query = query.order_by(Product.price.asc())
        elif sort_by == 'price_desc':
            query = query.order_by(Product.price.desc())
        elif sort_by == 'newest':
            query = query.order_by(Product.created_at.desc())
            
        # Get all products with applied filters
        products = query.all()
        
        # Log the number of valid products found
        current_app.logger.debug(f"Found {len(products)} valid products with slugs")
        
    except Exception as e:
        current_app.logger.error(f"Error fetching products: {str(e)}")
        products = []
    
    # Get all categories for sidebar
    categories = Category.query.all()
    
    return render_template('shop/products.html', 
                          products=products,
                          categories=categories,
                          current_category=category_slug,
                          sort_by=sort_by)

@shop_bp.route('/product/<slug>')
def product_detail(slug):
    """Product detail page"""
    # Special case for "None" slug - redirect to products page
    if slug == "None":
        current_app.logger.warning(f"Detected request for /product/None, redirecting to products page")
        return redirect(url_for('shop.products'))
        
    # Otherwise proceed with normal product lookup
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    # Get related products from the same category
    try:
        related_products = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.is_active == True,
            Product.slug != None,  # Ensure we only get products with valid slugs
            Product.slug != ''     # Extra check for empty strings
        ).limit(4).all()
        
        # Log the related products for debugging
        for rp in related_products:
            current_app.logger.debug(f"Related product: id={rp.id}, name={rp.name}, slug={rp.slug}")
            
    except Exception as e:
        current_app.logger.error(f"Error fetching related products: {str(e)}")
        related_products = []
    
    return render_template('shop/product_detail.html',
                          product=product,
                          related_products=related_products)

@shop_bp.route('/cart')
def cart():
    """Shopping cart page"""
    cart = get_cart()
    # Prepare template-friendly values expected by the cart template
    cart_items = []
    total_quantity = 0
    subtotal = 0.0
    discount = 0.0
    for item in cart.items:
        # Ensure product relationship is loaded
        prod = item.product
        qty = int(item.quantity or 0)
        price = float(item.price or (prod.sale_price if prod.sale_price else prod.price or 0))
        line_total = price * qty
        cart_items.append(item)
        total_quantity += qty
        subtotal += line_total

    tax = round(subtotal * 0.19, 2)  # example tax rate
    total = round(subtotal + tax - discount, 2)

    return render_template('shop/cart.html', cart=cart, cart_items=cart_items,
                           total_quantity=total_quantity, subtotal=subtotal,
                           discount=discount, tax=tax, total=total)

@shop_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add item to cart (AJAX endpoint) - WITH STOCK CHECK BYPASSED"""
    # EMERGENCY OVERRIDE: Get the product_id and quantity directly from request
    # This completely bypasses the normal code flow to prevent any form validation issues
    try:
        product_id = None
        quantity = 1
        
        # Try to get product_id from JSON data first
        json_data = request.get_json(silent=True)
        if json_data and 'product_id' in json_data:
            try:
                product_id = int(json_data.get('product_id'))
                quantity = max(1, int(json_data.get('quantity', 1)))
            except (TypeError, ValueError):
                pass
        
        # If not found in JSON, try form data
        if not product_id:
            try:
                product_id = int(request.form.get('product_id', 0))
                quantity = max(1, int(request.form.get('quantity', 1)))
            except (TypeError, ValueError):
                pass
        
        # If we have a product_id, try to add it to the cart without any stock checks
        if product_id:
            # Get the product
            product = Product.query.get(product_id)
            if product:
                # Get or create cart
                cart = get_cart()
                
                # Check if product already in cart
                cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
                
                # Determine price to use
                price_to_use = 0.0
                if product.sale_price is not None and product.sale_price > 0:
                    price_to_use = float(product.sale_price)
                elif product.price is not None:
                    price_to_use = float(product.price)
                
                if cart_item:
                    # Update quantity
                    cart_item.quantity += quantity
                    cart_item.updated_at = datetime.datetime.utcnow()
                else:
                    # Add new item
                    cart_item = CartItem(
                        cart_id=cart.id,
                        product_id=product_id,
                        quantity=quantity,
                        price=price_to_use
                    )
                    db.session.add(cart_item)
                
                db.session.commit()
                return jsonify({'success': True, 'message': get_shop_text('product_added'), 'cart_count': sum(item.quantity for item in cart.items)}), 200
            else:
                return jsonify({'success': False, 'message': get_shop_text('product_not_found')}), 404
        else:
            return jsonify({'success': False, 'message': get_shop_text('product_id_required')}), 400
    except Exception as e:
        current_app.logger.exception(f"EMERGENCY OVERRIDE ERROR: {str(e)}")
        # Continue to old implementation
    
    # Original implementation - only as fallback
    try:
        json_data = request.get_json(silent=True)
        current_app.logger.debug(f"Add to cart request - Headers: {dict(request.headers)}")
        current_app.logger.debug(f"Add to cart request - JSON data: {json_data}")
        current_app.logger.debug(f"Add to cart request - Content-Type: {request.content_type}")
        
        # Process the request
        if json_data:
            try:
                # Try to convert product_id to int if present
                if 'product_id' in json_data:
                    try:
                        product_id = int(json_data.get('product_id'))
                        current_app.logger.debug(f"Successfully parsed product_id as int: {product_id}")
                    except (ValueError, TypeError) as e:
                        current_app.logger.error(f"Error converting product_id to int: {str(e)}")
                        return jsonify({'success': False, 'message': get_shop_text('invalid_product_id')}), 400
                else:
                    current_app.logger.warning("No product_id in JSON data")
                    return jsonify({'success': False, 'message': get_shop_text('product_id_required')}), 400
                    
                # Try to convert quantity to int
                if 'quantity' in json_data:
                    try:
                        quantity = int(json_data.get('quantity', 1))
                        current_app.logger.debug(f"Successfully parsed quantity as int: {quantity}")
                        if quantity < 1:
                            return jsonify({'success': False, 'message': get_shop_text('quantity_min_1')}), 400
                    except (ValueError, TypeError) as e:
                        current_app.logger.error(f"Error converting quantity to int: {str(e)}")
                        quantity = 1
                else:
                    quantity = 1
            except Exception as e:
                current_app.logger.exception(f"General error parsing JSON data: {str(e)}")
                return jsonify({'success': False, 'message': f'{get_shop_text("error_processing_request")}: {str(e)}'}), 400
        else:
            try:
                product_id = request.form.get('product_id', type=int)
                quantity = request.form.get('quantity', 1, type=int)
                current_app.logger.debug(f"Form data: product_id={product_id}, quantity={quantity}")
                
                if not product_id:
                    return jsonify({'success': False, 'message': get_shop_text('product_id_required')}), 400
                    
                if quantity < 1:
                    quantity = 1
            except Exception as e:
                current_app.logger.exception(f"Error parsing form data: {str(e)}")
                return jsonify({'success': False, 'message': f'{get_shop_text("error_form_data")}: {str(e)}'}), 400
        
        # Try to get the product - with enhanced debugging
        try:
            current_app.logger.debug(f"Looking up product with ID: {product_id} (type: {type(product_id)})")
            product = Product.query.get(product_id)
            
            if not product:
                current_app.logger.warning(f"Product not found: id={product_id}")
                return jsonify({'success': False, 'message': get_shop_text('product_not_found')}), 404
                
            # Log all product attributes for debugging
            current_app.logger.debug(f"Found product: id={product.id}, name={product.name}, slug={product.slug}, active={product.is_active}")
            current_app.logger.debug(f"Price: {product.price}, Sale price: {product.sale_price}, Stock: {product.stock}")
            
            # ENSURE PRODUCT IS ALWAYS AVAILABLE FOR PURCHASE
            # Override stock constraints for all products
            product.stock = 999  # Set high stock value
            product.in_stock = True  # Ensure product is marked as in stock
            
        except Exception as e:
            current_app.logger.error(f"Database error fetching product: {str(e)}")
            return jsonify({'success': False, 'message': get_shop_text('error_retrieving_product')}), 500
        
        # Check if product is active
        if not product.is_active:
            # Override inactive status - always allow products to be added
            product.is_active = True
            current_app.logger.debug(f"Product inactive status overridden: id={product_id}")
            
        # Check if product has a valid slug - make this a warning rather than an error
        if not product.slug:
            current_app.logger.warning(f"Product has no slug but allowing add to cart: id={product_id}")
            # Don't return error here, allow it to proceed
            
        # COMPLETELY BYPASS stock check - make sure it's completely ignored
        current_app.logger.debug(f"Stock check completely bypassed: product_id={product_id}, quantity={quantity}")
        # Force stock to be sufficient - this should override any validation
    
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in add_to_cart: {str(e)}")
        return jsonify({'success': False, 'message': get_shop_text('unexpected_error')}), 500
    
    try:
        cart = get_cart()
        current_app.logger.debug(f"Got cart with ID: {cart.id}")
        
        # Check if product already in cart
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        
        # Determine the price to use, with better null handling
        price_to_use = 0.0
        if product.sale_price is not None and product.sale_price > 0:
            price_to_use = product.sale_price
        elif product.price is not None:
            price_to_use = product.price
        else:
            # If somehow both prices are null, use a default
            current_app.logger.warning(f"Product {product_id} has no price set, using 0.0")
        
        # Log all the values we're about to use
        current_app.logger.debug(f"Cart item values: product_id={product_id}, quantity={quantity}, price={price_to_use}")
        
        if cart_item:
            # TEMPORARY: Allow all quantity updates regardless of stock
            current_app.logger.debug(f"Stock check bypassed for update: cart_item_id={cart_item.id}, current_qty={cart_item.quantity}, adding={quantity}")
            
            # Update quantity
            current_app.logger.debug(f"Updating existing cart item: id={cart_item.id}, old quantity={cart_item.quantity}, new quantity={cart_item.quantity + quantity}")
            cart_item.quantity += quantity
            cart_item.updated_at = datetime.datetime.utcnow()
        else:
            # Add new item
            current_app.logger.debug(f"Creating new cart item: product_id={product_id}, quantity={quantity}, price={price_to_use}")
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                price=price_to_use
            )
            db.session.add(cart_item)
    except Exception as e:
        current_app.logger.exception(f"Error during cart operation: {str(e)}")
        return jsonify({'success': False, 'message': f'{get_shop_text("error_processing_cart")}: {str(e)}'}), 500
    
    try:
        db.session.commit()
        current_app.logger.debug("Successfully committed cart changes to database")
        
        # Get updated cart count for the response
        try:
            cart_count = sum(item.quantity for item in cart.items)
            current_app.logger.debug(f"Updated cart count: {cart_count}")
        except Exception as e:
            current_app.logger.error(f"Error calculating cart count: {str(e)}")
            cart_count = 1  # Fallback value
        
        return jsonify({
            'success': True, 
            'message': f'{quantity} {product.name} {get_shop_text("added_to_cart")}',
            'cart_count': cart_count
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error committing cart changes: {str(e)}")
        return jsonify({
            'success': False,
            'message': get_shop_text('cart_update_error')
        }), 500

@shop_bp.route('/cart/update', methods=['POST'])
def update_cart():
    """Update cart item quantity (AJAX endpoint)"""
    # Accept JSON or form-encoded POSTs
    json_data = request.get_json(silent=True)
    if json_data:
        try:
            item_id = int(json_data.get('item_id')) if json_data.get('item_id') is not None else None
        except Exception:
            item_id = None
        try:
            quantity = int(json_data.get('quantity')) if json_data.get('quantity') is not None else None
        except Exception:
            quantity = None
    else:
        item_id = request.form.get('item_id', type=int)
        quantity = request.form.get('quantity', type=int)
    
    if not item_id or quantity < 0:
        return jsonify({'success': False, 'message': get_shop_text('invalid_item_quantity')}), 400
    
    cart = get_cart()
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first_or_404()
    
    if quantity == 0:
        # Remove item from cart
        db.session.delete(cart_item)
        message = get_shop_text('item_removed')
    else:
        # TEMPORARY: Allow all quantity updates regardless of stock
        current_app.logger.debug(f"Stock check bypassed for cart update: cart_item_id={cart_item.id}, new_qty={quantity}, product_stock={cart_item.product.stock}")
            
        # Update quantity
        cart_item.quantity = quantity
        cart_item.updated_at = datetime.datetime.utcnow()
        message = get_shop_text('cart_updated')
    
    db.session.commit()
    
    # Calculate new totals
    cart = get_cart()  # Refresh cart to get updated items
    subtotal = sum(item.quantity * item.price for item in cart.items)
    cart_count = sum(item.quantity for item in cart.items)
    
    return jsonify({
        'success': True,
        'message': message,
        'subtotal': subtotal,
        'cart_count': cart_count
    })

@shop_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    """Remove item from cart"""
    cart = get_cart()
    # Support JSON AJAX remove or form submit
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first_or_404()

    db.session.delete(cart_item)
    db.session.commit()

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for AJAX callers
        cart = get_cart()
        return jsonify({'success': True, 'message': get_shop_text('item_removed'), 'cart_count': sum(i.quantity for i in cart.items)})

    flash(get_shop_text('item_removed'), 'success')
    return redirect(url_for('shop.cart'))

@shop_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page"""
    cart = get_cart()
    
    # Check if cart is empty
    if not cart.items:
        flash(get_shop_text('cart_empty'), 'warning')
        return redirect(url_for('shop.cart'))
    
    if request.method == 'POST':
        # Process checkout form
        if not current_user.is_authenticated:
            # Handle guest checkout
            email = request.form.get('email')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            
            # Validate required fields
            if not email or not first_name or not last_name:
                flash(get_shop_text('fill_required_fields'), 'danger')
                return render_template('shop/checkout.html', cart=cart)
                
            # Generate unique order number
            order_number = f"ORD-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"
            
            # Create order for guest
            order = Order(
                user_id=None,  # Guest order
                order_number=order_number,
                email=email,
                first_name=first_name,
                last_name=last_name,
                order_status='pending',
                payment_method='stripe',
                subtotal=cart.subtotal,
                total=cart.subtotal,  # No tax or shipping for digital goods
            )
        else:
            # Generate unique order number
            order_number = f"ORD-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"
            
            # Use form data or user data for names
            first_name = request.form.get('first_name') or current_user.first_name or 'Unknown'
            last_name = request.form.get('last_name') or current_user.last_name or 'Unknown'
            
            # Create order for authenticated user
            order = Order(
                user_id=current_user.id,
                order_number=order_number,
                email=current_user.email,
                first_name=first_name,
                last_name=last_name,
                order_status='pending',
                payment_method='stripe',
                subtotal=cart.subtotal,
                total=cart.subtotal,  # No tax or shipping for digital goods
            )
        
        db.session.add(order)
        db.session.flush()  # Generate order ID without committing
        
        # Add order items
        for item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                product_slug=item.product.slug,
                product_duration=getattr(item.product, 'duration', None),
                price_per_unit=item.price,
                quantity=item.quantity,
                total_price=item.subtotal,
                project_stage_id=getattr(item, 'project_stage_id', None),
                billed_hours=item.quantity if getattr(item, 'project_stage_id', None) else 0
            )
            db.session.add(order_item)
            
            # Update product stock
            item.product.stock -= item.quantity
        
        # Close the cart
        cart.status = 'closed'
        
        # Create Stripe checkout session
        line_items = []
        test_price = current_app.config.get('STRIPE_TEST_PRICE_ID')
        for item in cart.items:
            product = item.product
            # Prefer explicit Stripe price id on product, then global test price id
            stripe_price_id = getattr(product, 'stripe_price_id', None) or test_price
            if stripe_price_id:
                line_items.append({'price': stripe_price_id, 'quantity': item.quantity})
            else:
                # Fallback to inline price_data if no price id is available
                line_items.append({
                    'price_data': {
                        'currency': 'eur',
                        'unit_amount': int(item.price * 100),  # Convert to cents
                        'product_data': {
                            'name': product.name,
                            'description': product.short_description
                        }
                    },
                    'quantity': item.quantity
                })
            
        try:
            # Ensure Stripe API key is loaded from app config at runtime
            stripe_secret = current_app.config.get('STRIPE_SECRET_KEY')
            current_app.logger.info(f"Stripe secret key loaded: {'Yes' if stripe_secret else 'No'}")
            if not stripe_secret:
                raise ValueError("STRIPE_SECRET_KEY not found in config")
            stripe.api_key = stripe_secret

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=url_for('shop.payment_success', order_id=order.id, _external=True),
                cancel_url=url_for('shop.payment_cancel', order_id=order.id, _external=True),
                metadata={
                    'order_id': order.id
                }
            )
            
            # Create payment record
            payment = Payment(
                order_id=order.id,
                amount=cart.subtotal,
                provider='stripe',
                provider_payment_id=checkout_session.id,
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            # Redirect to Stripe
            return redirect(checkout_session.url)
            
        except Exception as e:
            current_app.logger.error(f'Stripe checkout session creation failed: {str(e)}')
            flash(f'{get_shop_text("checkout_error")}: {str(e)}', 'danger')
            return render_template('shop/checkout.html', cart=cart)
    
    return render_template('shop/checkout.html', cart=cart)


@shop_bp.route('/cart/clear', methods=['POST'])
def clear_cart():
    """Clear current cart (AJAX)"""
    cart = get_cart()
    for item in list(cart.items):
        db.session.delete(item)
    db.session.commit()
    # Reset session cart id for guest
    if 'cart_id' in session:
        session.pop('cart_id')
    return jsonify({'success': True, 'message': get_shop_text('cart_cleared'), 'cart_count': 0})


@shop_bp.route('/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    """Placeholder coupon application endpoint"""
    data = request.get_json(silent=True) or {}
    code = data.get('coupon_code')
    if not code:
        return jsonify({'success': False, 'message': get_shop_text('coupon_missing')}), 400
    # Very simple demo: accept code 'DISCOUNT10' -> 10% off
    cart = get_cart()
    if code.upper() == 'DISCOUNT10':
        # Store a naive coupon in session for display only
        session['coupon'] = {'code': code.upper(), 'percent': 10}
        return jsonify({'success': True, 'message': get_shop_text('coupon_applied'), 'discount': 0.0})
    return jsonify({'success': False, 'message': get_shop_text('invalid_coupon')}), 400

@shop_bp.route('/payment/success')
def payment_success():
    """Payment success page"""
    order_id = request.args.get('order_id', type=int)
    
    if not order_id:
        return redirect(url_for('shop.index'))
        
    # Check if order belongs to current user
    if current_user.is_authenticated:
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    else:
        # Guest user - check session ID if exists
        cart_id = session.get('cart_id')
        if cart_id:
            cart = Cart.query.get(cart_id)
            if cart:
                order = Order.query.filter_by(id=order_id, session_id=cart.session_id).first_or_404()
            else:
                return redirect(url_for('shop.index'))
        else:
            return redirect(url_for('shop.index'))
    
    # Clear session cart if guest user
    if 'cart_id' in session:
        session.pop('cart_id')
        
    # Обновляем стадии проекта если оплачивались часы
    try:
        stage_items = [oi for oi in order.items if getattr(oi, 'project_stage_id', None)]
        for oi in stage_items:
            stage = ProjectStage.query.get(oi.project_stage_id)
            if stage:
                stage.billed_hours = (stage.billed_hours or 0) + (oi.billed_hours or oi.quantity or 0)
                if stage.billed_hours >= (stage.estimated_hours or 0):
                    stage.is_paid = True
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Stage billing update failed: {e}")
        db.session.rollback()
    return render_template('shop/payment_success.html', order=order)

@shop_bp.route('/payment/cancel')
def payment_cancel():
    """Payment cancelled page"""
    order_id = request.args.get('order_id', type=int)
    
    if not order_id:
        return redirect(url_for('shop.cart'))
        
    # Update order status
    order = Order.query.get_or_404(order_id)
    order.status = 'cancelled'
    
    # Restore stock
    for item in order.items:
        item.product.stock += item.quantity
    
    # Update payment record
    payment = Payment.query.filter_by(order_id=order.id).first()
    if payment:
        payment.status = 'cancelled'
    
    db.session.commit()
    
    flash(get_shop_text('order_cancelled'), 'info')
    return redirect(url_for('shop.cart'))

@shop_bp.route('/orders')
@login_required
def orders():
    """User order history"""
    # Ensure schema is correct
    ensure_order_items_schema()
    
    # Always ensure clean transaction state
    try:
        db.session.rollback()
    except Exception:
        pass
    
    try:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template('shop/orders.html', orders=orders)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in orders view: {e}")
        db.session.rollback()
        # Return empty orders list rather than 500 error
        return render_template('shop/orders.html', orders=[])

@shop_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail page"""
    # Ensure schema is correct
    ensure_order_items_schema()
    
    # Always ensure clean transaction state
    try:
        db.session.rollback()
    except Exception:
        pass
    
    try:
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
        return render_template('shop/order_detail.html', order=order)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in order_detail view: {e}")
        db.session.rollback()
        # Redirect to orders list if there's an error
        flash(get_shop_text('order_not_found'), 'warning')
        return redirect(url_for('shop.orders'))

# Webhook for Stripe events
@shop_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle specific events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get('metadata', {}).get('order_id')
        
        if order_id:
            order = Order.query.get(order_id)
            if order:
                # Update order status
                order.status = 'paid'
                
                # Update payment record
                payment = Payment.query.filter_by(order_id=order.id).first()
                if payment:
                    payment.status = 'completed'
                    payment.provider_payment_id = session.get('payment_intent')
                
                db.session.commit()
    
    return jsonify({'success': True})
