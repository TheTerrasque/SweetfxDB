from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from . import models as gamedb

class LoginReq(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginReq, self).dispatch(*args, **kwargs)

class PaginateMixin(object):
    paginate_by = 25

class GQsMixin(object):
    queryset = gamedb.Game.active.all()    