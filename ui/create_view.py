import customtkinter as ctk
from tkinter import filedialog
import threading

from core.environment import verificar_ambiente
from core.project_creator import criar_projeto


class CreateView(ctk.CTkFrame):
    def __init__(self, parent, logs_view):
        super().__init__(parent)

        self.logs_view = logs_view

        titulo = ctk.CTkLabel(
            self,
            text="Create React Native Project",
            font=("Arial", 20, "bold")
        )
        titulo.pack(pady=20)

        self.entry_nome = ctk.CTkEntry(self, width=350, placeholder_text="Nome do projeto")
        self.entry_nome.pack(pady=10)

        self.opcao_tipo = ctk.CTkOptionMenu(
            self, values= ["Expo", "React Native CLI"]
        )
        self.opcao_tipo.set("Expo")

        self.pasta_label = ctk.CTkLabel(self, text="Nenhuma pasta selecionada")
        self.pasta_label.pack(pady=5)

        btn_pasta = ctk.CTkButton(self, text="Escolher pasta", command=self.escolher_pasta)
        btn_pasta.pack(pady=10)

        self.btn_criar = ctk.CTkButton(
            self,
            text="Criar Projeto",
            width=220,
            height=40,
            command=self.iniciar_criacao
        )
        self.btn_criar.pack(pady=30)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(pady=10)
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(self, text="Aguardando...")
        self.status_label.pack(pady=5)

    def escolher_pasta(self):
        pasta = filedialog.askdirectory()
        self.pasta_label.configure(text=pasta)

    
    def iniciar_criacao(self):
        nome = self.entry_nome.get()
        tipo = self.opcao_tipo.get()
        pasta = self.pasta_label.cget("text")

        if not nome or pasta == "Nenhuma pasta selecionada":
            self.logs_view.add_log("Erro: configure o projeto primeiro.")
            return

        ok, mensagem = verificar_ambiente()

        self.logs_view.add_log(mensagem)

        if not ok:
            self.logs_view.add_log("Erro de ambiente.")
            return

        self.atualizar_progresso(0.1, "Verificando ambiente...")
        self.atualizar_progresso(0.25, "Ambiente OK")
        self.logs_view.add_log("Iniciando criação do projeto...")

        threading.Thread(
            target=self.executar_processo,
            args=(nome, tipo, pasta),
            daemon=True
        ).start()

    def executar_processo(self, nome, tipo, pasta):
        self.atualizar_progresso(0.4, "Criando projeto...")

        criar_projeto(nome, tipo, pasta, self.logs_view.add_log)

        self.atualizar_progresso(0.9, "Finalizando...")

        self.progress.set(1)
        self.status_label.configure(text="Projeto criado com sucesso!")
        self.logs_view.add_log("Finalizado.")

        self.progress.stop()
        self.status_label.configure(text="Projeto criado com sucesso!")
        self.logs_view.add_log("Finalizado.")

    def atualizar_progresso(self, valor, texto):
        self.progress.set(valor)
        self.status_label.configure(text=texto)
