import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CulturalRegion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('region_type', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('boundary', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='HeritageRoute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('route_type', models.CharField(choices=[('WALKING', 'Walking Route'), ('CRAFT', 'Craft Trail'), ('CULTURAL', 'Cultural Route'), ('CYCLING', 'Cycling Route'), ('OTHER', 'Other')], default='CULTURAL', max_length=50)),
                ('description', models.TextField(blank=True)),
                ('path', django.contrib.gis.db.models.fields.LineStringField(srid=4326)),
                ('distance_km', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ArtisanLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('artisan_name', models.CharField(max_length=150)),
                ('craft_type', models.CharField(choices=[('POTTERY', 'Pottery'), ('WEAVING', 'Weaving'), ('WOODCARVING', 'Woodcarving'), ('TEXTILES', 'Traditional Textiles'), ('JEWELLERY', 'Jewellery'), ('LEATHER', 'Leatherwork'), ('PAINTING', 'Traditional Painting'), ('OTHER', 'Other')], default='OTHER', max_length=50)),
                ('description', models.TextField(blank=True)),
                ('address', models.CharField(max_length=255)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('website', models.URLField(blank=True)),
                ('opening_hours', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='artisans', to='heritage.culturalregion')),
            ],
        ),
    ]
