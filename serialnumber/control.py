# encoding=utf8

from flask import (Flask, request, session, g, redirect, url_for, abort,
                   render_template, flash)
app = Flask('serialnumber')

from . import util, settings
app.config.from_object(settings)

from . model import session_factory, Supplier, Product, Document, SerialNumber
Session = session_factory(app.config['DATABASE'], app.config['DEBUG'])

from sqlalchemy import or_

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

@app.template_filter('split')
def split_filter(s, sep=None):
    return s.split(sep)


def filter_query(search, query, fields):
    for arg in search:
        arg = "%{0}%".format(arg)
        ft = or_(*[field.like(arg) for field in fields])
        query = query.filter(ft)

    return query

def parse_search(s):
    search = {0: []}
    if s:
        for arg in s.split():
            v = arg.split(':')
            if len(v) == 1:
                search[0].extend(v)
            else:
                search.setdefault(*v)
    return search


@app.route('/')
def list_serials():
    query = g.db_session.query(SerialNumber).\
        join(Document).\
        join(Product).\
        join(Supplier).\
        order_by(Document.date.desc())

    search = parse_search(request.args.get('s'))
    query = filter_query(search[0], query,
                         (Document.number, Document.date, Supplier.name,
                          Product.name, SerialNumber.number))
    if 'nota' in search:
        query = query.filter(Document.number == search['nota'])

    return render_template('list_serials.html', serials=query)

@app.route('/documents')
def list_documents():
    query = g.db_session.query(Document).\
        join(Supplier).\
        order_by(Document.date.desc())

    search = parse_search(request.args.get('s'))
    query = filter_query(search[0], query,
                         (Document.number, Document.date, Supplier.name))
    if 'nota' in search:
        query = query.filter(Document.number == search['nota'])

    return render_template('list_documents.html', docs=query)

@app.route('/update/<int:serial_id>', methods=['GET', 'POST'])
def update_serials(serial_id):
    if not session.get('logged_in'):
        abort(401)

    query = g.db_session.query(SerialNumber).filter_by(id=serial_id)
    sn = query.first()
    if request.method == 'POST':
        if sn:
            serials = ','.join(request.form.getlist('serial'))
            query.update({'number': serials})
            flash(u"Números de série registrados com sucesso")
        else:
            flash(u"Não foi possível registrar os números de série")
        return redirect(url_for('list_serials'))

    return render_template('update_serials.html', serial=sn)

@app.route('/import', methods=['POST'])
def import_xml():
    if not session.get('logged_in'):
        abort(401)

    values = {}
    xml_file = request.files['xml-file']
    if xml_file.filename == '':
        flash(u"Nenhum arquivo enviado", 'error')
    elif xml_file.mimetype != 'text/xml':
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
            for prod in xml_doc['products']:
                product = g.db_session.query(Product).\
                    filter_by(name=prod['name']).\
                    filter_by(supplier=supplier).first() \
                    or Product(name=prod['name'], supplier=supplier)
                sn = SerialNumber(product=product, document=document,
                                  quantity=prod['qnt'])
                g.db_session.add(sn)
            values['s'] = "nota:%d" % number
            flash(u"Uma nova nota foi importada com sucesso")
        else:
            flash(u"Essa nota já foi importada anteriormente", 'error')

    return redirect(url_for('list_serials', **values))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        users = app.config['USERS']
        if users.get(request.form['username']) == request.form['password']:
            session['logged_in'] = True
            flash(u"Você está conectado")
            return redirect(url_for('list_serials'))
        else:
            error = u"Nome de usuário ou senha inválido"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash(u"Você está desconectado")
    return redirect(url_for('list_serials'))
