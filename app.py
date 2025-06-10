# app.py

# ─── Monkey‐patch for Flask-WTF Recaptcha on Werkzeug ≥2.3 ────────────
import werkzeug.urls
from urllib.parse import urlencode
werkzeug.urls.url_encode = staticmethod(urlencode)

# ─── Now safe to import Flask-WTF and your modules ─────────────────────
from flask import Flask, render_template, session, flash, send_file, redirect, url_for, request
from forms import (
    EligibilityForm,
    ChildInfoForm,
    ApplicantInfoForm,
    OtherParentInfoForm,
    BankInfoForm,
    ResidencyAbroadForm,
    IncomeBeforeBirthForm
)  # Import all required forms

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, BooleanField, RadioField
from wtforms.validators import DataRequired, Email, Length, Optional
from pdf_filler import fill_page1_only, fill_page2_only # your PDF helper
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Ensure upload folder exists
os.makedirs('uploads', exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def eligibility():
    form = EligibilityForm()
    if form.validate_on_submit():
        if form.citizenship.data == 'non_eu' and form.residence_permit.data == 'no':
            flash('Nicht-EU Staatsangehörige benötigen eine gültige Aufenthaltserlaubnis.', 'danger')
            return render_template('eligibility.html', form=form)

        if form.lives_with_child.data == 'no' or form.cares_for_child.data == 'no':
            flash('Sie müssen mit dem Kind im Haushalt leben und es persönlich betreuen.', 'danger')
            return render_template('eligibility.html', form=form)

        if form.plans_to_work_more_than_32h.data == 'yes':
            flash('Sie dürfen nicht mehr als 32 Stunden pro Woche arbeiten.', 'danger')
            return render_template('eligibility.html', form=form)

        session['eligibility'] = {
            'citizenship': form.citizenship.data,
            'residence_permit': form.residence_permit.data,
            'lives_with_child': form.lives_with_child.data,
            'cares_for_child': form.cares_for_child.data,
            'max_work_hours': form.plans_to_work_more_than_32h.data
        }
        return redirect(url_for('child_info'))
    return render_template('eligibility.html', form=form)


@app.route('/child', methods=['GET', 'POST'])
def child_info():
    form = ChildInfoForm()
    if form.validate_on_submit():
        child = {
            'is_born': form.is_born.data,
            'vorname': form.vorname.data or "",
            'nachname': form.nachname.data or "",
            'geburtsdatum': form.geburtsdatum.data.strftime('%d.%m.%Y') if form.geburtsdatum.data else "",
            'fruehgeboren': form.fruehgeboren.data or False,
            'due_date': form.due_date.data.strftime('%d.%m.%Y') if form.due_date.data else "",
            'behinderung': form.behinderung.data or False,
            'multiple_births': form.multiple_births.data or "1",
            'multi_name_1': form.multi_name_1.data or "",
            'multi_name_2': form.multi_name_2.data or "",
            'multi_name_3': form.multi_name_3.data or "",
            'multi_name_4': form.multi_name_4.data or "",
        }
        session['child_info'] = child

        flash("Kinderangaben wurden gespeichert!", "success")
        
        return redirect(url_for('applicant_info'))

    return render_template('child_info.html', form=form)

# app.py (within applicant_info route)
@app.route('/applicant', methods=['GET', 'POST'])
def applicant_info():
    form = ApplicantInfoForm()
    if form.validate_on_submit():
        session['applicant_info'] = {
            'vorname': form.vorname.data,
            'nachname': form.nachname.data,
            'geburtsdatum': form.geburtsdatum.data.strftime('%Y-%m-%d'),
            'geschlecht': form.geschlecht.data,
            'steuer_id': form.steuer_id.data,
            'address_street': form.strasse.data,
            'address_housenumber': form.hausnummer.data,
            'address_addon': form.adresszusatz.data,
            'address_plz': form.plz.data,
            'address_city': form.wohnort.data,
            'email': form.email.data,
            'telefon': form.telefon.data,
            'other_parent_status': form.other_parent_status.data,
            'lives_in_germany': form.lives_in_germany.data,
            'residency_start_date_type': form.residency_start_date_type.data,
            'residency_start_date': form.residency_start_date.data.strftime('%d.%m.%Y') if form.residency_start_date.data else "",
        }

        # Conditional redirection based on residency status
        if form.lives_in_germany.data == 'no':
            return redirect(url_for('residency_abroad')) # NEW: Redirect to foreign residency questions
        elif form.other_parent_status.data == 'both':
            return redirect(url_for('other_parent_info'))
        else:
            return redirect(url_for('income_before_birth'))
    return render_template('applicant_info.html', form=form)
    
    
@app.route('/residency-abroad', methods=['GET', 'POST'])
def residency_abroad():
    form = ResidencyAbroadForm()
    if form.validate_on_submit():
        # Combine selected social security types into a string or list
        german_ss_types = []
        if form.german_ss_kranken.data: german_ss_types.append('Krankenversicherung')
        if form.german_ss_pflege.data: german_ss_types.append('Pflegeversicherung')
        if form.german_ss_renten.data: german_ss_types.append('Rentenversicherung')
        if form.german_ss_arbeitslosen.data: german_ss_types.append('Arbeitslosenversicherung')

        session['residency_abroad_info'] = {
            'reason_abroad': form.reason_abroad.data,
            'date_of_departure': form.date_of_departure.data.strftime('%d.%m.%Y'),
            'expected_date_of_return': form.expected_date_of_return.data.strftime('%d.%m.%Y') if form.expected_date_of_return.data else '',
            'foreign_country': form.foreign_country.data,
            'foreign_street': form.foreign_street.data,
            'foreign_housenumber': form.foreign_housenumber.data,
            'foreign_plz': form.foreign_plz.data,
            'foreign_city': form.foreign_city.data,
            'employer_abroad': form.employer_abroad.data,
            'german_social_security_abroad': form.german_social_security_abroad.data,
            'german_social_security_types': german_ss_types, # Storing as list
            'foreign_social_security': form.foreign_social_security.data,
            'foreign_social_security_details': form.foreign_social_security_details.data,
        }

        applicant_info = session.get('applicant_info', {})
        if applicant_info.get('other_parent_status') == 'both':
            return redirect(url_for('other_parent_info'))
        else:
            return redirect(url_for('income_info'))
    elif request.method == 'GET' and 'residency_abroad_info' in session:
        data = session['residency_abroad_info']
        form.reason_abroad.data = data.get('reason_abroad')
        form.date_of_departure.data = datetime.strptime(data['date_of_departure'], '%d.%m.%Y').date() if data.get('date_of_departure') else None
        form.expected_date_of_return.data = datetime.strptime(data['expected_date_of_return'], '%d.%m.%Y').date() if data.get('expected_date_of_return') else None
        form.foreign_country.data = data.get('foreign_country')
        form.foreign_street.data = data.get('foreign_street')
        form.foreign_housenumber.data = data.get('foreign_housenumber')
        form.foreign_plz.data = data.get('foreign_plz')
        form.foreign_city.data = data.get('foreign_city')
        form.employer_abroad.data = data.get('employer_abroad')
        form.german_social_security_abroad.data = data.get('german_social_security_abroad')
        # Re-set checkboxes based on stored list
        if data.get('german_social_security_types'):
            if 'Krankenversicherung' in data['german_social_security_types']: form.german_ss_kranken.data = True
            if 'Pflegeversicherung' in data['german_social_security_types']: form.german_ss_pflege.data = True
            if 'Rentenversicherung' in data['german_social_security_types']: form.german_ss_renten.data = True
            if 'Arbeitslosenversicherung' in data['german_social_security_types']: form.german_ss_arbeitslosen.data = True
        form.foreign_social_security.data = data.get('foreign_social_security')
        form.foreign_social_security_details.data = data.get('foreign_social_security_details')

    return render_template('residency_abroad.html', form=form)




@app.route('/other-parent', methods=['GET', 'POST'])
def other_parent_info():
    applicant_data = session.get('applicant_info', {})
    if not applicant_data or applicant_data.get('other_parent_status') != 'both':
        return redirect(url_for('income_info'))

    form = OtherParentInfoForm()
    if form.validate_on_submit():
        session['other_parent_info'] = {
            'vorname': form.vorname.data,
            'nachname': form.nachname.data,
            'geburtsdatum': form.geburtsdatum.data.strftime('%Y-%m-%d'),
            'geschlecht': form.geschlecht.data,
            'steuer_id': form.steuer_id.data,
            'email': form.email.data,
            'telefon': form.telefon.data,
            'same_address_as_applicant': form.same_address_as_applicant.data # Add this field to your form
        }
        if not form.same_address_as_applicant.data:
            session['other_parent_info'].update({
                'address_street': form.strasse.data,
                'address_plz': form.plz.data,
                'address_city': form.wohnort.data,
                'address_housenumber': form.housenumber.data, # Assuming a housenumber field
                'address_addon': form.address_addon.data # Assuming an address_addon field
            })
        return redirect(url_for('income_info'))

    return render_template('other_parent_info.html', form=form)

@app.route('/income', methods=['GET'])
def income_info():
    # Placeholder for income information page
    # You would typically have a form here as well, and upon submission,
    # redirect to the next step, which would be the bank info.
    return redirect(url_for('bank_info')) # Redirect to bank_info as the next step

@app.route('/bank', methods=['GET', 'POST'])
def bank_info():
    form = BankInfoForm()
    if form.validate_on_submit():
        # Save bank data to session
        session['bank_info'] = { # Changed from bank_data to bank_info for consistency
            'iban': form.iban.data,
            'bic': form.bic.data
        }
        flash('Bankdaten erfolgreich gespeichert!', 'success')
        # Instead of generating PDF here, redirect to the summary page
        return redirect(url_for('summary_page'))
    return render_template('bank_info.html', form=form)


# New route for the summary page
@app.route('/summary')
def summary_page():
    # You can pass session data to the summary template if you want to display a review
    return render_template('summary.html')


@app.route('/generate-pdf')
def generate_pdf():
    child_info = session.get('child_info', {})
    applicant_info = session.get('applicant_info', {})
    other_parent_info = session.get('other_parent_info', {})
    bank_info = session.get('bank_info', {}) # Retrieve bank info from session
    residency_abroad_info = session.get('residency_abroad_info', {}) # Retrieve new session data


    # Check if essential data is present before attempting to generate PDF
    if not child_info or not applicant_info or not bank_info:
        flash("Einige erforderliche Angaben fehlen. Bitte füllen Sie alle Formulare aus.", "danger")
        return redirect(url_for('summary_page')) # Redirect to summary or an appropriate page

    template_pdf = "Berlin-antrag-auf-elterngeld.pdf" #
    temp_page1_output = "temp_page1_filled.pdf"
    final_output_pdf = "Elterngeld_Antrag_Filled.pdf"

    try:
        # Fill Page 1
        pdf_page1_data = {
            "Vornamen": child_info.get('vorname', ''),
            "Nachname": child_info.get('nachname', ''),
            "Vornamen bei Zwillingen, Drillingen, Mehrlingen": "", # Assuming this is filled by multi_name fields
            "Vorname01": child_info.get('multi_name_1', ''),
            "Vorname02": child_info.get('multi_name_2', ''),
            "Vorname03": child_info.get('multi_name_3', ''),
            "Vorname04": child_info.get('multi_name_4', ''),
            "Vorname05": "", # Assuming no more than 4 multi_names in your form
            "Geburtsdatum": child_info.get('geburtsdatum', ''),
            "Ja01": ("Ja" if child_info.get('fruehgeboren') else ""),
            "Ursprünglich errechneter Geburtstermin": child_info.get('due_date', ''),
            "Nein": "", "keine": "", "insgesamt": "", "Anzahl": "", # These seem like fixed fields in the PDF template
            "Adresse der Behörde": "" # This might be filled with a fixed value or from config
        }
        fill_page1_only(
            template_path=template_pdf,
            output_path=temp_page1_output,
            child_info=pdf_page1_data
        )

        # Fill Page 2 using the PDF that now has page 1 filled
        fill_page2_only(
            template_path=temp_page1_output,
            output_path=final_output_pdf,
            applicant_info=applicant_info,
            other_parent_info=other_parent_info
        )
        
        # Clean up temporary file
        if os.path.exists(temp_page1_output):
            os.remove(temp_page1_output)

        return send_file(
            final_output_pdf,
            as_attachment=True,
            download_name="Elterngeld_Antrag_Filled.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        flash(f"Fehler beim Generieren des PDFs: {e}", "danger")
        app.logger.error(f"PDF Generation Error: {e}")
        return redirect(url_for('summary_page')) # Redirect to summary page on error
        
        
# --- NEW ROUTE: Income Before Birth ---
@app.route('/income-before-birth', methods=['GET', 'POST'])
def income_before_birth():
    form = IncomeBeforeBirthForm()
    if form.validate_on_submit():
        income_data = {
            'assessment_period_type': form.assessment_period_type.data,
            'other_assessment_reason': form.other_assessment_reason.data,
            'other_assessment_start_month': form.other_assessment_start_month.data,
            'other_assessment_start_year': form.other_assessment_start_year.data,
            'other_assessment_end_month': form.other_assessment_end_month.data,
            'other_assessment_end_year': form.other_assessment_end_year.data,
            'has_employed_income': form.has_employed_income.data,
            'employer_name': form.employer_name.data,
            'gross_income_months': [
                str(form.gross_income_month_1.data) if form.gross_income_month_1.data is not None else None,
                str(form.gross_income_month_2.data) if form.gross_income_month_2.data is not None else None,
                str(form.gross_income_month_3.data) if form.gross_income_month_3.data is not None else None,
                str(form.gross_income_month_4.data) if form.gross_income_month_4.data is not None else None,
                str(form.gross_income_month_5.data) if form.gross_income_month_5.data is not None else None,
                str(form.gross_income_month_6.data) if form.gross_income_month_6.data is not None else None,
                str(form.gross_income_month_7.data) if form.gross_income_month_7.data is not None else None,
                str(form.gross_income_month_8.data) if form.gross_income_month_8.data is not None else None,
                str(form.gross_income_month_9.data) if form.gross_income_month_9.data is not None else None,
                str(form.gross_income_month_10.data) if form.gross_income_month_10.data is not None else None,
                str(form.gross_income_month_11.data) if form.gross_income_month_11.data is not None else None,
                str(form.gross_income_month_12.data) if form.gross_income_month_12.data is not None else None,
            ],
            'has_mutterschaftsgeld': form.has_mutterschaftsgeld.data,
            'mutterschaftsgeld_amount': str(form.mutterschaftsgeld_amount.data) if form.mutterschaftsgeld_amount.data is not None else None,
            'has_krankentagegeld': form.has_krankentagegeld.data,
            'krankentagegeld_amount': str(form.krankentagegeld_amount.data) if form.krankentagegeld_amount.data is not None else None,
            'has_kurzarbeitergeld': form.has_kurzarbeitergeld.data,
            'kurzarbeitergeld_amount': str(form.kurzarbeitergeld_amount.data) if form.kurzarbeitergeld_amount.data is not None else None,
            'has_elterngeld_older_child': form.has_elterngeld_older_child.data,
            'elterngeld_older_child_amount': str(form.elterngeld_older_child_amount.data) if form.elterngeld_older_child_amount.data is not None else None,
            'has_other_income': form.has_other_income.data,
            'other_income_amount': str(form.other_income_amount.data) if form.other_income_amount.data is not None else None,
            'has_self_employed_income': form.has_self_employed_income.data,
            'self_employment_activity_type': form.self_employment_activity_type.data,
            'profit_assessment_start_month': form.profit_assessment_start_month.data,
            'profit_assessment_start_year': form.profit_assessment_start_year.data,
            'profit_assessment_end_month': form.profit_assessment_end_month.data,
            'profit_assessment_end_year': form.profit_assessment_end_year.data,
            'profit_amount': str(form.profit_amount.data) if form.profit_amount.data is not None else None,
        }
        session['income_before_birth_info'] = income_data
        return redirect(url_for('income_info')) # Redirect to the next income page (which is currently a dummy)
    elif request.method == 'GET' and 'income_before_birth_info' in session:
        data = session['income_before_birth_info']
        form.assessment_period_type.data = data.get('assessment_period_type')
        form.other_assessment_reason.data = data.get('other_assessment_reason')
        form.other_assessment_start_month.data = data.get('other_assessment_start_month')
        form.other_assessment_start_year.data = data.get('other_assessment_start_year')
        form.other_assessment_end_month.data = data.get('other_assessment_end_month')
        form.other_assessment_end_year.data = data.get('other_assessment_end_year')
        form.has_employed_income.data = data.get('has_employed_income')
        form.employer_name.data = data.get('employer_name')
        if data.get('gross_income_months'):
            if data['gross_income_months'][0] is not None: form.gross_income_month_1.data = Decimal(data['gross_income_months'][0])
            if data['gross_income_months'][1] is not None: form.gross_income_month_2.data = Decimal(data['gross_income_months'][1])
            if data['gross_income_months'][2] is not None: form.gross_income_month_3.data = Decimal(data['gross_income_months'][2])
            if data['gross_income_months'][3] is not None: form.gross_income_month_4.data = Decimal(data['gross_income_months'][3])
            if data['gross_income_months'][4] is not None: form.gross_income_month_5.data = Decimal(data['gross_income_months'][4])
            if data['gross_income_months'][5] is not None: form.gross_income_month_6.data = Decimal(data['gross_income_months'][5])
            if data['gross_income_months'][6] is not None: form.gross_income_month_7.data = Decimal(data['gross_income_months'][6])
            if data['gross_income_months'][7] is not None: form.gross_income_month_8.data = Decimal(data['gross_income_months'][7])
            if data['gross_income_months'][8] is not None: form.gross_income_month_9.data = Decimal(data['gross_income_months'][8])
            if data['gross_income_months'][9] is not None: form.gross_income_month_10.data = Decimal(data['gross_income_months'][9])
            if data['gross_income_months'][10] is not None: form.gross_income_month_11.data = Decimal(data['gross_income_months'][10])
            if data['gross_income_months'][11] is not None: form.gross_income_month_12.data = Decimal(data['gross_income_months'][11])
        form.has_mutterschaftsgeld.data = data.get('has_mutterschaftsgeld')
        form.mutterschaftsgeld_amount.data = Decimal(data['mutterschaftsgeld_amount']) if data.get('mutterschaftsgeld_amount') else None
        form.has_krankentagegeld.data = data.get('has_krankentagegeld')
        form.krankentagegeld_amount.data = Decimal(data['krankentagegeld_amount']) if data.get('krankentagegeld_amount') else None
        form.has_kurzarbeitergeld.data = data.get('has_kurzarbeitergeld')
        form.kurzarbeitergeld_amount.data = Decimal(data['kurzarbeitergeld_amount']) if data.get('kurzarbeitergeld_amount') else None
        form.has_elterngeld_older_child.data = data.get('has_elterngeld_older_child')
        form.elterngeld_older_child_amount.data = Decimal(data['elterngeld_older_child_amount']) if data.get('elterngeld_older_child_amount') else None
        form.has_other_income.data = data.get('has_other_income')
        form.other_income_amount.data = Decimal(data['other_income_amount']) if data.get('other_income_amount') else None
        form.has_self_employed_income.data = data.get('has_self_employed_income')
        form.self_employment_activity_type.data = data.get('self_employment_activity_type')
        form.profit_assessment_start_month.data = data.get('profit_assessment_start_month')
        form.profit_assessment_start_year.data = data.get('profit_assessment_start_year')
        form.profit_assessment_end_month.data = data.get('profit_assessment_end_month')
        form.profit_assessment_end_year.data = data.get('profit_assessment_end_year')
        form.profit_amount.data = Decimal(data['profit_amount']) if data.get('profit_amount') else None


    return render_template('income_before_birth.html', form=form)
    

if __name__ == '__main__':
    app.run(debug=True)
