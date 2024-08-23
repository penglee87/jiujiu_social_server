import os
import click
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Follow, Role, Permission, Post, Comment

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from dotenv import load_dotenv

#dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print('wsgi_DEV_DATABASE_URL:', os.environ.get('DEV_DATABASE_URL'))

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Follow=Follow, Role=Role,Permission=Permission,
                 Post=Post, Comment=Comment)


@app.cli.command()
@click.argument('test_names', nargs=-1)
def test(test_names):
    """Run the unit tests."""
    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5000, debug=True)
        #socketio.run(app, host='127.0.0.1', port=5000, debug=True)
        #server = pywsgi.WSGIServer(('127.0.0.1', 5000), app, handler_class=WebSocketHandler)
        #server = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler)
        #server.serve_forever()
    except KeyboardInterrupt:
        print("Server is stopping...")