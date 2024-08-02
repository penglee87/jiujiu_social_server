import os
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
#from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_pagedown import PageDown
from flask_socketio import SocketIO
from config import config


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()
socketio = SocketIO()

#login_manager = LoginManager()
#login_manager.login_view = 'api_v2.login'
jwt = JWTManager()


def create_app(config_name):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    #login_manager.init_app(app)
    jwt.init_app(app)
    pagedown.init_app(app)
    #register_extensions(app)

    #from app.blueprints.api.v0 import api_bl
    #app.register_blueprint(api_bl, url_prefix='/api')

    #from app.blueprints.api.v1 import api_bl as api_v1_bl
    #app.register_blueprint(api_v1_bl, url_prefix='/api/v1')

    from app.blueprints.api.v2 import api_bl as api_v2_bl
    app.register_blueprint(api_v2_bl, url_prefix='/api/v2')

    
    from . import events
    socketio.init_app(app)

    #from app.blueprints.api.v3 import create_v3
    #app.register_blueprint(create_v3(), url_prefix='/api/v3')

    # 打印所有已注册的路由
    #with app.app_context():
    #    print("Registered routes:")
    #    for rule in app.url_map.iter_rules():
    #        print(rule)
    
    #register_blueprints(app)

    return app

#def register_extensions(app):
#    bootstrap.init_app(app)
#    mail.init_app(app)
#    moment.init_app(app)
#    db.init_app(app)
#    login_manager.init_app(app)
#    pagedown.init_app(app)

#def register_blueprints(app):
#    app.register_blueprint(main_bl)
#    app.register_blueprint(auth_bl, url_prefix='/auth')
#    app.register_blueprint(api_bl, url_prefix='/api/v1')