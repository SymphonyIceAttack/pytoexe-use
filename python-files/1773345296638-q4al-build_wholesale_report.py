#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

import pandas as pd


REPORT_COLUMNS = [
    "Дата",
    "Наименование товара",
    "Регион заказа",
    "ID заказчика",
    "Заказано, шт",
    "Выкуплено, шт",
    "Затраты (в случае отказа)",
    "Комментарии",
]

MONTH_NAMES = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}

REGION_MAP = {
    "Москва, МО и Дальние регионы": "МСК",
    "Санкт-Петербург и СЗО": "Санкт-Петербург",
    "Беларусь": "Белорусь",
}

PRODUCT_NAME_MAP = {
    "260320250001": "Кабель для айфона, провод для айфона, зарядка для iphone, 1 метр, чёрный (1шт), Gerlax",
    "260320250005": "Кабель micro usb, 1 метр, черный (1 шт), Gerlax",
    "260320250008": "Кабель usb type c, провод type c, зарядка type c, 1 метр, черный (1 шт), Gerlax",
    "260320250011": "Повербанк 10000 mah (22,5W), GERLAX, белый (Р118Р)",
    "260320250012": "Повербанк 10000 mah (20W), GERLAX, белый (Р119Р)",
    "260320250013": "Повербанк 20000 mah (22,5W), GERLAX, черный (Р218Р)",
    "260320250014": "Зарядное устройство type c / зарядка / блок питания / быстрая зарядка / Gerlax, белый (20W)",
}


@dataclass
class SheetPayload:
    name: str
    frame: pd.DataFrame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Собирает отчет по оптовым заказам из сырого Ozon CSV."
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        default="orders.csv",
        help="Путь к исходному CSV. По умолчанию: orders.csv",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="wholesale_report.xlsx",
        help="Путь к итоговому XLSX. По умолчанию: wholesale_report.xlsx",
    )
    parser.add_argument(
        "--min-qty",
        type=int,
        default=9,
        help="Минимальное количество в группе, чтобы считать заказ оптовым. По умолчанию: 9",
    )
    return parser.parse_args()


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace("\xa0", " ")
    return " ".join(text.split()).strip()


def normalize_region(value: object) -> str:
    cleaned = clean_text(value)
    return REGION_MAP.get(cleaned, cleaned)


def normalize_product_name(article: object, raw_name: object) -> str:
    article_key = clean_text(article)
    if article_key in PRODUCT_NAME_MAP:
        return PRODUCT_NAME_MAP[article_key]
    return clean_text(raw_name)


def build_comment(delivered: int, cancelled: int, in_transit: int, ordered: int) -> str:
    if ordered == 0:
        return ""
    if delivered == ordered:
        return "Выкуплен"
    if in_transit == ordered:
        return "Доставляется"
    if cancelled == ordered:
        return "Отменён"
    if delivered > 0 and in_transit > 0 and cancelled == 0:
        return f"{in_transit} доставляется"
    if delivered > 0 and cancelled > 0 and in_transit == 0:
        return f"Выкуплено {delivered} из {ordered}, отменено {cancelled}"
    if delivered == 0 and cancelled > 0 and in_transit > 0:
        return f"Доставляется {in_transit}, отменено {cancelled}"
    if delivered > 0 and cancelled > 0 and in_transit > 0:
        return f"Выкуплено {delivered}, доставляется {in_transit}, отменено {cancelled}"
    return "Требует проверки"


def refusal_cost(
    delivered: int, cancelled: int, in_transit: int, source_cost: float
) -> object:
    if source_cost > 0:
        return round(source_cost, 2)
    if in_transit > 0 and cancelled == 0:
        return ""
    if delivered == 0 and cancelled == 0 and in_transit == 0:
        return ""
    return 0


def pick_mode(values: Iterable[str]) -> str:
    cleaned = [clean_text(value) for value in values if clean_text(value)]
    if not cleaned:
        return ""
    counts = Counter(cleaned)
    return counts.most_common(1)[0][0]


def load_source(path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        sep=";",
        encoding="utf-8-sig",
        dtype={
            "Номер заказа": "string",
            "Номер отправления": "string",
            "Артикул": "string",
        },
    )

    df["Количество"] = (
        pd.to_numeric(df["Количество"], errors="coerce").fillna(0).astype(int)
    )
    df["Стоимость доставки"] = pd.to_numeric(
        df["Стоимость доставки"], errors="coerce"
    ).fillna(0.0)
    df["accepted_at"] = pd.to_datetime(df["Принят в обработку"], errors="coerce")
    df = df[df["accepted_at"].notna()].copy()

    df["accepted_date"] = df["accepted_at"].dt.normalize()
    df["order_prefix"] = (
        df["Номер заказа"].astype("string").str.split("-").str[0].fillna("")
    )
    df["posting_base"] = (
        df["Номер отправления"].astype("string").str.rsplit("-", n=1).str[0].fillna("")
    )
    df["product_name"] = [
        normalize_product_name(article, name)
        for article, name in zip(df["Артикул"], df["Название товара"])
    ]
    df["region_name"] = df["Кластер отгрузки"].map(normalize_region)
    return df


def build_report(df: pd.DataFrame, min_qty: int) -> list[SheetPayload]:
    rows: list[dict[str, object]] = []

    for posting_base, group in df.groupby("posting_base", dropna=False):
        if not posting_base:
            continue

        ordered = int(group["Количество"].sum())
        if ordered < min_qty:
            continue

        status = group["Статус"].fillna("")
        delivered = int(group.loc[status.eq("Доставлен"), "Количество"].sum())
        cancelled = int(group.loc[status.eq("Отменён"), "Количество"].sum())
        in_transit = int(group.loc[status.eq("Доставляется"), "Количество"].sum())

        accepted_date = group["accepted_date"].min()
        rows.append(
            {
                "Дата": accepted_date.strftime("%d.%m.%y"),
                "_sort_date": accepted_date,
                "_month": accepted_date.to_period("M"),
                "_month_number": accepted_date.month,
                "_year": accepted_date.year,
                "Наименование товара": pick_mode(group["product_name"]),
                "Регион заказа": pick_mode(group["region_name"]),
                "ID заказчика": pick_mode(group["order_prefix"]),
                "Заказано, шт": ordered,
                "Выкуплено, шт": delivered if (delivered or cancelled) else "",
                "Затраты (в случае отказа)": refusal_cost(
                    delivered=delivered,
                    cancelled=cancelled,
                    in_transit=in_transit,
                    source_cost=float(group["Стоимость доставки"].sum()),
                ),
                "Комментарии": build_comment(
                    delivered=delivered,
                    cancelled=cancelled,
                    in_transit=in_transit,
                    ordered=ordered,
                ),
            }
        )

    report = pd.DataFrame(rows)
    if report.empty:
        return []

    report = report.sort_values(
        by=["_sort_date", "Регион заказа", "ID заказчика", "Наименование товара"],
        kind="stable",
    )

    month_year_counts = (
        report[["_month_number", "_year"]]
        .drop_duplicates()
        .groupby("_month_number")
        .size()
        .to_dict()
    )

    sheets: list[SheetPayload] = []
    for month_key, month_frame in report.groupby("_month", sort=True):
        month_number = int(month_key.month)
        year = int(month_key.year)
        base_name = MONTH_NAMES[month_number]
        if month_year_counts.get(month_number, 0) > 1:
            sheet_name = f"{base_name}_{year}"
        else:
            sheet_name = base_name

        visible = month_frame[REPORT_COLUMNS].reset_index(drop=True)
        sheets.append(SheetPayload(name=sheet_name[:31], frame=visible))

    return sheets


def column_letter(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def xml_text(value: str) -> str:
    escaped = escape(value)
    if value != value.strip() or "\n" in value:
        return f'<t xml:space="preserve">{escaped}</t>'
    return f"<t>{escaped}</t>"


def write_sheet_xml(frame: pd.DataFrame) -> str:
    rows_xml: list[str] = []

    all_rows = [REPORT_COLUMNS] + frame.values.tolist()
    for row_index, row_values in enumerate(all_rows, start=1):
        cells_xml: list[str] = []
        for col_index, value in enumerate(row_values, start=1):
            cell_ref = f"{column_letter(col_index)}{row_index}"
            if value == "" or pd.isna(value):
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                numeric = float(value)
                if math.isfinite(numeric):
                    text_value = (
                        str(int(numeric))
                        if numeric.is_integer()
                        else str(round(numeric, 2))
                    )
                    cells_xml.append(f'<c r="{cell_ref}"><v>{text_value}</v></c>')
                    continue
            text = clean_text(value)
            cells_xml.append(
                f'<c r="{cell_ref}" t="inlineStr"><is>{xml_text(text)}</is></c>'
            )
        rows_xml.append(f'<row r="{row_index}">{"".join(cells_xml)}</row>')

    max_row = len(all_rows)
    max_col = len(REPORT_COLUMNS)
    dimension = f"A1:{column_letter(max_col)}{max_row}"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/>'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f"<sheetData>{''.join(rows_xml)}</sheetData>"
        "</worksheet>"
    )


def build_xlsx(output_path: Path, sheets: list[SheetPayload]) -> None:
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    workbook_sheets = []
    workbook_rels = []
    content_overrides = []

    for idx, sheet in enumerate(sheets, start=1):
        sheet_id = f"rId{idx}"
        workbook_sheets.append(
            f'<sheet name="{escape(sheet.name)}" sheetId="{idx}" r:id="{sheet_id}"/>'
        )
        workbook_rels.append(
            (
                f'<Relationship Id="{sheet_id}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{idx}.xml"/>'
            )
        )
        content_overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{idx}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )

    workbook_rels.append(
        '<Relationship Id="rIdStyles" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
    )

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/styles.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                '<Override PartName="/docProps/core.xml" '
                'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                '<Override PartName="/docProps/app.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
                f"{''.join(content_overrides)}"
                "</Types>"
            ),
        )
        archive.writestr(
            "_rels/.rels",
            (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="xl/workbook.xml"/>'
                '<Relationship Id="rId2" '
                'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
                'Target="docProps/core.xml"/>'
                '<Relationship Id="rId3" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
                'Target="docProps/app.xml"/>'
                "</Relationships>"
            ),
        )
        archive.writestr(
            "docProps/app.xml",
            (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
                'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
                "<Application>Codex</Application>"
                f'<HeadingPairs><vt:vector size="2" baseType="variant">'
                "<vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant>"
                f"<vt:variant><vt:i4>{len(sheets)}</vt:i4></vt:variant>"
                "</vt:vector></HeadingPairs>"
                f'<TitlesOfParts><vt:vector size="{len(sheets)}" baseType="lpstr">'
                f"{''.join(f'<vt:lpstr>{escape(sheet.name)}</vt:lpstr>' for sheet in sheets)}"
                "</vt:vector></TitlesOfParts>"
                "</Properties>"
            ),
        )
        archive.writestr(
            "docProps/core.xml",
            (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                "<cp:coreProperties "
                'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/" '
                'xmlns:dcterms="http://purl.org/dc/terms/" '
                'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                "<dc:creator>Codex</dc:creator>"
                "<cp:lastModifiedBy>Codex</cp:lastModifiedBy>"
                "<dc:title>Отчет по оптовикам</dc:title>"
                f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
                f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
                "</cp:coreProperties>"
            ),
        )
        archive.writestr(
            "xl/workbook.xml",
            (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<workbookPr defaultThemeVersion="164011"/>'
                '<bookViews><workbookView activeTab="0"/></bookViews>'
                f"<sheets>{''.join(workbook_sheets)}</sheets>"
                "</workbook>"
            ),
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f"{''.join(workbook_rels)}"
                "</Relationships>"
            ),
        )
        archive.writestr(
            "xl/styles.xml",
            (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
                '<fills count="2"><fill><patternFill patternType="none"/></fill>'
                '<fill><patternFill patternType="gray125"/></fill></fills>'
                '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
                '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
                '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
                "</styleSheet>"
            ),
        )

        for idx, sheet in enumerate(sheets, start=1):
            archive.writestr(
                f"xl/worksheets/sheet{idx}.xml", write_sheet_xml(sheet.frame)
            )


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_csv)
    output_path = Path(args.output)

    source = load_source(input_path)
    sheets = build_report(source, min_qty=args.min_qty)
    if not sheets:
        raise SystemExit("Подходящих оптовых заказов не найдено.")

    build_xlsx(output_path, sheets)

    total_rows = sum(len(sheet.frame) for sheet in sheets)
    print(
        f"Готово: {output_path} | листов: {len(sheets)} | строк отчета: {total_rows} | min_qty: {args.min_qty}"
    )
    for sheet in sheets:
        print(f"- {sheet.name}: {len(sheet.frame)} строк")


if __name__ == "__main__":
    main()
