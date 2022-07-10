import json
import os

import boto3
import prometheus_client
import redis
import requests
import spacy
import uvicorn

from ast import literal_eval
from celery import Celery
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from prometheus_client import Gauge, Histogram
from starlette import status

from nlp import RequestModel, ResponseModel, RequestModelPlain, ResponseModelPlain
from tasks.nlp_task import translation_task, translation_no_celery

load_dotenv()

SUCCESS_STATE = 'SUCCESS'
FAILURE_STATE = 'FAILURE'
API_KEY = os.environ['API_KEY']
API_KEY_NAME = "X-API-KEY"
PORT = os.environ['PORT_NUM']

spacy.load('en_core_web_sm')
print('loaded spacy')

s3 = boto3.client('s3', region_name=os.environ['REGION'],
                  aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                  aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
                  )

r = redis.Redis(
    host=os.environ['REDIS_HOST'],
    port=os.environ['REDIS_PORT'],
    db=os.environ['REDIS_DB'],
    password=os.environ['REDIS_PASSWORD']
)

app = FastAPI()

print('loaded fastapi')

api_key_header_auth = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
inf = float("inf")
graphs = {
    'hc': Gauge("python_request_health_check_status",
                "Check availability of unsuccessful requests"),
    'resp_time': Histogram("python_response_time",
                           "Histogram with measurements of response time",
                           buckets={1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                                    inf})
}

print('initialized graphs')


def get_api_key(api_key_header: str = Security(api_key_header_auth)):
    if api_key_header != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )


celery_app = Celery('main',
                    broker=os.environ['CELERY_BROKER_URL'],
                    backend=os.environ['CELERY_BACKEND'],
                    include=['tasks.nlp_task']
                    )

print('initialized celery')


@app.post("/translate", dependencies=[Security(get_api_key)],
          response_model=ResponseModel)
def translation(request: RequestModel):
    request_dict = request.dict()
    task = translation_task.delay(request_dict['document_id'],
                                  request_dict['source_locale'],
                                  request_dict['target_locale'])
    return ResponseModel(
        task_id=task.task_id,
        task_status=task.state,
        bundle={},
        error={}
    )


@app.get('/translate', dependencies=[Security(get_api_key)],
         response_model=ResponseModel)
def get_translation_status(task_id: str):
    task = translation_task.AsyncResult(task_id)
    if task.state == SUCCESS_STATE:
        output = task.get()
    else:
        if task.state == FAILURE_STATE:
            r = redis.StrictRedis.from_url(os.environ['CELERY_BACKEND'])
            task_in_redis = r.get(f'celery-task-meta-{task.task_id}')
            error = literal_eval(task_in_redis.decode('utf-8'))["result"]
        output = {}
    return ResponseModel(
        task_id=task.task_id,
        task_status=task.state,
        bundle=output,
        error=error
    )


@app.get('/hc')
def health_check():
    translation_payload = json.dumps(
        {'document_id': 'healthcheck', 'locale': 'ru'})
    r = requests.post('https://machine-translation-ru-en-service.dev.onexcare.com/translate',
                      data=translation_payload,
                      headers={
                          "X-API-KEY": os.environ[
                              'X_API_Key']
                      }
                      )
    print('posted a request')

    if r.status_code != 200:
        graphs['hc'].set(0)
        print('0')
        return '400', 400
    else:
        graphs['hc'].set(1)
        print('1')
        return '200', 200


@app.route('/metrics')
def request_hc():
    res = []
    for k, v in graphs.items():
        res.append(prometheus_client.generate_latest(v))
    return ResponseModel(res, mimetype='text/plain')


@app.post('/translate_sync',
          dependencies=[Security(get_api_key)],
          response_model=ResponseModelPlain)
def translation(request: RequestModelPlain):
    print('started task')
    request_dict = request.dict()
    print('init request')
    result = translation_no_celery(request_dict['text'],
                                   request_dict['source_locale'],
                                   request_dict['target_locale']
                                   )
    return ResponseModelPlain(
        text=request_dict['text'],
        translation=result
    )


if __name__ == "__main__":
    print('started app')
    uvicorn.run(app, host='0.0.0.0', port=int(PORT), debug=True,
                )
