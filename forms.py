# forms.py

# ─── Monkey-patch for Flask-WTF / Werkzeug 3.x compatibility ───
# Flask-WTF tries: from werkzeug.urls import url_encode
# In Werkzeug 3.x, url_encode is gone, so we provide it via urllib.parse.urlencode.

import werkzeug
import urllib.parse
import types

# Ensure werkzeug.urls namespace exists
if not hasattr(werkzeug, "urls"):
    werkzeug.urls = types.SimpleNamespace()

# Map werkzeug.urls.url_encode → urllib.parse.urlencode
werkzeug.urls.url_encode = urllib.parse.urlencode
# ─────────────────────────────────────────────────────────────────────

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DateField,
    BooleanField,
    RadioField,
    SelectField,
    SubmitField,
    EmailField,
)
from wtforms.validators import DataRequired, Length, Email, Optional, ValidationError
from datetime import date, timedelta

class ChildInfoForm(FlaskForm):
    # … your existing fields and custom validate() …
    is_born = RadioField(
        'Ist das Kind bereits geboren?',
        choices=[('yes', 'Ja'), ('no', 'Nein')],
        validators=[DataRequired(message="Wählen Sie Ja oder Nein")],
        default='yes'
    )
    vorname = StringField('Vorname des Kindes', validators=[Optional()])
    nachname = StringField('Nachname des Kindes', validators=[Optional()])
    geburtsdatum = DateField(
        'Geburtsdatum des Kindes',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={"type": "date"}
    )
    fruehgeboren = BooleanField('Frühgeboren (≥ 6 Wochen vor Termin)')
    behinderung = BooleanField('Kind hat Behinderung')
    multiple_births = SelectField(
        'Wie viele Kinder wurden insgesamt geboren?',
        choices=[('1','1'), ('2','2'), ('3','3'), ('4+','4 oder mehr')],
        validators=[Optional()]
    )
    submit = SubmitField('Weiter')

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        if self.is_born.data == 'yes':
            today = date.today()
            if not self.vorname.data or not self.nachname.data:
                msg = 'Vorname und Nachname sind erforderlich'
                self.vorname.errors.append(msg)
                self.nachname.errors.append(msg)
                return False

            if not self.geburtsdatum.data:
                self.geburtsdatum.errors.append('Geburtsdatum ist erforderlich')
                return False

            if self.geburtsdatum.data > today:
                self.geburtsdatum.errors.append('Geburtsdatum liegt in der Zukunft')
                return False

            three_months_ago = today - timedelta(days=90)
            if self.geburtsdatum.data < three_months_ago:
                self.geburtsdatum.errors.append(
                    'Elterngeldantrag sollte innerhalb 3 Monate nach der Geburt gestellt werden'
                )
                return False

            if not self.multiple_births.data:
                self.multiple_births.errors.append('Bitte angeben, wie viele Kinder geboren wurden')
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


class ApplicantInfoForm(FlaskForm):
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
    strasse = StringField('Straße und Nr.', validators=[DataRequired(message="Pflichtfeld")])
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
