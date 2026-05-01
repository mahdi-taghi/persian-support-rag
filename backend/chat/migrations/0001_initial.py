from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ChatLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("user_message", models.TextField()),
                ("ai_response", models.TextField()),
                ("handoff_required", models.BooleanField(default=False)),
                ("handoff_reason", models.TextField(blank=True, null=True)),
                ("request_received_at", models.DateTimeField()),
                ("response_generated_at", models.DateTimeField()),
                ("processing_time_ms", models.PositiveIntegerField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
