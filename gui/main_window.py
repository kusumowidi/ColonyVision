"""Main dashboard window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QScrollArea, QVBoxLayout, QWidget

from gui.dashboard_page import DashboardPage
from gui.header import Header
from gui.sidebar import Sidebar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ColonyVision AI")
        self.resize(1440, 900)
        self._ui_zoom = 1.0
        self._build_layout()
        self._apply_zoom()

    def _build_layout(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.header = Header()
        content_layout.addWidget(self.header)
        scroll = QScrollArea()
        scroll.setObjectName("DashboardScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dashboard = DashboardPage()
        scroll.setWidget(self.dashboard)
        content_layout.addWidget(scroll, 1)
        root.addWidget(content, 1)
        self.setCentralWidget(central)

    def wheelEvent(self, event: QWheelEvent):  # noqa: N802 - Qt override
        if not (event.modifiers() & Qt.ControlModifier):
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        if delta == 0:
            event.accept()
            return
        factor = 1.08 if delta > 0 else 1.0 / 1.08
        self._ui_zoom = max(0.82, min(1.35, self._ui_zoom * factor))
        self._apply_zoom()
        event.accept()

    def _apply_zoom(self) -> None:
        self.setStyleSheet(_dashboard_stylesheet(self._ui_zoom))
        if hasattr(self, "sidebar"):
            self.sidebar.apply_zoom(self._ui_zoom)
        if hasattr(self, "header"):
            self.header.apply_zoom(self._ui_zoom)
        if hasattr(self, "dashboard"):
            self.dashboard.apply_zoom(self._ui_zoom)


def _dashboard_stylesheet(zoom: float = 1.0) -> str:
    def px(value: float) -> int:
        return max(1, int(round(value * zoom)))

    base_font = px(13)
    brand_font = px(20)
    small_font = px(12)
    card_radius = px(8)
    meta_radius = px(10)
    pill_radius = px(14)
    header_font = px(25)
    section_font = px(16)
    metric_font = px(30)
    button_radius = px(8)
    field_radius = px(8)
    stylesheet = """
    QMainWindow, QWidget {
        background-color: #F6FAFB; color: #12304A; font-family: Segoe UI, Arial, sans-serif;
        font-size: __BASE_FONT__px;
    }
    QLabel { background-color: transparent; }
    QScrollArea#DashboardScroll { background-color: #F6FAFB; border: none; }
    QFrame#Sidebar {
        background-color: #05263B; border: none; border-right: 1px solid #0B3A5A;
    }
    QLabel#SidebarBrand { color: white; font-size: __BRAND_FONT__px; font-weight: 800; letter-spacing: 0px; }
    QLabel#SidebarSubtitle { color: #9EDADF; font-size: __SMALL_FONT__px; font-weight: 600; }
    QLabel#SidebarFooter {
        color: #B6D3E3; background-color: #08324F; border: 1px solid #104867;
        border-radius: __CARD_RADIUS__px; padding: __PAD12__px; line-height: 145%;
    }
    QPushButton#SidebarButton {
        color: #DCEAF3; text-align: left; padding: __PAD12__px __PAD14__px; border: none; border-radius: __BUTTON_RADIUS__px;
        background-color: transparent; font-weight: 650;
    }
    QPushButton#SidebarButton:hover { background-color: #0B3A5A; color: white; }
    QPushButton#SidebarButton[active="true"] { background-color: #00A6A6; color: white; }
    QFrame#Header { background-color: #F6FAFB; border: none; }
    QLabel#HeaderTitle { font-size: __HEADER_FONT__px; font-weight: 800; color: #092E49; }
    QLabel#HeaderSubtitle, QLabel#ProfileLabel, QLabel#MutedLabel { color: #6B8793; }
    QFrame#Card {
        background-color: #FFFFFF; border: 1px solid #E1ECEF; border-radius: __CARD_RADIUS__px;
    }
    QFrame#MetaCard {
        background-color: #FFFFFF; border: 1px solid #DDECEF; border-radius: __META_RADIUS__px;
    }
    QFrame#WorkflowCard {
        background-color: #FFFFFF; border: 1px solid #DDECEF; border-radius: __META_RADIUS__px;
    }
    QLabel#StepPill {
        color: #6B8793; background-color: #F2F8F9; border: 1px solid #DDECEF;
        border-radius: __PILL_RADIUS__px; padding: __PAD7__px __PAD12__px; font-weight: 700;
    }
    QLabel#StepPill[active="true"] {
        color: white; background-color: #00A6A6; border-color: #00A6A6;
    }
    QLabel#FieldLabel { color: #496B7A; font-size: __SMALL_FONT__px; font-weight: 700; }
    QLabel#SectionTitle { font-size: __SECTION_FONT__px; font-weight: 800; color: #092E49; }
    QLabel#MetricTitle { color: #6B8793; font-weight: 700; font-size: __SMALL_FONT__px; }
    QLabel#MetricValue { color: #009C9A; font-size: __METRIC_FONT__px; font-weight: 800; }
    QLabel#MetricHelper { color: #6B8793; font-size: __SMALL_FONT__px; }
    QPushButton#PrimaryButton {
        background-color: #009C9A; color: white; border: none; border-radius: __BUTTON_RADIUS__px;
        padding: __PAD10__px __PAD16__px; font-weight: 750;
    }
    QPushButton#PrimaryButton:hover { background-color: #007F82; }
    QPushButton#PrimaryButton:disabled { background-color: #A7D8DA; color: #F7FAFC; }
    QPushButton#SecondaryButton {
        background-color: #FFFFFF; color: #073763; border: 1px solid #B8D7DF; border-radius: __BUTTON_RADIUS__px;
        padding: __PAD10__px __PAD16__px; font-weight: 750;
    }
    QPushButton#SecondaryButton:hover { background-color: #EAFBFA; border-color: #00A6A6; color: #007F82; }
    QLineEdit, QDoubleSpinBox, QSpinBox {
        background-color: #FFFFFF; border: 1px solid #D6E6EA; border-radius: __FIELD_RADIUS__px; padding: __PAD8__px;
        selection-background-color: #00A6A6;
    }
    QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus { border: 1px solid #00A6A6; }
    QTableWidget#HistoryTable {
        background-color: white; alternate-background-color: #F8FCFC; gridline-color: #E1ECEF;
        border: none; color: #12304A;
    }
    QHeaderView::section {
        background-color: #EAFBFA; color: #073763; padding: __PAD8__px; border: none; font-weight: 750;
    }
    QScrollBar:vertical {
        background: #F6FAFB; width: 10px; margin: 4px;
    }
    QScrollBar::handle:vertical {
        background: #B8D7DF; border-radius: 5px; min-height: 28px;
    }
    QScrollBar::handle:vertical:hover { background: #00A6A6; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    """
    replacements = {
        "__BASE_FONT__": base_font,
        "__BRAND_FONT__": brand_font,
        "__SMALL_FONT__": small_font,
        "__CARD_RADIUS__": card_radius,
        "__META_RADIUS__": meta_radius,
        "__PILL_RADIUS__": pill_radius,
        "__HEADER_FONT__": header_font,
        "__SECTION_FONT__": section_font,
        "__METRIC_FONT__": metric_font,
        "__BUTTON_RADIUS__": button_radius,
        "__FIELD_RADIUS__": field_radius,
        "__PAD7__": px(7),
        "__PAD8__": px(8),
        "__PAD10__": px(10),
        "__PAD12__": px(12),
        "__PAD14__": px(14),
        "__PAD16__": px(16),
    }
    for token, value in replacements.items():
        stylesheet = stylesheet.replace(token, str(value))
    return stylesheet
