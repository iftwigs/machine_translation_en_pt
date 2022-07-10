import os
from dotenv import load_dotenv
from celery import Celery

load_dotenv()

celery_app = Celery('mt-service',
                    broker=os.environ['CELERY_BROKER_URL'],
                    backend=os.environ['CELERY_BACKEND'],
                    task_track_started=True,
                    include=['tasks.nlp_task']
                    )
