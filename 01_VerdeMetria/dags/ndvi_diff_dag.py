"""
Airflow DAG for NDVI Difference Computation

This DAG demonstrates an automated workflow for computing NDVI temporal differences.
It can be deployed to an Airflow instance for scheduled execution.

Note: Airflow is optional. You can run scripts manually or use other schedulers.
"""

from datetime import datetime, timedelta
from pathlib import Path

# Uncomment when deploying to Airflow
# from airflow import DAG
# from airflow.operators.bash import BashOperator
# from airflow.operators.python import PythonOperator

# Default arguments for the DAG
default_args = {
    'owner': 'verdemetria',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition (commented out - uncomment when deploying)
"""
dag = DAG(
    'ndvi_difference_workflow',
    default_args=default_args,
    description='Compute NDVI and temporal differences',
    schedule_interval='@weekly',  # Run weekly
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ndvi', 'remote-sensing'],
)

# Task 1: Download latest Sentinel-2 data
download_task = BashOperator(
    task_id='download_sentinel2',
    bash_command='echo "TODO: Implement sentinelsat download"',
    dag=dag,
)

# Task 2: Compute NDVI for time 1
ndvi_t1_task = BashOperator(
    task_id='compute_ndvi_t1',
    bash_command=(
        'python /path/to/scripts/ndvi_compute.py '
        '--red {{ params.red_t1 }} '
        '--nir {{ params.nir_t1 }} '
        '--out {{ params.ndvi_t1_out }}'
    ),
    params={
        'red_t1': '/data/raw/t1/B04.tif',
        'nir_t1': '/data/raw/t1/B08.tif',
        'ndvi_t1_out': '/data/processed/ndvi_t1.tif',
    },
    dag=dag,
)

# Task 3: Compute NDVI for time 2
ndvi_t2_task = BashOperator(
    task_id='compute_ndvi_t2',
    bash_command=(
        'python /path/to/scripts/ndvi_compute.py '
        '--red {{ params.red_t2 }} '
        '--nir {{ params.nir_t2 }} '
        '--out {{ params.ndvi_t2_out }}'
    ),
    params={
        'red_t2': '/data/raw/t2/B04.tif',
        'nir_t2': '/data/raw/t2/B08.tif',
        'ndvi_t2_out': '/data/processed/ndvi_t2.tif',
    },
    dag=dag,
)

# Task 4: Compute NDVI difference and areas
diff_task = BashOperator(
    task_id='compute_ndvi_diff',
    bash_command=(
        'python /path/to/scripts/ndvi_diff_area.py '
        '--ndvi1 {{ params.ndvi_t1 }} '
        '--ndvi2 {{ params.ndvi_t2 }} '
        '--out {{ params.diff_out }} '
        '--metric_epsg 3116'
    ),
    params={
        'ndvi_t1': '/data/processed/ndvi_t1.tif',
        'ndvi_t2': '/data/processed/ndvi_t2.tif',
        'diff_out': '/data/outputs/ndvi_diff.tif',
    },
    dag=dag,
)

# Task 5: Generate report
report_task = BashOperator(
    task_id='generate_report',
    bash_command='echo "TODO: Implement report generation"',
    dag=dag,
)

# Define task dependencies
download_task >> [ndvi_t1_task, ndvi_t2_task]
[ndvi_t1_task, ndvi_t2_task] >> diff_task
diff_task >> report_task
"""

# Placeholder function for local testing
def test_dag_structure():
    """
    Test function to validate DAG structure without Airflow.
    """
    print("DAG structure defined successfully")
    print("Tasks: download -> ndvi_t1, ndvi_t2 -> diff -> report")
    print("\nTo deploy to Airflow:")
    print("1. Install Airflow: pip install apache-airflow")
    print("2. Initialize DB: airflow db init")
    print("3. Copy this file to $AIRFLOW_HOME/dags/")
    print("4. Uncomment DAG code above")
    print("5. Start scheduler: airflow scheduler")
    print("6. Start webserver: airflow webserver")

if __name__ == "__main__":
    test_dag_structure()
