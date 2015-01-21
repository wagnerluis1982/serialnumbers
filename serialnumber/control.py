from flask import (Flask, request, session, g, redirect, url_for, abort,
                   render_template, flash)
app = Flask('serialnumber')

from . import model, settings
app.config.from_object(settings)
Session = model.session_factory(app.config['DATABASE'], app.config['DEBUG'])

@app.before_request
def before_request():
    g.db_session = Session()

@app.teardown_request
def teardown_request(exception):
    db_session = getattr(g, 'db_session', None)
    if db_session is not None:
        db_session.commit()
        db_session.close()
