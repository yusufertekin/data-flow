import os

from datetime import timedelta

import requests

from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.python_operator import PythonOperator

from mohawk import Sender
from mohawk.exc import HawkFail

from dataflow.meta.dataset_pipelines import OMISDatasetPipeline
from dataflow.utils import XCOMIntegratedPostgresOperator


dataset_pipelines = [OMISDatasetPipeline]

credentials = {
    'id': os.environ.get('HAWK_ID'),
    'key': os.environ.get('HAWK_KEY'),
    'algorithm': os.environ.get('HAWK_ALGORITHM'),
}


def run_flow(source_url, **kwargs):
    """Run a recursive flow to fetch data from source and insert into to the target.
    Args:
        source_url (str): URL for API Endpoint to fetch data from source.

    Source endpoint has to accept GET request and respond with HTTP 200 OK for success.
    Needs to be paginated, response is expected to have below structure;
    {
        'next': <link_to_next_page>,
        'results': [list of dict]
    }

    Example source_url.
        source_url = https://datahub-api-demo.london.cloudapps.digital/v4/datasets/omis-dataset
    TODO:
        By the impletation of other Datasets pipeline, there will be more generic structure to
        support various pipeline types.
    """
    results = []
    while True:
        sender = Sender(
            credentials,
            source_url,
            'get',
            always_hash_content=False
        )

        response = requests.get(
            source_url,
            headers={'Authorization': sender.request_header}
        )
        if response.status_code != 200:
            raise Exception(
                f'GET request to {source_url} is unsuccessful\n'
                f'Message: {response.text}'
            )
        try:
            sender.accept_response(response.headers['Server-Authorization'],
                                   content=response.content,
                                   content_type=response.headers['Content-Type'])
        except HawkFail as e:
            raise Exception(f'HAWK Authentication failed {str(e)}')

        response_json = response.json()
        if 'results' not in response_json or 'next' not in response_json:
            raise Exception('Unexpected response structure')

        results += response_json['results']
        next_page = response_json['next']
        if next_page:
            source_url = next_page
            print('Moving on to the next page')
        else:
            break

    print('Fetching from source completed')
    print(f'Response Data: \n {results}')
    return results


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

check_if_table_exists = """
    SELECT to_regclass('{{ table_name }}');
"""

delete_all_and_insert = """
    {% if task_instance.xcom_pull(task_ids="check-if-table-exists")[0][0] and
        task_instance.xcom_pull(task_ids="check-if-table-exists")[0][0] != 'None' %}

        CREATE TABLE "{{ table_name }}_copy" as
            SELECT * from "{{ table_name }}"
        with no data;
        INSERT INTO "{{ table_name }}_copy" (
        {% for _, tt_field_name, _ in field_mapping %}
            {{ tt_field_name }}{{ "," if not loop.last }}
        {% endfor %}
        )
        VALUES
        {% for omis_record in task_instance.xcom_pull(task_ids="run-omis-dataset-flow")  %}
        (
            {% for st_field_name, _, _ in field_mapping %}
                {% if not omis_record[st_field_name] or omis_record[st_field_name] == 'None' %}
                    NULL
                {% else %}
                    {{ omis_record[st_field_name] | replace('"', "'") | tojson | replace('"', "'") }}
                {% endif %}
                {{ "," if not loop.last }}
            {% endfor %}
        {{ ")," if not loop.last }}
        {% endfor %}
        );
        DROP TABLE "{{ table_name }}_copy";
        DELETE FROM "{{ table_name }}";
    {% else %}
        CREATE TABLE "{{ table_name }}" (
        {% for _, tt_field_name, tt_field_constraints in field_mapping %}
            {{ tt_field_name }} {{ tt_field_constraints }}{{ "," if not loop.last }}
        {% endfor %}
        );
    {% endif %}

    INSERT INTO "{{ table_name }}" (
    {% for _, tt_field_name, _ in field_mapping %}
        {{ tt_field_name }}{{ "," if not loop.last }}
    {% endfor %}
    )
    VALUES
    {% for omis_record in task_instance.xcom_pull(task_ids="run-omis-dataset-flow")  %}
    (
        {% for st_field_name, _, _ in field_mapping %}
            {% if not omis_record[st_field_name] or omis_record[st_field_name] == 'None' %}
                NULL
            {% else %}
                {{ omis_record[st_field_name] | replace('"', "'") | tojson | replace('"', "'") }}
            {% endif %}
            {{ "," if not loop.last }}
        {% endfor %}
    {{ ")," if not loop.last }}
    {% endfor %}
    );
"""


for flow in dataset_pipelines:
    with DAG(
        flow.__name__,
        catchup=False,
        default_args=default_args,
        start_date=flow.start_date,
        end_date=flow.end_date,
        schedule_interval='@monthly',
        user_defined_macros={
            'table_name': flow.table_name,
            'field_mapping': flow.field_mapping
        }
    ) as dag:
        t1 = PythonOperator(
            task_id='run-omis-dataset-flow',
            python_callable=run_flow,
            provide_context=True,
            op_args=[f'{flow.source_url}'],
        )

        t2 = XCOMIntegratedPostgresOperator(
            task_id='check-if-table-exists',
            sql=check_if_table_exists,
            postgres_conn_id=flow.target_db
        )

        t3 = PostgresOperator(
            task_id='delete-all-and-insert',
            sql=delete_all_and_insert,
            parameters={
                'table_name': flow.table_name,
                'field_mapping': flow.field_mapping
            },
            postgres_conn_id=flow.target_db,
        )
        t3 << [t1, t2]
        globals()[flow.__name__] = dag
