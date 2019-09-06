from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.postgres_operator import PostgresOperator


class XCOMIntegratedPostgresOperator(PostgresOperator):

    def execute(self, context):
        self.log.info('Executing: %s', self.sql)
        self.hook = PostgresHook(postgres_conn_id=self.postgres_conn_id,
                                 schema=self.database)
        return self.hook.get_records(self.sql, parameters=self.parameters)
