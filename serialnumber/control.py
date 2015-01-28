# encoding=utf8

from flask import (Flask, request, session, g, redirect, url_for, abort,
                   render_template, flash)
app = Flask('serialnumber')

from . import util, settings
app.config.from_object(settings)

from . model import session_factory, Supplier, Product, Document, SerialNumber
Session = session_factory(app.config['DATABASE'], app.config['DEBUG'])

from werkzeug import MultiDict
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

@app.template_filter('multijoin')
def multijoin_filter(mdict, sepin, sepout):
    if mdict:
        kwargs = dict({'multi': True} if isinstance(mdict, MultiDict) else ())
        return sepout.join([sepin.join(kv) for kv in mdict.items(**kwargs)])
    else:
        return ""


def get_search(s, empty, look):
    d = MultiDict()
    if s:
        for arg in s.split():
            kv = arg.split(':')
            if len(kv) == 1:
                d.add(empty, arg)
            elif kv[0] in look:
                d.add(*kv)
    return d


@app.route('/')
def list_serials():
    query = g.db_session.query(SerialNumber).join(Document).join(Product).\
        order_by(Document.date.desc())

    search = get_search(request.args.get('s'), empty='sn', look=['sn', 'nota'])
    search.update({
        'nota': request.args.getlist('nota'),
    })
    if search:
        if 'sn' in search:
            ft = or_(*[SerialNumber.number.like("%{0}%".format(sn))
                       for sn in search.getlist('sn')])
            query = query.filter(ft)
        if 'nota' in search:
            ft = or_(*[Document.number == nota
                       for nota in search.getlist('nota')])
            query = query.filter(ft)
        g.search = search

    return render_template('list_serials.html', serials=query)

@app.route('/documents')
def list_documents():
    query = g.db_session.query(Document).order_by(Document.date.desc())

    search = get_search(request.args.get('s'), empty='nota', look=['nota'])
    if search:
        if 'nota' in search:
            ft = or_(*[Document.number == nota
                       for nota in search.getlist('nota')])
            query = query.filter(ft)
        g.search = search

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
    url = url_for('list_serials')

    if not session.get('logged_in'):
        abort(401)
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
            url += "?nota=%d" % number
            flash(u"Uma nova nota foi importada com sucesso")
        else:
            flash(u"Essa nota já foi importada anteriormente", 'error')

    return redirect(url)

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
