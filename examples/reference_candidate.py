"""Protocol demonstration only: shares the oracle and is NOT an independent baseline."""
import json
import sys
from antegraph_bench.runner import oracle
print(json.dumps(oracle(json.load(sys.stdin))))
