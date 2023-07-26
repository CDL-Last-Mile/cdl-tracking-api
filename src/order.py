from flask import (
    Blueprint, request, jsonify, current_app
)
from datetime import datetime
import json 
from collections import OrderedDict
from decimal import Decimal
from sqlalchemy import text
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import TrackingUser, TrackingUserAccount

# from src.db import get_db
from src.queries import (
    GET_PACKAGE_SCANS, 
    GET_ORDER_TRACKING_ID
)
import base64
from . import fl_db
from src.user import get_user_accounts

order = Blueprint('order', __name__, url_prefix='/order')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def format_date(date_str):
    if not date_str: 
        return ''
    dt = datetime.strftime(date_str, '%a, %d %b %Y %H:%M:%S')
    dt = dt.strip()
    dt = datetime.strptime(dt, '%a, %d %b %Y %H:%M:%S')
    output_string = dt.isoformat()
    return output_string

def format_response(shipment_info=[], package_info=[], event_info=[], show_vpod=False):
    shipment_data = []
    exception_time = None

    # Shipment data
    if len(shipment_info):
        shipment_data = OrderedDict([
            ("orderTrackingId", shipment_info["OrderTrackingID"]),
            ("accountNo", shipment_info["AccountNo"]),
            ("shipmentCreated", format_date(shipment_info["ShipmentCreated"])),
            ("orderStatus", shipment_info["OrderStatus"]),
            ("clientRefNo", shipment_info["ClientRefNo"]),
            ("clientRefNo2", shipment_info["ClientRefNo2"]),
            ("clientRefNo3", shipment_info["ClientRefNo3"]),
            ("clientRefNo4", shipment_info["ClientRefNo4"]),
            ("driverName", shipment_info["DriverName"]),
            ("pickupAddress", OrderedDict([
                ("name", shipment_info["PcoName"]),
                ("contact", shipment_info["PContact"]),
                ("street", shipment_info["PStreet"]),
                ("street2", shipment_info["PStreet2"]),
                ("city", shipment_info["pcity"]),
                ("state", shipment_info["PState"]),
                ("zip", shipment_info["PZip"]),
                ("specialInstructions", shipment_info["PSpecInstr"])
            ])),
            ("deliveryAddress", OrderedDict([
                ("name", shipment_info["Dconame"]),
                ("contact", shipment_info["Dcontact"]),
                ("street", shipment_info["DStreet"]),
                ("street2", shipment_info["Dstreet2"]),
                ("city", shipment_info["DCity"]),
                ("state", shipment_info["DState"]),
                ("zip", shipment_info["DZip"]),
                ("specialInstructions", shipment_info["DSpecInstr"])
            ]))
        ])
    
    # Event Data 
    # Exception data
    exception_data = []
    event_data = []
    if len(event_info):
        for event in event_info: 
            if event['TrackingEvents'] is not None:
                if event['TrackingEvents'] == 'Driver en-route to delivery'  or event['TrackingEvents'] == 'Package Scanned At Delivery':
                    e_data = OrderedDict([
                        ('trackingEvent', event['TrackingEvents']), 
                        ('trackingEventTimestamp', format_date(event['aTimeStamp'])), 
                        ('eventCity', event['DCity']), 
                        ('eventState', event['DState']), 
                        ('lat', event['Lat']), 
                        ('long', event['long'])
                    ])
                else:
                    e_data = OrderedDict([
                        ('trackingEvent', event['TrackingEvents']), 
                        ('trackingEventTimestamp', format_date(event['aTimeStamp'])), 
                        ('eventCity', event['City']), 
                        ('eventState', event['State']), 
                        ('lat', event['Lat']), 
                        ('long', event['long'])
                    ])
                event_data.append(e_data)
       
            if event['isException'] and event['ExceptionDetails'] is not None:
                info_data = OrderedDict([
                    ('exception', event['Exception']),
                    ('exceptionDetails', event['ExceptionDetails']), 
                    ('exceptionTimeStamp', format_date(event['aTimeStamp'])),
                    # ('suppressOnCompletion', event['SuppressOnCompletion'])
                ])
                exception_time = event['aTimeStamp']
                exception_data.append(info_data)
    # Package Scans
    package_scans_data = []
    if len(package_info): 
        for scan in package_info:
            if scan['SCANlocation'] is not None or scan['SCANdetails'] is not None:
                if exception_time and scan['aTimeStamp'] < exception_time:
                    scan_data = OrderedDict([
                        ('scanLocation', scan['SCANlocation']), 
                        ('scanDetails', scan['SCANdetails']), 
                        ('scanTime', format_date(scan['aTimeStamp']))
                    ])
                    package_scans_data.append(scan_data)
            
    # Order packages
    order_packages = OrderedDict([
        ('packageCount', shipment_info["PackageCount"]),
        ('packageName', shipment_info["PackageName"])
    ])
    
    # Package data
    package_data = OrderedDict()
    package_data = OrderedDict([
            ("refNo", shipment_info["RefNo"]),
            ("refNo2", shipment_info["RefNo2"]),
            ("refNo3", shipment_info["RefNo3"]),
            ("refNo4", shipment_info["RefNo4"]),
            ("packageName", shipment_info["PackageName"])
        ])
        
    if shipment_info["Weight"] is not None and shipment_info["Weight"] != "":
        package_data['weight'] = round(float(shipment_info["Weight"]), 2)

    if shipment_info["Length"] is not None and shipment_info["Length"] != "":
        package_data['length'] = round(float(shipment_info["Length"]), 2)

    if shipment_info["Width"] is not None and shipment_info["Width"] != "":
        package_data['width'] = round(float(shipment_info["Width"]), 2)

    if shipment_info["Height"] is not None and shipment_info["Height"] != "":
        package_data['height'] = round(float(shipment_info["Height"]), 2)

    if len(package_scans_data):
        package_data['packageScans'] = package_scans_data

    # POD Data
    vpod = ''
    pod = ''
    if show_vpod:
        if shipment_info['Vpod'] != '' and shipment_info['Vpod'] is not None:
            vpod_bytes = shipment_info['Vpod'].encode('utf-8')
            vpod = base64.b64encode(vpod_bytes).decode('utf-8')
        if shipment_info['PodSignature'] != '' and shipment_info['PodSignature'] is not None:
            pod_bytes = shipment_info['PodSignature'].encode('utf-8')
            pod = base64.b64encode(pod_bytes).decode('utf-8')
    pod_data = OrderedDict([
        ("podName", shipment_info['PODname']),
        ("podSignature", pod),
        ("vpod", vpod),
        ("poDcompletion", format_date(shipment_info['PODcompletion']))
    ]) if show_vpod else None

    # Dates
    pickup_target_from = format_date(shipment_info["PickupTargetFrom"])
    pickup_target_to = format_date(shipment_info["PickupTargetTo"])
    delivery_target_from = format_date(shipment_info["DeliveryTargetFrom"])
    delivery_target_to = format_date(shipment_info["DeliveryTargetTo"])
    pickup_arrival = format_date(shipment_info["PickupArrival"])
    delivery_arrival = format_date(shipment_info['DeliveryArrival'])
    pickup_departure = format_date(shipment_info["PickupDeparture"])
    delivery_departure = format_date(shipment_info['DeliveryDeparture'])

    mileTotal = ''
    if shipment_info["MileageTotal"] is not None and shipment_info["MileageTotal"] != "":
        mileTotal = round(float(shipment_info["MileageTotal"]), 2)

    response = OrderedDict([
        ('shipmentData', shipment_data),
        ('orderPackages', order_packages),
        ('packageData', package_data),
        ('mileageTotal', mileTotal),
        ('pickupTargetFrom', pickup_target_from),
        ('pickupTargetTo', pickup_target_to),
        ('deliveryTargetFrom', delivery_target_from),
        ('deliveryTargetTo', delivery_target_to),
        ('pickupArrival', pickup_arrival),
        ('pickupDeparture', pickup_departure),
        ('deliveryArrival', delivery_arrival),
        ('deliveryDeparture', delivery_departure),
        ('exceptionData', exception_data),
        ('isTrackingListEmpty', False),
        ('eventBasedData', event_data),
        ('podData', pod_data)
    ])

    if show_vpod and pod_data is not None:
        response['podData'] = pod_data
    
    return response


def execute_procedure(sp_name=None, orderTrackingId=None, accountNo=None, createdDate=None, deliveredDate=None, lastUpdateDate=None):
    if sp_name == 'sp_TrackingAPI_GetOrderShipmentInfo':
        stmt = text(f"EXEC {sp_name} :orderTrackingId, :accountNo")
        cursor = fl_db.session.execute(stmt, {'orderTrackingId': orderTrackingId, 'accountNo': accountNo})

    if sp_name == 'sp_TrackingAPI_GetOrderTrackingEvent':
        stmt = text(f"EXEC {sp_name} :orderTrackingId")
        cursor = fl_db.session.execute(stmt, {'orderTrackingId': orderTrackingId})

    if sp_name == 'sp_TrackingAPI_CreatedOn':
        stmt = text(f"EXEC {sp_name} :inputDate, :accountNo")
        cursor = fl_db.session.execute(stmt, {'inputDate': createdDate, 'accountNo': accountNo})

    if sp_name == 'sp_TrackingAPI_DeliveredOn':
        stmt = text(f"EXEC {sp_name} :inputDate, :accountNo")
        cursor = fl_db.session.execute(stmt, {'inputDate': deliveredDate, 'accountNo': accountNo})

    if sp_name == 'sp_TrackingAPI_LastUpdatedOnTime':
        stmt = text(f"EXEC {sp_name} :inputDate, :accountNo")
        cursor = fl_db.session.execute(stmt, {'inputDate': lastUpdateDate, 'accountNo': accountNo})
      
    rows = cursor.fetchall()
    columns = cursor.keys()

    # Convert the result set to a list of dictionaries for JSON serialization
    order_data = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(columns):
            if isinstance(row[i], bytes):
                row_dict[col] = row[i].decode('ISO-8859-1')
            else:
                row_dict[col] = row[i]
        order_data.append(row_dict)

    return order_data

def get_order_tracking_id(orderTrackingId):
    try: 
        if type(orderTrackingId) == str:
            order_data = fl_db.session.execute(GET_ORDER_TRACKING_ID, {'refNo': orderTrackingId })
            order_data = order_data.mappings().all()
            if len(order_data):
                order_data = order_data[0]['OrderTrackingID']
                return float(order_data)
            else: 
                return jsonify({"error": "Unable to find matching OrdertakcingID for " + orderTrackingId}), 500
        elif type(orderTrackingId) == float: 
            return orderTrackingId
        else:
            return jsonify({"error": "Invalid OrderTrackingID/RefNo " + orderTrackingId}), 500
    except Exception as e:
        current_app.logger.error(e)
    return jsonify({"error": "Something went wrong"}), 500

def get_user():
    try:
        user_id = get_jwt_identity()
        current_user = fl_db.session.query(TrackingUserAccount.account_no, TrackingUserAccount.tracking_user_id, TrackingUserAccount.date_created).filter(TrackingUserAccount.tracking_user_id == user_id)
        return current_user
    except Exception as e: 
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@order.route('/get-tracking-info', methods=['GET'])
@jwt_required()
def get_tracking_info():
    try:
        request_data = request.get_json()
        response = []
        order_tracking_ids = request_data.get('orderTrackingIds')
        account_no = request_data.get('accountNo')
        show_vpod = request_data.get('showVpod') or False
        msg = ''
        missing_orders = []
        user_id = get_jwt_identity()
        user_accounts = get_user_accounts(int(user_id))
        if str(account_no) not in user_accounts: 
            return jsonify({"error": "You do not have the right privildeges to this Account Number"}), 400
        if account_no is None or order_tracking_ids is None or len(order_tracking_ids) == 0: 
            return jsonify({"error": "Account Number and Order Tracking IDs  are required"}), 400
        if len(order_tracking_ids) > 5: 
            return jsonify({"error": "You can only request info on max 5 orders at once"}), 400
        if len(order_tracking_ids):
            for orderTrackingId in order_tracking_ids:
                orderTrackingId = get_order_tracking_id(orderTrackingId)
                shipment_sp = 'sp_TrackingAPI_GetOrderShipmentInfo'
                event_sp = 'sp_TrackingAPI_GetOrderTrackingEvent'
                shipment_data = execute_procedure(sp_name=shipment_sp, orderTrackingId=orderTrackingId, accountNo=account_no)
                if len(shipment_data):
                    shipment_data = shipment_data[0]
                    event_data = execute_procedure(sp_name=event_sp, orderTrackingId=orderTrackingId)
                    package_scans_proxy = fl_db.session.execute(GET_PACKAGE_SCANS, {'orderTrackingId': orderTrackingId})
                    package_scans_data = package_scans_proxy.mappings().all()
                    order_data =  format_response(shipment_info=shipment_data, package_info=package_scans_data, event_info=event_data, show_vpod=show_vpod)
                    response.append(order_data) 
                else:
                    missing_orders.append(orderTrackingId)
        if len(missing_orders):
            msg = 'Unable to find any record for orderTrackingId(s): ' + str(missing_orders)
        else:
            msg = 'Order Info returned successfully'
        json_response = json.dumps(OrderedDict([('response', response), ('total', len(order_tracking_ids)), ('msg', msg)]), cls=DecimalEncoder, sort_keys=False)
        return json_response, 200
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500
    

@order.route('/created-on-date', methods=['GET'])
@jwt_required()
def get_orders_created_by_date_rte():
    try: 
        request_data = request.get_json()
        created_date = request_data.get('createdOnDate')
        account_no = request_data.get('accountNo')
        user_id = get_jwt_identity()
        user_accounts = get_user_accounts(int(user_id))
        if str(account_no) not in user_accounts: 
            return jsonify({"error": "You do not have the right privildeges to this Account Number"}), 400
        if account_no is None or created_date is None: 
            return jsonify({"error": "Account Number and Created Date are required"}), 400
        info_by_created_date_sp = 'sp_TrackingAPI_CreatedOn'
        orders = execute_procedure(sp_name=info_by_created_date_sp, createdDate=created_date, accountNo=account_no)
        return jsonify({'response': orders, 'total': len(orders)})
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500

@order.route('/delivered-on-date', methods=['GET'])
@jwt_required()
def get_orders_delivered_by_date_rte():
    try: 
        request_data = request.get_json()
        delivered_date = request_data.get('deliveredOnDate')
        account_no = request_data.get('accountNo')
        user_id = get_jwt_identity()
        user_accounts = get_user_accounts(int(user_id))
        if str(account_no) not in user_accounts: 
            return jsonify({"error": "You do not have the right privildeges to this Account Number"}), 400
        if account_no is None or delivered_date is None: 
            return jsonify({"error": "Account Number and Delivered Date are required"}), 400
        info_by_created_date_sp = 'sp_TrackingAPI_DeliveredOn'
        orders = execute_procedure(sp_name=info_by_created_date_sp, deliveredDate=delivered_date, accountNo=account_no)
        return jsonify({'response': orders, 'total': len(orders)})
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500

@order.route('/last-update-date', methods=['GET'])
@jwt_required()
def get_orders_last_update_by_date_rte():
    try: 
        request_data = request.get_json()
        last_update_date = request_data.get('updateOnDate')
        account_no = request_data.get('accountNo')
        user_id = get_jwt_identity()
        user_accounts = get_user_accounts(int(user_id))
        if str(account_no) not in user_accounts: 
            return jsonify({"error": "You do not have the right privildeges to this Account Number"}), 400
        if account_no is None or last_update_date is None: 
            return jsonify({"error": "Account Number and Last Update Date are required"}), 400
        input_date = datetime.strptime(last_update_date, "%Y-%m-%d %H:%M")
        info_by_created_date_sp = 'sp_TrackingAPI_LastUpdatedOnTime'
        orders = execute_procedure(sp_name=info_by_created_date_sp, lastUpdateDate=input_date, accountNo=account_no)
        return jsonify({'response': orders, 'total': len(orders)})
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500







