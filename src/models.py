from . import fl_db

class TrackingUserType(fl_db.Model):
    __tablename__ = "TrackingUserType"
    tracking_user_type_id = fl_db.Column(fl_db.Integer, primary_key=True)
    user_type = fl_db.Column(fl_db.String(50))
    date_created = fl_db.Column(fl_db.DateTime)
    date_modified = fl_db.Column(fl_db.DateTime)
    active = fl_db.Column(fl_db.Integer)

class TrackingUser(fl_db.Model):
    __tablename__ = "TrackingUser"
    tracking_user_id = fl_db.Column(fl_db.Integer, primary_key=True)
    first_name = fl_db.Column(fl_db.String(50))
    last_name = fl_db.Column(fl_db.String(50))
    email = fl_db.Column(fl_db.String(200))
    hash_password = fl_db.Column(fl_db.String(255))
    tracking_user_type_id = fl_db.Column(fl_db.Integer)
    date_created = fl_db.Column(fl_db.DateTime)
    date_modified = fl_db.Column(fl_db.DateTime)
    active = fl_db.Column(fl_db.Integer)

    def __init__(self):
        pass

    def is_active(self):
        return True
    
    def get_id(self):
           return (self.tracking_user_id)
    
class TrackingUserAccount(fl_db.Model):
    __tablename__ = "TrackingUserAccount"
    tracking_user_account_id = fl_db.Column(fl_db.Integer, primary_key=True)
    tracking_user_id = fl_db.Column(fl_db.Integer)
    account_no = fl_db.Column(fl_db.String(18))
    date_created = fl_db.Column(fl_db.DateTime)
    date_modified = fl_db.Column(fl_db.DateTime)
    active = fl_db.Column(fl_db.Integer)

class TrackingSubscription(fl_db.Model):
     __tablename__ = "TrackingSubscription"
     tracking_subscription_id = fl_db.Column(fl_db.Integer, primary_key=True)
     account_no = fl_db.Column(fl_db.String(50))
     email = fl_db.Column(fl_db.String(50))
     order_tracking_ids = fl_db.Column(fl_db.Text)
     active = fl_db.Column(fl_db.Integer)
