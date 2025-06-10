# fill_overlay.py

import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter
import pikepdf

def overlay_fill(template_path: str, output_path: str, data: dict):
    """
    1. Decrypt the protected Berlin Elterngeld PDF (template_path) into 'decrypted_elterngeld.pdf'
    2. Create an in-memory overlay PDF that draws only text at fixed coordinates.
    3. Merge overlay onto each decrypted page and write final PDF to output_path.
    """

    # ─── Step 1: Decrypt into a relative file ────────────────────────────
    decrypted_path = "decrypted_elterngeld.pdf"
    with pikepdf.open(template_path) as pdf:
        pdf.save(decrypted_path)

    reader = PdfReader(decrypted_path)
    num_pages = len(reader.pages)

    # ─── Step 2: Build in-memory overlay PDF ────────────────────────────
    overlay_buffer = io.BytesIO()
    overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=A4)

    FeldPositionen = {
        'Kind_Vorname':      (0, 150, 710, 10),
        'Kind_Nachname':     (0, 350, 710, 10),
        'Kind_Geburtsdatum': (0, 150, 690, 10),
        'Kind_Fruehgeboren': (0, 150, 670, 8),
        'Kind_Behinderung':  (0, 150, 655, 8),
        'Kind_Mehrlinge':    (0, 350, 670, 10),

        'Antr_Vorname':      (1, 150, 750, 10),
        'Antr_Nachname':     (1, 350, 750, 10),
        'Antr_Geburtsdatum': (1, 150, 730, 10),
        'Antr_Geschlecht':   (1, 150, 710, 10),
        'Antr_SteuerID':     (1, 350, 710, 10),
        'Antr_Strasse':      (1, 150, 690, 10),
        'Antr_PLZ':          (1, 150, 670, 10),
        'Antr_Ort':          (1, 350, 670, 10),
        'Antr_Email':        (1, 150, 650, 10),
        'Antr_Telefon':      (1, 350, 650, 10),
        'Antr_Status':       (1, 150, 630, 10),

        'OEP_Vorname':       (2, 150, 750, 10),
        'OEP_Nachname':      (2, 350, 750, 10),
        'OEP_Geburtsdatum':  (2, 150, 730, 10),
        'OEP_Geschlecht':    (2, 150, 710, 10),
        'OEP_SteuerID':      (2, 350, 710, 10),
        'OEP_Email':         (2, 150, 690, 10),
        'OEP_Telefon':       (2, 350, 690, 10),

        'Income_Art':        (3, 150, 750, 10),
        'Income_Betrag':     (3, 350, 750, 10),
        'Income_Ersatz':     (3, 150, 730, 10),
        'Income_Details':    (3, 150, 710, 10),

        'Bank_IBAN':         (4, 150, 600, 10),
        'Bank_BIC':          (4, 350, 600, 10),
        'Bank_Kontoinh':     (4, 150, 580, 10),
    }

    for page_num in range(num_pages):
        for field_name, (seite, x, y, font_size) in FeldPositionen.items():
            if seite != page_num:
                continue

            mapping = {
                'Kind_Vorname':       ('child_info', 'vorname'),
                'Kind_Nachname':      ('child_info', 'nachname'),
                'Kind_Geburtsdatum':  ('child_info', 'geburtsdatum'),
                'Kind_Fruehgeboren':  ('child_info', 'fruehgeboren'),
                'Kind_Behinderung':   ('child_info', 'behinderung'),
                'Kind_Mehrlinge':     ('child_info', 'multiple_births'),

                'Antr_Vorname':       ('applicant_info', 'vorname'),
                'Antr_Nachname':      ('applicant_info', 'nachname'),
                'Antr_Geburtsdatum':  ('applicant_info', 'geburtsdatum'),
                'Antr_Geschlecht':    ('applicant_info', 'geschlecht'),
                'Antr_SteuerID':      ('applicant_info', 'steuer_id'),
                'Antr_Strasse':       ('applicant_info', 'address_street'),
                'Antr_PLZ':           ('applicant_info', 'address_plz'),
                'Antr_Ort':           ('applicant_info', 'address_city'),
                'Antr_Email':         ('applicant_info', 'email'),
                'Antr_Telefon':       ('applicant_info', 'telefon'),
                'Antr_Status':        ('applicant_info', 'other_parent_status'),

                'OEP_Vorname':        ('other_parent_info', 'vorname'),
                'OEP_Nachname':       ('other_parent_info', 'nachname'),
                'OEP_Geburtsdatum':   ('other_parent_info', 'geburtsdatum'),
                'OEP_Geschlecht':     ('other_parent_info', 'geschlecht'),
                'OEP_SteuerID':       ('other_parent_info', 'steuer_id'),
                'OEP_Email':          ('other_parent_info', 'email'),
                'OEP_Telefon':        ('other_parent_info', 'telefon'),

                'Income_Art':         ('income_info', 'income_type'),
                'Income_Betrag':      ('income_info', 'income_amount'),
                'Income_Ersatz':      ('income_info', 'received_benefits'),
                'Income_Details':     ('income_info', 'benefits_details'),

                'Bank_IBAN':          ('bank_info', 'iban'),
                'Bank_BIC':           ('bank_info', 'bic'),
                'Bank_Kontoinh':      ('bank_info', 'account_holder'),
            }

            section_key, data_key = mapping[field_name]
            value = data.get(section_key, {}).get(data_key, '')

            if isinstance(value, bool):
                value = 'Ja' if value else 'Nein'

            overlay_canvas.setFont("Helvetica", font_size)
            overlay_canvas.drawString(x, y, str(value))

        overlay_canvas.showPage()

    overlay_canvas.save()
    overlay_buffer.seek(0)

    overlay_reader = PdfReader(overlay_buffer)
    writer = PdfWriter()

    for page_num in range(num_pages):
        original_page = reader.pages[page_num]
        overlay_page = overlay_reader.pages[page_num]
        original_page.merge_page(overlay_page)
        writer.add_page(original_page)

    with open(output_path, 'wb') as f:
        writer.write(f)
