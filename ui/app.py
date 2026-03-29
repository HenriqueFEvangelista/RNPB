import customtkinter as ctk

from ui.logs_view import LogsView
from ui.create_view import CreateView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def start_app():
    app = ctk.CTk()
    app.title("RNPB - React Native Project Builder")
    app.geometry("900x520")

    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(0, weight=1)

    sidebar = ctk.CTkFrame(app, width=200)
    sidebar.grid(row=0, column=0, sticky="ns")

    main_frame = ctk.CTkFrame(app)
    main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    logs_view = LogsView(main_frame)
    create_view = CreateView(main_frame, logs_view)

    for frame in (create_view, logs_view):
        frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(frame):
        frame.tkraise()

    btn_create = ctk.CTkButton(sidebar, text="Create Project", command=lambda: show_frame(create_view))
    btn_create.pack(pady=10, padx=20)

    btn_logs = ctk.CTkButton(sidebar, text="Logs", command=lambda: show_frame(logs_view))
    btn_logs.pack(pady=10, padx=20)

    show_frame(create_view)

    app.mainloop()