# encoding=utf8

from flask import (Flask, request, session, g, redirect, url_for, abort,
                   render_template, flash)
app = Flask('serialnumber')

from . import util, settings
app.config.from_object(settings)

from . model import session_factory, Supplier, Product, Document, SerialNumber
Session = session_factory(app.config['DATABASE'], app.config['DEBUG'])

@app.before_request
def before_request():
    g.db_session = Session()

@app.teardown_request
def teardown_request(exception):
    db_session = getattr(g, 'db_session', None)
    if db_session is not None:
        db_session.commit()
        db_session.close()


@app.template_filter('dateformat')
def date_filter(s, fmt="%d/%m/%Y"):
    return s.strftime(fmt)


@app.route('/')
def list_serials():
    resultset = g.db_session.query(SerialNumber)
    return render_template('list_serials.html', serials=resultset)

@app.route('/import', methods=['POST'])
def import_xml():
    if not session.get('logged_in'):
        abort(401)
    xml_file = request.files['xml-file']
    if xml_file.mimetype != 'text/xml':
        flash(u"Arquivo enviado deve ser do tipo XML", 'error')
    else:
        xml_doc = util.parse_nfe_document(xml_file)
        # supplier
        cnpj = xml_doc['supplier.cnpj']
        supplier = g.db_session.query(Supplier).filter_by(cnpj=cnpj).first() \
            or Supplier(cnpj=cnpj, name=xml_doc['supplier.name'])
        # document
        number = xml_doc['number']
        document = g.db_session.query(Document).filter_by(number=number).\
            filter_by(supplier=supplier).first()
        # products, serialnumbers
        if document is None:
            document = Document(number=number, date=xml_doc['date'],
                                supplier=supplier)
            for prod_name in xml_doc['products']:
                product = g.db_session.query(Product).\
                    filter_by(name=prod_name).\
                    filter_by(supplier=supplier).first() \
                    or Product(name=prod_name, supplier=supplier)
                sn = SerialNumber(product=product, document=document)
                g.db_session.add(sn)
            flash(u"Uma nova nota foi importada com sucesso")
        else:
            flash(u"Essa nota já foi importada anteriormente", 'error')

    return redirect(url_for('list_serials'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = u"Nome de usuário inválido"
        elif request.form['password'] != app.config['PASSWORD']:
            error = u"Senha inválida"
        else:
            session['logged_in'] = True
            flash(u"Você está conectado")
            return redirect(url_for('list_serials'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash(u"Você está desconectado")
    return redirect(url_for('list_serials'))
