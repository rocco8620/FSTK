import json
import logging

import requests

from fstk import Globals


def request(method, path, params=None, timeout=60):
    if params is None:
        params = {}

    headers = { 'X-Redmine-API-Key': Globals.config['options']['redmine']['apikey'] }
    url = Globals.config['options']['redmine']['host'] + path
    logging.debug('Redmine call {} {} {}'.format(method, url, params))
    try:
        resp = requests.request(method, url, headers=headers, params=params, timeout=timeout)
        if resp.status_code != 200:
            logging.info('The status code recevied was {}, expected 200'.format(resp.status_code))
            return False, 'The status code recevied was {}, expected 200'.format(resp.status_code)

        return True, resp.text

    except requests.exceptions.ConnectionError as e:
        logging.info('Redmine api call failed: Connection failed: {}'.format(e))
        return False, 'Redmine api call failed: Connection failed: {}'.format(e)

    except Exception as e:
        logging.info('Redmine api call failed: Unknow error occurred: {}'.format(e))
        return False, 'Redmine api call failed: Unknow error occurred: {}'.format(e)



def get_tickets_title(numbers):
    if not isinstance(numbers, list):
        numbers = [numbers]

    numbers = list(set(numbers))

    numbers = [ str(n) for n in numbers ]

    succes, text = request('GET', '/issues.json', params={'issue_id': ','.join(numbers), 'status_id': '*'})

    if not succes:
        return None

    j = json.loads(text)

    ris = {}

    for issue in j['issues']:
        ris[str(issue['id'])] = issue['subject']

    return ris

    # {"issues": [{"id": 7211, "project": {"id": 81, "name": "SIEM"}, "tracker": {"id": 8, "name": "Progettazione"},
    #              "status": {"id": 1, "name": "Nuovo"}, "priority": {"id": 2, "name": "Normale"},
    #              "author": {"id": 7, "name": "Moreno Versolatto"}, "assigned_to": {"id": 16, "name": "Rocco Mancin"},
    #              "category": {"id": 206, "name": "Documentazione"}, "fixed_version": {"id": 5, "name": "SIEM Cloud"},
    #              "subject": "Progettazione di una Wiki per l'installatore e il supporto",
    #              "description": "Decidiamo di implementare il manuale in una wiki, all'interno della dashboard (autenticata)\r\nVogliamo selezionare uno strumento che, dato il codice, genera HTML statico, da far servire a Python (e.g. Sphinx) (AP Moreno)\r\nRocco fa una valutazione/progettazione dell'architettura (AP Rocco)\r\nCi diamo scadenza per il lavoro prototipo (30 aprile) / completamento (14 maggio)\r\n",
    #              "start_date": "2021-03-26", "due_date": "2021-04-23", "done_ratio": 0,
    #              "created_on": "2021-03-26T09:30:47Z", "updated_on": "2021-03-26T09:33:39Z"},
    #             {"id": 7210, "project": {"id": 81, "name": "SIEM"}, "tracker": {"id": 10, "name": "Documentazione"},
    #              "status": {"id": 1, "name": "Nuovo"}, "priority": {"id": 2, "name": "Normale"},
    #              "author": {"id": 7, "name": "Moreno Versolatto"},
    #              "assigned_to": {"id": 7, "name": "Moreno Versolatto"},
    #              "category": {"id": 206, "name": "Documentazione"}, "fixed_version": {"id": 5, "name": "SIEM Cloud"},
    #              "parent": {"id": 7211},
    #              "subject": "Selezionare uno strumento che, dato il codice, genera HTML statico (Wiki)",
    #              "description": "Vogliamo selezionare uno strumento che, dato il codice, genera HTML statico, da far servire a Python",
    #              "start_date": "2021-03-26", "due_date": "2021-04-23", "done_ratio": 0, "estimated_hours": 8.0,
    #              "created_on": "2021-03-26T09:29:13Z", "updated_on": "2021-03-26T09:32:10Z"}], "total_count": 2,
    #  "offset": 0, "limit": 25}

def are_redmine_creds_valid():
    succes, _ = request('GET', '/issues.json', params={'limit': 1})
    return succes