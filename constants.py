import re
import os

PICKLE_TEST_DETAILS_FILE = "./localstack/testdetails.pickle"

GO_TEST_REGEX = "^func TestAcc(.*)$"
GO_PATTERN = re.compile(GO_TEST_REGEX)

ROOT_DIR = "localstack"
TEST_LIST_FILE = f"{ROOT_DIR}/test-list.yaml"
TEST_REPORT_FILENAME = f"{ROOT_DIR}/report.html"

TEST_DIR = "./internal/service"
TEST_REGEX = "internal/service/**/*_test.go"

TEST_ENV_PARAMS = {
    'AWS_DEFAULT_REGION': 'us-east-1',
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test',
    'TF_ACC': 'true',
}

TEST_ARG_PARAMS = {
    '-v': '',
    '-timeout': '60m',
    '-count': '1',
}
GO_TEST_CMD = "go test"

LOG_PATH = f"{ROOT_DIR}/logs"

LOCALSTACK_ENDPOINT = "http://localhost:4566"

SERVICES_TO_TEST = ["s3"]

HTTP_SERVER_HOST = "localhost"
HTTP_SERVER_PORT = 8000