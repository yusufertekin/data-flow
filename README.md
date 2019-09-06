# Data Flow

## Data Flow uses airflow to manage data pipelines;
## Currently between datahub and dataworkspace. It manages a certain pipeline structure until more pipelines introduced:
- Task 1: Check if target table exists (PostgresOperator)
- Task 2: Get all paginated data from source by making hawk authenticated GET request to given source API's URL. (PythonOperator)
- Task 3: If target table in place (result from Task 1), test validity of incoming data by creating copy table and inserting data there before doing any change on target table. Then, insert fetched data (result from Task 2) into target table

Task 1 and Task 2 are independent and running in parallel.

Task 3 requires on successful run of Task 1 and Task2.

There are currently two generic pipeline structure uses meta objects to dynamically creates DAGs.

They are placed under dataflow/meta folder. Please check regarding docstrings for more information about meta objects.

## To add your dataset pipeline, modify dataflow/meta/datasets_flow.py
## Example DatasetFlow
```
class OMISDatasetPipeline:
    # Target table name
    table_name = 'omis_dataset'
    # Source API access url
    source_url = 'https://datahub-api-demo.london.cloudapps.digital/v4/dataset/omis-dataset'
    # Target Database
    target_db = 'datasets_db'
    # Start date for this flow
    start_date = datetime.now().replace(day=1)
    # End date for this flow
    end_date = datetime(2019, 12, 01)
    # Maps source API response fields with target db columns
    # (source_response_field_name, target_table_field_name, target_table_field_constraints)
    field_mapping = [
        (
            'reference',
            'omis_order_reference',
            'character varying(100) PRIMARY KEY'
        ),
        (
            'company__name',
            'company_name',
            'character varying(255) NOT NULL'
        )
        (
            'completed_on',
            'completion_date',
            'timestamp with time zone'
        ),
        (
            'delivery_date',
            'delivery_date',
            'date'
        ),
        (
            'cancellation_reason__name',
            'cancellation_reason',
            'text'
        ),
	...
   ]
``` 

## To add your view pipeline, modify dataflow/meta/view_pipelines.py
## Example ViewPipeline

```
class CompletedOMISOrderViewPipeline():
    view_name = 'completed_omis_orders'
    table_name = 'omis_dataset'
    target_db = 'datasets_db'
    start_date = datetime(2017, 11, 1)
    end_date = datetime(2018, 2, 1)
    # Runs the task from start date to end date or now in scheduled interval
    catchup = True
    # (field_name, field_alias)
    fields = [
        ('company_name', 'Company Name'),
        ('dit_team', 'DIT Team'),
        ('subtotal', 'Subtotal'),
        ('uk_region', 'UK Region'),
        ('market', 'Market'),
        ('sector', 'Sector'),
        ('services', 'Services'),
        ('delivery_date', 'Delivery Date'),
        ('payment_received_date', 'Payment Received Date'),
        ('completion_date', 'Completion Date')
    ]
    # ds is a macro provided by airflow holds execution date in 'YYYY-MM-DD' format
    where_clause = (
        "order_status = 'complete' AND "
        "date_trunc('month', completion_date)::DATE = "
        "date_trunc('month', to_date('{{ ds }}', 'YYYY-MM-DD'));"
    )
    schedule_interval = '@monthly'
```


## Useful Information
- Airflow runs on UTC timezone by the community to prevent confusion that's why UI values are displayed in UTC timezone.
- Possible schedule_interval values. For more info: (https://airflow.apache.org/scheduler.html)

             '@once' # Schedule once and only once
             '@hourly' # Run once an hour at the beginning of the hour
             '@daily' # Run once a day at midnight CRON: 0 0 * * *
             '@weekly' # Run once a week at midnight on Sunday morning CRON: 0 0 * * 0
             '@monthly' # Run once a month at midnight of the first day of the month CRON: 0 0 1 * *
             '@yearly' # Run once a year at midnight of January 1 CRON: 0 0 1 1 *
