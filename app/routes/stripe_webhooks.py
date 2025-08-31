from flask import Blueprint, request, jsonify, current_app
from app.models.order import Order, OrderStatus, PaymentStatus
from app import db
import stripe
import logging

stripe_webhooks = Blueprint('stripe_webhooks', __name__)

@stripe_webhooks.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        logging.error("Stripe webhook secret is not configured")
        return jsonify({'status': 'error', 'message': 'Webhook secret not configured'}), 400
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        logging.error(f"Invalid payload: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logging.error(f"Invalid signature: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        # Payment was successful, update the order
        session = event['data']['object']
        
        # Get the order ID from the client_reference_id
        order_id = session.get('client_reference_id')
        if order_id:
            order = Order.query.get(int(order_id))
            if order:
                # Update order status
                order.payment_status = PaymentStatus.PAID.name.lower()
                order.order_status = OrderStatus.PROCESSING.name.lower()
                order.payment_intent_id = session.get('payment_intent')
                db.session.commit()
                
                # Log the successful payment
                logging.info(f"Payment for order {order.order_number} was successful")
    
    elif event['type'] == 'payment_intent.payment_failed':
        # Payment failed, update the order
        payment_intent = event['data']['object']
        
        # Try to find the order with this payment intent ID
        order = Order.query.filter_by(payment_intent_id=payment_intent['id']).first()
        if order:
            # Update order status
            order.payment_status = PaymentStatus.FAILED.name.lower()
            db.session.commit()
            
            # Log the failed payment
            logging.error(f"Payment for order {order.order_number} failed: {payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')}")
    
    # Return a 200 response to acknowledge receipt of the event
    return jsonify({'status': 'success'})
