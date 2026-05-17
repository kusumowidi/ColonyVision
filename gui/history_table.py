"""Recent analysis history table."""

from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from core.cfu import format_scientific


class HistoryTable(QTableWidget):
    COLUMNS = ["Sample ID", "Media Type", "AI Count", "Final Count", "CFU/ml", "Status", "Date", "Actions"]

    def __init__(self, parent=None):
        super().__init__(0, len(self.COLUMNS), parent)
        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setObjectName("HistoryTable")
        self.setShowGrid(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setMinimumHeight(190)

    def set_rows(self, rows: list[dict]) -> None:
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row.get("sample_id", ""),
                row.get("media_type", ""),
                row.get("ai_count", ""),
                row.get("final_count", "") or "-",
                _format_cfu(row.get("cfu_ml", "")),
                row.get("status", ""),
                str(row.get("created_at", ""))[:10],
                "View",
            ]
            for col_index, value in enumerate(values):
                self.setItem(row_index, col_index, QTableWidgetItem(str(value)))
        self.resizeColumnsToContents()


def _format_cfu(value) -> str:
    try:
        return format_scientific(float(value))
    except (TypeError, ValueError):
        return "-"
