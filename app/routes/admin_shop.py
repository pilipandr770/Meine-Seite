from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy import desc
from werkzeug.utils import secure_filename
from app.models.product import Product, Category, ProductImage, ProductReview
from app.models.order import Order, OrderStatus, PaymentStatus, OrderItem
from app.models.coupon import Coupon
from app import db
import os
import uuid
from datetime import datetime
from flask import current_app

admin_shop = Blueprint('admin_shop', __name__)

# Utility Functions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, subfolder='products', product_id=None, category_id=None):
    current_app.logger.debug(f"save_image called with subfolder={subfolder}, product_id={product_id}, category_id={category_id}")
    if file and allowed_file(file.filename):
        current_app.logger.debug(f"File is valid: {file.filename}, mimetype: {file.mimetype}")
        filename = secure_filename(file.filename)
        # Add unique identifier to filename to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        current_app.logger.debug(f"Generated unique filename: {unique_filename}")
        
        try:
            # Prefer storing image binary in DB for production portability
            from app.models.product import ProductImage, db
            
            # Check if it's a category image
            if category_id is not None:
                current_app.logger.debug(f"Storing image in DB for category_id={category_id}")
                # Import Category to update its fields directly
                from app.models.product import Category
                
                category = Category.query.get(category_id)
                if not category:
                    current_app.logger.error(f"Category with ID {category_id} not found")
                    return None
                
                file.stream.seek(0)
                binary = file.read()
                current_app.logger.debug(f"Read {len(binary)} bytes from category file")
                
                # Store directly in Category model's new fields
                category.image_data = binary
                category.image_content_type = file.mimetype
                category.image_filename = unique_filename
                
                # Update URL to point to the category image service route
                db.session.flush()  # ensure category ID is available
                return f'/category_media/category-image/{category.id}'
                
            # Only store in DB if we have a product_id to satisfy NOT NULL constraint
            elif product_id is not None:
                current_app.logger.debug(f"Storing image in DB for product_id={product_id}")
                file.stream.seek(0)
                binary = file.read()
                current_app.logger.debug(f"Read {len(binary)} bytes from file")
                img = ProductImage(
                    product_id=product_id,
                    url=None,
                    alt=file.filename,
                    data=binary,
                    filename=unique_filename,
                    content_type=file.mimetype
                )
                db.session.add(img)
                db.session.flush()  # get id
                current_app.logger.debug(f"Image stored in DB with ID: {img.id}")
                # do not commit here; caller may commit transaction
                return url_for('media.serve_image', image_id=img.id)
            # if no product_id provided, fall back to filesystem below
            current_app.logger.debug(f"No product_id or category_id provided, falling back to filesystem storage")
        except Exception as e:
            current_app.logger.exception(f'Failed to save image to DB: {str(e)}, falling back to filesystem')
            
        # Either product_id was None or DB storage failed, try filesystem
        try:
            current_app.logger.debug(f"Attempting to save image to filesystem in subfolder: {subfolder}")
            static_folder = current_app.static_folder or os.path.join('app', 'static')
            upload_folder = os.path.join(static_folder, 'uploads', subfolder)
            current_app.logger.debug(f"Upload folder path: {upload_folder}")
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            current_app.logger.debug(f"Final file path: {file_path}")
            
            # Reset file position to beginning before saving
            file.stream.seek(0)
            current_app.logger.debug("File position reset to beginning")
            
            # Check if file has content
            content = file.read()
            file.stream.seek(0)  # Reset again after reading
            current_app.logger.debug(f"File content length before save: {len(content)}")
            
            # Now save the file
            file.save(file_path)
            
            # Verify the file was saved correctly
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                current_app.logger.debug(f"File saved successfully. File size: {file_size} bytes")
                if file_size == 0:
                    current_app.logger.error("File was saved but is empty!")
                    
            url = url_for('static', filename=f'uploads/{subfolder}/{unique_filename}')
            current_app.logger.debug(f"Generated URL: {url}")
            return url
        except Exception as e:
            current_app.logger.exception(f'Failed to save uploaded image to filesystem: {str(e)}')
            return None
    else:
        if not file:
            current_app.logger.error("No file provided")
        else:
            current_app.logger.error(f"File has invalid extension: {file.filename}")
        return None

# Product Management
@admin_shop.route('/products')
@login_required
def products():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Get query parameters
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status')
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = Product.query
    
    # Apply filters
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if status == 'active':
        query = query.filter(Product.is_active == True)
    elif status == 'inactive':
        query = query.filter(Product.is_active == False)
    elif status == 'featured':
        query = query.filter(Product.is_featured == True)
    
    # Apply sorting
    if sort == 'name_asc':
        query = query.order_by(Product.name.asc())
    elif sort == 'name_desc':
        query = query.order_by(Product.name.desc())
    elif sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())
    
    # Get products
    products = query.all()
    
    # Get all categories
    categories = Category.query.all()
    
    return render_template(
        'admin/shop/products.html',
        products=products,
        categories=categories,
        search=search,
        category_id=category_id,
        status=status,
        sort=sort
    )

@admin_shop.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        price = request.form.get('price')
        
        if not name or not price:
            flash('Name and price are required fields', 'danger')
            return redirect(url_for('admin_shop.add_product'))
        
        try:
            # Create product
            product = Product(
                name=name,
                category_id=category_id if category_id else None,
                price=float(price),
                sale_price=float(request.form.get('sale_price')) if request.form.get('sale_price') else None,
                short_description=request.form.get('short_description'),
                description=request.form.get('description'),
                duration=int(request.form.get('duration')) if request.form.get('duration') else None,
                format=request.form.get('format'),
                language=request.form.get('language'),
                prerequisites=request.form.get('prerequisites'),
                includes=request.form.get('includes'),
                is_active=bool(request.form.get('is_active')),
                is_featured=bool(request.form.get('is_featured')),
                in_stock=bool(request.form.get('in_stock', True))
            )
            
            db.session.add(product)
            db.session.flush()  # Get product ID for image saving
            
            # Handle image upload with product_id available
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    image_path = save_image(file, product_id=product.id)
                    if image_path:
                        product.image = image_path
            
            db.session.commit()  # Actually save the product
            
            flash('Product added successfully', 'success')
            return redirect(url_for('admin_shop.products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
            return redirect(url_for('admin_shop.add_product'))
    
    # Get all categories for the form
    categories = Category.query.all()
    
    return render_template(
        'admin/shop/product_form.html',
        categories=categories,
        product=None
    )

@admin_shop.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            db.session.add(product)
            db.session.flush()  # ensure product.id available for image save

            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    image_path = save_image(file, product_id=product.id)
                    if image_path:
                        product.image = image_path

            db.session.commit()
            product.includes = request.form.get('includes')
            product.is_active = bool(request.form.get('is_active'))
            product.is_featured = bool(request.form.get('is_featured'))
            product.in_stock = bool(request.form.get('in_stock'))
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    image_path = save_image(file, product_id=product.id)
                    if image_path:
                        product.image = image_path
            
            db.session.commit()
            
            flash('Product updated successfully', 'success')
            return redirect(url_for('admin_shop.products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
            return redirect(url_for('admin_shop.edit_product', product_id=product_id))
    
    # Get all categories for the form
    categories = Category.query.all()
    
    return render_template(
        'admin/shop/product_form.html',
        product=product,
        categories=categories
    )

@admin_shop.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    product = Product.query.get_or_404(product_id)
    
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Category Management
@admin_shop.route('/categories')
@login_required
def categories():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    categories = Category.query.all()
    
    return render_template(
        'admin/shop/categories.html',
        categories=categories
    )

@admin_shop.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        
        if not name:
            flash('Name is required', 'danger')
            return redirect(url_for('admin_shop.add_category'))
        
        try:
            # Create category
            category = Category(
                name=name,
                description=request.form.get('description'),
                is_active=bool(request.form.get('is_active', True))
            )
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    current_app.logger.info(f"Processing image upload for category: {name}")
                    # Make a clean copy of the file to avoid stream position issues
                    file.stream.seek(0)
                    
                    # Save to database - pass category_id = None since it's not created yet
                    db.session.add(category)
                    db.session.flush()  # To get the category ID
                    
                    image_path = save_image(file, subfolder='categories', category_id=category.id)
                    if image_path:
                        category.image = image_path
                        current_app.logger.info(f"Image path set for category: {image_path}")
                    else:
                        current_app.logger.error("Failed to save category image")
                        flash('Failed to save category image', 'warning')
            
            db.session.add(category)
            db.session.commit()
            
            flash('Category added successfully', 'success')
            return redirect(url_for('admin_shop.categories'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding category: {str(e)}', 'danger')
            return redirect(url_for('admin_shop.add_category'))
    
    return render_template(
        'admin/shop/category_form.html',
        category=None
    )

@admin_shop.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        try:
            # Update category
            category.name = request.form.get('name')
            category.description = request.form.get('description')
            category.is_active = bool(request.form.get('is_active'))
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    current_app.logger.info(f"Processing image upload for category update: {category.name}")
                    # Make a clean copy of the file to avoid stream position issues
                    file.stream.seek(0)
                    
                    # Save to database - pass the existing category.id
                    image_path = save_image(file, subfolder='categories', category_id=category.id)
                    if image_path:
                        category.image = image_path
                        current_app.logger.info(f"Updated image path for category: {image_path}")
                    else:
                        current_app.logger.error("Failed to save category image on update")
                        flash('Failed to update category image', 'warning')
            
            db.session.commit()
            
            flash('Category updated successfully', 'success')
            return redirect(url_for('admin_shop.categories'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'danger')
            return redirect(url_for('admin_shop.edit_category', category_id=category_id))
    
    return render_template(
        'admin/shop/category_form.html',
        category=category
    )

@admin_shop.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    category = Category.query.get_or_404(category_id)
    
    # Check if category has products
    if category.products:
        return jsonify({
            'success': False, 
            'message': 'Cannot delete category with associated products'
        })
    
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Order Management
@admin_shop.route('/orders')
@login_required
def orders():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Get query parameters
    search = request.args.get('search', '')
    status = request.args.get('status')
    payment_status = request.args.get('payment_status')
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = Order.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Order.order_number.ilike(f'%{search}%')) | 
            (Order.email.ilike(f'%{search}%')) |
            (Order.first_name.ilike(f'%{search}%')) |
            (Order.last_name.ilike(f'%{search}%'))
        )
    
    if status:
        query = query.filter(Order.order_status == status)
    
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)
    
    # Apply sorting
    if sort == 'total_asc':
        query = query.order_by(Order.total.asc())
    elif sort == 'total_desc':
        query = query.order_by(Order.total.desc())
    else:  # newest
        query = query.order_by(Order.created_at.desc())
    
    # Get orders
    orders = query.all()
    
    # Get statuses for filter dropdowns
    order_statuses = [e.value for e in OrderStatus]
    payment_statuses = [e.value for e in PaymentStatus]
    
    return render_template(
        'admin/shop/orders.html',
        orders=orders,
        order_statuses=order_statuses,
        payment_statuses=payment_statuses,
        search=search,
        status=status,
        payment_status=payment_status,
        sort=sort
    )

@admin_shop.route('/orders/<int:order_id>')
@login_required
def view_order(order_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    order = Order.query.get_or_404(order_id)
    
    return render_template(
        'admin/shop/order_detail.html',
        order=order
    )

@admin_shop.route('/orders/update-status', methods=['POST'])
@login_required
def update_order_status():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json()
    order_id = data.get('order_id')
    new_status = data.get('status')
    
    order = Order.query.get_or_404(order_id)
    
    try:
        order.order_status = new_status
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_shop.route('/orders/update-payment-status', methods=['POST'])
@login_required
def update_payment_status():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json()
    order_id = data.get('order_id')
    new_status = data.get('status')
    
    order = Order.query.get_or_404(order_id)
    
    try:
        order.payment_status = new_status
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Reviews Management
@admin_shop.route('/reviews')
@login_required
def reviews():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Get query parameters
    status = request.args.get('status')
    product_id = request.args.get('product_id', type=int)
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = ProductReview.query
    
    # Apply filters
    if status == 'approved':
        query = query.filter(ProductReview.is_approved == True)
    elif status == 'pending':
        query = query.filter(ProductReview.is_approved == False)
    
    if product_id:
        query = query.filter(ProductReview.product_id == product_id)
    
    # Apply sorting
    if sort == 'rating_asc':
        query = query.order_by(ProductReview.rating.asc())
    elif sort == 'rating_desc':
        query = query.order_by(ProductReview.rating.desc())
    else:  # newest
        query = query.order_by(ProductReview.created_at.desc())
    
    # Get reviews
    reviews = query.all()
    
    # Get all products for filter dropdown
    products = Product.query.all()
    
    return render_template(
        'admin/shop/reviews.html',
        reviews=reviews,
        products=products,
        status=status,
        product_id=product_id,
        sort=sort
    )

@admin_shop.route('/reviews/approve/<int:review_id>', methods=['POST'])
@login_required
def approve_review(review_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    review = ProductReview.query.get_or_404(review_id)
    
    try:
        review.is_approved = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_shop.route('/reviews/reject/<int:review_id>', methods=['POST'])
@login_required
def reject_review(review_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    review = ProductReview.query.get_or_404(review_id)
    
    try:
        review.is_approved = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_shop.route('/reviews/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    review = ProductReview.query.get_or_404(review_id)
    
    try:
        db.session.delete(review)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Coupon Management
@admin_shop.route('/coupons')
@login_required
def coupons():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Get query parameters
    status = request.args.get('status')
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = Coupon.query
    
    # Apply filters
    if status == 'active':
        query = query.filter(Coupon.is_active == True)
    elif status == 'inactive':
        query = query.filter(Coupon.is_active == False)
    
    # Apply sorting
    if sort == 'code':
        query = query.order_by(Coupon.code)
    elif sort == 'value_desc':
        query = query.order_by(Coupon.discount_value.desc())
    else:  # newest
        query = query.order_by(Coupon.created_at.desc())
    
    # Get coupons
    coupons = query.all()
    
    return render_template(
        'admin/shop/coupons.html',
        coupons=coupons,
        status=status,
        sort=sort
    )

@admin_shop.route('/coupons/add', methods=['GET', 'POST'])
@login_required
def add_coupon():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        code = request.form.get('code')
        discount_type = request.form.get('discount_type')
        discount_value = request.form.get('discount_value')
        
        if not code or not discount_type or not discount_value:
            flash('Code, discount type, and discount value are required', 'danger')
            return redirect(url_for('admin_shop.add_coupon'))
        
        try:
            # Create coupon
            coupon = Coupon(
                code=code.upper(),
                description=request.form.get('description'),
                discount_type=discount_type,
                discount_value=float(discount_value),
                is_active=bool(request.form.get('is_active', True)),
                usage_limit=int(request.form.get('usage_limit')) if request.form.get('usage_limit') else None
            )
            
            # Handle valid_from date
            if request.form.get('valid_from'):
                valid_from = datetime.strptime(request.form.get('valid_from'), '%Y-%m-%d')
                coupon.valid_from = valid_from
            
            # Handle valid_to date
            if request.form.get('valid_to'):
                valid_to = datetime.strptime(request.form.get('valid_to'), '%Y-%m-%d')
                coupon.valid_to = valid_to
            
            db.session.add(coupon)
            db.session.commit()
            
            flash('Coupon added successfully', 'success')
            return redirect(url_for('admin_shop.coupons'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding coupon: {str(e)}', 'danger')
            return redirect(url_for('admin_shop.add_coupon'))
    
    return render_template(
        'admin/shop/coupon_form.html',
        coupon=None
    )

@admin_shop.route('/coupons/edit/<int:coupon_id>', methods=['GET', 'POST'])
@login_required
def edit_coupon(coupon_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    coupon = Coupon.query.get_or_404(coupon_id)
    
    if request.method == 'POST':
        try:
            # Update coupon
            coupon.code = request.form.get('code').upper()
            coupon.description = request.form.get('description')
            coupon.discount_type = request.form.get('discount_type')
            coupon.discount_value = float(request.form.get('discount_value'))
            coupon.is_active = bool(request.form.get('is_active'))
            coupon.usage_limit = int(request.form.get('usage_limit')) if request.form.get('usage_limit') else None
            
            # Handle valid_from date
            if request.form.get('valid_from'):
                valid_from = datetime.strptime(request.form.get('valid_from'), '%Y-%m-%d')
                coupon.valid_from = valid_from
            else:
                coupon.valid_from = None
            
            # Handle valid_to date
            if request.form.get('valid_to'):
                valid_to = datetime.strptime(request.form.get('valid_to'), '%Y-%m-%d')
                coupon.valid_to = valid_to
            else:
                coupon.valid_to = None
            
            db.session.commit()
            
            flash('Coupon updated successfully', 'success')
            return redirect(url_for('admin_shop.coupons'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating coupon: {str(e)}', 'danger')
            return redirect(url_for('admin_shop.edit_coupon', coupon_id=coupon_id))
    
    return render_template(
        'admin/shop/coupon_form.html',
        coupon=coupon
    )

@admin_shop.route('/coupons/delete/<int:coupon_id>', methods=['POST'])
@login_required
def delete_coupon(coupon_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    coupon = Coupon.query.get_or_404(coupon_id)
    
    # Check if coupon has been used in orders
    if coupon.orders:
        return jsonify({
            'success': False, 
            'message': 'Cannot delete coupon that has been used in orders'
        })
    
    try:
        db.session.delete(coupon)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Dashboard
@admin_shop.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Orders statistics
    total_orders = Order.query.count()
    completed_orders = Order.query.filter_by(order_status='completed').count()
    pending_orders = Order.query.filter_by(order_status='pending').count()
    
    # Calculate revenue
    revenue = db.session.query(db.func.sum(Order.total)).filter(
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    # Top products
    top_products = db.session.query(
        Product, 
        db.func.sum(OrderItem.quantity).label('total_quantity')
    ).join(
        OrderItem, 
        OrderItem.product_id == Product.id
    ).group_by(
        Product.id
    ).order_by(
        db.desc('total_quantity')
    ).limit(5).all()
    
    # Recent reviews
    recent_reviews = ProductReview.query.order_by(
        ProductReview.created_at.desc()
    ).limit(5).all()
    
    # Pending reviews count
    pending_reviews = ProductReview.query.filter_by(is_approved=False).count()
    
    return render_template(
        'admin/shop/dashboard.html',
        recent_orders=recent_orders,
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        revenue=revenue,
        top_products=top_products,
        recent_reviews=recent_reviews,
        pending_reviews=pending_reviews
    )


@admin_shop.route('/uploads-status')
@login_required
def uploads_status():
    """Admin-only endpoint that reports whether product/category image files exist on disk.
    Returns JSON with lists of products and categories and a boolean `exists` flag.
    """
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    results = {'products': [], 'categories': []}

    static_folder = current_app.static_folder or os.path.join('app', 'static')

    # Products
    for p in Product.query.all():
        img = p.image or ''
        fs_path = None
        exists = False
        if img.startswith('/static/'):
            rel = img.replace('/static/', '', 1)
            fs_path = os.path.join(static_folder, rel)
            exists = os.path.exists(fs_path)
        results['products'].append({
            'id': p.id,
            'name': p.name,
            'image': img,
            'file_path': fs_path,
            'exists': exists
        })

    # Categories
    for c in Category.query.all():
        img = c.image or ''
        fs_path = None
        exists = False
        if img.startswith('/static/'):
            rel = img.replace('/static/', '', 1)
            fs_path = os.path.join(static_folder, rel)
            exists = os.path.exists(fs_path)
        results['categories'].append({
            'id': c.id,
            'name': c.name,
            'image': img,
            'file_path': fs_path,
            'exists': exists
        })

    return jsonify(results)
