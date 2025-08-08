import subprocess

def run_tests():
    result = subprocess.run(["pytest", "--maxfail=1"], capture_output=True, text=True)
    return result.stdout or result.stderr
