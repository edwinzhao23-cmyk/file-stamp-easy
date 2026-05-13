from __future__ import annotations


APP_QSS = """
* {
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #111827;
}

QMainWindow {
    background: #F6F8FA;
}

QFrame#TopBar,
QFrame#LogPanel {
    background: #FFFFFF;
    border: 1px solid #DDE3EA;
}

QFrame#Card {
    background: #FFFFFF;
    border: 1px solid #DDE3EA;
    border-radius: 8px;
}

QLabel#AppTitle {
    font-size: 20px;
    font-weight: 700;
    color: #0F172A;
}

QLabel#CardTitle {
    font-size: 14px;
    font-weight: 700;
    color: #0F172A;
}

QLabel#MutedText {
    color: #6B7280;
}

QPushButton {
    min-height: 30px;
    padding: 0 12px;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    background: #FFFFFF;
}

QPushButton:hover {
    background: #F1F5F9;
    border-color: #94A3B8;
}

QPushButton:pressed {
    background: #E2E8F0;
}

QPushButton:disabled {
    color: #9CA3AF;
    background: #F3F4F6;
    border-color: #E5E7EB;
}

QPushButton#PrimaryButton {
    min-height: 36px;
    font-weight: 700;
    color: #FFFFFF;
    background: #D71920;
    border-color: #C5161D;
}

QPushButton#PrimaryButton:hover {
    background: #C5161D;
}

QPushButton#DangerButton {
    color: #B91C1C;
    background: #FEF2F2;
    border-color: #FECACA;
}

QLineEdit,
QComboBox,
QDoubleSpinBox,
QSpinBox {
    min-height: 30px;
    padding: 0 8px;
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
}

QLineEdit:focus,
QComboBox:focus,
QDoubleSpinBox:focus,
QSpinBox:focus {
    border-color: #0D9488;
}

QCheckBox,
QRadioButton {
    spacing: 6px;
}

QScrollArea {
    border: none;
    background: transparent;
}

QGroupBox {
    border: none;
    margin: 0;
}

QSplitter::handle {
    background: #E5E7EB;
}

QProgressBar {
    height: 8px;
    border: none;
    border-radius: 4px;
    background: #E5E7EB;
}

QProgressBar::chunk {
    border-radius: 4px;
    background: #0D9488;
}
"""

