# Generated by Django 5.2 on 2025-04-14 21:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('question_type', models.CharField(choices=[('multiple', 'Choix multiple'), ('single', 'Choix unique'), ('text', 'Réponse texte')], default='single', max_length=8)),
                ('order', models.PositiveIntegerField(default=1)),
                ('points', models.PositiveIntegerField(default=1)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=200)),
                ('is_correct', models.BooleanField(default=False)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='quizzes.question')),
            ],
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('time_limit', models.PositiveIntegerField(blank=True, help_text='Temps limite en minutes (optionnel)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chapter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quizzes', to='courses.chapter')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quizzes', to='courses.course')),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='quizzes.quiz'),
        ),
        migrations.CreateModel(
            name='QuizAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text_answer', models.TextField(blank=True, null=True)),
                ('is_correct', models.BooleanField(default=False)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quizzes.question')),
                ('selected_choices', models.ManyToManyField(blank=True, to='quizzes.choice')),
            ],
        ),
        migrations.CreateModel(
            name='QuizResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField()),
                ('max_score', models.FloatField()),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('time_taken', models.PositiveIntegerField(blank=True, help_text='Temps pris en secondes', null=True)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='quizzes.quiz')),
            ],
        ),
    ]
