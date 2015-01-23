from datetime import date
import xml.etree.ElementTree as ET

def elem(tree, *children, **kwargs):
    ns = "{%s}" % kwargs.get('ns', "http://www.portalfiscal.inf.br/nfe")
    return tree.find('/'.join(["%s%s" % (ns, child) for child in children]))

def iterelem(tree, *children, **kwargs):
    ns = "{%s}" % kwargs.get('ns', "http://www.portalfiscal.inf.br/nfe")
    return tree.iterfind('/'.join(["%s%s" % (ns, child) for child in children]))


def parse_nfe_document(filename):
    doc = {}

    tree = ET.parse(filename)
    xinfNFe = elem(tree, "NFe", "infNFe")

    version = float(xinfNFe.get("versao"))
    f = {'id': "ide", 'number': "nNF", 'date': "dhEmi",
         'sup': "emit", 'sup.cnpj': "CNPJ", 'sup.name': "xNome",
         'detail': "det", 'prod': "prod", 'prod.name': "xProd",
         'prod.qnt': "qCom"}
    if version == 3.1:
        pass
    elif version == 2.0:
        f.update({'date': "dEmi"})

    xid = elem(xinfNFe, f['id'])
    doc['number'] = int(elem(xid, f['number']).text)
    doc['date'] = date(*map(int, elem(xid, f['date']).text[0:10].split('-')))

    xsup = elem(xinfNFe, f['sup'])
    doc['supplier.cnpj'] = elem(xsup, f['sup.cnpj']).text
    doc['supplier.name'] = elem(xsup, f['sup.name']).text

    doc['products'] = products = []
    for xprod in iterelem(xinfNFe, f['detail'], f['prod']):
        prod = {'name': elem(xprod, f['prod.name']).text,
                'qnt': int(elem(xprod, f['prod.qnt']).text)}
        products.append(prod)

    return doc
