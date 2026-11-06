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
QLineEdit[invalid="true"] {
    border: 2px solid #ff7b86;
    background: #38252e;
}
QLabel#inlineError {
    color: #ff9ca3;
    font-size: 12px;
}
QLabel#validationBanner {
    color: #ffd0d4;
    background: #442730;
    border: 1px solid #a45060;
    border-radius: 7px;
    padding: 11px 13px;
    font-weight: 600;
}
QToolButton#wizardStepButton {
    background: #242e3d;
    color: #acb7c7;
    border: 1px solid #3a465a;
    border-radius: 9px;
    padding: 8px;
    font-weight: 500;
}
QToolButton#wizardStepButton:hover { background: #35465d; }
QToolButton#wizardStepButton[stepState="current"] {
    background: #29456d;
    border: 2px solid #79a8ff;
    color: #ffffff;
    font-weight: 700;
}
QToolButton#wizardStepButton[stepState="completed"] {
    background: #26463d;
    border: 1px solid #4a9f82;
    color: #ccf4de;
}
QProgressBar#wizardProgress {
    min-height: 5px;
    max-height: 5px;
    border: 0;
    background: #303b4b;
    border-radius: 2px;
}
QProgressBar#wizardProgress::chunk { background: #71a5ff; border-radius: 2px; }
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
