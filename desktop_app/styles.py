"""
Global QSS stylesheet for the OpenComputer Desktop application.
Premium flat design with gradient sidebar, glassmorphism cards, refined palette.
"""

MAIN_STYLE = """
/* ── Global ──────────────────────────────────────────────────────── */
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", "Noto Sans CJK SC", "PingFang SC",
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #f0f2f8;
}

/* ── Sidebar ─────────────────────────────────────────────────────── */
#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #0f2439, stop:0.4 #0f3460, stop:1 #0a1628);
    min-width: 200px;
    max-width: 200px;
}

#sidebar QPushButton, QPushButton#navBtn {
    background-color: transparent;
    color: rgba(178, 200, 220, 200);
    border: none;
    text-align: left;
    padding: 12px 18px;
    font-size: 13px;
    border-left: 3px solid transparent;
    border-radius: 0;
    margin: 1px 0;
    letter-spacing: 0.3px;
}

#sidebar QPushButton:hover, QPushButton#navBtn:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #e8ecf2;
    border-left: 3px solid rgba(0, 210, 170, 0.4);
}

#sidebar QPushButton:checked, QPushButton#navBtn:checked,
#sidebar QPushButton[active="true"] {
    background-color: rgba(0, 210, 170, 0.12);
    color: #ffffff;
    border-left: 3px solid #00d2aa;
    font-weight: bold;
}

#sidebarTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: bold;
    padding: 20px 20px 10px 20px;
}

#sidebarSubtitle {
    color: rgba(180, 200, 220, 0.6);
    font-size: 11px;
    padding: 0px 20px 20px 20px;
}

/* ── Content area ────────────────────────────────────────────────── */
#contentArea {
    background-color: #f0f2f8;
}

/* ── Page title ──────────────────────────────────────────────────── */
#pageTitle {
    font-size: 24px;
    font-weight: bold;
    color: #1a2332;
    padding: 12px 0px 4px 0px;
    letter-spacing: -0.3px;
}

#pageSubtitle {
    font-size: 13px;
    color: #6b7b8d;
    padding-bottom: 14px;
    line-height: 1.4;
}

/* ── Cards ───────────────────────────────────────────────────────── */
#card {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 12px;
    padding: 22px;
}

#cardTitle {
    font-size: 16px;
    font-weight: bold;
    color: #1a2332;
    padding-bottom: 8px;
}

/* ── Form elements ───────────────────────────────────────────────── */
QLabel {
    color: #2d3a4a;
}

QLineEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1.5px solid #e0e4ec;
    border-radius: 8px;
    padding: 9px 14px;
    color: #2d3a4a;
    min-height: 22px;
    selection-background-color: #00d2aa;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1.5px solid #00b894;
    background-color: #fafbff;
}

QLineEdit:hover, QSpinBox:hover, QComboBox:hover {
    border: 1.5px solid #c0c8d8;
}

QLineEdit::placeholder {
    color: #a8b2c0;
}

QLineEdit[echoMode="2"] {
    lineedit-password-character: 9679;
}

QComboBox::drop-down {
    border: none;
    width: 32px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8090a0;
    margin-right: 12px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e0e4ec;
    border-radius: 6px;
    selection-background-color: #00d2aa;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    border-radius: 4px;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #0984e3, stop:1 #0770c9);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 26px;
    font-size: 14px;
    font-weight: bold;
    min-height: 22px;
    letter-spacing: 0.2px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #0a90f0, stop:1 #0880de);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #065fa3, stop:1 #0660a5);
}

QPushButton:disabled {
    background: #c8d0dc;
    color: #f0f2f6;
}

QPushButton#btnDanger {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e74c3c, stop:1 #c0392b);
}

QPushButton#btnDanger:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f05545, stop:1 #d04030);
}

QPushButton#btnSuccess {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #00d2aa, stop:1 #00b894);
}

QPushButton#btnSuccess:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #00e0b8, stop:1 #00c8a4);
}

QPushButton#btnSecondary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5a6c7e, stop:1 #4a5c6e);
}

QPushButton#btnSecondary:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #6a7c8e, stop:1 #5a6c7e);
}

QPushButton#btnOutline {
    background: transparent;
    color: #0984e3;
    border: 1.5px solid #0984e3;
}

QPushButton#btnOutline:hover {
    background: rgba(9, 132, 227, 0.08);
}

/* ── Tables ──────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 10px;
    gridline-color: #f0f2f6;
    selection-background-color: rgba(0, 210, 170, 0.15);
    selection-color: #1a2332;
    alternate-background-color: #fafbfd;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #f4f5f8;
}

QTableWidget::item:selected {
    background-color: rgba(0, 210, 170, 0.12);
    color: #1a2332;
}

QHeaderView::section {
    background-color: #f8f9fc;
    color: #4a5568;
    border: none;
    border-bottom: 2px solid #e0e4ec;
    padding: 10px 12px;
    font-weight: 600;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Text browser / log area ─────────────────────────────────────── */
QTextBrowser {
    background-color: #ffffff;
    color: #2d3a4a;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 10px;
    padding: 14px;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
    line-height: 1.5;
}

QPlainTextEdit {
    background-color: #1a2332;
    color: #c8d6e5;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 10px;
    padding: 14px;
    font-family: "Cascadia Code", "Consolas", "Source Code Pro",
                 "DejaVu Sans Mono", monospace;
    font-size: 13px;
    selection-background-color: #00d2aa;
    selection-color: #ffffff;
}

/* ── Progress bar ────────────────────────────────────────────────── */
QProgressBar {
    background-color: #e8ecf2;
    border: none;
    border-radius: 8px;
    height: 22px;
    text-align: center;
    color: #2d3a4a;
    font-weight: bold;
    font-size: 12px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d2aa, stop:1 #00b894);
    border-radius: 8px;
}

/* ── Scroll bars ─────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}

QScrollBar::handle:vertical {
    background: rgba(120, 140, 160, 0.35);
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(120, 140, 160, 0.55);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 2px 4px;
}

QScrollBar::handle:horizontal {
    background: rgba(120, 140, 160, 0.35);
    border-radius: 4px;
    min-width: 40px;
}

QScrollBar::handle:horizontal:hover {
    background: rgba(120, 140, 160, 0.55);
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Tab widget ──────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 10px;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background-color: #f0f2f8;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 22px;
    margin-right: 3px;
    color: #6b7b8d;
    font-size: 13px;
}

QTabBar::tab:hover {
    background-color: #e8ecf4;
    color: #2d3a4a;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #00b894;
    font-weight: bold;
    border-bottom: 2px solid #ffffff;
}

/* ── Status labels ───────────────────────────────────────────────── */
#statusOk {
    color: #00b894;
    font-weight: bold;
    font-size: 13px;
}

#statusError {
    color: #e74c3c;
    font-weight: bold;
    font-size: 13px;
}

#statusWarn {
    color: #f39c12;
    font-weight: bold;
    font-size: 13px;
}

/* ── Group Box ───────────────────────────────────────────────────── */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 12px;
    margin-top: 18px;
    padding: 18px;
    padding-top: 32px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 18px;
    padding: 0 10px;
    color: #00b894;
    font-size: 13px;
    letter-spacing: 0.3px;
}

/* ── Checkbox ────────────────────────────────────────────────────── */
QCheckBox {
    spacing: 10px;
    color: #2d3a4a;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #d0d8e4;
    border-radius: 5px;
    background: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #00b894;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #00d2aa, stop:1 #00b894);
    border-color: #00b894;
}

/* ── Splitter ────────────────────────────────────────────────────── */
QSplitter::handle {
    background: #e0e4ec;
    border-radius: 2px;
}

QSplitter::handle:horizontal {
    width: 3px;
    margin: 8px 1px;
}

QSplitter::handle:vertical {
    height: 3px;
    margin: 1px 8px;
}

QSplitter::handle:hover {
    background: #00d2aa;
}

/* ── List Widget ─────────────────────────────────────────────────── */
QListWidget {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 10px;
    padding: 6px;
    outline: none;
}

QListWidget::item {
    padding: 10px 14px;
    border-radius: 6px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background: rgba(0, 210, 170, 0.12);
    color: #1a2332;
    font-weight: 500;
}

QListWidget::item:hover {
    background-color: #f4f6fa;
}

/* ── Tooltip ─────────────────────────────────────────────────────── */
QToolTip {
    background-color: #1a2332;
    color: #e8ecf2;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}

/* ── Scroll Area ─────────────────────────────────────────────────── */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* ── Menu ─────────────────────────────────────────────────────────── */
QMenu {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 30px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: rgba(0, 210, 170, 0.12);
    color: #1a2332;
}
"""
