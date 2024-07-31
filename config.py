import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
#dotenv_path = os.path.join(basedir, '.env')
#if os.path.exists(dotenv_path):
#    load_dotenv(dotenv_path)


class Config:
    #SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    JWT_SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME','380517767@qq.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD','******')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = '380517767@qq.com'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN','380517767@qq.com')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASKY_POSTS_PER_PAGE = 20
    FLASKY_FOLLOWERS_PER_PAGE = 50
    FLASKY_COMMENTS_PER_PAGE = 30
    WECHAT_APPID = os.environ.get('WECHAT_APPID') or 'wxee9a920f1b1275c2'
    WECHAT_APPSECRET = os.environ.get('WECHAT_APPSECRET') or 'c31df25075d020fa02b95971bca42669'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    print('DevelopmentConfig_SQLALCHEMY_DATABASE_URI',SQLALCHEMY_DATABASE_URI)


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
