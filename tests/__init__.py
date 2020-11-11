import os
import sys
print("tests __init__.py")
os.environ['W1THERMSENSOR_NO_KERNEL_MODULE'] = '1'
# Add tests dir to PYTHONPATH to make the tests/RPi module mock available in tests
sys.path.insert(0, os.path.join(os.getcwd(), "tests"))
print("sys.path=" + str(sys.path))