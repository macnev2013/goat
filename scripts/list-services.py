import os
import glob
import re

TEST_SERVICES = ["s3", "ec2", "route53", "route53resolver"]
REPO_PATH = "../terraform-provider-aws"
TEST_DIR_REGEX = f"{REPO_PATH}/internal/service/**/*_test.go"
GO_TEST_REGEX = "^func TestAcc(.*)$"
GO_PATTERN = re.compile(GO_TEST_REGEX)


services = []

if not os.path.exists(REPO_PATH):
    raise Exception(f"Path {REPO_PATH} does not exist.")
for path in glob.glob(TEST_DIR_REGEX):
    service_name = path.split("/")[-2]
    services.append(service_name)

print(list(set(services)))