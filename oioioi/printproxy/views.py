import tempfile

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from oioioi.base.permissions import enforce_condition, is_superuser
from oioioi.printproxy.forms import PrintproxyForm
from oioioi.printproxy.utils import print_filename

@enforce_condition(is_superuser)
def printproxy(request):
    form = PrintproxyForm()
    if request.method == 'POST':
        form = PrintproxyForm(request.POST, request.FILES)
        if form.is_valid():
            upl_file = request.FILES['file']
            with tempfile.NamedTemporaryFile(
                mode='wb',
                buffering=0,
                suffix=upl_file.name,
            ) as f:
                for c in upl_file.chunks():
                    f.write(c)
                print_filename(f.name)
            messages.success(request, _("Success!"))
            form = PrintproxyForm()
    return TemplateResponse(
        request,
        'printproxy/printproxy.html',
        context={
            'form': form,
        },
    )
