from email.policy import default
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
@click.option(
    "--server",
    "-s",
    is_flag=True,
    default=False,
    help="Start a local server to view the report",
)
def report(server):
    """Generate report from test details"""
    TEST_ENV_PARAMS.update(os.environ.copy())
    test_manager = TestSummary()
    test_manager.generate_report()
    if server:
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
@click.option(
    "--pattern",
    "-p",
    help="Pattern to match test names against",
)
def run(services, force_run, test_list_file, pattern):
    """Run tests for given services"""
    print(f"Services to test: {services}")
    TEST_ENV_PARAMS.update(os.environ.copy())
    if not check_health_status():
        print(
            "Localstack is not running. Please start localstack before running tests."
        )
        os._exit(1)
    test_manager = TestSummary(test_list_file=test_list_file)
    print("Running tests...")
    services = [service for service in services.split(",") if len(service) > 0]
    for service in services:
        test_manager.execute_tests(
            service=service, pattern=pattern, force_run=force_run
        )


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
@click.option("--all", "-a", is_flag=True, default=False, help="Returns all services")
def list_services(all):
    """Get list of service"""
    test_manager = TestSummary()
    services = test_manager.get_services_list(all)
    test_manager.save()
    print(services)


@click.command(name="print-summary", help="Gets the summary of the tests")
@click.option("--service-name", "-s", help="Service name for test")
def print_summary(service_name):
    """Gets the summary of the tests"""
    test_manager = TestSummary()
    test_manager.print_summary(service_name)


@click.command(name="get-yaml", help="Gets the yaml of the tests")
@click.option("--output-file", "-o", help="Name of output file")
def get_yaml(output_file):
    """Gets the yaml of the tests"""
    test_manager = TestSummary()
    test_manager.get_yaml(output_file)


@click.command(name="list", help="List down the test cases")
@click.option("--pattern", "-p", help="patterns in the test you want to search for")
def list_tests(pattern):
    """List down the test cases"""
    test_manager = TestSummary()
    test_manager.list_tests(pattern)

@click.command(name="local", help="runs tests for local execution")
@click.option("--pattern", "-p", help="patterns in the test you want to run")
def local(pattern):
    """runs tests for local execution"""
    test_manager = TestSummary()
    test_manager.local(pattern)


cli.add_command(generate)
cli.add_command(report)
cli.add_command(run)
cli.add_command(get_details)
cli.add_command(list_services)
cli.add_command(print_summary)
cli.add_command(get_yaml)
cli.add_command(list_tests)
cli.add_command(local)
cli()
