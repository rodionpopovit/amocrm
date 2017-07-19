from datetime import date, timedelta


from django import forms
import requests
from django.core.exceptions import ValidationError


class AuthForm(forms.Form):
    login = forms.EmailField(initial='vlad.korpusov@mail.ru')
    api_key = forms.CharField(min_length=32, max_length=32, initial='10ff349e1cbd8de126924b6eecfc61bd')
    domain = forms.CharField(initial='new596d0be6580de.amocrm.ru')

    def auth(self):
        domain = self.data.get('domain')
        url = 'https://{}/private/api/auth.php'.format(domain)
        data = {
            'USER_LOGIN': self.data.get('login'),
            'USER_HASH': self.data.get('api_key')
        }
        try:
            response = requests.post(url, data)
        except Exception:
            raise ValidationError('Ошибка при авторизации на amocrm api.')
        else:
            if response.status_code != 200:
                raise ValidationError('Ошибка при авторизации на amocrm api.')
            return response


    def get_leads(self):
        auth_response = self.auth()
        domain = self.data.get('domain')
        url = 'https://{}/private/api/v2/json/leads/list'.format(domain)

        response = requests.get(url=url, cookies=auth_response.cookies)
        if response.status_code == 200:
            return response.json()
        raise ValidationError('Ошибка при авторизации на amocrm api.')

