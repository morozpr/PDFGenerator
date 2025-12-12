# 🛠️ ReportLab PDF Instruction Generator (GUI)

This project is a Python desktop application with a graphical user interface (GUI), built using CustomTkinter. Its core function is to facilitate the rapid and standardized creation of multi-page PDF instructions, technical manuals, or data sheets featuring a fixed header, image grid layouts, and structured text formatting.

The implementation focuses on precise layout control using the ReportLab library, including custom font handling for Cyrillic support and structured spacing management.

## ✨ Key Features

* **GUI Interface:** User-friendly data entry.
* **Data Management:** Support for saving and loading instruction data in JSON format, enabling easy revision and backup.
* **ReportLab Layout:** Generates a two-page PDF with layout components.

## 🚀 Requirements and Setup

To run this project, you will need Python 3.x and the following libraries.

### Installation of Dependencies

```bash
pip install customtkinter reportlab tkcalendar

Important Note: For proper Cyrillic character support within the generated PDF (ReportLab), the following font files must be available in the directory where the script is executed:

    arial.ttf

    arialbd.ttf (for bold text)
```

## 📂 Structure of the Generated PDF

# The final document is structured across two pages with mandatory elements:
Page 1

    Header (Top): A detailed table containing car/module specifics, revision, and program version number.

    Body Content: Heading and formatted text for connection diagram and essential notes.

    Image Grid: Selected photographs illustrating the setup.

    Footer (Bottom): Generation date, user email, and page numbering.

Page 2

    Header (Top): Repeat of the detailed header table.

    Body Content: Heading and formatted text for detailed description and indicators.

    Footer (Bottom): Repeat of the footer details and page numbering.
