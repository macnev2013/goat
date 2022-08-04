from constants import GO_TEST_CMD, TEST_DIR, TEST_ARG_PARAMS, LOCALSTACK_ENDPOINT, HTTP_SERVER_HOST, HTTP_SERVER_PORT
import requests
import http.server

def get_str_from_dict(dict_obj):
    str_obj = ""
    for key in dict_obj:
        if dict_obj[key] == "":
            str_obj += f"{key} "
        else:
            str_obj += f"{key}={dict_obj[key]} "
    return str_obj.strip(" ")

def get_test_id(service_name, test_name):
    return f"{service_name}_{test_name}"

def get_test_run_command(service_name, test_name):
    command = f"{GO_TEST_CMD} {TEST_DIR}/{service_name}/ {get_str_from_dict(TEST_ARG_PARAMS)} -run {test_name}"
    return command.split(" ")

def check_health_status():
    try:
        response = requests.get(LOCALSTACK_ENDPOINT)
    except Exception:
        return False
    if response.status_code == 200:
        return True
    else:
        return False

def run_report_server():
    web_server = http.server.HTTPServer((HTTP_SERVER_HOST, HTTP_SERVER_PORT), http.server.SimpleHTTPRequestHandler)
    try:
        print(f"Starting webserver at: http://{HTTP_SERVER_HOST}:{HTTP_SERVER_PORT}")
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass
    web_server.server_close()
    print("Server stopped")
