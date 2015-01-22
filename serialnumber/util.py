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

    ide = elem(infNFe, "ide")
    doc['number'] = int(elem(ide, "nNF").text)
    doc['date'] = date(*map(int, elem(ide, "dhEmi").text[0:10].split('-')))

    emit = elem(infNFe, "emit")
    doc['supplier.cnpj'] = elem(emit, "CNPJ").text
    doc['supplier.name'] = elem(emit, "xNome").text

    det = elem(infNFe, "det")
    doc['products'] = products = []
    for prod in iterelem(det, "prod"):
        products.append(elem(prod, "xProd").text)

    return doc
