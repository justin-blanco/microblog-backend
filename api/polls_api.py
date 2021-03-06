import configparser
import logging.config
import boto3
from boto3.dynamodb.conditions import Key
from pprint import pprint
from botocore.exceptions import ClientError
from falcon import response
from decimal import Decimal

import hug

# Load configuration
config = configparser.ConfigParser()
config.read("./etc/polls_api.ini")
logging.config.fileConfig(
    config["logging"]["config"], disable_existing_loggers=False)

# Arguements to inject into route functions


@hug.directive()
def boto(url="http://localhost:8000", table="Polls", **kwargs):
    return boto3.resource('dynamodb', endpoint_url=url).Table(table)


@hug.directive()
def log(name=__name__, **kwargs):
    return logging.getLogger(name)

# Routes
# Returns all polls of all users


@hug.get("/polls/", output=hug.output_format.pretty_json)
def get_polls(response, db: boto):
    results = []

    scan_kwargs = {
        'FilterExpression': Key('user').between(*(0, 100)),
        'ProjectionExpression': "#ur, question, info.responses",
        'ExpressionAttributeNames': {"#ur": "user"}
    }

    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        resp = db.scan(**scan_kwargs)
        results.append(resp.get('Items', []))
        start_key = resp.get('LastEvaluatedKey', None)
        done = start_key is None
    return results

# Returns the polls of a user


@hug.get("/polls/users/{user_id}", output=hug.output_format.pretty_json)
def get_user_polls(
    response,
    user_id: hug.types.number,
    db: boto
):
    response = db.query(
        KeyConditionExpression=Key('user').eq(user_id)
    )
    return response['Items']

@hug.get("/polls/questions/{question}", output=hug.output_format.pretty_json)
def get_question(
    response,
    question: hug.types.text,
    db: boto
):
    print('\n\n\n', question, '\n\n\n\n')
    response = db.query(
        IndexName="QuestionIndex",
        KeyConditionExpression=Key('question').eq(question)
    )
    return response['Items']

# vote for on a user poll


@hug.put("/polls/users/{user_id}", status=hug.falcon.HTTP_201)
def add_vote(
    response,
    user_id: hug.types.number,
    question: hug.types.text,
    voter: hug.types.number,
    option: hug.types.text,
    db: boto
):
    try:
        resp = db.update_item(
            Key={
                'user': user_id,
                'question': question
            },
            UpdateExpression="set responses.#option.score = responses.#option.score + :r, responses.#option.voters.#voter = :v",
            ConditionExpression="attribute_not_exists(responses.voters.#voter)",
            ExpressionAttributeNames={
                '#option': option,
                '#voter': str(voter)
            },
            ExpressionAttributeValues={
                ':r': Decimal(1),
                ':v': Decimal(voter)
            },
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            return {"error": "User already voted"}
        else:
            raise
    else:
        return resp

# @hug.post("/polls/", status=hug.falcon.HTTP_201)
# def create_poll(
#     response,
#     user_id: hug.types.number,
#     question: hug.types.text,
#     responses: hug.types.multiple,
#     db: boto
# ):
#     try:
#         resp = db.put_item(
#             Item={
#                 'user': user_id,
                
#             }
#         )
