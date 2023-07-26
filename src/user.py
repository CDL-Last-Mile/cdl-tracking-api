from flask import (
    Blueprint, request, jsonify
)
from datetime import datetime
from src.models import TrackingUserType, TrackingUser, TrackingUserAccount
from . import fl_db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash


user = Blueprint('user', __name__)

@user.route('/user-type', methods=['POST'])
@jwt_required()
def add_portal_user_type_rte():
    user_types = []
    success = False 
    try:
        user_id = int(get_jwt_identity())
        user = TrackingUser.query.filter_by(tracking_user_id=user_id).first()
        if user.tracking_user_type_id < 2:
            return jsonify({"error": "You do not have enough privileges for this action. Please contact the Administrator"}), 401
        request_data = request.get_json()
        user_type = request_data.get('user_type')
        if not user_type: 
            return jsonify({'message': 'All fields are required.'}), 400
        user_type_exists = TrackingUserType.query.filter_by(user_type=user_type).first()
        if user_type_exists is not None: 
            return jsonify({"error": "This user type already exists"}), 401
        if user_type:
            new_user_type = TrackingUserType()
            new_user_type.user_type = str(user_type)
            new_user_type.active = 1
            new_user_type.date_created = datetime.now()
            fl_db.session.add(new_user_type)
            fl_db.session.commit()
            
            user_types, success, msg = get_tracking_user_types()
            return jsonify({"message": "User Type added", "user_types": user_types, "success": success}), 201
    except Exception as e: 
        print(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500

@user.route('/user-types', methods=['GET'])
def get_user_types_rte(): 
    try: 
        user_types, success, msg = get_tracking_user_types()
        return jsonify({"message": "User Types Retrieved Successfully", "user_types": user_types, "success": success}), 200
    except Exception as e: 
        print(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500

@user.route('/register', methods=['POST'])
@jwt_required()
def register_user_rte():
    success = False 
    user = []
    msg = ''
    try:
        user_id = int(get_jwt_identity())
        user = TrackingUser.query.filter_by(tracking_user_id=user_id).first()
        if user.tracking_user_type_id < 2:
            return jsonify({"error": "You do not have enough privileges for this action. Please contact the Administrator"}), 401
        request_data = request.get_json()
        first_name = request_data.get('first_name')
        last_name = request_data.get('last_name')
        email = request_data.get('email')
        password = request_data.get('password')
        account_no = request_data.get('account_no')
        user_type_id = request_data.get('user_type_id')
        if not first_name or not last_name or not password or not account_no or not user_type_id: 
            return jsonify({'message': 'All fields are required.'}), 400
        if not isinstance(account_no, list):
            return jsonify({'message': 'Account Numbers should be a list'}), 400
        dbquery = fl_db.session.query(TrackingUser.email)
        dbquery = dbquery.filter(TrackingUser.email == email).first()
        if dbquery is not None: 
            success = False
            msg = 'Email already exists.'
            return jsonify({"error": "This user email already exists"}), 401

        new_user = TrackingUser()
        new_user.first_name = first_name
        new_user.active = 1
        new_user.tracking_user_type_id = user_type_id
        new_user.last_name = last_name
        new_user.hash_password = generate_password_hash(password)
        new_user.email = email
        new_user.date_created = datetime.now()
        fl_db.session.add(new_user)
        fl_db.session.flush()

        for account in account_no: 
            new_user_account = TrackingUserAccount()
            new_user_account.account_no = account
            new_user_account.date_created = datetime.now()
            new_user_account.active = True
            new_user_account.tracking_user_id = new_user.tracking_user_id
            fl_db.session.add(new_user_account)
        fl_db.session.commit()
        user = get_tracking_user_by_id(new_user.tracking_user_id)
        success = True
        msg = 'User registered successfully'
        return jsonify({"user": user[0], "message": msg, "success": success}), 201
    except Exception as e: 
        print(e)
        msg = e
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": msg}), 500

@user.route('/account', methods=['POST'])
@jwt_required()
def add_account_rte(): 
    msg = ''
    try:
        admin_id = int(get_jwt_identity())
        user = TrackingUser.query.filter_by(tracking_user_id=admin_id).first()
        if user.tracking_user_type_id < 2:
            return jsonify({"error": "You do not have enough privileges for this action. Please contact the Administrator"}), 401
        request_data = request.get_json()
        user_id = request_data.get('user_id')
        account_no = request_data.get('account_no')

        if not user_id or not account_no: 
            return jsonify({'message': 'All fields are required'}), 400
        if not isinstance(account_no, list):
            return jsonify({'message': 'Account Numbers should be a list'}), 400
        current_accounts = get_user_accounts(user_id)

        for new_account in account_no:
            if str(new_account) not in current_accounts: 
                new_user_account = TrackingUserAccount()
                new_user_account.account_no = new_account
                new_user_account.date_created = datetime.now()
                new_user_account.active = True
                new_user_account.tracking_user_id = user_id
                fl_db.session.add(new_user_account)
        fl_db.session.commit()
        return jsonify({"message": 'Accounts added successfully', "success": True}), 201
    except Exception as e: 
        print(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500

@user.route('/accounts', methods=['GET'])
@jwt_required()
def get_accounts_rte(): 
    try: 
        user_id = int(get_jwt_identity())
        if not user_id: 
            return jsonify({'message': 'Hmmm! Not sure we recognize you'}), 400
        
        user_accounts = get_user_accounts(user_id)

        return jsonify({'accounts': user_accounts, 'success': True, 'message': 'Accounts retrieved successfully'})
    except Exception as e: 
        print(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500


@user.route("/login", methods=['POST'])
def login_rte():
    try: 
        request_data = request.get_json()
        email = request_data.get('email')
        password = request_data.get('password')
        user = TrackingUser.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.hash_password, password):
            return jsonify({"msg": 'Unable to login with credentials provided', "success": False}), 401
        
        access_token = create_access_token(identity=user.tracking_user_id)
        return jsonify({"msg": 'You are successfully logged in!', "success": True, "access_token": access_token, "user_id":user.tracking_user_id}), 200  
          
    except Exception as e: 
        print(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500
    
@user.route("/admin-login", methods=['POST'])
def admin_login_rte():
    try: 
        request_data = request.get_json()
        email = request_data.get('email')
        password = request_data.get('password')
        user = TrackingUser.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.hash_password, password) or user.tracking_user_type_id < 2:
            return jsonify({"msg": 'Unable to login with credentials provided', "success": False}), 401
        
        access_token = create_access_token(identity=user.tracking_user_id)
        return jsonify({"msg": 'You are successfully logged in!', "success": True, "access_token": access_token, "user_id":user.tracking_user_id}), 200  
          
    except Exception as e: 
        print(e)
        return jsonify({"error": "Oops! We just ran into an error in the server.", "msg": e}), 500

def get_tracking_user_by_id(tracking_user_id): 
    user = []
    success = False
    msg = ''
    try: 
        dbquery = fl_db.session.query(
            TrackingUser.tracking_user_id,
            TrackingUser.first_name,
            TrackingUser.last_name,
            TrackingUser.active,
            TrackingUser.email,
            TrackingUser.tracking_user_type_id, 
            TrackingUserAccount.account_no, 
            TrackingUserType.user_type)
        dbquery = dbquery.join(TrackingUserAccount, TrackingUser.tracking_user_id == TrackingUserAccount.tracking_user_id)
        dbquery = dbquery.filter(TrackingUser.tracking_user_id == tracking_user_id)
        dbquery = dbquery.join(TrackingUserType, TrackingUser.tracking_user_type_id == TrackingUserType.tracking_user_type_id)
        user =  [r._asdict() for r in dbquery.all()]
        success = True 
        msg = "User data retrieved successfully "
    except Exception as e: 
        print(e)
        msg = e 
    return user, success, msg

def get_user_accounts(user_id):
    accounts = []
    try:
        dbquery = fl_db.session.query(TrackingUserAccount.account_no).filter(TrackingUserAccount.tracking_user_id == user_id, TrackingUserAccount.active == 1)
        account_list = [r._asdict() for r in dbquery.all()]
        accounts = [account['account_no'] for account in account_list]
    except Exception as e:
        print(e)
    return accounts

def get_tracking_user_types(): 
    user_types = []
    success = False
    msg = ''
    try: 
        dbquery = fl_db.session.query(
            TrackingUserType.tracking_user_type_id, 
            TrackingUserType.user_type,
            TrackingUserType.active)
        user_types =  [r._asdict() for r in dbquery.all()]
        success = True 
        msg = "User Types retrieved successfully "
    except Exception as e: 
        print(e)
        msg = e 
    return user_types, success, msg