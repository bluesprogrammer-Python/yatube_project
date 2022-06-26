from django.core.paginator import Paginator
from Yatube.settings import VIEW_COEFF


def paginator_fun(queryset, request):
    result = Paginator(queryset, VIEW_COEFF)
    page_number = request.GET.get('page')
    page_obj = result.get_page(page_number)
    return page_obj
