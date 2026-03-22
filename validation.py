import math
from werkzeug.exceptions import BadRequest


ALLOWED_SAVE_KEYS = {'pizzeriaName', 'money', 'totalEarned', 'clickValue', 'upgrades', 'lastSave',
                     'earnedAchievements', 'totalClicks', 'streak', 'lastLoginDate', 'prestigeLevel',
                     'lastSpinDate', 'boostType', 'boostMult', 'boostEnd'}
ALLOWED_UPGRADE_IDS = {
    'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'c10', 'c11', 'c12',
    'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10'
}
ALLOWED_ACHIEVEMENT_IDS = {f'a{i}' for i in range(1, 22)}


def validate_save_payload(data):
    if not isinstance(data, dict):
        raise BadRequest('Save data must be a JSON object.')

    unknown_keys = set(data.keys()) - ALLOWED_SAVE_KEYS
    if unknown_keys:
        raise BadRequest(f'Unknown save fields: {", ".join(sorted(unknown_keys))}.')

    required_keys = ALLOWED_SAVE_KEYS - set(data.keys())
    if required_keys:
        raise BadRequest(f'Missing save fields: {", ".join(sorted(required_keys))}.')

    pizzeria_name = validate_name(data.get('pizzeriaName'), 'pizzeriaName')
    money = validate_number(data.get('money'), 'money', minimum=0)
    total_earned = validate_number(data.get('totalEarned'), 'totalEarned', minimum=0)
    click_value = validate_number(data.get('clickValue'), 'clickValue', minimum=1)
    upgrades = validate_upgrades(data.get('upgrades'))
    last_save = validate_number(data.get('lastSave'), 'lastSave', minimum=0, integer_only=True)
    earned_achievements = validate_earned_achievements(data.get('earnedAchievements'))
    total_clicks = validate_number(data.get('totalClicks'), 'totalClicks', minimum=0, integer_only=True)
    streak = validate_number(data.get('streak'), 'streak', minimum=0, integer_only=True)
    last_login_date = validate_last_login_date(data.get('lastLoginDate'))
    prestige_level = validate_number(data.get('prestigeLevel'), 'prestigeLevel', minimum=0, integer_only=True)
    last_spin_date = validate_last_login_date(data.get('lastSpinDate'))
    boost_type = validate_boost_type(data.get('boostType'))
    boost_mult = validate_number(data.get('boostMult'), 'boostMult', minimum=1, maximum=10)
    boost_end  = validate_number(data.get('boostEnd'),  'boostEnd',  minimum=0, integer_only=True)

    return {
        'pizzeriaName': pizzeria_name,
        'money': money,
        'totalEarned': total_earned,
        'clickValue': click_value,
        'upgrades': upgrades,
        'lastSave': last_save,
        'earnedAchievements': earned_achievements,
        'totalClicks': total_clicks,
        'streak': streak,
        'lastLoginDate': last_login_date,
        'prestigeLevel': prestige_level,
        'lastSpinDate': last_spin_date,
        'boostType': boost_type,
        'boostMult': boost_mult,
        'boostEnd': boost_end,
    }


def validate_leaderboard_payload(data):
    if not isinstance(data, list):
        raise BadRequest('Leaderboard data must be a JSON array.')

    if len(data) > 10:
        raise BadRequest('Leaderboard can contain at most 10 entries.')

    validated_entries = []
    for index, entry in enumerate(data, start=1):
        if not isinstance(entry, dict):
            raise BadRequest(f'Leaderboard entry {index} must be an object.')

        allowed_keys = {'name', 'pps', 'total'}
        unknown_keys = set(entry.keys()) - allowed_keys
        if unknown_keys:
            raise BadRequest(f'Unknown leaderboard fields in entry {index}: {", ".join(sorted(unknown_keys))}.')

        missing_keys = allowed_keys - set(entry.keys())
        if missing_keys:
            raise BadRequest(f'Missing leaderboard fields in entry {index}: {", ".join(sorted(missing_keys))}.')

        validated_entries.append({
            'name': validate_name(entry.get('name'), f'entry {index} name'),
            'pps': validate_number(entry.get('pps'), f'entry {index} pps', minimum=0),
            'total': validate_number(entry.get('total'), f'entry {index} total', minimum=0),
        })

    return validated_entries


def validate_name(value, field_name):
    if not isinstance(value, str):
        raise BadRequest(f'{field_name} must be a string.')

    value = value.strip()
    if not value:
        raise BadRequest(f'{field_name} cannot be empty.')

    if value.isdigit():
        raise BadRequest(f'{field_name} cannot contain only numbers.')

    if len(value) > 30:
        raise BadRequest(f'{field_name} must be at most 30 characters long.')

    return value


def validate_number(value, field_name, minimum=None, maximum=None, integer_only=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadRequest(f'{field_name} must be a number.')

    if not math.isfinite(value):
        raise BadRequest(f'{field_name} must be a finite number.')

    if minimum is not None and value < minimum:
        raise BadRequest(f'{field_name} must be at least {minimum}.')

    if maximum is not None and value > maximum:
        raise BadRequest(f'{field_name} must be at most {maximum}.')

    if integer_only:
        if isinstance(value, float) and not value.is_integer():
            raise BadRequest(f'{field_name} must be an integer.')
        return int(value)

    return value


_ALLOWED_BOOST_TYPES = {'click', 'pps', 'all'}


def validate_boost_type(value):
    if value is None:
        return None
    if not isinstance(value, str) or value not in _ALLOWED_BOOST_TYPES:
        raise BadRequest(f'boostType must be null or one of: {", ".join(sorted(_ALLOWED_BOOST_TYPES))}.')
    return value


def validate_upgrades(value):
    if not isinstance(value, dict):
        raise BadRequest('upgrades must be an object.')

    validated_upgrades = {}
    for upgrade_id, purchased in value.items():
        if upgrade_id not in ALLOWED_UPGRADE_IDS:
            raise BadRequest(f'Unknown upgrade id: {upgrade_id}.')
        if not isinstance(purchased, bool):
            raise BadRequest(f'Upgrade {upgrade_id} must be true or false.')
        validated_upgrades[upgrade_id] = purchased

    return validated_upgrades


import re as _re


def validate_last_login_date(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise BadRequest('lastLoginDate must be a string or null.')
    if not _re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise BadRequest('lastLoginDate must be in YYYY-MM-DD format.')
    return value


def validate_earned_achievements(value):
    if not isinstance(value, dict):
        raise BadRequest('earnedAchievements must be an object.')

    validated = {}
    for ach_id, earned in value.items():
        if ach_id not in ALLOWED_ACHIEVEMENT_IDS:
            raise BadRequest(f'Unknown achievement id: {ach_id}.')
        if not isinstance(earned, bool):
            raise BadRequest(f'Achievement {ach_id} must be true or false.')
        validated[ach_id] = earned

    return validated


NICKNAME_MIN_LEN = 3
NICKNAME_MAX_LEN = 30
PASSWORD_MIN_LEN = 6
PASSWORD_MAX_LEN = 128


def validate_register_payload(data):
    if not isinstance(data, dict):
        raise BadRequest('Request body must be a JSON object.')
    allowed = {'nickname', 'password'}
    unknown = set(data.keys()) - allowed
    if unknown:
        raise BadRequest(f'Unknown fields: {", ".join(sorted(unknown))}.')
    missing = allowed - set(data.keys())
    if missing:
        raise BadRequest(f'Missing fields: {", ".join(sorted(missing))}.')
    return {
        'nickname': validate_nickname(data['nickname']),
        'password': validate_password(data['password']),
    }


def validate_login_payload(data):
    if not isinstance(data, dict):
        raise BadRequest('Request body must be a JSON object.')
    allowed = {'nickname', 'password'}
    unknown = set(data.keys()) - allowed
    if unknown:
        raise BadRequest(f'Unknown fields: {", ".join(sorted(unknown))}.')
    missing = allowed - set(data.keys())
    if missing:
        raise BadRequest(f'Missing fields: {", ".join(sorted(missing))}.')
    return {
        'nickname': validate_nickname(data['nickname']),
        'password': validate_password(data['password']),
    }


def validate_nickname(value):
    if not isinstance(value, str):
        raise BadRequest('nickname must be a string.')
    value = value.strip()
    if len(value) < NICKNAME_MIN_LEN:
        raise BadRequest(f'Nickname musí mít alespoň {NICKNAME_MIN_LEN} znaky.')
    if len(value) > NICKNAME_MAX_LEN:
        raise BadRequest(f'Nickname může mít nejvýše {NICKNAME_MAX_LEN} znaků.')
    if value.isdigit():
        raise BadRequest('Nickname nemůže obsahovat jen čísla.')
    return value


def validate_password(value):
    if not isinstance(value, str):
        raise BadRequest('password must be a string.')
    if len(value) < PASSWORD_MIN_LEN:
        raise BadRequest(f'Heslo musí mít alespoň {PASSWORD_MIN_LEN} znaků.')
    if len(value) > PASSWORD_MAX_LEN:
        raise BadRequest(f'Heslo může mít nejvýše {PASSWORD_MAX_LEN} znaků.')
    return value


def validate_leaderboard_post_payload(data):
    if not isinstance(data, dict):
        raise BadRequest('Leaderboard data must be a JSON object.')
    allowed = {'pps', 'total'}
    unknown = set(data.keys()) - allowed
    if unknown:
        raise BadRequest(f'Unknown fields: {", ".join(sorted(unknown))}.')
    missing = allowed - set(data.keys())
    if missing:
        raise BadRequest(f'Missing fields: {", ".join(sorted(missing))}.')
    return {
        'pps': validate_number(data['pps'], 'pps', minimum=0),
        'total': validate_number(data['total'], 'total', minimum=0),
    }


def validate_change_password_payload(data):
    if not isinstance(data, dict):
        raise BadRequest('Request body must be a JSON object.')
    allowed = {'old_password', 'new_password'}
    unknown = set(data.keys()) - allowed
    if unknown:
        raise BadRequest(f'Unknown fields: {", ".join(sorted(unknown))}.')
    missing = allowed - set(data.keys())
    if missing:
        raise BadRequest(f'Missing fields: {", ".join(sorted(missing))}.')
    return {
        'old_password': validate_password(data['old_password']),
        'new_password': validate_password(data['new_password']),
    }