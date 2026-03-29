import subprocess
import shutil


def criar_projeto(nome, tipo, pasta, log_callback):
    npx = shutil.which("npx") or shutil.which("npx.cmd")

    if not npx:
        log_callback("Erro: npx não encontrado.")
        return

    if tipo == "Expo":
        comando = [
            npx,
            "create-expo-app@latest",
            nome,
            "--template",
            "blank",
            "--yes"
        ]
    else:
        comando = ["npx", "react-native", "init", nome]

    log_callback("Executando comando:")
    log_callback(" ".join(comando))

    process = subprocess.Popen(
        comando,
        cwd=pasta,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        text=True,
        shell=True
    )

    # aceita automaticamente a instalação
    process.stdin.write("y\n")
    process.stdin.flush()

    for linha in process.stdout:
        log_callback(linha.strip())

    process.wait()