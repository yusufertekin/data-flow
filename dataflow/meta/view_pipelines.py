from datetime import datetime


class CompletedOMISOrderViewPipeline():
    view_name = 'completed_omis_orders'
    table_name = 'omis_dataset'
    target_db = 'datasets_db'
    start_date = datetime(2017, 11, 1)
    end_date = datetime(2018, 2, 1)
    catchup = True
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
        ('completion_date', 'Completion Date'),
    ]
    where_clause = (
        "order_status = 'complete' AND "
        "date_trunc('month', completion_date)::DATE = "
        "date_trunc('month', to_date('{{ ds }}', 'YYYY-MM-DD'));"
    )
    schedule_interval = '@monthly'


class CancelledOMISOrderViewPipeline():
    view_name = 'cancelled_omis_orders'
    table_name = 'omis_dataset'
    target_db = 'datasets_db'
    start_date = datetime(2017, 11, 1)
    end_date = datetime(2018, 2, 1)
    catchup = True
    fields = [
        ('omis_order_reference', 'OMIS Order Reference'),
        ('company_name', 'Company Name'),
        ('net_price', 'Net Price'),
        ('dit_team', 'DIT Team'),
        ('market', 'Market'),
        ('sector', 'Sector'),
        ('created_date', 'Created Date'),
        ('cancelled_date', 'Cancelled Date'),
        ('cancellation_reason', 'Cancellation Reason'),
    ]
    where_clause = (
        "order_status = 'cancelled' AND "
        "cancelled_date::DATE >= "
        "date_trunc('year', to_date('{{ first_day_of_financial_year }}', 'YYYY-MM-DD'));"
    )
    params = {
        'first_day_of_financial_year': datetime(2017, 10, 1)
    }
    schedule_interval = '@monthly'


class OMISClientSurveyViewPipeline():
    view_name = 'omis_client_survey'
    table_name = 'omis_dataset'
    target_db = 'datasets_db'
    start_date = datetime(2017, 11, 1)
    end_date = datetime(2018, 2, 1)
    catchup = True
    fields = [
        ('company_name', 'Company Name'),
        ('contact_first_name', 'Contact First Name'),
        ('contact_last_name', 'Contact Last Name'),
        ('contact_email', 'Contact Email'),
        ('company_trading_address_line_1', 'Company Trading Address Line 1'),
        ('company_trading_address_line_2', 'Company Trading Address Line 2'),
        ('company_trading_address_town', 'Company Trading Address Town'),
        ('company_trading_address_county', 'Company Trading Address County'),
        ('company_trading_address_postcode', 'Company Trading Address Postcode'),
        ('company_registered_address_1', 'Company Registered Address 1'),
        ('company_registered_address_2', 'Company Registered Address 2'),
        ('company_registered_address_town', 'Company Registered Address Town'),
        ('company_registered_address_county', 'Company Registered Address County'),
        ('company_registered_address_country', 'Company Registered Address Country'),
        ('company_registered_address_postcode', 'Company Registered Address Postcode'),
    ]
    where_clause = (
        "order_status = 'complete' AND "
        "date_trunc('month', completion_date)::DATE = "
        "date_trunc('month', to_date('{{ ds }}', 'YYYY-MM-DD'));"
    )
    schedule_interval = '@monthly'
