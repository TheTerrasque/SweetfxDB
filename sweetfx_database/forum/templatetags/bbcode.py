from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from sweetfx_database.gamedb import models as gamedb
from sweetfx_database.forum import models as forumdb

from django.utils.html import urlize
import re

register = template.Library()

def get_match(func):
    def inner(match):
        text = match.group(1)
        return func(text)
    return inner

@get_match
def bb_preset(match):
    try:
        r = gamedb.Preset.objects.get(id=match)
        return u'<span class="bb_preset"><a href="%s">%s</a> for <a href="%s">%s</a></span>' % (r.get_absolute_url(), r.title, r.game.get_absolute_url(), r.game.title)
    except:
        return match + u"[No such preset]"

@get_match
def bb_game(match):
    try:
        r = gamedb.Game.objects.get(id=match)
        return u'<span class="bb_game"><a href="%s">%s</a></span>' % (r.get_absolute_url(), r.title)
    except:
        return match + u"[No such game]"

RX = [
    ("u", r"<span class='bb_u'>\1</span>"),
    ("b", r"<span class='bb_b'>\1</span>"),
    ("i", r"<span class='bb_i'>\1</span>"),
    ("quote", r"<div class='bb_quote'>\1</div>"),
    ("preset", bb_preset),
    ("game", bb_game),
]

RXC = []

def compile_regex():
    for k, v in RX:
        RXC.append((re.compile(r"\[%s\](.+?)\[/%s\]" % (k, k), re.I|re.M|re.S), v))

compile_regex()

def do_bbcode(text):
    for rx, bla in RXC:
        text = rx.sub(bla, text)
    return u"<div class='bbtext'>%s</div>" %text

@register.simple_tag
def get_latest_forumthreads(string=None):
    if not string:
        num = 5
    else:
        num = int(string)
    return forumdb.ForumThread.objects.latest_threads().select_related("last_post", "forum").order_by("-updated")[:num]

@register.simple_tag
def get_latest_forumposts(string=None):
    if not string:
        num = 5
    else:
        num = int(string)
    return forumdb.ForumPost.objects.order_by("-id")[:num]
    

@register.filter(needs_autoescape=True)
def bbcode(text, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    
    text = esc(text)
    text = urlize(text)
    result =  do_bbcode(text)
    return mark_safe(result)
