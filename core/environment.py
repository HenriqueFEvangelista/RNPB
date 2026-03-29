import subprocess
import shutil

def verificar_node():
    try:
        subprocess.run(["node", "-v"], capture_output=True, check=True)
        return True
    except:
        return False


def verificar_npm():
    try:
        subprocess.run(["npm", "-v"], capture_output=True, check=True)
        return True
    except:
        return False


def verificar_npx():
    try:
        subprocess.run(["npx", "-v"], capture_output=True, check=True)
        return True
    except:
        return False


def verificar_ambiente():
    if shutil.which("node") is None:
        return False, "Node.js não encontrado."

    if shutil.which("npm") is None:
        return False, "npm não encontrado."

    return True, "Ambiente OK"