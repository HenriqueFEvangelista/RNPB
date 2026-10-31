"""Tema simples QSS para a interface desktop do RNPB."""

APP_STYLE = """
QWidget {
    background: #171b23;
    color: #eaf0fa;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QLabel#pageTitle {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
}
QLabel#muted { color: #aab5c6; }
QFrame#sidebar {
    background: #222937;
    border-right: 1px solid #394456;
}
QLineEdit, QComboBox, QPlainTextEdit {
    background: #232b39;
    border: 1px solid #455166;
    border-radius: 7px;
    padding: 9px;
    selection-background-color: #477be1;
}
QLineEdit:focus, QPlainTextEdit:focus { border-color: #76a3ff; }
QPushButton {
    background: #303d50;
    border: 1px solid #46566e;
    border-radius: 7px;
    padding: 10px 16px;
}
QPushButton:hover { background: #40526a; }
QPushButton:disabled, QComboBox:disabled { color: #8893a4; }
QPushButton#primaryButton { background: #3a70d6; border-color: #578af2; }
QPushButton#primaryButton:hover { background: #4b81e2; }
QProgressBar {
    border: 1px solid #455166;
    background: #232b39;
    border-radius: 6px;
    min-height: 16px;
    text-align: center;
}
QProgressBar::chunk { background: #578af2; border-radius: 5px; }
"""
