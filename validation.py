import math
from werkzeug.exceptions import BadRequest


ALLOWED_SAVE_KEYS = {'pizzeriaName', 'money', 'totalEarned', 'clickValue', 'upgrades', 'lastSave'}
ALLOWED_UPGRADE_IDS = {
    'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'c10', 'c11', 'c12',
    'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10'
}


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

    return {
        'pizzeriaName': pizzeria_name,
        'money': money,
        'totalEarned': total_earned,
        'clickValue': click_value,
        'upgrades': upgrades,
        'lastSave': last_save,
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


def validate_number(value, field_name, minimum=None, integer_only=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadRequest(f'{field_name} must be a number.')

    if not math.isfinite(value):
        raise BadRequest(f'{field_name} must be a finite number.')

    if minimum is not None and value < minimum:
        raise BadRequest(f'{field_name} must be at least {minimum}.')

    if integer_only:
        if isinstance(value, float) and not value.is_integer():
            raise BadRequest(f'{field_name} must be an integer.')
        return int(value)

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