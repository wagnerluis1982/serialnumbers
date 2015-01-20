from sqlalchemy import (create_engine, Column, Integer, String, Date,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base

def db_engine(database, debug):
    return create_engine("sqlite:///%s" % database, echo=debug)


def session_factory(*args):
    if len(args) == 1:
        engine = args[0]
    elif len(args) == 2:
        engine = db_engine(*args)
    else:
        return

    return sessionmaker(bind=engine)


Base = declarative_base()

class SerialNumber(Base):
    __tablename__ = 'serialnumbers'
    __table_args__ = (
        UniqueConstraint('product_id', 'document_id', 'number'),
    )

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    number = Column(String(50), nullable=True)

    product = relationship('Product', backref='serialnumbers')
    document = relationship('Document', backref='serialnumbers')

    def __repr__(self):
        return "<SerialNumber(number='%s')>" % self.number


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))

    products = association_proxy('serialnumbers', 'product')

    def __repr__(self):
        return "<Document(number='%d')>" % self.number


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))

    documents = association_proxy('serialnumbers', 'document')

    def __repr__(self):
        return "<Product(name='%s')>" % self.name


class Supplier(Base):
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    cnpj = Column(String(14), nullable=False, unique=True)
    name = Column(String(255), nullable=False)

    documents = relationship('Document', backref='supplier')
    products = relationship('Product', backref='supplier')

    def __repr__(self):
        return "<Supplier(cnpj='%s')>" % self.cnpj
