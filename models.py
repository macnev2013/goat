import glob
import multiprocessing
import pickle
import re
import os
import signal
import sys
import time
import subprocess
from colorama import Fore
from constants import (
    REPO_PATH,
    SERVICES_TO_TEST,
    TEST_DIR_REGEX,
    PICKLE_TEST_DETAILS_FILE,
    GO_PATTERN,
    TEST_LIST_FILE,
    LOG_PATH,
    TEST_ENV_PARAMS,
    TEST_REPORT_FILENAME,
    PROCESS_POOL,
)
from utils import get_test_run_command
from utils import get_test_id
import multiprocessing.dummy


class TestDetail:
    def __init__(self, service_name, test_name):
        self.service_name = service_name
        self.test_name = test_name
        self.return_code = None
        self.start_time: time
        self.end_time: time
        self.process_start_time: time
        self.process_end_time: time
        self.completed = False

    @property
    def elapsed_time(self):
        diff = self.end_time - self.start_time
        return time.strftime("%Mm %Ss", time.gmtime(diff))

    @property
    def process_elapsed_time(self):
        diff = self.process_end_time - self.process_start_time
        return time.strftime("%M.%S", time.gmtime(diff))

    @property
    def logfile_path(self):
        return f"{LOG_PATH}/{self.service_name}"

    def create_dir(self):
        os.makedirs(self.logfile_path, exist_ok=True)

    def pre_tests(self):
        self.start_time = time.time()
        self.process_start_time = time.process_time()
        self.create_dir()

    def post_tests(self):
        self.process_end_time = time.process_time()
        self.end_time = time.time()
        self.completed = True

    def run(self):
        command = get_test_run_command(self.service_name, self.test_name)
        stdout = open(f"{self.logfile_path}/{self.test_name}_stdout.log", "w")
        stderr = open(f"{self.logfile_path}/{self.test_name}_stderr.log", "w")
        TEST_ENV_PARAMS.update(os.environ.copy())
        process = subprocess.Popen(
            command,
            env=TEST_ENV_PARAMS,
            stdout=stdout,
            stderr=stderr,
            cwd=REPO_PATH,
        )
        test_id = get_test_id(self.service_name, self.test_name)
        PROCESS_POOL[test_id] = process
        process.wait()
        stdout.close()
        stderr.close()
        self.return_code = process.returncode

    def pre_print(self):
        print(f"{Fore.BLUE}[RUNNING] :: {self.test_name}")

    def post_print(self):
        if self.return_code != 0:
            print(
                f"{Fore.RED}[FAILED]  :: {self.test_name} - Execution Time: {self.elapsed_time} seconds - CPU Time: {self.process_elapsed_time} seconds"
            )
        else:
            print(
                f"{Fore.GREEN}[PASSED]  :: {self.test_name} - Execution Time: {self.elapsed_time} seconds - CPU Time: {self.process_elapsed_time} seconds"
            )

    def execute(self):
        try:
            self.pre_print()
            self.pre_tests()
            self.run()
            self.post_tests()
            self.post_print()
        except KeyboardInterrupt:
            pass


class TestSummary:
    test_details = {}
    export_dict = {}
    summary = {}
    report = {}

    def __init__(self, test_list_file=None):
        self.pickle_file = PICKLE_TEST_DETAILS_FILE
        if test_list_file:
            self.test_list_file = test_list_file
        else:
            self.test_list_file = TEST_LIST_FILE
        self.load()
        self.pool = multiprocessing.dummy.Pool(processes=1)

        signal.signal(signal.SIGINT, self.termination_handler)
        signal.signal(signal.SIGTERM, self.termination_handler)

    def termination_handler(self, signal, frame):
        print(f"Exiting gracefully with signal {signal}")
        self.pool.close()
        self.pool.terminate()
        for test_id in PROCESS_POOL:
            if PROCESS_POOL[test_id]:
                print(f"{Fore.RED}[ABORTED]  :: {test_id}")
                PROCESS_POOL[test_id].kill()
        print("All processes are killed...")
        sys.exit(0)

    def save(self):
        with open(self.pickle_file, "wb") as file:
            pickle.dump(self.test_details, file)

    def load(self):
        if os.path.exists(self.pickle_file):
            with open(self.pickle_file, "rb") as file:
                self.test_details = pickle.load(file)
        else:
            self.scrape_tests()
            self.save()

    def scrape_tests(self):
        if not os.path.exists(REPO_PATH):
            raise Exception(f"Path {REPO_PATH} does not exist.")
        for path in glob.glob(TEST_DIR_REGEX):
            service_name = path.split("/")[-2]
            for i, line in enumerate(open(path)):
                for match in re.finditer(GO_PATTERN, line):
                    test_name = match[1].split("(")[0]
                    test_id = get_test_id(service_name, test_name)
                    if not self.test_details.get(test_id):
                        self.test_details[test_id] = TestDetail(service_name, test_name)

    def export_test_details(self):
        self.generate_internal_dict()
        file = open(self.test_list_file, "w")
        for service_name in self.export_dict:
            file.write(f"{service_name}:\n")
            for test_name in self.export_dict[service_name]:
                file.write(f"  - {test_name}\n")
        file.close()
        print("Test Details Exported.")

    def generate_internal_dict(self, force=False):
        if len(self.export_dict) == 0 or force:
            for test in self.test_details.values():
                if not self.export_dict.get(test.service_name):
                    self.export_dict[test.service_name] = []
                self.export_dict[test.service_name].append(test.test_name)

    def execute_tests(self, service, pattern=None, force_run=False):
        self.generate_internal_dict()
        print("Creating execution pool...")
        pool_args = []
        for test_name in self.export_dict[service]:
            test_id = get_test_id(service, test_name)
            test_detail = self.test_details.get(test_id)
            if self.test_details[test_id].completed and not force_run:
                print(f"[SKIP]    :: {test_detail.test_name}")
                continue
            if service and service == test_detail.service_name and pattern:
                if re.search(pattern, test_name):
                    pool_args.append(test_detail)
                    continue
            pool_args.append(test_detail)
            break
        try:
            print(f"Added {len(pool_args)} tests in the pool")
            self.pool.map(TestDetail.execute, pool_args)
            print("Pool Exited.")
        except Exception as e:
            print("Exception - Pool Exited due to : ", e)
            self.pool.close()
            self.pool.terminate()
            self.save()
            sys.exit(1)
        finally:
            self.pool.close()
            self.pool.terminate()
            self.save()
            sys.exit(0)

    def generate_summary_dict(self):
        for test_id in self.test_details:
            test_detail = self.test_details.get(test_id)
            if not self.summary.get(test_detail.service_name):
                self.summary[test_detail.service_name] = {
                    "passed": 0,
                    "failed": 0,
                    "total": 0,
                    "completed": 0,
                }
            self.summary[test_detail.service_name]["total"] += 1
            if not test_detail.completed:
                continue
            self.summary[test_detail.service_name]["completed"] += 1
            if test_detail.return_code == 0:
                self.summary[test_detail.service_name]["passed"] += 1
            else:
                self.summary[test_detail.service_name]["failed"] += 1

    def generate_report_dict(self):
        for test_id in self.test_details:
            test_detail = self.test_details.get(test_id)

            if not test_detail.completed:
                continue

            if not self.report.get(test_detail.service_name):
                self.report[test_detail.service_name] = {}

            if not self.report[test_detail.service_name].get(test_detail.test_name):
                self.report[test_detail.service_name][test_detail.test_name] = {}

            if test_detail.completed:
                self.report[test_detail.service_name][test_detail.test_name][
                    "return_code"
                ] = test_detail.return_code
                self.report[test_detail.service_name][test_detail.test_name][
                    "elapsed_time"
                ] = test_detail.elapsed_time
                self.report[test_detail.service_name][test_detail.test_name][
                    "process_elapsed_time"
                ] = test_detail.process_elapsed_time

    def generate_report(self):
        self.generate_report_dict()
        self.generate_summary_dict()

        report = open(TEST_REPORT_FILENAME, "w")
        report.write(
            f"""<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.1.3/dist/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">\n"""
        )
        report.write(f"<body class='p-4'>")
        for service_name in self.report:
            report.write(f"<h3>{service_name}</h3>\n")

            # report summary
            report.write(f"<table border='1' class='table'>\n")
            report.write(
                f"<tr><th>Total:</th><td>{self.summary[service_name]['total']}</td></tr>\n"
            )
            report.write(
                f"<tr><th>Passed:</th><td>{self.summary[service_name]['passed']}</td></tr>\n"
            )
            report.write(
                f"<tr><th>Failed:</th><td>{self.summary[service_name]['failed']}</td></tr>\n"
            )
            report.write(
                f"<tr><th>Completed:</th><td>{self.summary[service_name]['completed']}</td></tr>\n"
            )
            report.write(f"</table>\n")

            # report tests
            report.write(f"<table border='1' class='table'>\n")
            report.write(
                f"<tr><th>Test Name</th><th>Status</th><th>Duration</th><th>out</th><th>err</th></tr>\n"
            )
            for test_name in self.report[service_name]:
                test_id = get_test_id(service_name, test_name)
                test_detail = self.test_details.get(test_id)

                status = "PASSED" if test_detail.return_code == 0 else "FAILED"
                color = "red" if status == "FAILED" else "green"
                elapsed_time = test_detail.elapsed_time

                out_log = f"<a href='/{test_detail.logfile_path}/{test_detail.test_name}_stdout.log'>stdout</a>"
                err_log = f"<a href='/{test_detail.logfile_path}/{test_detail.test_name}_stderr.log'>stderr</a>"
                report.write(
                    f"<tr style='color: {color}'><td>{test_name}</td><td>{status}</td><td>{elapsed_time}</td><td>{out_log}</td><td>{err_log}</td></tr>\n"
                )

        report.write("</table></body>\n")
        report.close()
        print("Test Reports Exported.")

    def get_test_details(self, service_name, test_filename, test_name):
        test_id = get_test_id(service_name, test_filename, test_name)
        print(self.test_details.get(test_id).__dict__)

    def print_summary(self, service_name):
        self.generate_summary_dict()
        for service in self.summary:
            if service_name and service_name != service:
                continue
            print(f"-----{service}-----")
            print(f"Total: {self.summary[service]['total']}")
            print(f"Completed: {self.summary[service]['completed']}")
            print(f"Passed: {self.summary[service]['passed']}")
            print(f"Failed: {self.summary[service]['failed']}")

    def get_services_list(self, all):
        self.generate_internal_dict()
        services = []
        if all:
            services = list(self.export_dict.keys())
        else:
            services = [
                service
                for service in self.export_dict.keys()
                if service in SERVICES_TO_TEST
            ]
        return services

    def get_yaml(self, output_file):
        self.generate_report_dict()
        file = open(output_file, "w")
        for services in self.report:
            file.write(f"{services}:\n")
            for test_name in self.report[services]:
                if self.report[services][test_name]["return_code"] == 0:
                    file.write(f"    - TestAcc{test_name}\n")
        file.close()
