# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-23 22:57


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artshow', '0003_piece_bids_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='bidder',
            name='details_changed',
            field=models.BooleanField(default=False),
        ),
    ]
