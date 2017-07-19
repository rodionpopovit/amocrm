import time
from datetime import date

from django.core.exceptions import ValidationError
from django.views.generic.edit import FormView

from metrics.forms import AuthForm


STEP_DECIDE = '15636928'  # Принимают решение
STEP_AGREEMENT = '15636931'  # Согласование договора
STEP_SUCCESS = '142'  # Успешно реализованы

APPROVED_STEPS = [STEP_DECIDE, STEP_AGREEMENT]

class MetricsView(FormView):
    template_name = 'metrics.html'
    form_class = AuthForm

    def form_valid(self, form):
        return super(MetricsView, self).form_valid(form)


    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            try:
                leads = form.get_leads()
            except ValidationError as ex:
                form.add_error(None, ex.message)
                return self.form_invalid(form)
            else:
                context = self.get_context_data()
                context['metrics'] = self.month_metrics(leads['response']['leads'])
                return self.render_to_response(context)
        else:
            return self.form_invalid(form)

    def timestamp(self, date):
        return time.mktime(date.timetuple())

    def get_by_month_leads(self, leads):
        dates = [
            [self.timestamp(date(2017, 5, 1)), self.timestamp(date(2017, 6, 1))],
            [self.timestamp(date(2017, 6, 1)), self.timestamp(date(2017, 7, 1))],
            [self.timestamp(date(2017, 7, 1)), self.timestamp(date(2017, 8, 1))],
        ]
        result = []
        for dt in dates:
            result.append([lead for lead in leads if
                           dt[0] <= lead['date_create'] < dt[1]])
        return result

    def month_metrics(self, leads):
        result = []
        for month_leads in self.get_by_month_leads(leads):
            result.append(self.get_leads_metrics(month_leads))
        return result

    def get_leads_metrics(self, leads):
        return {
            'amount': self.get_amount(leads),
            'avg_check': self.get_avg_check(leads),
            'success_leads': self.get_success_leads(leads),
            'success_leads_users': self.get_success_leads_users(leads),
            'almost_success_leads': self.get_almost_success_leads(leads),
            'almost_success_leads_users': self.get_almost_success_leads_users(leads),
        }

    # доход успешно реализованы   | сумма выручки по всем заявкам, проходивших шаг воронки “Успешно реализованы”
    def get_amount(self, leads):
        amount = 0

        for lead in leads:
            if lead['status_id'] == STEP_SUCCESS:
                amount += float(lead['price']) if lead['price'] else 0
        return amount

    # ср. чек успешно реализованы | ср. чек по заявкам, проходивших шаг воронки “Успешно реализованы”
    def get_avg_check(self, leads):
        prices = []

        for lead in leads:
            if lead['status_id'] == STEP_SUCCESS:
                if lead['price']:
                    prices.append(float(lead['price']))

        return round(sum(prices) / float(len(prices)), 2) if prices else 0

    # заявки успешно реализованы  | количество заявок, проходивших шаг воронки “Успешно реализованы”
    def get_success_leads(self, leads):
        return len([lead for lead in leads if lead['status_id'] == STEP_SUCCESS])

    # лиды успешно реализованы    | количество пользователей, которые совершили заявку, проходившую шаг воронки “Успешно реализованы”
    def get_success_leads_users(self, leads):
        users = []
        for lead in leads:
            if lead['status_id'] == STEP_SUCCESS:
                users.append(lead['main_contact_id'])
        return len(set(users))

    # заявки подтверждены         | количество сделок, проходивших хотя бы одну из 2 предпоследних шагов воронки (2 шага до “Успешно реализован”)
    def get_almost_success_leads(self, leads):
        return len([lead for lead in leads if lead['status_id'] in APPROVED_STEPS])

    # лиды подтверждены           | количество пользователей, которые совершили заявку, проходившую хотя бы одну из 2 предпоследних шагов воронки (2 шага до “Успешно реализован”)
    def get_almost_success_leads_users(self, leads):
        users = []
        for lead in leads:
            if lead['status_id'] in APPROVED_STEPS:
                users.append(lead['main_contact_id'])
        return len(set(users))
