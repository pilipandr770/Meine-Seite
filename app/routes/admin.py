"""Admin routes and controllers"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.database import db
from app.models.user import User
from app.models.product import Category, Product, ProductImage, ProductReview
from app.models.order import Order, OrderItem, Payment
from app.utils.decorators import admin_required
from app.utils.slug import generate_slug
from app.forms.admin import CategoryForm, ProductForm, OrderStatusForm
import datetime

admin_bp = Blueprint("admin", __name__)

# Dashboard
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    # Get counts for the dashboard
    products_count = Product.query.count()
    orders_count = Order.query.count()
    users_count = User.query.filter(User.is_admin == False).count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Order.total)) \
                    .filter(Order.status == 'paid').scalar() or 0
    
    # Get pending orders
    pending_orders = Order.query.filter_by(status='pending').count()
    
    # Get low stock products
    low_stock_products = Product.query.filter(Product.stock <= 3).all()
    
    return render_template('admin/dashboard.html', 
                          products_count=products_count,
                          orders_count=orders_count,
                          users_count=users_count,
                          recent_orders=recent_orders,
                          total_revenue=total_revenue,
                          pending_orders=pending_orders,
                          low_stock_products=low_stock_products)

# Categories
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """List all categories"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories/index.html', categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    """Create a new category"""
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            slug=generate_slug(form.name.data),
            description=form.description.data,
            image=form.image.data if hasattr(form, 'image') else None
        )
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/categories/create.html', form=form)

@admin_bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    """Edit a category"""
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        if category.slug != generate_slug(form.name.data):
            category.slug = generate_slug(form.name.data)
        category.description = form.description.data
        if hasattr(form, 'image') and form.image.data:
            category.image = form.image.data
        
        db.session.commit()
        flash('Category updated successfully', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/categories/edit.html', form=form, category=category)

@admin_bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    """Delete a category"""
    category = Category.query.get_or_404(id)
    
    # Check if category has products
    if category.products:
        flash('Cannot delete category with products', 'danger')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully', 'success')
    return redirect(url_for('admin.categories'))

# Products
@admin_bp.route('/products')
@login_required
@admin_required
def products():
    """List all products"""
    products = Product.query.order_by(Product.name).all()
    return render_template('admin/products/index.html', products=products)

@admin_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_product():
    """Create a new product"""
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            slug=generate_slug(form.name.data),
            description=form.description.data,
            short_description=form.short_description.data,
            price=form.price.data,
            sale_price=form.sale_price.data if form.sale_price.data else None,
            image=form.image.data if hasattr(form, 'image') and form.image.data else None,
            stock=form.stock.data,
            is_active=form.is_active.data,
            is_featured=form.is_featured.data,
            category_id=form.category_id.data,
            duration=form.duration.data,
            is_virtual=form.is_virtual.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product created successfully', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/products/create.html', form=form)

@admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    """Edit a product"""
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
    
    if form.validate_on_submit():
        product.name = form.name.data
        if product.slug != generate_slug(form.name.data):
            product.slug = generate_slug(form.name.data)
        product.description = form.description.data
        product.short_description = form.short_description.data
        product.price = form.price.data
        product.sale_price = form.sale_price.data if form.sale_price.data else None
        if hasattr(form, 'image') and form.image.data:
            product.image = form.image.data
        product.stock = form.stock.data
        product.is_active = form.is_active.data
        product.is_featured = form.is_featured.data
        product.category_id = form.category_id.data
        product.duration = form.duration.data
        product.is_virtual = form.is_virtual.data
        product.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/products/edit.html', form=form, product=product)

@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    """Delete a product"""
    product = Product.query.get_or_404(id)
    
    # Check if product has order items
    if product.order_items:
        flash('Cannot delete product with orders', 'danger')
        return redirect(url_for('admin.products'))
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully', 'success')
    return redirect(url_for('admin.products'))

# Orders
@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """List all orders"""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders/index.html', orders=orders)

@admin_bp.route('/orders/<int:id>')
@login_required
@admin_required
def view_order(id):
    """View a single order"""
    order = Order.query.get_or_404(id)
    return render_template('admin/orders/view.html', order=order)

@admin_bp.route('/orders/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(id):
    """Update order status"""
    order = Order.query.get_or_404(id)
    form = OrderStatusForm()
    
    if form.validate_on_submit():
        order.status = form.status.data
        db.session.commit()
        flash('Order status updated', 'success')
    
    return redirect(url_for('admin.view_order', id=id))

# Users
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users"""
    users = User.query.filter(User.id != current_user.id).order_by(User.username).all()
    return render_template('admin/users/index.html', users=users)

@admin_bp.route('/users/<int:id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(id):
    """Toggle admin status for a user"""
    user = User.query.get_or_404(id)
    
    # Cannot modify admin status for self
    if user.id == current_user.id:
        flash('You cannot change your own admin status', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'Admin status for {user.username} has been updated', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:id>/toggle_active', methods=['POST'])
@login_required
@admin_required
def toggle_active(id):
    """Toggle active status for a user"""
    user = User.query.get_or_404(id)
    
    # Cannot deactivate self
    if user.id == current_user.id:
        flash('You cannot deactivate yourself', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}', 'success')
    return redirect(url_for('admin.users'))

# API Routes (for AJAX)
@admin_bp.route('/api/dashboard/sales', methods=['GET'])
@login_required
@admin_required
def dashboard_sales():
    """API endpoint for dashboard sales chart"""
    # Get sales data for the last 30 days
    today = datetime.datetime.utcnow().date()
    start_date = today - datetime.timedelta(days=30)
    
    sales = db.session.query(
        db.func.date(Order.created_at).label('date'),
        db.func.sum(Order.total).label('total')
    ).filter(
        Order.created_at >= start_date,
        Order.status == 'paid'
    ).group_by(
        db.func.date(Order.created_at)
    ).all()
    
    # Format data for chart
    dates = [(start_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
    sales_dict = {s.date.strftime('%Y-%m-%d'): float(s.total) for s in sales}
    sales_data = [sales_dict.get(date, 0) for date in dates]
    
    return jsonify({
        'dates': dates,
        'sales': sales_data
    })
