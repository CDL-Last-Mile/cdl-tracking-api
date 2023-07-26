import pyodbc
import re

import click
from flask import current_app, g
from sqlalchemy import create_engine


def get_db():
    if 'db' not in g:
        database_uri = "mssql+pymssql://CDL_OrderCleanup:nyc!123xyz@172.24.32.210/CDLData"
        g.db = create_engine(database_uri)

    return g.db.connect()


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.dispose()


def init_db():
    db = get_db()

    # check if schema already exists

    result = db.execute("SELECT name FROM sysobjects WHERE xtype='U' AND name='PortalDistribution';")
    table_exists = result.fetchone() is not None

    if not table_exists:
        with current_app.open_resource('schema.sql') as f:
            db.execute(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
