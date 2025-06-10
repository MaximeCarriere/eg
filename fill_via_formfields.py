# fill_via_formfields.py

import pikepdf
from PyPDF2 import PdfReader, PdfWriter

def fill_elterngeld_acroform(template_path: str, output_path: str, data: dict):
    """
    1. Decrypt the Berlin form.
    2. Use PdfReader to list all AcroForm fields.
    3. Build a values_to_set dict mapping each field name → string/“Ja”/“”.
    4. Clone into a PdfWriter, call update_page_form_field_values() per page,
       and save.
    """

    # ─── Step 1: Decrypt into a temp file ─────────────────────────────────────
    temp_decrypted = "decrypted_elterngeld.pdf"
    with pikepdf.open(template_path) as pdf:
        pdf.save(temp_decrypted)

    # ─── Step 2: Read fields with PdfReader ───────────────────────────────────
    reader = PdfReader(temp_decrypted)
    fields = reader.get_fields() or {}
    # fields is a dict: { fieldname → FieldObject }

    # ─── Step 3: Build values_to_set mapping ──────────────────────────────────
    # (Use your exact field_map from earlier.)
    field_map = {
        # Example mappings (add every field you need):
        'Vornamen':      ('child_info', 'vorname'),
        'Nachname':      ('child_info', 'nachname'),
        'Geburtsdatum':  ('child_info', 'geburtsdatum'),
        'Ja01':          ('child_info', 'fruehgeboren'),
        'Nein':          ('child_info', 'fruehgeboren'),
        # … fill out all your fields exactly as they appear …
        'Vornamen_2':    ('applicant_info', 'vorname'),
        'Nachname_2':    ('applicant_info', 'nachname'),
        'Geburtsdatum_2':('applicant_info', 'geburtsdatum'),
        'weiblich':      ('applicant_info', 'geschlecht'),
        'männlich':      ('applicant_info', 'geschlecht'),
        'divers':        ('applicant_info', 'geschlecht'),
        'SteuerIdentifikationsnummer': ('applicant_info', 'steuer_id'),
        'Straße':        ('applicant_info', 'address_street'),
        'Hausnr':        ('applicant_info', 'address_street'),
        'Postleitzahl':  ('applicant_info', 'address_plz'),
        'Ort':           ('applicant_info', 'address_city'),
        'EMailAdresse':  ('applicant_info', 'email'),
        'Telefonnummer Angabe freiwillig': ('applicant_info', 'telefon'),
        # … Other Parent Info, Income Info, Bank Info fields …
        'Kontonummer IBAN': ('bank_info', 'iban'),
        'BIC':              ('bank_info', 'bic'),
        'Vornamen_7':       ('bank_info', 'account_holder'),
        'Ja_S23-1':         ('bank_info', 'own_account'),
        'Nein, das ist das Konto des anderen Eltenteils; dessen Name ist in diesem Formular eingetragen_1':
                              ('bank_info', 'own_account'),
        'Nein, das ist das Konto von_1': ('bank_info', 'own_account'),
    }

    values_to_set = {}
    for fieldname, (section_key, data_key) in field_map.items():
        if fieldname not in fields:
            # if the PDF doesn't actually have that field name, skip it:
            continue

        section = data.get(section_key, {})
        raw = section.get(data_key, "")
        if isinstance(raw, bool):
            # Checkboxes / radios: set “Ja” if True, blank if False
            values_to_set[fieldname] = "Ja" if raw else ""
        else:
            # Text fields
            values_to_set[fieldname] = str(raw)

    # ─── Step 4: Clone to PdfWriter and fill values ───────────────────────────
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)  # copy pages + /AcroForm

    # Now write those values into each page’s form:
    for page in writer.pages:
        writer.update_page_form_field_values(page, values_to_set)

    # ─── Step 5: Save out the filled PDF ──────────────────────────────────────
    with open(output_path, "wb") as out_f:
        writer.write(out_f)
