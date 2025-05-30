# Generated by Django 5.2 on 2025-04-25 12:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sacco', '0011_loan_loan_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoanProductType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='loanplan',
            name='product_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='loan_plans', to='sacco.loanproducttype'),
        ),
    ]
