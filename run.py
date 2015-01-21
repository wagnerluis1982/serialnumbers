if __name__ == '__main__':
    import sys
    from serialnumber import model, control

    if len(sys.argv) == 1:
        control.app.run(host='0.0.0.0')
    elif sys.argv[1] == 'database':
        db_engine = model.db_engine(control.app.config['DATABASE'],
                                    control.app.config['DEBUG'])
        model.Base.metadata.drop_all(db_engine)
        model.Base.metadata.create_all(db_engine)
