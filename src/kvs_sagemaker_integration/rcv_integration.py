import asyncio
import itertools
import json
import os
from copy import copy
import errno
import shutil
import sys
import tempfile
import time

import cv2
import numpy as np

from logger import Logger
from mot import Tracker
from rcvprocessor import Processor, FrameContainer
from src.kvs_sagemaker_integration.boto import DynamoDBClient, put_item, S3Client, put_object, SSMClient, put_parameter
from src.kvs_sagemaker_integration.hls import Writer

logger = Logger(__name__).get()

background_tasks = set()


#
async def main():
    stream = os.getenv("KVS_STREAM")

    logger.info(f"Kinesis Video Stream: {stream}")

    lambda_function_name = os.getenv("LAMBDA_FUNCTION_NAME")

    logger.info(f"Lambda Function Name: {lambda_function_name}")

    ssm_name = os.getenv("SSM_PARAMETER")

    logger.info(f"SSM Parameter Name: {ssm_name}")

    stream_id = int(time.time())

    logger.info(f'stream Id: {stream_id}')

    ssm_val = dict(sid=str(stream_id))

    async with SSMClient() as ssm_client:
        await put_parameter(ssm_client, ssm_name, ssm_val)

    logger.info(f'SSM Parameter {ssm_name}: {ssm_val}')

    tracker = Tracker()

    writer = Writer()

    frames = FrameContainer()

    tmpdir = tempfile.mkdtemp()
    try:
        async for fragment in Processor(lambda_function_name, stream):
            logger.info(f"fragment: {fragment}")

            for frame in fragment.frames:
                frames.insert(frame)

            if len(frames) > writer.fps * writer.hls_time:
                task = asyncio.create_task(coro(copy(frames), writer, tracker, tmpdir, stream_id))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

                frames = FrameContainer()

            await asyncio.sleep(0)

    except (KeyboardInterrupt, SystemExit):
        pass

    except Exception as err:
        message = f"{type(err).__name__}: {err}"
        logger.error(message, exc_info=True)

    finally:
        ssm_val = dict(sid=str("0"))

        async with SSMClient() as ssm_client:
            await put_parameter(ssm_client, ssm_name, ssm_val)

        logger.info(f'ssm parameter {ssm_name}: {ssm_val}')

        try:
            shutil.rmtree(tmpdir)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise


async def coro(frames, writer, tracker, tmpdir, stream_id):
    items = ""

    for frame in frames:
        frame.labels = json.loads(frame.labels)["Results"]

    if all(frame.labels for frame in frames):
        mot_response = [tracker.update(frame) for frame in frames]

        trackers = list(itertools.chain.from_iterable(mot_response))

        items = ", ".join(str(val) for val in {item["tracking"]: item["id"] for item in trackers}.values())

    logger.info(f"items: {items}")

    if items:
        table = os.getenv("DYNAMODB_TABLE")
        item = {
            "StreamId": {"N": str(stream_id)},
            "Time": {"N": str(int(time.time()))},
            "Category": {"S": items},
        }
        async with DynamoDBClient() as dynamodb_client:
            task = asyncio.create_task(put_item(dynamodb_client, table, item))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
            await task

    images = [img_labels(frame.img, frame.labels) for frame in frames]

    path = writer.write_video(images, out_dir=tmpdir)

    logger.info(f"Created HSL fragment: {path}")

    bucket = os.getenv("S3_BUCKET")

    async with S3Client() as s3_client:
        key = f"stream/{stream_id}/{path.name}"

        s3_tasks = list()

        task = asyncio.create_task(put_object(s3_client, bucket, key, str(path)))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        s3_tasks.append(task)

        logger.info(f"Manifest: \n{writer.manifest}")

        key = f"stream/{stream_id}/{stream_id}.m3u8"

        task = asyncio.create_task(put_object(s3_client, bucket, key, writer.manifest))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        s3_tasks.append(task)

        await asyncio.gather(*s3_tasks)


def img_labels(img: np.ndarray, labels: list) -> np.ndarray:
    for label in labels:
        img = img_label(img, label)
    return img


def img_label(img: np.ndarray, label: dict) -> np.ndarray:
    color = (0, 255, 0)
    text_color = (0, 0, 0)

    start_point = (label.get('left'), label.get('top'))
    end_point = (label.get('right'), label.get('bottom'))
    img = cv2.rectangle(img, start_point, end_point, color, 2)

    label_point = (label.get('left') + 10, label.get('top') - 10)
    label_text = f"{label.get('id')}"

    (w, h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    start_point = (label.get('left'), label.get('top') - h - 20)
    end_point = (label.get('left') + w + 30, label.get('top'))
    img = cv2.rectangle(img, start_point, end_point, color, -1)

    cv2.putText(img, label_text, label_point, cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
    return img


#
# def run(stream, endpoint):
def run():
    with asyncio.Runner() as runner:
        try:
            # runner.run(main(stream, endpoint))
            runner.run(main())
        except (KeyboardInterrupt, SystemExit):
            pass
        except Exception as err:
            message = f"{type(err).__name__}: {err}"
            logger.error(message, exc_info=True)

    return sys.exit(0)
