
# Assicuriamoci di avere i tools installati
pip install --upgrade twine
# carichiamo le credenziali
source credentials.sh
# better safe than sorry
echo "Are you sure you want to upload the package to pypi?"
read -r
echo "Really sure?"
read -r
# upload
python3 -m twine upload dist/*.whl
