from pprint import pprint
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal


def get_poll(user, question, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource(
            'dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.Table('Polls')

    try:
        response = table.get_item(Key={'user': user, 'question': question})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print('Response:')
        print(response, '\n\n\n')
        return response['Item']


def update_poll(user, question, option, voter, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource(
            'dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.Table('Polls')

    response = table.update_item(
        Key={
            'user': user,
            'question': question
        },
        UpdateExpression="set responses.#option.score = responses.#option.score + :r, responses.#option.voters.#voter = :v",
        ConditionExpression="attribute_not_exists(responses.#option.voters.#voter)",
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
    return response


if __name__ == '__main__':
    poll = update_poll(1, "Go real left international cut TV interview.", "protect", 2)
    if poll:
        print("Get poll succeeded:")
        pprint(poll, sort_dicts=False)
