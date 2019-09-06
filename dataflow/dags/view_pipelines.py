import os

from datetime import timedelta

from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator

from dataflow.meta.view_pipelines import (
    CancelledOMISOrderViewPipeline,
    OMISClientSurveyViewPipeline,
    CompletedOMISOrderViewPipeline
)
from dataflow.utils import XCOMIntegratedPostgresOperator


view_pipelines = [
    CompletedOMISOrderViewPipeline,
    CancelledOMISOrderViewPipeline,
    OMISClientSurveyViewPipeline
]

DEBUG = os.environ.get('DEBUG')


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

create_view = """
    DROP VIEW IF EXISTS {{ view_name }}_{{ ds | replace('-', '_') }};
    CREATE VIEW {{ view_name }}_{{ ds | replace('-', '_') }} AS SELECT
    {% for field_name, field_alias in fields %}
        {{ field_name }} AS "{{ field_alias }}"{{ "," if not loop.last }}
    {% endfor %}
    FROM "{{ table_name }}"
    WHERE

"""

if DEBUG:
    list_all_views = """
        select table_schema as schema_name,
               table_name as view_name
        from information_schema.views
        where table_schema not in ('information_schema', 'pg_catalog')
        order by schema_name,
                 view_name;
    """


for pipeline in view_pipelines:
    user_defined_macros = {
        'view_name': pipeline.view_name,
        'table_name': pipeline.table_name,
        'fields': pipeline.fields,
    }
    if getattr(pipeline, 'params', None):
        user_defined_macros.update(pipeline.params)

    with DAG(
        pipeline.__name__,
        catchup=pipeline.catchup,
        default_args=default_args,
        start_date=pipeline.start_date,
        end_date=pipeline.end_date,
        schedule_interval=pipeline.schedule_interval,
        user_defined_macros=user_defined_macros
    ) as dag:
        PostgresOperator(
            task_id='create-view',
            sql=create_view + pipeline.where_clause,
            postgres_conn_id=pipeline.target_db
        )
        if DEBUG:
            XCOMIntegratedPostgresOperator(
                task_id='list-views',
                sql=list_all_views,
                postgres_conn_id=pipeline.target_db
            )

        globals()[pipeline.__name__] = dag
