from datetime import date
import xml.etree.ElementTree as ET

def elem(tree, *children, **kwargs):
    ns = "{%s}" % kwargs.get('ns', "http://www.portalfiscal.inf.br/nfe")
    return tree.find('/'.join(["%s%s" % (ns, child) for child in children]))

def iterelem(tree, *children, **kwargs):
    ns = "{%s}" % kwargs.get('ns', "http://www.portalfiscal.inf.br/nfe")
    return tree.iter('/'.join(["%s%s" % (ns, child) for child in children]))


def parse_nfe_document(filename):
    doc = {}

    tree = ET.parse(filename)
    infNFe = elem(tree, "NFe", "infNFe")

    version = float(infNFe.get("versao"))
    f = {'id': "ide", 'number': "nNF", 'date': "dhEmi",
         'sup': "emit", 'sup.cnpj': "CNPJ", 'sup.name': "xNome",
         'sale': "det", 'prod': "prod", 'prod.name': "xProd"}
    if version == 3.1:
        pass
    elif version == 2.0:
        f.update({'date': "dEmi"})

    ide = elem(infNFe, f['id'])
    doc['number'] = int(elem(ide, f['number']).text)
    doc['date'] = date(*map(int, elem(ide, f['date']).text[0:10].split('-')))

    emit = elem(infNFe, f['sup'])
    doc['supplier.cnpj'] = elem(emit, f['sup.cnpj']).text
    doc['supplier.name'] = elem(emit, f['sup.name']).text

    det = elem(infNFe, f['sale'])
    doc['products'] = products = []
    for prod in iterelem(det, f['prod']):
        products.append(elem(prod, f['prod.name']).text)

    return doc
