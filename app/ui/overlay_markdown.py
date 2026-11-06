from PySide6.QtGui import QFont, QFontDatabase, QRawFont, QTextCharFormat, QTextCursor, QTextFormat, QTextFrameFormat, QTextTable

from .theme_tokens import qcolor


def set_styled_markdown(document, text: str, *, theme_name: str, setter=None):
    # The importer initially assigns a Latin monospace font to code. Apply our
    # CJK-aware formatting before the visible document can lay out those runs.
    enabled = document.isLayoutEnabled()
    document.setLayoutEnabled(False)
    try:
        (setter or document.setMarkdown)(text)
        style_markdown_document(document, theme_name=theme_name)
    finally:
        document.setLayoutEnabled(enabled)


def _code_font_runs(text: str, raw_font, coverage):
    start = offset = 0
    previous = None
    for character in text:
        codepoint = ord(character)
        if codepoint not in coverage:
            coverage[codepoint] = raw_font.supportsCharacter(codepoint)
        fixed = coverage[codepoint]
        if previous is not None and fixed != previous:
            yield start, offset, previous
            start = offset
        previous = fixed
        offset += 2 if codepoint > 0xFFFF else 1
    if previous is not None:
        yield start, offset, previous


def style_markdown_document(document, *, theme_name: str):
    code_background = qcolor("surface_panel", theme_name=theme_name)
    foreground = qcolor("overlay_body_fg", theme_name=theme_name)
    link_color = qcolor("primary", theme_name=theme_name)
    fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    fixed_raw_font = QRawFont.fromFont(fixed_font)
    body_font = document.defaultFont()
    coverage = {}
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
        iterator = block.begin()
        fragments = []
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.isValid():
                fragments.append((fragment.position(), fragment.text(), QTextCharFormat(fragment.charFormat())))
            iterator += 1
        for position, text, original in fragments:
            update = QTextCharFormat(original)
            if heading:
                update.clearProperty(QTextFormat.FontSizeAdjustment)
                scale = {1: 1.35, 2: 1.22, 3: 1.12}.get(heading, 1.0)
                update.setFontPointSize(body_font.pointSizeF() * scale)
            is_code = code_block or original.fontFixedPitch()
            if is_code:
                update.setBackground(code_background)
                update.setForeground(foreground)
                update.setFontPointSize(body_font.pointSizeF())
            if original.isAnchor():
                update.setForeground(link_color)
                update.setFontUnderline(True)
            if is_code:
                for start, end, use_fixed in _code_font_runs(text, fixed_raw_font, coverage):
                    run = QTextCharFormat(update)
                    font = fixed_font if use_fixed else body_font
                    run.setFontFamilies(font.families())
                    run.setFontStyleHint(font.styleHint())
                    run.setFontFixedPitch(use_fixed)
                    cursor = QTextCursor(document)
                    cursor.setPosition(position + start)
                    cursor.setPosition(position + end, QTextCursor.KeepAnchor)
                    cursor.setCharFormat(run)
            elif heading or original.isAnchor():
                cursor = QTextCursor(document)
                cursor.setPosition(position)
                cursor.setPosition(position + len(text.encode("utf-16-le")) // 2, QTextCursor.KeepAnchor)
                cursor.setCharFormat(update)
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
