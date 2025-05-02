import json

import sqlalchemy as db
from sqlalchemy import text, Column, inspect, Table

from nlq.data_access.dynamo_connection import ConnectConfigEntity
from utils.logging import getLogger

logger = getLogger()

class RelationDatabase():
    db_mapping = {
        'mysql': 'mysql+pymysql',
        'postgresql': 'postgresql+psycopg2',
        'redshift': 'redshift+psycopg2',
        'starrocks': 'starrocks',
        'clickhouse': 'clickhouse',
        'hive': 'hive',
        'athena': 'awsathena+rest',
        'bigquery': 'bigquery',
        'presto': 'presto',
        'sqlserver': 'mssql+pymssql',
        'maxcompute': 'odps'
        # Add more mappings here for other databases
    }

    @classmethod
    def get_db_url(cls, db_type, user, password, host, port, db_name):
        if db_type == "hive":
            db_url = db.engine.URL.create(
                drivername=cls.db_mapping[db_type],
                username=user,
                password=password,
                host=host,
                port=port,
                database=db_name,
                query={'auth': 'LDAP'}
            )
        elif db_type == "athena":
            db_url = db.engine.URL.create(
                drivername=cls.db_mapping[db_type],
                query={'s3_staging_dir': db_name}
            )
            logger.info(f"db_url: {db_url}")
        elif db_type == 'bigquery':
            password = json.loads(password)
            db_url = db.engine.URL.create(
                drivername=cls.db_mapping[db_type],
                host=host,  # BigQuery project. Note: without dataset
                query={'credentials_path': json.dumps(password)}
            )
        elif db_type == 'presto':
            db_url = db.engine.URL.create(
                drivername=cls.db_mapping[db_type],
                host=host,
                port=port,
                database=db_name
            )
        elif db_type == 'sqlserver':
            db_url = db.engine.URL.create(
                drivername=cls.db_mapping[db_type],
                username=user,
                password=password,
                host=host,
                port=port,
                database=db_name
            )
            return db_url
        elif db_type == 'maxcompute':
            db_url = 'odps://%s:%s@%s/?endpoint=%s' % (
                user,
                password,
                db_name,
                host)
        else:
            db_url = db.engine.URL.create(
                drivername=cls.db_mapping[db_type],
                username=user,
                password=password,
                host=host,
                port=port,
                database=db_name
            )
        return db_url

    @classmethod
    def test_connection(cls, db_type, user, password, host, port, db_name) -> bool:
        try:
            if db_type == 'athena':
                engine = db.create_engine(
                    'awsathena+rest://@athena.{region_name}.amazonaws.com/{database_name}'.format(
                        region_name='us-west-2',
                        database_name=db_name
                    ),
                    connect_args={'s3_staging_dir': db_name}
                )
            else:
                if db_type == "bigquery":
                    password = json.loads(password)
                    engine = db.create_engine(url=host, credentials_info=password)
                else:
                    engine = db.create_engine(cls.get_db_url(db_type, user, password, host, port, db_name))
            connection = engine.connect()
            return True
        except Exception as e:
            logger.exception(e)
            logger.error(f"Failed to connect: {str(e)}")
            return False

    @classmethod
    def get_all_schema_names_by_connection(cls, connection: ConnectConfigEntity):
        db_type = connection.db_type
        db_url = cls.get_db_url(db_type, connection.db_user, connection.db_pwd, connection.db_host, connection.db_port,
                                connection.db_name)
        if db_type == "bigquery":
            password = json.loads(connection.db_pwd)
            engine = db.create_engine(url=connection.db_host, credentials_info=password)
        else:
            engine = db.create_engine(db_url)
        inspector = inspect(engine)

        if db_type == 'postgresql':
            schemas = [schema for schema in inspector.get_schema_names() if
                       schema not in ('pg_catalog', 'information_schema', 'public')]
        elif db_type in ('redshift', 'mysql', 'starrocks', 'clickhouse', 'hive', 'athena', 'bigquery', 'presto', 'sqlserver', 'maxcompute'):
            schemas = inspector.get_schema_names()
        else:
            raise ValueError("Unsupported database type")

        return schemas

    @classmethod
    def get_all_schema_and_table_names_by_connection(cls, connection: ConnectConfigEntity):
        db_type = connection.db_type
        db_url = cls.get_db_url(db_type, connection.db_user, connection.db_pwd, connection.db_host, connection.db_port,
                                connection.db_name)
        if db_type == "bigquery":
            password = json.loads(connection.db_pwd)
            engine = db.create_engine(url=connection.db_host, credentials_info=password)
        else:
            engine = db.create_engine(db_url)
        inspector = inspect(engine)

        if db_type == 'postgresql':
            schemas = [schema for schema in inspector.get_schema_names() if
                       schema not in ('pg_catalog', 'information_schema', 'public')]
        elif db_type in ('redshift', 'mysql', 'starrocks', 'clickhouse', 'hive', 'athena', 'bigquery', 'presto', 'sqlserver', 'maxcompute'):
            schemas = inspector.get_schema_names()
        else:
            raise ValueError("Unsupported database type")

        schema_table_dict = {}
        for schema in schemas:
            schema_table_dict[schema] = inspector.get_table_names(schema=schema)
        return schema_table_dict

    @classmethod
    def get_all_tables_by_connection(cls, connection: ConnectConfigEntity, schemas=None):
        if schemas is None:
            schemas = []
        metadata = cls.get_metadata_by_connection(connection, schemas)
        return metadata.tables.keys()

    @classmethod
    def get_metadata_by_connection(cls, connection, schemas):
        db_url = cls.get_db_url(connection.db_type, connection.db_user, connection.db_pwd, connection.db_host,
                                connection.db_port, connection.db_name)
        if connection.db_type == "bigquery":
            password = json.loads(connection.db_pwd)
            engine = db.create_engine(url=connection.db_host, credentials_info=password)
        else:
            engine = db.create_engine(db_url)
        # connection = engine.connect()
        metadata = db.MetaData()
        if connection.db_type == 'bigquery':
            metadata.reflect(bind=engine)
            return metadata
        elif connection.db_type == 'presto':
            for s in schemas:
                metadata.reflect(bind=engine, schema=s)
            return metadata
        else:
            for s in schemas:
                metadata.reflect(bind=engine, schema=s, views=True)
            # metadata.reflect(bind=engine)
            return metadata
    @classmethod
    def get_metadata_only_table_by_connection(cls, connection, schemas_table_dict):
        db_url = cls.get_db_url(connection.db_type, connection.db_user, connection.db_pwd, connection.db_host,
                                connection.db_port, connection.db_name)
        if connection.db_type == "bigquery":
            password = json.loads(connection.db_pwd)
            engine = db.create_engine(url=connection.db_host, credentials_info=password)
        else:
            engine = db.create_engine(db_url)
        # connection = engine.connect()
        metadata = db.MetaData()
        schemas = list(schemas_table_dict.keys())
        if connection.db_type == 'bigquery':
            metadata.reflect(bind=engine)
            return metadata
        elif connection.db_type == 'presto':
            for s in schemas:
                tables = schemas_table_dict[s]
                metadata.reflect(bind=engine, schema=s, only=tables)
            return metadata
        else:
            for s in schemas:
                tables = schemas_table_dict[s]
                metadata.reflect(bind=engine, schema=s, views=True, only=tables)
            # metadata.reflect(bind=engine)
            return metadata

    @classmethod
    def get_metadata_by_table(cls, connection, tables):
        db_url = cls.get_db_url(connection.db_type, connection.db_user, connection.db_pwd, connection.db_host,
                                connection.db_port, connection.db_name)
        if connection.db_type == "bigquery":
            password = json.loads(connection.db_pwd)
            engine = db.create_engine(url=connection.db_host, credentials_info=password)
        else:
            engine = db.create_engine(db_url)
            logger.info(db_url)
        metadata = db.MetaData()
        table_info = {}
        try:
            for each_table in tables:
                table_info[each_table] = {}
                logger.info(each_table)
                if "." in each_table:
                    schema, table = each_table.split(".")[0], each_table.split(".")[1]
                    table = Table(table, metadata, autoload_with=engine, schema=schema)
                else:
                    table = Table(each_table, metadata, autoload_with=engine)
                logger.info(table)
                for column in table.columns:
                    logger.info(f"  Column Name: {column.name}, Data Type: {column.type}")
                    table_info[each_table][column.name] = column.type
        except Exception as e:
            logger.error(f"Error loading table column {tables}: {e}")
        return table_info

    @classmethod
    def get_table_definition_by_connection(cls, connection: ConnectConfigEntity, schemas_table_dict):
        # metadata = cls.get_metadata_by_connection(connection, schemas)
        metadata = cls.get_metadata_only_table_by_connection(connection, schemas_table_dict)
        table_names = []
        for each_schema, tables in schemas_table_dict.items():
            for each_table in tables:
                table_names.append(each_schema + "." + each_table)
        tables = metadata.tables
        table_info = {}
        if connection.db_type == 'hive':
            tables_comment = cls.get_hive_table_comment(connection, table_names)
        else:
            tables_comment = {}

        for table_name, table in tables.items():
            # If table name is provided, only generate DDL for those tables. Otherwise, generate DDL for all tables.
            if len(table_names) > 0 and table_name not in table_names:
                continue
            # Start the DDL statement
            table_comment = f'-- {table.comment}' if table.comment else ''
            ddl = f"CREATE TABLE {table_name} {table_comment} \n (\n"

            if table_name in tables_comment:
                column_comment_value = tables_comment[table_name]
            else:
                column_comment_value = {}
            for column in table.columns:
                column: Column
                # get column description
                if column.comment is None:
                    if column.name in column_comment_value:
                        column.comment = column_comment_value[column.name]
                column_comment = f'COMMENT {column.comment}' if column.comment else ''
                ddl += f"  {column.name} {column.type.__visit_name__} {column_comment},\n"
            ddl = ddl.rstrip(',\n') + "\n)"  # Remove the last comma and close the CREATE TABLE statement
            table_info[table_name] = {}
            table_info[table_name]['ddl'] = ddl
            table_info[table_name]['description'] = table.comment
            logger.info(f'added table {table_name} to table_info dict')

        return table_info

    @classmethod
    def get_table_column_definition_by_connection(cls, connection: ConnectConfigEntity, table_names):
        table_column = cls.get_metadata_by_table(connection, table_names)
        return table_column

    @classmethod
    def get_hive_table_comment(cls, connection, table_names):
        table_name_comment = {}
        try:
            db_url = cls.get_db_url(connection.db_type, connection.db_user, connection.db_pwd, connection.db_host,
                                    connection.db_port, connection.db_name)
            engine = db.create_engine(db_url)
            for each_table in table_names:
                table_name_comment[each_table] = {}
                with engine.connect() as connection:
                    sql = "describe " + each_table
                    result = connection.execute(sql)
                    for row in result:
                        if len(row) == 3:
                            table_name_comment[each_table][row[0]] = "'" + row[2] + "'"
            return table_name_comment
        except Exception as e:
            logger.error(f"Failed to get table comment: {str(e)}")
            return table_name_comment

    @classmethod
    def get_db_url_by_connection(cls, connection: ConnectConfigEntity):
        db_url = cls.get_db_url(connection.db_type, connection.db_user, connection.db_pwd, connection.db_host,
                                connection.db_port, connection.db_name)
        return db_url

    @classmethod
    def get_password_host_by_connection(cls, connection: ConnectConfigEntity):
        return connection.db_pwd, connection.db_host
