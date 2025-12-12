import customtkinter as ctk
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak,
    PageTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from tkinter import filedialog
import os
import datetime
import json
from tkcalendar import Calendar
import tkinter as tk

# Fonts
FONT_FILE = 'arial.ttf'
FONT_FILE_BOLD = 'arialbd.ttf'

try:
    pdfmetrics.registerFont(TTFont('RusFont', FONT_FILE))
    pdfmetrics.registerFont(TTFont('RusFont-Bold', FONT_FILE_BOLD))

    FONT_NAME = 'RusFont'
    FONT_NAME_BOLD = 'RusFont-Bold'

except Exception as exc:
    print(f"Внимание: Не удалось зарегистрировать русские шрифты. Используется Helvetica. Ошибка: {exc}")
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'

# general page settings
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 1.5 * cm
HEADER_HEIGHT = 1.0 * cm
FOOTER_HEIGHT = 0.5 * cm
TEXT_WIDTH = PAGE_WIDTH - 2 * MARGIN
COLUMNS = 3
COL_WIDTH = TEXT_WIDTH / COLUMNS
IMAGE_MAX_HEIGHT = 180


def get_custom_styles():
    # setting styles
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10
    ))

    styles.add(ParagraphStyle(
        name='H1_Custom',
        parent=styles['CustomNormal'],
        fontName=FONT_NAME_BOLD,
        fontSize=14,
        spaceAfter=12,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='HeaderDetail',
        parent=styles['CustomNormal'],
        fontName=FONT_NAME,
        fontSize=7
    ))

    styles.add(ParagraphStyle(
        name='HeaderDetailBold',
        parent=styles['HeaderDetail'],
        fontName=FONT_NAME_BOLD,
        fontSize=7
    ))

    return styles


STYLES = get_custom_styles()


# generating pdf

def _create_header_table(data):
    # page header

    line1 = [
        [
            Paragraph("<b>Марка, Модель</b>", STYLES['HeaderDetail']),
            Paragraph("<b>Модуль</b>", STYLES['HeaderDetail']),
            Paragraph("<b>Год</b>", STYLES['HeaderDetail']),
            Paragraph("<b>Rev.:</b>", STYLES['HeaderDetail']),
        ],
        [
            Paragraph(data.get("car_make", ""), STYLES['HeaderDetailBold']),
            Paragraph(data.get("module_no", ""), STYLES['HeaderDetailBold']),
            Paragraph(data.get("year", ""), STYLES['HeaderDetailBold']),
            Paragraph(data.get("revision", ""), STYLES['HeaderDetailBold']),
        ]
    ]

    line2 = [
        [
            Paragraph("<b>Версия:</b>", STYLES['HeaderDetail']),
            Paragraph("программа №: <b>{}</b> от: <b>{}</b>".format(
                data.get("program_no", ""),
                data.get("program_date", "")
            ), STYLES['HeaderDetail']),
            "",
        ]
    ]

    header_data = line1 + line2
    col_widths = [12 * cm, 3.5 * cm, 1.5 * cm, 1.5 * cm]

    table = Table(header_data, colWidths=col_widths)

    table.setStyle(TableStyle([
        ('SPAN', (1, 2), (3, 2)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    return table


def _image_grid_flowable(image_paths):
    # image grid
    if not image_paths:
        return Spacer(1, 1)

    table_data = []
    current_row = []

    for path in image_paths:
        if os.path.exists(path):
            try:
                img = Image(path, width=COL_WIDTH - 10, height=IMAGE_MAX_HEIGHT, kind='proportional')
                img.hAlign = 'CENTER'
                current_row.append(img)
            except Exception as err:
                current_row.append(Paragraph(f"Ошибка: {err}", STYLES['HeaderDetail']))
        else:
            current_row.append(Paragraph("Файл не найден", STYLES['HeaderDetail']))

        if len(current_row) == COLUMNS:
            table_data.append(current_row)
            current_row = []

    if current_row:
        while len(current_row) < COLUMNS:
            current_row.append(Paragraph(" ", STYLES['CustomNormal']))
        table_data.append(current_row)

    image_table = Table(table_data, colWidths=[COL_WIDTH] * COLUMNS)

    image_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))

    return image_table


class InstructionDocTemplate(BaseDocTemplate):
    # define template

    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)

        self.doc_data = kw.get('doc_data', {})

        self.addPageTemplates(self._create_page_template())

    def _create_page_template(self):
        main_frame = Frame(
            MARGIN,
            MARGIN + FOOTER_HEIGHT,
            TEXT_WIDTH,
            PAGE_HEIGHT - 2 * MARGIN - HEADER_HEIGHT,
            id='main_content'
        )

        return [
            PageTemplate(
                id='OneCol',
                frames=[main_frame],
                onPage=self.page_layout
            )
        ]

    def page_layout(self, canvas, _doc):
        # static elements
        canvas.saveState()

        header_table = _create_header_table(self.doc_data)
        header_table.wrapOn(canvas, TEXT_WIDTH, HEADER_HEIGHT)
        header_table.drawOn(canvas, MARGIN, PAGE_HEIGHT - MARGIN - HEADER_HEIGHT)

        footer_text = f"Generated: {self.doc_data.get('generation_date', 'N/A')} by {self.doc_data.get('user_email', 'N/A')}"
        p_footer = Paragraph(footer_text, STYLES['HeaderDetail'])
        p_footer.wrapOn(canvas, 10 * cm, 0.5 * cm)
        p_footer.drawOn(canvas, MARGIN, MARGIN / 2)

        total_pages = 2  # Хардкодим, как было в предыдущей версии
        p_num_text = f"PAGE {canvas.getPageNumber()} / {total_pages}"
        p_num = Paragraph(p_num_text, STYLES['HeaderDetail'])
        p_num.wrapOn(canvas, 5 * cm, 0.5 * cm)

        p_num.drawOn(canvas, MARGIN + 12 * cm, MARGIN / 2)

        canvas.restoreState()


def create_instruction_pdf_advanced(filename, data, image_paths):
    # generating pdf

    doc = InstructionDocTemplate(
        filename,
        doc_data=data,
        pagesize=A4
    )

    story = []

    # schemas
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Схема подключения и инструкции:</b>", STYLES['H1_Custom']))

    description_paragraphs = data.get("connection_description", "").split('\n')
    for p_text in description_paragraphs:
        if p_text.strip():
            story.append(Paragraph(p_text, STYLES['CustomNormal']))
            story.append(Spacer(1, 8))

    story.append(Spacer(1, 15))

    # image grid
    story.append(_image_grid_flowable(image_paths))

    story.append(Spacer(1, 15))

    # description section
    story.append(PageBreak())
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Дополнительное описание / Индикаторы:</b>", STYLES['H1_Custom']))

    full_desc_paragraphs = data.get("full_description", "").split('\n')
    for p_text in full_desc_paragraphs:
        if p_text.strip():
            story.append(Paragraph(p_text, STYLES['CustomNormal']))
            story.append(Spacer(1, 8))

    try:
        doc.build(story)
        return True
    except Exception as err:
        print(f"Ошибка при генерации PDF: {err}")
        return False


# GUI

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PDF Instruction Generator")
        self.geometry("700x850")

        # initialize attributes
        self.image_paths = []
        self.user_email = "support@farvater-can.ru"
        self.fields = {}
        self.date_entry_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))

        self.connection_desc_textbox = None
        self.full_desc_textbox = None
        self.image_label = None
        self.status_label = None
        self.image_button = None
        self.generate_button = None
        self.load_button = None
        self.save_button = None


        ctk.set_default_color_theme("blue")
        ctk.set_appearance_mode("System")

        self.create_widgets()

    def open_calendar_picker(self):
        # calendar

        # pop-up window
        top = ctk.CTkToplevel(self)
        top.title("Выбор даты")
        top.geometry("280x300")

        top.grab_set()

        # 2. calendar widget
        try:
            current_date_str = self.date_entry_var.get()
            if current_date_str:
                year, month, day = map(int, current_date_str.split('-'))
            else:
                today = datetime.date.today()
                year, month, day = today.year, today.month, today.day
        except:
            today = datetime.date.today()
            year, month, day = today.year, today.month, today.day

        cal = Calendar(top,
                       selectmode='day',
                       year=year,
                       month=month,
                       day=day,
                       date_pattern='y-mm-dd')
        cal.pack(pady=20, padx=20)

        # save & close
        def set_date():
            selected_date = cal.get_date()
            self.date_entry_var.set(selected_date)
            top.destroy()

        # btn
        ctk.CTkButton(top, text="Выбрать", command=set_date).pack(pady=5)

        # disable focus
        top.bind('<Destroy>', lambda e: self.grab_release())

    def create_widgets(self):

        main_frame = ctk.CTkScrollableFrame(self, label_text="Ввод данных")
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # header data
        header_label = ctk.CTkLabel(main_frame, text="Шапка:", font=("Arial", 16, "bold"))
        header_label.pack(pady=(10, 5), anchor="w")

        header_grid_frame = ctk.CTkFrame(main_frame)
        header_grid_frame.pack(padx=10, fill="x")

        fields_data = [
            ("Марка/Модель:", "car_make", "DONG FENG GX (DFH4180)"),
            ("Модуль №:", "module_no", "005540xx"),
            ("Год:", "year", "2022+"),
            ("Ревизия:", "revision", "00"),
            ("Программа №:", "program_no", "14931")
        ]

        for i, (label_text, key, default) in enumerate(fields_data):
            row, col = divmod(i, 2)
            ctk.CTkLabel(header_grid_frame, text=label_text).grid(row=row, column=col * 2, padx=5, pady=5, sticky="w")
            entry = ctk.CTkEntry(header_grid_frame, width=150)
            entry.grid(row=row, column=col * 2 + 1, padx=5, pady=5, sticky="ew")
            entry.insert(0, default)
            self.fields[key] = entry

            # date picker
            date_row = 3
            date_col_start = 0

            ctk.CTkLabel(header_grid_frame, text="Дата программы:").grid(row=date_row, column=date_col_start, padx=5,
                                                                         pady=5, sticky="w")

            date_input_frame = ctk.CTkFrame(header_grid_frame, fg_color="transparent")
            date_input_frame.grid(row=date_row, column=date_col_start + 1, padx=5, pady=5, sticky="ew")

            date_entry = ctk.CTkEntry(date_input_frame, width=120, textvariable=self.date_entry_var)
            date_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
            self.fields["program_date"] = date_entry

            date_button = ctk.CTkButton(date_input_frame, text="📅", width=30, command=self.open_calendar_picker)
            date_button.pack(side="left", padx=(0, 0))

            # connection description
        ctk.CTkLabel(main_frame, text="Описание схемы/подключения:", font=("Arial", 14, "bold")).pack(
            pady=(10, 0), anchor="w")
        self.connection_desc_textbox = ctk.CTkTextbox(main_frame, height=80)
        self.connection_desc_textbox.pack(padx=10, pady=5, fill="x")
        self.connection_desc_textbox.insert("0.0",
                                            "CAN3 не подключать.\nCAN1 подключать.\nVCC к +12В.\nСхема прилагается.")

        # additional description
        ctk.CTkLabel(main_frame, text="Полное описание/индикаторы:", font=("Arial", 14, "bold")).pack(
            pady=(10, 0), anchor="w")
        self.full_desc_textbox = ctk.CTkTextbox(main_frame, height=150)
        self.full_desc_textbox.pack(padx=10, pady=5, fill="x")
        self.full_desc_textbox.insert("0.0",
                                      "• Особенности работы индикатора А\n• Калибровка датчика В\n• Примечания по эксплуатации.")

        # images
        ctk.CTkLabel(main_frame, text="Фотографии оборудования:", font=("Arial", 14, "bold")).pack(
            pady=(10, 0), anchor="w")

        image_frame = ctk.CTkFrame(main_frame)
        image_frame.pack(padx=10, pady=10, fill="x")

        self.image_button = ctk.CTkButton(image_frame, text="Выбрать изображения",
                                          command=self.select_image)
        self.image_button.pack(side="left", padx=10, pady=10)

        self.image_label = ctk.CTkLabel(image_frame, text="Файлы не выбраны.")
        self.image_label.pack(side="left", padx=10, pady=10)

        # control buttons
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(padx=20, pady=(0, 10), fill="x")

        self.generate_button = ctk.CTkButton(control_frame, text="СГЕНЕРИРОВАТЬ PDF", command=self.generate_pdf_action,
                                             height=40, font=("Arial", 16, "bold"))
        self.generate_button.pack(side="right", padx=(10, 0), fill="x", expand=True)

        self.load_button = ctk.CTkButton(control_frame, text="ЗАГРУЗИТЬ ДАННЫЕ (JSON)", command=self.load_data_action,
                                         height=40)
        self.load_button.pack(side="left", padx=(0, 10), fill="x", expand=True)

        self.save_button = ctk.CTkButton(control_frame, text="СОХРАНИТЬ ДАННЫЕ (JSON)", command=self.save_data_action,
                                         height=40)
        self.save_button.pack(side="left", fill="x", expand=True)

        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.pack(pady=5)

    # processing data

    def collect_data(self):
        # collect data to dictionary
        data = {key: entry.get() for key, entry in self.fields.items()}
        data["connection_description"] = self.connection_desc_textbox.get("1.0", "end-1c")
        data["full_description"] = self.full_desc_textbox.get("1.0", "end-1c")
        data["image_paths"] = self.image_paths
        data["generation_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["user_email"] = self.user_email
        return data

    def update_gui_from_data(self, data):
        # update data from dictionary
        for key, entry in self.fields.items():
            entry.delete(0, 'end')
            entry.insert(0, data.get(key, ''))

        self.connection_desc_textbox.delete("1.0", "end")

        # connection_description not None
        conn_desc = data.get("connection_description", '')
        if conn_desc is not None:
            self.connection_desc_textbox.insert("1.0", conn_desc)

        self.full_desc_textbox.delete("1.0", "end")
        full_desc = data.get("full_description", '')
        if full_desc is not None:
            self.full_desc_textbox.insert("1.0", full_desc)

        self.image_paths = data.get("image_paths", [])
        self.image_label.configure(text=f"Выбрано файлов: {len(self.image_paths)}")

    def load_data_action(self):
        # load data from JSON
        json_path = filedialog.askopenfilename(
            title="Загрузить данные инструкции (JSON)",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if json_path:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.update_gui_from_data(data)
                    self.status_label.configure(text=f"Данные успешно загружены из {os.path.basename(json_path)}.",
                                                text_color="green")
            except Exception as err:
                self.status_label.configure(text=f"ОШИБКА загрузки JSON: {err}", text_color="red")
        else:
            self.status_label.configure(text="Загрузка отменена.", text_color="gray")

    def save_data_action(self):
        # save data to JSON
        pdf_data = self.collect_data()

        initial_file = f"{pdf_data.get('car_make', 'new')}-{pdf_data.get('module_no', 'data')}.json"
        json_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=initial_file,
            title="Сохранить данные инструкции как",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )

        if json_path:
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(pdf_data, f, ensure_ascii=False, indent=4)
                self.status_label.configure(text=f"Данные успешно сохранены в {os.path.basename(json_path)}.",
                                            text_color="green")
            except Exception as err:
                self.status_label.configure(text=f"ОШИБКА сохранения JSON: {err}", text_color="red")
        else:
            self.status_label.configure(text="Сохранение отменено.", text_color="gray")

    def select_image(self):
        # selec images
        paths = filedialog.askopenfilenames(
            title="Выберите изображения (любое количество)",
            filetypes=(("Image files", "*.png;*.jpg;*.jpeg"), ("All files", "*.*"))
        )
        if paths:
            self.image_paths = list(paths)
            count = len(self.image_paths)
            self.image_label.configure(text=f"Выбрано файлов: {count}")
            self.status_label.configure(text=f"{count} изображений выбрано.", text_color="orange")
        else:
            self.image_paths = []
            self.image_label.configure(text="Файлы не выбраны.")

    def generate_pdf_action(self):
        # collect data and generate PDF

        pdf_data = self.collect_data()

        if not pdf_data["car_make"]:
            self.status_label.configure(text="Заполните Марку/Модель.", text_color="red")
            return

        initial_file = f"{pdf_data['car_make']}-{pdf_data['module_no']}_инструкция.pdf"
        output_filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=initial_file,
            title="Сохранить PDF-инструкцию как",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
        )

        if not output_filename:
            self.status_label.configure(text="Сохранение PDF отменено.", text_color="gray")
            return

        self.status_label.configure(text="Генерация PDF...", text_color="blue")
        self.update()

        success = create_instruction_pdf_advanced(output_filename, pdf_data, self.image_paths)

        if success:
            self.status_label.configure(text=f"Успешно! Сохранено как: {os.path.basename(output_filename)}",
                                        text_color="green")
        else:
            self.status_label.configure(text="ОШИБКА генерации PDF. Проверьте консоль.", text_color="red")


if __name__ == "__main__":
    app = App()
    app.mainloop()