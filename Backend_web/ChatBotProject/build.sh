#!/bin/bash

echo "🚀 Fanamboarana ny tetikasa ChatBotBuilder..."

# Fametrahana ny fitaovana
pip install --upgrade pip
pip install -r requirements.txt

# Fanangonana ny static files
python manage.py collectstatic --no-input

# Fampiharana ny migration
python manage.py migrate

echo "✅ Famonoana vita!"