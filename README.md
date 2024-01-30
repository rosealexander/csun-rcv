# CSUN-RCV Integration Module

The CSUN-RCV Integration Module serves as the backbone for integrating various services within the system using AWS services such as Kinesis Video Stream (KVS), DynamoDB, S3, and AWS Lambda.

## Functionality

- **Kinesis Video Stream Integration**: Retrieves video from Kinesis Video Stream for processing.
- **Frame Processing with Lambda**: Each frame of the video is processed using AWS Lambda functions.
- **HLS Fragmentation**: Processed frames are reconstructed and saved to S3 as HLS fragments.
- **Stream ID Management**: The current stream ID is stored in a system parameter.
- **Object Detection Algorithm**: Utilizes AWS Lambda to process live video through an object detection algorithm.
- **Multiple Object Tracking**: Employs the SORT (Simple Online and Realtime Tracking) algorithm for multiple object tracking.
- **Data Persistence**: Information about newly detected objects is saved to DynamoDB.

## Usage

To run the CSUN-RCV Integration Module, set the following environment variables:

- DYNAMODB_TABLE: Name of the DynamoDB table where data will be stored.
- KVS_STREAM: Name of the Kinesis Video Stream providing live video data.
- LAMBDA_FUNCTION_NAME: Name of the AWS Lambda function responsible for frame processing.
- LOG_LEVEL: Level of logging verbosity (e.g., INFO, DEBUG).
- S3_BUCKET: Name of the S3 bucket where processed frames will be stored.
- SSM_PARAMETER: Path to the AWS Systems Manager parameter containing system metadata.

Execute the following command:

```bash
python csun-rcv/src/csun_rcv
```

## Integration with UI

This module serves as a backend for the [CSUN-RCV UI demo repository](https://github.com/rosealexander/csun-rcv-ui-demo).

## License

This project is licensed under the MIT License. See the LICENSE file for details.
