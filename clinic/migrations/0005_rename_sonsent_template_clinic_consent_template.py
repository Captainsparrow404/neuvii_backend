from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0004_alter_clinic_clinic_admin'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clinic',
            old_name='sonsent_template',
            new_name='consent_template',
        ),
    ]