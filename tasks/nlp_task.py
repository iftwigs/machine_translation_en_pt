import json
import os

import boto3
from botocore.exceptions import ClientError

import translate
from nlp import Results
from tasks.celery_app import celery_app

os.environ['BUCKET'] = "c-locale-eng"
KEY = os.urandom(32)

S3_CLIENT = boto3.client('s3', region_name=os.environ['REGION'],
                         aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                         aws_secret_access_key=os.environ[
                             'AWS_SECRET_ACCESS_KEY']
                         )

LOCALES = ['en', 'pt']


@celery_app.task()
def translation_task(document_id, source_locale, target_locale, document_type):
    print('started the task')
    filename = f"Documents/{document_id}/{document_id}.json"
    res = {}
    print(filename)
    try:
        result_json = json.loads(
            S3_CLIENT.get_object(Bucket=os.environ['BUCKET'],
                                 Key=filename)[
                'Body'].read().decode('utf8')
        )
        print('got object')
        print(result_json)
        if source_locale not in LOCALES:
            print(f"Translation from {source_locale} is not possible.")
        else:
            if source_locale != 'en':
                translated = translate.get_translation(result_json['ocr']['all_plaintext'],
                                                       '{}-{}'.format(
                                                           source_locale,
                                                           target_locale),
                                                       document_type)
            else:
                print(
                    'The text is already in target language, no translation needed.')
                translated = result_json['ocr']['all_plaintext']
            results_ = {'document_id': document_id, 'content': translated}
            print(results_)
            try:
                result_json['translation'] = Results(**results_).dict()
                S3_CLIENT.put_object(Bucket=os.environ['BUCKET'],
                                     Key=filename,
                                     Body=json.dumps(result_json).encode(
                                         'utf8')
                                     )
            except TypeError:
                res['translation'] = Results(**results_).dict()
                S3_CLIENT.put_object(Bucket=os.environ['BUCKET'],
                                     Key=filename,
                                     Body=json.dumps(res).encode('utf8')
                                     )
            print('uploaded the file')
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'NoSuchKey':
            print(f"No file under name {filename} exists.")
    return document_id


def translation_no_celery(text, source_locale, target_locale):
    translated = translate.get_translation(text,
                                           '{}-{}'.format(
                                               source_locale,
                                               target_locale),
                                           )
    print(translated)
    return translated
