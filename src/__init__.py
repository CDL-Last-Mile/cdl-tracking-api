import os
from dotenv import load_dotenv
from flask import Flask, jsonify, flash, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail


from flask_cors import CORS
from werkzeug.middleware.dispatcher import DispatcherMiddleware

load_dotenv()

fl_db = SQLAlchemy(session_options={"autoflush": False})
bcrypt = Bcrypt()
cors = CORS()
jwt = JWTManager()
mail = Mail()



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)


    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_object('config')
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("TEST_DATABASE_URL")
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    "/orderfinder": app
    })

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # from . import db
    # db.init_app(app)
    bcrypt.init_app(app)
    fl_db.init_app(app)
    cors.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    @app.route('/hello')
    def hello():
        return jsonify({'message': 'Hello, World!'})
    
    from . import order, user, subscription
    app.register_blueprint(order.order)
    app.register_blueprint(user.user)
    app.register_blueprint(subscription.subscription)



    return app


