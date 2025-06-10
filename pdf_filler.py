import pikepdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject
import os

def fill_page1_only(template_path: str, output_path: str, child_info: dict):
    """
    Decrypt the PDF, fill only page 1 fields (Vornamen, Nachname, etc.) from child_info,
    then write out the combined PDF.
    """
    decrypted_temp_path = "decrypted_temp.pdf" # Use a unique temp name
    with pikepdf.open(template_path) as pdf:
        pdf.save(decrypted_temp_path)

    reader = PdfReader(decrypted_temp_path)
    writer = PdfWriter()

    root = reader.trailer["/Root"]
    if "/AcroForm" in root:
        writer._root_object.update({ NameObject("/AcroForm"): root["/AcroForm"] })
        writer._root_object["/AcroForm"].update({ NameObject("/NeedAppearances"): BooleanObject(True) })
    else:
        raise RuntimeError("No AcroForm in PDF")

    page1_fields = [
        "Vornamen", "Nachname",
        "Vornamen bei Zwillingen, Drillingen, Mehrlingen",
        "Vorname01", "Vorname02", "Vorname03", "Vorname04", "Vorname05",
        "Geburtsdatum", "Ja01",
        "Ursprünglich errechneter Geburtstermin",
        "Nein", "keine", "insgesamt", "Anzahl",
        "Adresse der Behörde",
    ]

    values = {}
    for fname in page1_fields:
        val = child_info.get(fname, "")
        if isinstance(val, bool):
            val = "Ja" if val else ""
        values[fname] = str(val)

    writer.add_page(reader.pages[0])
    writer.update_page_form_field_values(writer.pages[0], values)

    for p in reader.pages[1:]:
        writer.add_page(p)

    with open(output_path, "wb") as f:
        writer.write(f)
    os.remove(decrypted_temp_path) # Clean up temp file


def fill_page2_only(template_path, output_path, applicant_info, other_parent_info):
    reader = PdfReader(template_path)
    writer = PdfWriter()

    # Add all pages from the template PDF to the writer, starting from page 0
    # This ensures page 1 (index 0) and page 2 (index 1) are present
    for page in reader.pages:
        writer.add_page(page)

    # Set NeedAppearances for the writer's root object
    orig_root = reader.trailer["/Root"]
    if "/AcroForm" in orig_root:
        writer._root_object.update({NameObject("/AcroForm"): orig_root["/AcroForm"]})
        writer._root_object["/AcroForm"].update({NameObject("/NeedAppearances"): BooleanObject(True)})
    else:
        raise RuntimeError("No /AcroForm found in source PDF.")

    # Data mapping for the Applicant (usually the first set of fields on page 2)
    # These correspond to the PDF fields without a "_2" suffix, e.g., "Vornamen_2", "Nachname_2"
    applicant_data_map = {
        "Vornamen_2": applicant_info.get('vorname', ''),
        "Nachname_2": applicant_info.get('nachname', ''),
        "Geburtsdatum_2": applicant_info.get('geburtsdatum', ''),
        # Map form values to PDF checkbox values for gender
        "weiblich": "/On" if applicant_info.get('geschlecht') == 'weiblich' else "",
        "männlich": "/On" if applicant_info.get('geschlecht') == 'männlich' else "",
        "divers": "/On" if applicant_info.get('geschlecht') == 'divers' else "",
        "ohne Angabe nach Personenstandsgesetz": "/On" if applicant_info.get('geschlecht') == 'ohne Angaben' else "",
        "SteuerIdentifikationsnummer": applicant_info.get('steuer_id', ''),
        "Straße": applicant_info.get('address_street', ''),
        "Hausnr": applicant_info.get('address_housenumber', ''),
        "Postleitzahl": applicant_info.get('address_plz', ''),
        "Ort": applicant_info.get('address_city', ''),
        "Adresszusatz": applicant_info.get('address_addon', ''),
        # Map new residency fields
        "Ja_2": "/On" if applicant_info.get('lives_in_germany') == 'yes' else "",
        "seit meiner Geburt_2": "/On" if applicant_info.get('lives_in_germany') == 'yes' and applicant_info.get('residency_start_date_type') == 'birth' else "",
        "seit_2": "/On" if applicant_info.get('lives_in_germany') == 'yes' and applicant_info.get('residency_start_date_type') == 'date' else "",
        "Datum_2": applicant_info.get('residency_start_date', ''), # This should be 'DD.MM.YYYY'
    }
    # Update page 1 fields with applicant data
    writer.update_page_form_field_values(writer.pages[1], applicant_data_map)


    # Data mapping for the Other Parent (usually the second set of fields on page 2)
    # These correspond to the PDF fields with a "_2" suffix, e.g., "Vornamen_3", "Nachname_3"
    # Only fill if other_parent_info is provided and not empty
    if other_parent_info:
        other_parent_data_map = {
            "Vornamen_3": other_parent_info.get('vorname', ''),
            "Nachname_3": other_parent_info.get('nachname', ''),
            "Geburtsdatum_3": other_parent_info.get('geburtsdatum', ''), # Ensure format
            "weiblich_2": "/On" if other_parent_info.get('geschlecht') == 'w' else "",
            "männlich_2": "/On" if other_parent_info.get('geschlecht') == 'm' else "",
            "divers_2": "/On" if other_parent_info.get('geschlecht') == 'd' else "",
            "ohne Angabe nach Personenstandsgesetz_2": "/On" if other_parent_info.get('geschlecht') == 'o' else "",
            "SteuerIdentifikationsnummer_2": other_parent_info.get('steuer_id', ''),
            # Conditional address fields for other parent
            "Ich wohne mit dem anderen Elternteil zusammen": "/On" if other_parent_info.get('same_address_as_applicant') else "",
            "Straße_2": applicant_info.get('address_street', '') if other_parent_info.get('same_address_as_applicant') else other_parent_info.get('address_street', ''),
            "Hausnr_2": applicant_info.get('address_housenumber', '') if other_parent_info.get('same_address_as_applicant') else other_parent_info.get('address_housenumber', ''),
            "Postleitzahl_2": applicant_info.get('address_plz', '') if other_parent_info.get('same_address_as_applicant') else other_parent_info.get('address_plz', ''),
            "Ort_2": applicant_info.get('address_city', '') if other_parent_info.get('same_address_as_applicant') else other_parent_info.get('address_city', ''),
            "Adresszusatz_2": applicant_info.get('address_addon', '') if other_parent_info.get('same_address_as_applicant') else other_parent_info.get('address_addon', ''),
            # Add other other_parent-related fields from Page 2 if any, for example:
            "Ja_3": "", # Adjust if needed
            "seit meiner Geburt_3": "",
            "seit_3": "",
            "Datum_3": "",
        }
        writer.update_page_form_field_values(writer.pages[1], other_parent_data_map)

    # Write out final PDF
    with open(output_path, "wb") as f_out:
        writer.write(f_out)
    print(f"Page 2 filled and saved to: {output_path}")
