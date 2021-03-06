from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from core.exceptions import (
    UnknownError,
    UserNotExists,
    PrivateProfileError,
)
from core.consts import DEFAULT_FIFA_EDITION
from players.models import (
    DataUsersTeams,
    DataUsersCareerUsers,
)


def del_session_key(request, key):
    request.session.pop(key, None)


def set_currency(request):
    # Set Currency
    currency_symbols = ('$', '€', '£')
    if request.session.get('currency', None) is None:
        try:
            request.session['currency'] = request.user.profile.currency
        except:
            request.session['currency'] = 1

    if request.session.get('currency_symbol', None) is None:
        request.session['currency_symbol'] = currency_symbols[int(
            request.session['currency'])]


def get_current_user(request):
    # Set current User
    if 'owner' in request.GET:
        owner = request.GET['owner']
        try:
            user = User.objects.get(username=owner)
            is_profile_public = user.profile.is_public
        except User.DoesNotExist:
            raise UserNotExists(_("User '{}' does not exist.".format(owner)))
        except Exception as e:
            raise UnknownError(e)

        # Check if owner profile is private
        if not is_profile_public:
            raise PrivateProfileError(
                _("Sorry, {}'s profile is private. Profile visibility can be changed in Control Panel.").format(owner))

        current_user = owner
    elif request.user.is_authenticated:
        current_user = request.user
    else:
        current_user = "guest"

    return current_user


def get_fifa_edition(request, user=None):
    try:
        if not user:
            user = get_current_user(request)
        if isinstance(user, str):
            user = User.objects.get(username=user)

        return int(user.profile.fifa_edition)
    except Exception:
        return DEFAULT_FIFA_EDITION


def get_career_user(request, current_user=None):
    if current_user is None:
        current_user = "guest"

    if request.session.get('career_user', None) is None:
        career_user = DataUsersCareerUsers.objects.for_user(current_user).first()

        try:
            clubteamid = career_user.clubteamid
        except AttributeError:
            clubteamid = -1

        try:
            nationalteamid = career_user.nationalteamid
        except AttributeError:
            nationalteamid = -1

        fteamids = [clubteamid, nationalteamid]
        teams = list(DataUsersTeams.objects.for_user(current_user).filter(Q(teamid__in=fteamids)).iterator())

        clubteamname = ""
        nationalteamname = ""
        try:
            for team in teams:
                teamid = team.teamid
                if teamid == clubteamid:
                    clubteamname = team.teamname
                elif teamid == nationalteamid:
                    nationalteamname = team.teamname
        except AttributeError:
            pass

        request.session['career_user'] = {
            'clubteamid': clubteamid,
            'clubteamname': clubteamname,
            'nationalteamid': nationalteamid,
            'nationalteamname': nationalteamname,
        }

    return request.session.get('career_user', None)
