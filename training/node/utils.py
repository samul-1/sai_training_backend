import json
import os
import subprocess


def run_code_in_vm(code, testcases_json):
    """
    Takes in a string containing JS code and a list of testcases; runs the code in a JS
    virtual machine and returns the outputs given by the code in JSON format
    """

    node_vm_path = os.environ.get("NODE_VM_PATH", "training/node/vm.js")

    # call node subprocess and run user code against test cases
    res = subprocess.check_output(
        [
            "node",
            node_vm_path,
            code,
            json.dumps(testcases_json),
        ]
    )

    return json.loads(res)
