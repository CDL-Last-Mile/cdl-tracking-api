from flask import (
    Blueprint, request, jsonify, current_app, url_for
)
from datetime import datetime, timedelta
import json 
from collections import OrderedDict
from decimal import Decimal
from sqlalchemy import text
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import TrackingUser, TrackingUserAccount, TrackingSubscription
from flask_mail import Message
import config

# from src.db import get_db
from src.queries import (
    GET_CLIENT_ORDERS, 
    GET_ORDER_EVENTS
)
import base64
from . import fl_db, mail
from src.user import get_user_accounts

subscription = Blueprint('subscription', __name__, url_prefix='/subscription')

def get_all_client_orders(account_no):
    orders = []
    try:
        params = {
            'account_no': account_no
        }
        client_orders = fl_db.session.execute(GET_CLIENT_ORDERS, params)
        client_orders = client_orders.mappings().all()
        orders = [order['OrderTrackingID'] for order in client_orders]
    except Exception as e:
        print(e)
    return orders
    
@subscription.route('/subscribe', methods=['POST'])
@jwt_required()
def add_subscription_rte(): 
    msg = ''
    try:
        client_id = int(get_jwt_identity())
        user = TrackingUser.query.filter_by(tracking_user_id=client_id).first()
        if user.tracking_user_type_id != 1:
            return jsonify({"error": "You do not have enough privileges for this action. Please contact the Administrator"}), 401
        request_data = request.get_json()
        email = request_data.get('email')
        account_no = request_data.get('accountNo')
        order_tracking_ids = request_data.get('orderTrackingIds')
        all_orders = request_data.get('subscribeAll')
        current_accounts = get_user_accounts(client_id)
        if not email or not account_no: 
            return jsonify({'message': 'All fields are required'}), 400
        if not str(account_no) in current_accounts:
            return jsonify({'message': 'You do not have enough privilege to subscribe for this account.'}), 400
        if not isinstance(account_no, int) :
            return jsonify({'message': 'Account Numbers should be an integer or string'}), 400
        if all_orders is not None and all_orders is True:
            if not isinstance(all_orders, bool):
              return jsonify({'message': 'Order Tracking IDs should be a list'}), 400  
            tracking_id_str = ','.join(str(id) for id in get_all_client_orders(str(account_no)))
            new_subscription = TrackingSubscription()
            new_subscription.account_no = str(account_no)
            new_subscription.email = email
            new_subscription.active = 1
            new_subscription.order_tracking_ids = tracking_id_str
            fl_db.session.add(new_subscription)
            fl_db.session.commit()
            
        else:
            if not order_tracking_ids:
                return jsonify({'message': 'Order Tracking IDs is required'}), 400
            if not isinstance(order_tracking_ids, list):
                return jsonify({'message': 'Order Tracking IDs should be a list'}), 400
            tracking_id_str = ','.join(str(id) for id in order_tracking_ids)
            new_subscription = TrackingSubscription()
            new_subscription.account_no = str(account_no)
            new_subscription.email = email
            new_subscription.active = 1
            new_subscription.order_tracking_ids = tracking_id_str
            fl_db.session.add(new_subscription)
            fl_db.session.commit()
       
        return jsonify({"message": 'Accounts subscription successful', "success": True}), 201
    except Exception as e: 
        print(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500




@subscription.route('/update', methods=['GET'])
def process_update_rte():
    now = datetime.now()
    fifteen_minutes_ago = now - timedelta(minutes=5)
    event_ids = config.EVENT_IDS

    page = request.args.get('page', default=1, type=int)
    per_page = 100  # Adjust the batch size according to your needs

    query = fl_db.session.query(
        TrackingSubscription.account_no, 
        TrackingSubscription.order_tracking_ids,
        TrackingSubscription.email
    ).filter(
        TrackingSubscription.active == 1
    ).order_by(TrackingSubscription.account_no).paginate(page=page, per_page=per_page)

    for subscription in query.items:
        tracking_ids = subscription.order_tracking_ids.split(',')
        params = {
            'order_tracking_ids': tuple(tracking_ids),
            'account_no': subscription.account_no,
            'timestamp': fifteen_minutes_ago,
            'event_ids': tuple(event_ids)
        }
        
        event_data = fl_db.session.execute(GET_ORDER_EVENTS, params)
        updates = event_data.mappings().all()
        next_page_url = url_for('subscription.process_update_rte', page=query.next_num, _external=True)
        
        if len(updates) > 0:
            body = "Here are the recent updates on the following order you subscribed for: \n\n"
            body += "Tracking ID \t Event Name \t Time\n"
            
            for update in updates: 
                tracking_id = update['OrderTrackingID']
                event_name = update['NAME']
                timestamp = datetime.strftime(update['sTimeStamp'], '%Y-%m-%d %H:%M:%S')
                body += f"{tracking_id} \t {event_name} \t {timestamp}"
                body += f"\n"

            subject = "Order Updates"
            msg = Message(
                sender=str(config.MAIL_DEFAULT_SENDER),
                subject=subject,
                recipients=[subscription.email]
            )
            msg.body = body
            mail.send(msg)

    if query.has_next:
        next_page = request.base_url + f"?page={query.next_num}"
    else:
        next_page = None

    return jsonify({
        "message": 'Order updates sent successfully',
        "success": True,
        "next_page": next_page
    }), 200
