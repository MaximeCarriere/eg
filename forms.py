# forms.py

# ─── Monkey‐patch for Flask-WTF / Werkzeug ≥2.3 compatibility ────────────
import werkzeug.urls
from urllib.parse import urlencode

# now attach it
werkzeug.urls.url_encode = staticmethod(urlencode)

# ─── Rest of your imports ───────────────────────────────────────────────
from datetime import date, timedelta
from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, BooleanField, RadioField,
    SelectField, SubmitField, EmailField, TextAreaField, DecimalField
)
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError, NumberRange, Regexp # <--- Add Regexp
# ─────────────────────────────────────────────────────────────────────


class ChildInfoForm(FlaskForm):
    # This field matches the template's radio field structure
    is_born = RadioField(
        'Ist das Kind bereits geboren?',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired(message="Wählen Sie Ja oder Nein")],
        default='yes'
    )
    
    # Basic child information fields
    vorname = StringField('Vorname des Kindes', validators=[Optional()])
    nachname = StringField('Nachname des Kindes', validators=[Optional()])
    geburtsdatum = DateField(
        'Geburtsdatum des Kindes',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={"type": "date"}
    )
    
    # Early birth information
    fruehgeboren = BooleanField('Frühgeboren (mind. 6 Wochen vor Termin)')
    due_date = DateField(
        'Ursprünglich errechneter Geburtstermin',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={"type": "date"}
    )
    
    # Disability checkbox
    behinderung = BooleanField('Kind hat Behinderung')
    
    # Multiple births
    multiple_births = SelectField(
        'Wie viele Kinder insgesamt geboren?',
        choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5 oder mehr')],
        validators=[Optional()],
        default='1'
    )
    
    # Additional names for multiple births
    multi_name_1 = StringField('Vorname zweites Kind', validators=[Optional()])
    multi_name_2 = StringField('Vorname drittes Kind', validators=[Optional()])
    multi_name_3 = StringField('Vorname viertes Kind', validators=[Optional()])
    multi_name_4 = StringField('Vorname fünftes Kind', validators=[Optional()])

    submit = SubmitField('Weiter')

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        # Only validate if child is born
        if self.is_born.data == 'yes':
            today = date.today()
            
            # Name validation
            if not self.vorname.data or not self.vorname.data.strip():
                self.vorname.errors.append('Vorname ist erforderlich wenn das Kind geboren ist')
                return False
                
            if not self.nachname.data or not self.nachname.data.strip():
                self.nachname.errors.append('Nachname ist erforderlich wenn das Kind geboren ist')
                return False

            # Birth date validation
            if not self.geburtsdatum.data:
                self.geburtsdatum.errors.append('Geburtsdatum ist erforderlich wenn das Kind geboren ist')
                return False

            if self.geburtsdatum.data > today:
                self.geburtsdatum.errors.append('Geburtsdatum kann nicht in der Zukunft liegen')
                return False

            # Early birth validation - ADD THIS
            if self.fruehgeboren.data and not self.due_date.data:
                self.due_date.errors.append('Ursprünglicher Geburtstermin ist erforderlich bei Frühgeburt')
                return False

            if self.due_date.data and self.due_date.data <= self.geburtsdatum.data:
                self.due_date.errors.append('Ursprünglicher Termin muss nach dem tatsächlichen Geburtsdatum liegen')
                return False

            # Check if application is within 3 months of birth (warning, not error)
            if self.geburtsdatum.data < today - timedelta(days=90):
                # Don't return False for this - it's just a warning
                pass

            # Multiple births validation
            if not self.multiple_births.data:
                self.multiple_births.errors.append('Bitte Anzahl Kinder angeben')
                return False

        return True


class EligibilityForm(FlaskForm):
    citizenship = SelectField(
        'Staatsangehörigkeit',
        choices=[
            ('german', 'Deutsche'),
            ('eu', 'EU/EWR/Schweiz'),
            ('non_eu', 'Nicht-EU')
        ],
        validators=[DataRequired(message="Pflichtfeld")]
    )

    residence_permit = RadioField(
        'Gültiger Aufenthaltstitel, der Erwerbstätigkeit erlaubt:',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired(message="Wählen Sie Ja oder Nein")],
        default='no'
    )

    lives_with_child = RadioField(
        'Lebe ich mit dem Kind im selben Haushalt?',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired(message="Wählen Sie Ja oder Nein")],
        default='no'
    )

    cares_for_child = RadioField(
        'Betreue ich das Kind persönlich und erziehe es?',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired(message="Wählen Sie Ja oder Nein")],
        default='no'
    )

    plans_to_work_more_than_32h = RadioField(
        'Werde ich während des Elterngeldbezugs mehr als 32 Std/Woche arbeiten?',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired(message="Wählen Sie Ja oder Nein")],
        default='no'
    )

    submit = SubmitField('Weiter')


# forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, SelectField, RadioField, TextAreaField, # Keep TextAreaField
    BooleanField, # Import BooleanField for checkboxes
    SubmitField # Ensure SubmitField is imported if not already
)
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from datetime import date

# Define the form classes as provided in the problem description
# (ApplicantInfoForm remains largely unchanged, just ensuring it's shown for context)
class ApplicantInfoForm(FlaskForm):
    # ... (Your existing ApplicantInfoForm fields) ...
    vorname = StringField('Vorname', validators=[DataRequired(message="Pflichtfeld")])
    nachname = StringField('Nachname', validators=[DataRequired(message="Pflichtfeld")])
    geburtsdatum = DateField(
        'Geburtsdatum',
        format='%Y-%m-%d',
        validators=[DataRequired(message="Pflichtfeld")],
        render_kw={"type": "date"}
    )
    geschlecht = SelectField(
        'Geschlecht',
        choices=[
            ('weiblich','weiblich'),
            ('männlich','männlich'),
            ('divers','divers'),
            ('ohne Angaben','ohne Angabe')
        ],
        validators=[DataRequired(message="Pflichtfeld")]
    )
    steuer_id = StringField(
        'Steuer-Identifikationsnummer',
        validators=[DataRequired(message="Pflichtfeld"), Length(min=11, max=11, message="11-stellige ID erforderlich")]
    )
    strasse = StringField('Straße', validators=[DataRequired(message="Pflichtfeld")])
    hausnummer = StringField('Hausnummer', validators=[DataRequired(message="Pflichtfeld")])
    adresszusatz = StringField('Adresszusatz (optional)', validators=[Optional()])

    plz = StringField('Postleitzahl', validators=[DataRequired(message="Pflichtfeld"), Length(min=5, max=5, message="5-stellige PLZ erforderlich")])
    wohnort = StringField('Ort', validators=[DataRequired(message="Pflichtfeld")])

    email = EmailField('E-Mail (optional)', validators=[Optional(), Email(message="Ungültige E-Mail")])
    telefon = StringField('Telefonnummer (optional)', validators=[Optional()])

    other_parent_status = RadioField(
        'Wer stellt den Antrag?',
        choices=[
            ('both', 'Beide Elternteile'),
            ('solo', 'Nur ich (alleinerziehend)'),
            ('other_applied', 'Anderer Elternteil hat bereits Elterngeld beantragt'),
        ],
        validators=[DataRequired(message="Wählen Sie eine Option")],
        default='both'
    )

    lives_in_germany = RadioField(
        'Leben Sie in Deutschland? Haben Sie hier zum Beispiel Ihren dauerhaften Wohnsitz?', # Exact phrasing from PDF
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired("Bitte wählen Sie eine Option.")],
        default='yes'
    )
    residency_start_date_type = RadioField(
        'Wohnsitz/gewöhnlicher Aufenthalt in Deutschland seit:',
        choices=[
            ('birth', 'Geburt'),
            ('date', 'Datum')
        ],
        validators=[Optional()]
    )
    residency_start_date = DateField(
        'Datum (TT.MM.JJJJ)',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={"type": "date"}
    )

    submit = SubmitField('Weiter')

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        today = date.today()
        bd = self.geburtsdatum.data
        if bd > today:
            self.geburtsdatum.errors.append('Geburtsdatum kann nicht in der Zukunft liegen.')
            return False
        sixteen_years_ago = today.replace(year=today.year - 16)
        if bd > sixteen_years_ago:
            self.geburtsdatum.errors.append('Der Antragsteller muss mindestens 16 Jahre alt sein.')
            return False

        if not self.steuer_id.data.isdigit():
            self.steuer_id.errors.append('Steuer-ID muss nur aus Ziffern bestehen.')
            return False
        
        if self.lives_in_germany.data == 'yes':
            if not self.residency_start_date_type.data:
                self.residency_start_date_type.errors.append('Bitte wählen Sie, seit wann Sie Ihren Wohnsitz in Deutschland haben.')
                return False

            if self.residency_start_date_type.data == 'date':
                if not self.residency_start_date.data:
                    self.residency_start_date.errors.append('Bitte geben Sie das Startdatum Ihres Wohnsitzes an.')
                    return False
                if self.residency_start_date.data > today:
                    self.residency_start_date.errors.append('Das Startdatum kann nicht in der Zukunft liegen.')
                    return False
        
        return True


class ResidencyAbroadForm(FlaskForm):
    reason_abroad = TextAreaField(
        'Warum halten Sie sich im Ausland auf? (z. B. Entsendung, Studium, dauerhafter Wohnsitz)',
        validators=[DataRequired(message="Bitte geben Sie einen Grund an.")]
    )
    date_of_departure = DateField(
        'Datum der Ausreise',
        format='%Y-%m-%d',
        validators=[DataRequired(message="Pflichtfeld")],
        render_kw={"type": "date"}
    )
    expected_date_of_return = DateField(
        'Voraussichtliches Datum der Rückreise',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={"type": "date"}
    )
    foreign_country = StringField('Land', validators=[DataRequired(message="Pflichtfeld")])
    foreign_street = StringField('Straße', validators=[DataRequired(message="Pflichtfeld")])
    foreign_housenumber = StringField('Hausnummer', validators=[DataRequired(message="Pflichtfeld")])
    foreign_plz = StringField('Postleitzahl (falls zutreffend)', validators=[Optional()])
    foreign_city = StringField('Ort', validators=[DataRequired(message="Pflichtfeld")])

    employer_abroad = TextAreaField(
        'Genaue Anschrift des Arbeitgebers im Ausland (Name, Straße, Ort, Land)',
        validators=[Optional()]
    )

    german_social_security_abroad = RadioField(
        'Besteht im Ausland eine gesetzliche Kranken-, Pflege-, Renten- oder Arbeitslosenversicherung in Deutschland?',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired("Bitte wählen Sie eine Option.")],
        default='no'
    )
    german_social_security_types = StringField( # Will handle this as a comma-separated list or similar
        'Welche der oben genannten Versicherungen (falls zutreffend)?',
        validators=[Optional()]
    )
    # The PDF has checkboxes for Kranken, Pflege, Renten, Arbeitslosen. We'll simulate this with a StringField
    # or consider a MultiCheckboxField if WTForms-Plus is used. For simplicity, we'll use a StringField for now.
    # Alternatively, use individual BooleanFields and combine their values in app.py:
    german_ss_kranken = BooleanField('Krankenversicherung')
    german_ss_pflege = BooleanField('Pflegeversicherung')
    german_ss_renten = BooleanField('Rentenversicherung')
    german_ss_arbeitslosen = BooleanField('Arbeitslosenversicherung')


    foreign_social_security = RadioField(
        'Besteht eine soziale Sicherung nach dem Recht des Gastlandes?',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired("Bitte wählen Sie eine Option.")],
        default='no'
    )
    foreign_social_security_details = TextAreaField(
        'Welche Sozialversicherung im Gastland?',
        validators=[Optional()]
    )

    submit = SubmitField('Weiter')

    def validate_on_submit(self):
        # Base validation first
        if not super().validate_on_submit():
            return False
        
        # Custom validation for dates
        today = date.today()
        if self.date_of_departure.data and self.date_of_departure.data > today:
            self.date_of_departure.errors.append('Datum der Ausreise kann nicht in der Zukunft liegen.')
            return False
        
        if self.expected_date_of_return.data and self.expected_date_of_return.data < self.date_of_departure.data:
            self.expected_date_of_return.errors.append('Rückreisedatum kann nicht vor dem Ausreisedatum liegen.')
            return False

        # Conditional validation for German social security types
        if self.german_social_security_abroad.data == 'yes':
            if not (self.german_ss_kranken.data or self.german_ss_pflege.data or self.german_ss_renten.data or self.german_ss_arbeitslosen.data):
                self.german_social_security_types.errors.append('Bitte wählen Sie mindestens eine Versicherungsart.')
                return False
        
        # Conditional validation for foreign social security details
        if self.foreign_social_security.data == 'yes' and not self.foreign_social_security_details.data:
            self.foreign_social_security_details.errors.append('Bitte geben Sie die Art der Sozialversicherung im Gastland an.')
            return False

        return True
        
        
class OtherParentInfoForm(FlaskForm):
    vorname = StringField('Vorname des anderen Elternteils', validators=[DataRequired(message="Pflichtfeld")])
    nachname = StringField('Nachname des anderen Elternteils', validators=[DataRequired(message="Pflichtfeld")])
    geburtsdatum = DateField(
        'Geburtsdatum des anderen Elternteils',
        format='%Y-%m-%d',
        validators=[DataRequired(message="Pflichtfeld")],
        render_kw={"type": "date"}
    )
    geschlecht = SelectField(
        'Geschlecht des anderen Elternteils',
        choices=[
            ('weiblich','weiblich'),
            ('männlich','männlich'),
            ('divers','divers'),
            ('ohne Angaben','ohne Angabe')
        ],
        validators=[DataRequired(message="Pflichtfeld")]
    )
    steuer_id = StringField(
        'Steuer-Identifikationsnummer des anderen Elternteils',
        validators=[DataRequired(message="Pflichtfeld"), Length(min=11, max=11, message="11-stellige ID erforderlich")]
    )
    email = EmailField('E-Mail (optional)', validators=[Optional(), Email(message="Ungültige E-Mail")])
    telefon = StringField('Telefonnummer (optional)', validators=[Optional()])

    submit = SubmitField('Weiter')

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        today = date.today()
        bd = self.geburtsdatum.data
        if bd > today:
            self.geburtsdatum.errors.append('Geburtsdatum kann nicht in der Zukunft liegen.')
            return False

        if not self.steuer_id.data.isdigit():
            self.steuer_id.errors.append('Steuer-ID muss nur aus Ziffern bestehen.')
            return False

        return True

class IncomeForm(FlaskForm):
    """
    Schritt 4: Vor der Geburt – Einkommen & Einkommensersatzleistungen
    """

    # 1. Was für Einkünfte hatte der Antragsteller im Bemessungszeitraum?
    income_type = RadioField(
        'Welche Einkünfte hatten Sie im Bemessungszeitraum?',
        choices=[
            ('non_self_employed', 'Einkünfte aus nicht-selbstständiger Arbeit (z. B. Lohn/Gehalt)'),
            ('self_employed', 'Gewinneinkünfte (selbstständig, Gewerbebetrieb, Landwirtschaft)'),
            ('none', 'keine Einkünfte'),
        ],
        validators=[DataRequired(message="Bitte wählen Sie eine Einkunftsart")],
        default='non_self_employed'
    )

    # 2. Falls non-self or self-employed: Betrag angeben
    income_amount = StringField(
        'Gesamte Einkünfte im Bemessungszeitraum (Brutto in €)',
        validators=[Optional()],
        render_kw={"placeholder": "z. B. 24000"}
    )

    # 3. Einkommensersatzleistungen? (z. B. Arbeitslosengeld, Krankengeld, Kurzarbeitergeld, Insolvenzgeld, Bürgergeld)
    received_benefits = RadioField(
        'Haben Sie im Bemessungszeitraum Einkommensersatzleistungen bekommen?',
        choices=[('yes','Ja'), ('no','Nein')],
        validators=[DataRequired(message="Wählen Sie Ja oder Nein")],
        default='no'
    )

    # 4. Wenn ja: Art der Leistung(n)
    benefits_details = StringField(
        'Welche Einkommensersatzleistungen?',
        validators=[Optional()],
        render_kw={"placeholder": "z. B. Arbeitslosengeld, Bürgergeld …"}
    )

    submit = SubmitField('Weiter')

    def validate(self, **kwargs):
        """
        1) Wenn income_type != 'none', income_amount ist Pflicht und muss eine Zahl sein.
        2) Wenn received_benefits == 'yes', dann benefits_details ist Pflicht.
        """
        if not super().validate(**kwargs):
            return False

        # 1) Prüfen, ob Einkünfte angegeben wurden
        if self.income_type.data in ('non_self_employed', 'self_employed'):
            if not self.income_amount.data:
                self.income_amount.errors.append('Bitte geben Sie einen Betrag an.')
                return False
            # Prüfen, ob income_amount eine positive Zahl ist
            try:
                amt = float(self.income_amount.data.replace(',', '.'))
                if amt < 0:
                    raise ValueError
            except ValueError:
                self.income_amount.errors.append('Bitte geben Sie eine gültige Zahl (≥ 0) an.')
                return False

        # 2) Prüfen, ob Einkommensersatzleistungen konkret benannt wurden
        if self.received_benefits.data == 'yes':
            if not self.benefits_details.data.strip():
                self.benefits_details.errors.append('Bitte geben Sie an, welche Leistungen Sie erhalten haben.')
                return False

        return True


class BankInfoForm(FlaskForm):
    # IBAN (German format starts with "DE" followed by 20 digits)
    iban = StringField(
        'Kontonummer (IBAN)',
        validators=[
            DataRequired(),
            Regexp(r'^DE\d{20}$', message="Ungültige IBAN. Muss mit DE + 20 Ziffern sein.")
        ],
        render_kw={"placeholder": "DE00 0000 0000 0000 0000 00"}
    )

    bic = StringField(
        'BIC',
        validators=[
            DataRequired(),
            Length(min=8, max=11, message="BIC ist 8 oder 11 Zeichen lang.")
        ],
        render_kw={"placeholder": "z.B. DEUTDEFFXXX"}
    )

    account_holder = StringField(
        'Name des Kontoinhabers',
        validators=[DataRequired()]
    )

    own_account = RadioField(
        'Ist das Ihr eigenes Konto?',
        choices=[('yes', 'Ja, eigenes Konto'), ('other_parent', 'Nein, Konto des anderen Elternteils'), ('third', 'Nein, Konto einer dritten Person')],
        validators=[DataRequired(message="Bitte wählen Sie eine Option")],
        default='yes'
    )

    submit = SubmitField('PDF generieren')



# --- NEW CLASS: IncomeBeforeBirthForm ---
class IncomeBeforeBirthForm(FlaskForm):
    # 5.1 Bemessungszeitraum (Assessment Period)
    assessment_period_type = RadioField(
        'Bemessungszeitraum',
        choices=[
            ('standard', 'Die 12 Kalendermonate vor dem Geburtsmonat des Kindes'),
            ('other', 'Andere Kalendermonate (z. B. wegen Mutterschutz, Elterngeld für ein älteres Kind, etc.)')
        ],
        validators=[DataRequired("Bitte wählen Sie den Bemessungszeitraum.")]
    )
    other_assessment_reason = TextAreaField(
        'Begründung (falls "Andere Kalendermonate" gewählt)',
        validators=[Optional()]
    )
    other_assessment_start_month = SelectField(
        'Monat (von)',
        choices=[(str(i), str(i)) for i in range(1, 13)],
        validators=[Optional()]
    )
    other_assessment_start_year = StringField(
        'Jahr (von)',
        validators=[Optional(), Length(min=4, max=4, message="Bitte geben Sie ein 4-stelliges Jahr ein.")]
    )
    other_assessment_end_month = SelectField(
        'Monat (bis)',
        choices=[(str(i), str(i)) for i in range(1, 13)],
        validators=[Optional()]
    )
    other_assessment_end_year = StringField(
        'Jahr (bis)',
        validators=[Optional(), Length(min=4, max=4, message="Bitte geben Sie ein 4-stelliges Jahr ein.")]
    )

    # 5.2 Einkommen aus nichtselbständiger Arbeit (Income from Employment)
    has_employed_income = RadioField(
        'Hatten Sie Einkommen aus nichtselbständiger Arbeit (als Angestellter/Angestellte) vor der Geburt?',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired("Bitte geben Sie an, ob Sie Einkommen aus nichtselbständiger Arbeit hatten.")],
        default='no'
    )
    employer_name = StringField('Name des Arbeitgebers / Dienstherrn / Ausbildung', validators=[Optional()])

    # Dynamically create fields for 12 months of gross income
    # Note: For simplicity, we'll assume a fixed 12 months for now.
    # In a real application, you might generate these fields programmatically
    # based on the selected assessment period.
# Individual gross income fields for 12 months
    gross_income_month_1 = DecimalField('Bruttoarbeitslohn Monat 1 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_2 = DecimalField('Bruttoarbeitslohn Monat 2 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_3 = DecimalField('Bruttoarbeitslohn Monat 3 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_4 = DecimalField('Bruttoarbeitslohn Monat 4 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_5 = DecimalField('Bruttoarbeitslohn Monat 5 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_6 = DecimalField('Bruttoarbeitslohn Monat 6 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_7 = DecimalField('Bruttoarbeitslohn Monat 7 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_8 = DecimalField('Bruttoarbeitslohn Monat 8 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_9 = DecimalField('Bruttoarbeitslohn Monat 9 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_10 = DecimalField('Bruttoarbeitslohn Monat 10 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_11 = DecimalField('Bruttoarbeitslohn Monat 11 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])
    gross_income_month_12 = DecimalField('Bruttoarbeitslohn Monat 12 in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])

    # 5.3 Besondere Einnahmen (Special Income)
    # Checkboxes for special income types
    has_mutterschaftsgeld = BooleanField('Mutterschaftsgeld')
    mutterschaftsgeld_amount = DecimalField('Höhe des Mutterschaftsgeldes in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])

    has_krankentagegeld = BooleanField('Krankentagegeld')
    krankentagegeld_amount = DecimalField('Höhe des Krankentagegeldes in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])

    has_kurzarbeitergeld = BooleanField('Kurzarbeitergeld / Arbeitslosengeld I')
    kurzarbeitergeld_amount = DecimalField('Höhe des Kurzarbeitergeldes / Arbeitslosengeldes I in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])

    has_elterngeld_older_child = BooleanField('Elterngeld für ein älteres Kind')
    elterngeld_older_child_amount = DecimalField('Höhe des Elterngeldes für älteres Kind in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])

    has_other_income = BooleanField('Sonstige Einnahmen')
    other_income_amount = DecimalField('Höhe der sonstigen Einnahmen in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])


    # 5.4 Einkommen aus selbständiger Tätigkeit, Gewerbebetrieb, Land- und Forstwirtschaft (Self-Employment Income)
    has_self_employed_income = RadioField(
        'Hatten Sie Einkommen aus selbständiger Tätigkeit, Gewerbebetrieb, Land- und Forstwirtschaft vor der Geburt?',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired("Bitte geben Sie an, ob Sie Einkommen aus selbständiger Tätigkeit hatten.")],
        default='no'
    )
    self_employment_activity_type = StringField('Art der Tätigkeit', validators=[Optional()])
    profit_assessment_start_month = SelectField(
        'Ermittlungszeitraum des Gewinns (von Monat)',
        choices=[(str(i), str(i)) for i in range(1, 13)],
        validators=[Optional()]
    )
    profit_assessment_start_year = StringField(
        'Ermittlungszeitraum des Gewinns (von Jahr)',
        validators=[Optional(), Length(min=4, max=4, message="Bitte geben Sie ein 4-stelliges Jahr ein.")]
    )
    profit_assessment_end_month = SelectField(
        'Ermittlungszeitraum des Gewinns (bis Monat)',
        choices=[(str(i), str(i)) for i in range(1, 13)],
        validators=[Optional()]
    )
    profit_assessment_end_year = StringField(
        'Ermittlungszeitraum des Gewinns (bis Jahr)',
        validators=[Optional(), Length(min=4, max=4, message="Bitte geben Sie ein 4-stelliges Jahr ein.")]
    )
    profit_amount = DecimalField('Höhe des Gewinns in Euro', places=2, validators=[Optional(), NumberRange(min=0, message="Der Wert muss positiv sein.")])

    submit = SubmitField('Weiter')

    def validate_on_submit(self):
        if not super().validate_on_submit():
            return False

        # Conditional validation for "Other Assessment Period"
        if self.assessment_period_type.data == 'other':
            if not self.other_assessment_reason.data:
                self.other_assessment_reason.errors.append('Bitte geben Sie eine Begründung für den abweichenden Bemessungszeitraum an.')
            if not (self.other_assessment_start_month.data and self.other_assessment_start_year.data and
                    self.other_assessment_end_month.data and self.other_assessment_end_year.data):
                self.other_assessment_start_month.errors.append('Bitte geben Sie den vollständigen abweichenden Bemessungszeitraum an.')
            try:
                if self.other_assessment_start_year.data:
                    int(self.other_assessment_start_year.data)
                if self.other_assessment_end_year.data:
                    int(self.other_assessment_end_year.data)
            except ValueError:
                self.other_assessment_start_year.errors.append('Jahr muss eine gültige Zahl sein.')

        # Conditional validation for Employed Income
        if self.has_employed_income.data == 'yes':
            if not self.employer_name.data:
                self.employer_name.errors.append('Bitte geben Sie den Namen des Arbeitgebers an.')
            # You might want to add validation that at least some monthly income is entered,
            # but for now, Optional() allows empty fields if user chooses to not fill all 12.
            # A more robust check might be `if any(field.data for field in self.gross_income_months)`

        # Conditional validation for Special Income amounts if checkbox is checked
        if self.has_mutterschaftsgeld.data and self.mutterschaftsgeld_amount.data is None:
            self.mutterschaftsgeld_amount.errors.append('Bitte geben Sie die Höhe des Mutterschaftsgeldes an.')
        if self.has_krankentagegeld.data and self.krankentagegeld_amount.data is None:
            self.krankentagegeld_amount.errors.append('Bitte geben Sie die Höhe des Krankentagegeldes an.')
        if self.has_kurzarbeitergeld.data and self.kurzarbeitergeld_amount.data is None:
            self.kurzarbeitergeld_amount.errors.append('Bitte geben Sie die Höhe des Kurzarbeitergeldes / Arbeitslosengeldes I an.')
        if self.has_elterngeld_older_child.data and self.elterngeld_older_child_amount.data is None:
            self.elterngeld_older_child_amount.errors.append('Bitte geben Sie die Höhe des Elterngeldes für älteres Kind an.')
        if self.has_other_income.data and self.other_income_amount.data is None:
            self.other_income_amount.errors.append('Bitte geben Sie die Höhe der sonstigen Einnahmen an.')


        # Conditional validation for Self-Employed Income
        if self.has_self_employed_income.data == 'yes':
            if not self.self_employment_activity_type.data:
                self.self_employment_activity_type.errors.append('Bitte geben Sie die Art der Tätigkeit an.')
            if not (self.profit_assessment_start_month.data and self.profit_assessment_start_year.data and
                    self.profit_assessment_end_month.data and self.profit_assessment_end_year.data):
                self.profit_assessment_start_month.errors.append('Bitte geben Sie den vollständigen Ermittlungszeitraum des Gewinns an.')
            if self.profit_amount.data is None:
                self.profit_amount.errors.append('Bitte geben Sie die Höhe des Gewinns an.')
            try:
                if self.profit_assessment_start_year.data:
                    int(self.profit_assessment_start_year.data)
                if self.profit_assessment_end_year.data:
                    int(self.profit_assessment_end_year.data)
            except ValueError:
                self.profit_assessment_start_year.errors.append('Jahr muss eine gültige Zahl sein.')

        return True
