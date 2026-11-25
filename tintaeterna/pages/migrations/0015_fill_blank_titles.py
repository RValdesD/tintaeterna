from pathlib import Path

from django.db import migrations


def fill_blank_titles(apps, schema_editor):
    """Obras que quedaron sin título: usar el nombre del archivo sin extensión."""
    StoryUpload = apps.get_model("pages", "StoryUpload")
    for story in StoryUpload.objects.filter(title="").exclude(original_name=""):
        story.title = Path(story.original_name).stem[:200]
        story.save(update_fields=["title"])


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0014_reader_comment_replies"),
    ]

    operations = [
        migrations.RunPython(fill_blank_titles, migrations.RunPython.noop),
    ]