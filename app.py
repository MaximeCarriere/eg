# app.py

from flask import Flask, render_template, redirect, url_for, session, flash
from forms import EligibilityForm, ChildInfoForm, ApplicantInfoForm, OtherParentInfoForm
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
        session['child_info'] = {
            'is_born': form.is_born.data,
            'vorname': form.vorname.data,
            'nachname': form.nachname.data,
            'geburtsdatum': form.geburtsdatum.data.strftime('%Y-%m-%d') if form.geburtsdatum.data else None,
            'fruehgeboren': form.fruehgeboren.data,
            'behinderung': form.behinderung.data,
            'multiple_births': form.multiple_births.data,
        }
        return redirect(url_for('applicant_info'))
    return render_template('child_info.html', form=form)

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
            'address_plz': form.plz.data,
            'address_city': form.wohnort.data,
            'email': form.email.data,
            'telefon': form.telefon.data,
            'other_parent_status': form.other_parent_status.data,
        }

        # Decide where to go next:
        if form.other_parent_status.data == 'both':
            return redirect(url_for('other_parent_info'))
        else:
            # Skip Step 3 if single or other already applied.
            # For now, redirect to a placeholder "income" route.
            return redirect(url_for('income_info'))

    return render_template('applicant_info.html', form=form)

@app.route('/other-parent', methods=['GET', 'POST'])
def other_parent_info():
    """
    Step 3: Collect the other parent's details if both parents apply.
    """
    # If applicant indicated they do NOT need this step, redirect immediately:
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
            'telefon': form.telefon.data
        }
        return redirect(url_for('income_info'))

    return render_template('other_parent_info.html', form=form)

@app.route('/income', methods=['GET'])
def income_info():
    """
    Placeholder for Step 4: Einkommen.
    For now, just show a simple message.
    """
    return "<h3>Step 4: Income information (not yet implemented)</h3>"

if __name__ == '__main__':
    app.run(debug=True)
