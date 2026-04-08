import PySimpleGUI as sg
import pandas as pd
import numpy as np
from pathlib import Path

# ========== ОСНОВНЫЕ ФУНКЦИИ АНАЛИЗА (взяты из вашего скрипта) ==========
def load_balance(file_path):
    df = pd.read_excel(file_path, index_col=0)
    return df

class RatioCalculator:
    def __init__(self, f1, f2):
        self.f1 = f1
        self.f2 = f2
        self._extract()

    def _extract(self):
        self.oa = self.f1.loc['Оборотные активы'].iloc[-1]
        self.ko = self.f1.loc['Краткосрочные обязательства'].iloc[-1]
        self.ds = self.f1.loc['Денежные средства и денежные эквиваленты'].iloc[-1]
        self.kfv = self.f1.loc['Финансовые вложения (краткосрочные)'].iloc[-1]
        self.dz = self.f1.loc['Дебиторская задолженность'].iloc[-1]
        self.sk = self.f1.loc['Итого капитал'].iloc[-1]
        self.vb = self.f1.loc['Баланс'].iloc[-1]
        self.rev = self.f2.loc['Выручка'].iloc[-1]
        self.np = self.f2.loc['Чистая прибыль (убыток)'].iloc[-1]

    def current_ratio(self):
        return self.oa / self.ko if self.ko != 0 else 0

    def quick_ratio(self):
        return (self.ds + self.kfv + self.dz) / self.ko if self.ko != 0 else 0

    def absolute_liquidity(self):
        return (self.ds + self.kfv) / self.ko if self.ko != 0 else 0

    def autonomy_ratio(self):
        return self.sk / self.vb if self.vb != 0 else 0

    def roe(self):
        return (self.np / self.sk * 100) if self.sk != 0 else 0

    def ros(self):
        return (self.np / self.rev * 100) if self.rev != 0 else 0

def altman_z(f1, f2):
    try:
        ta = f1.loc['Баланс'].iloc[-1]
        re = f1.loc['Нераспределенная прибыль (непокрытый убыток)'].iloc[-1] if 'Нераспределенная прибыль' in f1.index else 0
        ebit = f2.loc['Прибыль (убыток) до налогообложения'].iloc[-1] if 'Прибыль (убыток) до налогообложения' in f2.index else f2.loc['Чистая прибыль (убыток)'].iloc[-1]
        equity = f1.loc['Итого капитал'].iloc[-1]
        sales = f2.loc['Выручка'].iloc[-1]
        wc = (f1.loc['Оборотные активы'].iloc[-1] - f1.loc['Краткосрочные обязательства'].iloc[-1])
        Z = (0.717 * (wc / ta)) + (0.847 * (re / ta)) + (3.107 * (ebit / ta)) + (0.420 * (equity / (ta - equity))) + (0.998 * (sales / ta))
        return Z
    except:
        return None

def generate_report(f1_path, f2_path, output_path):
    f1 = load_balance(f1_path)
    f2 = load_balance(f2_path)
    ratios = RatioCalculator(f1, f2)

    report_data = {
        'Показатель': [
            'Коэффициент текущей ликвидности',
            'Коэффициент быстрой ликвидности',
            'Коэффициент абсолютной ликвидности',
            'Коэффициент автономии',
            'Рентабельность собственного капитала, %',
            'Рентабельность продаж, %',
            'Z-счёт Альтмана (риск банкротства)'
        ],
        'Значение': [
            ratios.current_ratio(),
            ratios.quick_ratio(),
            ratios.absolute_liquidity(),
            ratios.autonomy_ratio(),
            ratios.roe(),
            ratios.ros(),
            altman_z(f1, f2)
        ]
    }
    df_report = pd.DataFrame(report_data)
    df_report.to_excel(output_path, index=False)
    return df_report

# ========== GUI-ОБОЛОЧКА ==========
def main():
    sg.theme('Default1')   # можно выбрать любую тему, например 'SystemDefault'

    layout = [
        [sg.Text("Выберите файл Бухгалтерского баланса (форма №1):", font=("Arial", 10))],
        [sg.Input(key='-BALANCE-', size=(60,1)), sg.FileBrowse(file_types=(("Excel files", "*.xlsx"),))],
        [sg.Text("Выберите файл Отчёта о финансовых результатах (форма №2):", font=("Arial", 10))],
        [sg.Input(key='-INCOME-', size=(60,1)), sg.FileBrowse(file_types=(("Excel files", "*.xlsx"),))],
        [sg.Text("Имя выходного файла (Excel):", font=("Arial", 10))],
        [sg.Input(key='-OUTPUT-', default_text="financial_report.xlsx", size=(40,1)), sg.Text(".xlsx")],
        [sg.Button("Выполнить анализ", key='-RUN-'), sg.Button("Выход", key='-EXIT-')],
        [sg.HorizontalSeparator()],
        [sg.Text("Результаты анализа:", font=("Arial", 10, "bold"))],
        [sg.Table(values=[], headings=['Показатель', 'Значение'], key='-TABLE-',
                  auto_size_columns=False, col0_width=45, col1_width=15,
                  justification='left', num_rows=8, enable_events=False)],
        [sg.Multiline(size=(80, 5), key='-LOG-', autoscroll=True, disabled=True, font=("Courier New", 9))]
    ]

    window = sg.Window("Финансовый анализ предприятия", layout, finalize=True)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, '-EXIT-'):
            break

        if event == '-RUN-':
            balance_file = values['-BALANCE-'].strip()
            income_file = values['-INCOME-'].strip()
            output_file = values['-OUTPUT-'].strip()
            if not output_file.endswith('.xlsx'):
                output_file += '.xlsx'

            # Очистка лога и таблицы
            window['-LOG-'].update('')
            window['-TABLE-'].update(values=[])

            # Проверка наличия файлов
            if not balance_file:
                window['-LOG-'].print("❌ Укажите файл баланса (форма №1).")
                continue
            if not income_file:
                window['-LOG-'].print("❌ Укажите файл отчёта о финансовых результатах (форма №2).")
                continue
            if not Path(balance_file).is_file():
                window['-LOG-'].print(f"❌ Файл баланса не найден: {balance_file}")
                continue
            if not Path(income_file).is_file():
                window['-LOG-'].print(f"❌ Файл отчёта не найден: {income_file}")
                continue

            try:
                window['-LOG-'].print("🔄 Выполняется анализ...")
                # Запуск расчёта
                df_result = generate_report(balance_file, income_file, output_file)
                # Отображение результатов в таблице
                table_data = df_result.values.tolist()
                window['-TABLE-'].update(values=table_data)
                window['-LOG-'].print(f"✅ Анализ завершён! Отчёт сохранён в файл: {output_file}")
                window['-LOG-'].print("🎉 Можно открыть полученный Excel-файл.")
            except Exception as e:
                window['-LOG-'].print(f"❌ Ошибка при выполнении анализа:\n{str(e)}")
                sg.popup_error(f"Произошла ошибка:\n{e}", title="Ошибка")

    window.close()

if __name__ == "__main__":
    main()