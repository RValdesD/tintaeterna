from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('pages', '0013_reader_comment_author')]
    operations = [
        migrations.AddField(
            model_name='comentarios', name='parent',
            field=models.ForeignKey(to='pages.comentarios', null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL, related_name='replies'),
        ),
    ]
