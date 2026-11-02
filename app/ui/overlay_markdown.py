from PySide6.QtGui import QFont, QFontDatabase, QTextCharFormat, QTextCursor, QTextFormat, QTextFrameFormat, QTextTable

from .theme_tokens import qcolor


def style_markdown_document(document, *, theme_name: str):
    code_background = qcolor("surface_panel", theme_name=theme_name)
    foreground = qcolor("overlay_body_fg", theme_name=theme_name)
    link_color = qcolor("primary", theme_name=theme_name)
    fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    block = document.begin()
    previous_code = False
    while block.isValid():
        block_format = block.blockFormat()
        code_block = block_format.nonBreakableLines() or block_format.hasProperty(QTextFormat.BlockCodeFence)
        if code_block:
            block_format.setBackground(code_background)
            block_format.setLeftMargin(10)
            block_format.setRightMargin(10)
            block_format.setNonBreakableLines(False)
            block_format.setTopMargin(0 if previous_code else 8)
            following = block.next().blockFormat()
            next_code = following.nonBreakableLines() or following.hasProperty(QTextFormat.BlockCodeFence)
            block_format.setBottomMargin(0 if next_code else 8)
            cursor = QTextCursor(block)
            cursor.setBlockFormat(block_format)
        heading = block_format.headingLevel()
        if heading:
            block_format.setTopMargin(14)
            block_format.setBottomMargin(6)
            QTextCursor(block).setBlockFormat(block_format)
        fragments = block.begin()
        while not fragments.atEnd():
            fragment = fragments.fragment()
            if fragment.isValid():
                original = fragment.charFormat()
                update = QTextCharFormat(original)
                if heading:
                    update.clearProperty(QTextFormat.FontSizeAdjustment)
                    scale = {1: 1.35, 2: 1.22, 3: 1.12}.get(heading, 1.0)
                    update.setFontPointSize(document.defaultFont().pointSizeF() * scale)
                if code_block or original.fontFixedPitch():
                    update.setBackground(code_background)
                    update.setForeground(foreground)
                    update.setFontFamilies([fixed_font.family()])
                    update.setFontPointSize(document.defaultFont().pointSizeF())
                if original.isAnchor():
                    update.setForeground(link_color)
                    update.setFontUnderline(True)
                if heading or code_block or original.fontFixedPitch() or original.isAnchor():
                    cursor = QTextCursor(document)
                    cursor.setPosition(fragment.position())
                    cursor.setPosition(fragment.position() + fragment.length(), QTextCursor.KeepAnchor)
                    cursor.setCharFormat(update)
            fragments += 1
        block = block.next()
        previous_code = code_block

    def style_tables(frame):
        for child in frame.childFrames():
            if isinstance(child, QTextTable):
                table_format = child.format()
                table_format.setCellPadding(6)
                table_format.setCellSpacing(0)
                table_format.setBorderBrush(qcolor("border_base", theme_name=theme_name))
                table_format.setHeaderRowCount(1)
                child.setFormat(table_format)
                first_cell = child.cellAt(0, 0)
                cursor = first_cell.firstCursorPosition()
                # The Markdown importer can insert an empty paragraph before the first header.
                while not cursor.block().text() and cursor.position() < first_cell.lastCursorPosition().position():
                    cursor.deleteChar()
                for row in range(child.rows()):
                    for column in range(child.columns()):
                        cell = child.cellAt(row, column)
                        cell_format = cell.format().toTableCellFormat()
                        cell_format.setBorder(1)
                        cell_format.setBorderStyle(QTextFrameFormat.BorderStyle_Solid)
                        cell_format.setBorderBrush(qcolor("border_base", theme_name=theme_name))
                        cell.setFormat(cell_format)
                        cursor = cell.firstCursorPosition()
                        last = cell.lastCursorPosition().position()
                        # Qt gives the first Markdown header cell different paragraph defaults.
                        while cursor.position() <= last:
                            block_format = cursor.blockFormat()
                            block_format.setTopMargin(0)
                            block_format.setBottomMargin(0)
                            cursor.setBlockFormat(block_format)
                            if not cursor.movePosition(QTextCursor.NextBlock):
                                break
                        if row == 0:
                            cursor = cell.firstCursorPosition()
                            cursor.setPosition(last, QTextCursor.KeepAnchor)
                            header = QTextCharFormat()
                            header.setFontWeight(QFont.Bold)
                            cursor.mergeCharFormat(header)
            style_tables(child)

    style_tables(document.rootFrame())
