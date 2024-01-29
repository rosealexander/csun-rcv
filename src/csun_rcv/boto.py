import json

from contextlib import AsyncExitStack

from aiobotocore.session import AioSession

from logger import Logger, logging_context

logger = Logger(__name__).get()


class DynamoDBClient:
    def __init__(self, **kwargs):
        self._exit_stack = AsyncExitStack()
        self._dynamodb_client = None

    async def __aenter__(self):
        dynamodb_client = AioSession().create_client('dynamodb')

        with logging_context('aiobotocore.credentials', 'WARN'):
            self._dynamodb_client = await self._exit_stack.enter_async_context(dynamodb_client)

        return self._dynamodb_client

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self._exit_stack.__aexit__(exc_t, exc_v, exc_tb)
        self._dynamodb_client = None


async def put_item(dynamodb_client, table_name, item):
    resp = await dynamodb_client.put_item(
        TableName=table_name,
        Item=item
    )
    return resp


class S3Client:
    def __init__(self, **kwargs):
        self._exit_stack = AsyncExitStack()
        self._s3_client = None

    async def __aenter__(self):
        s3_client = AioSession().create_client('s3')

        with logging_context('aiobotocore.credentials', 'WARN'):
            self._s3_client = await self._exit_stack.enter_async_context(s3_client)

        return self._s3_client

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self._exit_stack.__aexit__(exc_t, exc_v, exc_tb)
        self._s3_client = None


async def put_object(s3_client, bucket, key, path):
    data = open(path, 'rb')
    resp = await s3_client.put_object(Bucket=bucket, Key=key, Body=data)
    return resp


class SSMClient:
    def __init__(self, **kwargs):
        self._exit_stack = AsyncExitStack()
        self._ssm_client = None

    async def __aenter__(self):
        ssm_client = AioSession().create_client('ssm')

        self._ssm_client = await self._exit_stack.enter_async_context(ssm_client)

        return self._ssm_client

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self._exit_stack.__aexit__(exc_t, exc_v, exc_tb)
        self._ssm_client = None


#
def put_parameter(ssm_client, name, value):
    return ssm_client.put_parameter(
        Name=name,
        Overwrite=True,
        Value=json.dumps(value)
    )
