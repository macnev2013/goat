import os
from pydoc import cli
from constants import TEST_ENV_PARAMS, SERVICES_TO_TEST, TEST_LIST_FILE
from models import TestSummary
from utils import check_health_status, run_report_server
import click


@click.group(name="autest", help="Automated tests for localstack")
def cli():
    pass


@click.command(name="scrape", help="Scrape metadata from test files")
def generate():
    """Scrape metadata from test files"""
    TEST_ENV_PARAMS.update(os.environ.copy())
    test_manager = TestSummary()
    test_manager.scrape_tests()
    test_manager.export_test_details()
    test_manager.save()


@click.command(name="report", help="Generate report from test details")
def report():
    """Generate report from test details"""
    TEST_ENV_PARAMS.update(os.environ.copy())
    test_manager = TestSummary()
    test_manager.generate_report()
    run_report_server()


@click.command(name="run", help="Run tests for given services")
@click.option("--services", "-s", default=SERVICES_TO_TEST, help="Services to test")
@click.option(
    "--force-run", "-f", is_flag=True, default=False, help="Run tests forcefully"
)
@click.option(
    "--test-list-file",
    "-t",
    default=TEST_LIST_FILE,
    help="File containing test list: ./test-list.yaml",
)
def run(services, force_run, test_list_file):
    """Run tests for given services"""
    print(f"Services to test: {services}")
    TEST_ENV_PARAMS.update(os.environ.copy())
    test_manager = TestSummary(test_list_file=test_list_file)
    if not check_health_status():
        print(
            "Localstack is not running. Please start localstack before running tests."
        )
        os._exit(1)
    print("Running tests...")
    services = [service for service in services.split(",") if len(service) > 0]
    for service in services:
        test_manager.execute_tests(service, force_run)
        test_manager.save()

@click.command(name="run-services", help="Run tests for all services")
@click.option("--services", "-s", default=SERVICES_TO_TEST, help="Services to test")
def run_services(services):
    """Run tests for all services"""
    print(f"Services to test: {services}")
    # TEST_ENV_PARAMS.update(os.environ.copy())
    # test_manager = TestSummary()
    # if not check_health_status():
    #     print(
    #         "Localstack is not running. Please start localstack before running tests."
    #     )
    #     os._exit(1)
    # print("Running tests...")
    # services = [service for service in services.split(",") if len(service) > 0]
    # for service in services:
    #     test_manager.execute_tests(service)
    #     test_manager.save()



@click.command(name="details", help="Get test details")
@click.option("--service-name", "-s", help="Service name for test")
@click.option("--test-file", "-t", help="Test file name")
@click.option("--test-name", "-n", help="Test name")
def get_details(service_name, test_file, test_name):
    """Get test details"""
    test_manager = TestSummary()
    test_manager.get_test_details(service_name, test_file, test_name)
    test_manager.save()


@click.command(name="list-services", help="Get list of service")
def list_services():
    """Get list of service"""
    test_manager = TestSummary()
    services = test_manager.get_services_list()
    test_manager.save()
    print(services)


cli.add_command(generate)
cli.add_command(report)
cli.add_command(run)
cli.add_command(get_details)
cli.add_command(list_services)
cli()
