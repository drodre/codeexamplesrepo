import json
import os
import requests
import base64

def get_access_token(client_id, client_secret):
    """Obtiene un token de acceso de la API de InfoJobs."""
    url = "https://www.infojobs.net/oauth/authorize"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}'
    }
    params = {
        'grant_type': 'client_credentials',
        'scope': 'MY_APPLICATIONS,CANDIDATE_PROFILE_WITH_EMAIL,CANDIDATE_READ_CURRICULUMS,CV,JOB_SEARCH'
    }

    try:
        response = requests.post(url, headers=headers, params=params)
        response.raise_for_status()  # Lanza un error para respuestas 4xx/5xx
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el token de acceso: {e}")
        return None

def search_devops_jobs(access_token):
    """Busca ofertas de trabajo de DevOps en la API de InfoJobs."""
    url = "https://api.infojobs.net/api/9/offer"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'q': 'devops'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"Error al buscar ofertas de trabajo: {e}")
        return []

def get_credentials():
    """Lee las credenciales de la API desde config.json."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            client_id = config.get("client_id")
            client_secret = config.get("client_secret")
            if not client_id or not client_secret:
                raise ValueError("client_id y client_secret deben estar definidos en config.json")
            return client_id, client_secret
    except FileNotFoundError:
        print("Error: No se ha encontrado config.json. Por favor, créalo a partir de config.json.example.")
        return None, None
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error al leer config.json: {e}")
        return None, None

if __name__ == "__main__":
    client_id, client_secret = get_credentials()
    if client_id and client_secret:
        access_token = get_access_token(client_id, client_secret)
        if access_token:
            jobs = search_devops_jobs(access_token)
            if jobs:
                print(f"Se han encontrado {len(jobs)} ofertas de trabajo de DevOps:")
                for job in jobs:
                    print(f"- {job.get('title')} ({job.get('province', {}).get('value', 'N/A')})")
            else:
                print("No se han encontrado ofertas de trabajo de DevOps.")
