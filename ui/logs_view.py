import customtkinter as ctk

class LogsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        titulo = ctk.CTkLabel(
            self,
            text="Logs do Sistema",
            font=("Arial", 20, "bold")
        )
        titulo.pack(pady=20)

        self.log_box = ctk.CTkTextbox(self, width=600, height=300)
        self.log_box.pack(pady=10)

        self.log_box.insert("end", "RNPB iniciado...\n")

    def add_log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")