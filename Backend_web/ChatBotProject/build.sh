#!/usr/bin/env bash
# exit on error
set -o errexit

# Ampidira ny library rehetra
pip install -r requirements.txt

# Ataovy ny migration ny database
python manage.py makemigrations
python manage.py migrate

# Angony ny fichiers statiques (raha ilaina)
python manage.py collectstatic --no-input