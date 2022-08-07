import re
import os

ROOT_DIR = "."
PICKLE_TEST_DETAILS_FILE = f"{ROOT_DIR}/testdetails.pickle"
TEST_LIST_FILE = f"{ROOT_DIR}/test-list.yaml"
TEST_REPORT_FILENAME = f"{ROOT_DIR}/report.html"
LOG_PATH = f"{ROOT_DIR}/logs"

GO_TEST_REGEX = "^func TestAcc(.*)$"
GO_PATTERN = re.compile(GO_TEST_REGEX)

REPO_PATH="/home/runner/work/goat/goat/terraform-provider-aws"
TEST_DIR = "./internal/service"
TEST_DIR_REGEX = f"{REPO_PATH}/internal/service/**/*_test.go"

TEST_ENV_PARAMS = {
    'AWS_DEFAULT_REGION': 'us-east-1',
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test',
    'TF_ACC': 'true',
}

TEST_ARG_PARAMS = {
    '-v': '',
    '-timeout': '15m',
    '-count': '1',
}

GO_TEST_CMD = "go test"

LOCALSTACK_ENDPOINT = "http://localhost:4566"
SERVICES_TO_TEST = ["s3", "ec2", "route53", "route53resolver"]

HTTP_SERVER_HOST = "localhost"
HTTP_SERVER_PORT = 8000
