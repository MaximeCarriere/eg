# pdf_fill.py
from pdfrw import PdfReader, PdfWriter, PageMerge, PdfDict

# Mapping: interne Feldnamen im PDF → Schlüssel in unserer session-Datenstruktur
PDF_FIELD_MAP = {
    # Abschnitt „1. Angaben zum Kind“
    'Kind_Vorname':       ('child_info', 'vorname'),
    'Kind_Nachname':      ('child_info', 'nachname'),
    'Kind_Geburtsdatum':  ('child_info', 'geburtsdatum'),
    'Kind_Fruehgeboren':  ('child_info', 'fruehgeboren'),
    'Kind_Behinderung':   ('child_info', 'behinderung'),
    'Kind_Mehrlinge':     ('child_info', 'multiple_births'),
    # Abschnitt „2. Angaben zu den Eltern – Antragsteller“
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
    # Abschnitt „2. Angaben zu den Eltern – anderer Elternteil“
    'OEP_Vorname':        ('other_parent_info', 'vorname'),
    'OEP_Nachname':       ('other_parent_info', 'nachname'),
    'OEP_Geburtsdatum':   ('other_parent_info', 'geburtsdatum'),
    'OEP_Geschlecht':     ('other_parent_info', 'geschlecht'),
    'OEP_SteuerID':       ('other_parent_info', 'steuer_id'),
    'OEP_Email':          ('other_parent_info', 'email'),
    'OEP_Telefon':        ('other_parent_info', 'telefon'),
    # Abschnitt „6. Vor der Geburt: Einkommen“ (vereinfacht)
    'Income_Art':         ('income_info', 'income_type'),
    'Income_Betrag':      ('income_info', 'income_amount'),
    'Income_Ersatz':      ('income_info', 'received_benefits'),
    'Income_Details':     ('income_info', 'benefits_details'),
    # Abschnitt „5. Krankenversicherung“ (optional, falls implementiert)
    # …und so weiter, je nachdem, welche Formularfelder Sie befüllen wollen…
    # Abschnitt „Bankverbindung“
    'Bank_IBAN':          ('bank_info', 'iban'),
    'Bank_BIC':           ('bank_info', 'bic'),
    'Bank_Kontoinh':      ('bank_info', 'account_holder'),
}

def fill_elterngeld_form(template_path: str, output_path: str, session_data: dict):
    """
    Liest die PDF-Vorlage ein, befüllt alle in PDF_FIELD_MAP hinterlegten Felder
    mit Werten aus session_data und schreibt das Ergebnis unter output_path.
    """
    # PDF laden (ohne zu verändern)
    template_pdf = PdfReader(template_path)
    annotations = []

    # In jeder Seite nach Formularfeldern (Annotations) suchen
    for page in template_pdf.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                field = annot.get('/T')  # interner Feldname im PDF
                if field:
                    field_name = field[1:-1]  # remove parentheses
                    if field_name in PDF_FIELD_MAP:
                        section_key, data_key = PDF_FIELD_MAP[field_name]
                        # session_data[section_key][data_key] liefert den Wert (z.B. "Max")
                        value = session_data.get(section_key, {}).get(data_key, '')
                        # Checkbox‐Felder (Ja/Nein) müssen als "/Yes" oder "/Off" gesetzt werden:
                        if annot['/FT'] == '/Btn':  # Checkbox / RadioButton
                            # Wir nehmen an: Wenn value truthy und 'yes' / True → "/Yes", sonst "/Off"
                            if value in (True, 'yes', 'Ja', 'ja', 'True'):
                                annot.update(
                                    PdfDict(V='/Yes', AS=PdfDict('/Yes'))
                                )
                            else:
                                annot.update(
                                    PdfDict(V='/Off', AS=PdfDict('/Off'))
                                )
                        else:
                            # Textfeld oder Datum: Wir setzen /V und /DV (Default Value)
                            annot.update(
                                PdfDict(V=f"{value}", DV=f"{value}")
                            )
                        annotations.append(field_name)

    # Explizit alle Felder auf „read-only“ setzen, damit der Nutzer im End-PDF nicht mehr editieren kann
    if template_pdf.Root.AcroForm:
        template_pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfDict(True)))
        for field in template_pdf.Root.AcroForm.Fields:
            field.update(PdfDict(Ff=1))  # FF=1 → read-only

    # Fertiges PDF schreiben
    PdfWriter().write(output_path, template_pdf)
    return annotations
