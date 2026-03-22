# python.exe -m unittest discover -s testing -p "test_*.py"
import unittest
import math

from werkzeug.exceptions import BadRequest

from validation import (
    validate_earned_achievements,
    validate_boost_type,
    validate_change_password_payload,
    validate_last_login_date,
    validate_leaderboard_payload,
    validate_leaderboard_post_payload,
    validate_login_payload,
    validate_name,
    validate_number,
    validate_nickname,
    validate_password,
    validate_register_payload,
    validate_save_payload,
    validate_upgrades,
)


def build_valid_save_payload():
    return {
        'pizzeriaName': 'Moje Pizzerie',
        'money': 123.5,
        'totalEarned': 456.0,
        'clickValue': 2,
        'upgrades': {'c1': True, 'p1': False},
        'lastSave': 1730000000000,
        'earnedAchievements': {'a1': True, 'a2': False},
        'totalClicks': 42,
        'streak': 3,
        'lastLoginDate': '2026-03-22',
        'prestigeLevel': 1,
        'lastSpinDate': '2026-03-22',
        'boostType': 'pps',
        'boostMult': 2,
        'boostEnd': 1730000005000,
    }


class ValidationTests(unittest.TestCase):
    def assert_bad_request(self, fn, *args, msg_contains=None, **kwargs):
        """Pomocná metoda pro ověření, že validátor vyhodí BadRequest a volitelně obsahuje text chyby."""
        with self.assertRaises(BadRequest) as ctx:
            fn(*args, **kwargs)
        if msg_contains is not None:
            self.assertIn(msg_contains, str(ctx.exception))

    def test_validate_save_payload_accepts_valid_data(self):
        """Kontroluje happy-path pro celý save payload, aby se validní hra dala uložit bez chyby."""
        payload = build_valid_save_payload()

        validated = validate_save_payload(payload)

        self.assertEqual(validated['pizzeriaName'], 'Moje Pizzerie')
        self.assertEqual(validated['upgrades']['c1'], True)
        self.assertEqual(validated['boostType'], 'pps')
        self.assertEqual(validated['boostMult'], 2)

    def test_validate_save_payload_rejects_unknown_field(self):
        """Ověřuje odmítnutí neznámého pole, aby klient nemohl posílat nečekaná data."""
        payload = build_valid_save_payload()
        payload['unknownField'] = 1

        with self.assertRaises(BadRequest):
            validate_save_payload(payload)

    def test_validate_save_payload_requires_all_fields(self):
        """Hlídá, že povinná pole nelze vynechat, aby save měl vždy kompletní strukturu."""
        payload = build_valid_save_payload()
        payload.pop('boostEnd')

        with self.assertRaises(BadRequest):
            validate_save_payload(payload)

    def test_validate_save_payload_rejects_non_dict(self):
        """Potvrzuje, že save endpoint přijímá pouze JSON objekt a ne jiný datový typ."""
        self.assert_bad_request(validate_save_payload, [], msg_contains='JSON object')

    def test_validate_save_payload_coerces_integer_fields_from_float(self):
        """Testuje převod celočíselných float hodnot na int, aby se toleroval běžný JSON zápis čísla."""
        payload = build_valid_save_payload()
        payload['lastSave'] = 1730000000000.0
        payload['totalClicks'] = 42.0
        payload['streak'] = 3.0
        payload['prestigeLevel'] = 1.0
        payload['boostEnd'] = 1730000005000.0

        validated = validate_save_payload(payload)

        self.assertEqual(validated['lastSave'], 1730000000000)
        self.assertEqual(validated['totalClicks'], 42)
        self.assertEqual(validated['streak'], 3)
        self.assertEqual(validated['prestigeLevel'], 1)
        self.assertEqual(validated['boostEnd'], 1730000005000)

    def test_validate_save_payload_rejects_negative_money(self):
        """Zajišťuje, že peníze nemohou být záporné, což chrání konzistenci herního stavu."""
        payload = build_valid_save_payload()
        payload['money'] = -1

        self.assert_bad_request(validate_save_payload, payload, msg_contains='at least 0')

    def test_validate_save_payload_rejects_boost_mult_out_of_range(self):
        """Ověřuje horní limit násobitele boostu, aby nešlo uložit nepovoleně silný boost."""
        payload = build_valid_save_payload()
        payload['boostMult'] = 11

        self.assert_bad_request(validate_save_payload, payload, msg_contains='at most 10')

    def test_validate_save_payload_rejects_invalid_boost_type(self):
        """Kontroluje whitelist boost typů, aby prošly jen podporované hodnoty."""
        payload = build_valid_save_payload()
        payload['boostType'] = 'speed'

        self.assert_bad_request(validate_save_payload, payload, msg_contains='boostType must be null or one of')

    def test_validate_save_payload_trims_pizzeria_name(self):
        """Ověřuje normalizaci názvu pizzerie ořezáním mezer na začátku a konci."""
        payload = build_valid_save_payload()
        payload['pizzeriaName'] = '  Mega Pizza  '

        validated = validate_save_payload(payload)

        self.assertEqual(validated['pizzeriaName'], 'Mega Pizza')

    def test_validate_save_payload_rejects_unknown_upgrade_id(self):
        """Zabraňuje uložení neexistujícího upgradu, aby nebylo možné podvrhnout cizí ID."""
        payload = build_valid_save_payload()
        payload['upgrades'] = {'x999': True}

        self.assert_bad_request(validate_save_payload, payload, msg_contains='Unknown upgrade id')

    def test_validate_save_payload_rejects_unknown_achievement_id(self):
        """Hlídá, že achievements používají jen známá ID a nedochází k datovému šumu."""
        payload = build_valid_save_payload()
        payload['earnedAchievements'] = {'a999': True}

        self.assert_bad_request(validate_save_payload, payload, msg_contains='Unknown achievement id')

    def test_validate_save_payload_rejects_invalid_last_login_date_format(self):
        """Kontroluje formát data v save payloadu, aby byla data jednotná pro další zpracování."""
        payload = build_valid_save_payload()
        payload['lastLoginDate'] = '22-03-2026'

        self.assert_bad_request(validate_save_payload, payload, msg_contains='YYYY-MM-DD')

    def test_validate_number_rejects_boolean(self):
        """Ověřuje, že boolean není akceptován jako číslo, i když je v Pythonu podtyp int."""
        with self.assertRaises(BadRequest):
            validate_number(True, 'money')

    def test_validate_number_accepts_float_and_int(self):
        """Potvrzuje, že validátor čísla přijímá oba běžné numerické typy: int i float."""
        self.assertEqual(validate_number(5, 'x'), 5)
        self.assertEqual(validate_number(5.5, 'x'), 5.5)

    def test_validate_number_integer_only_converts_whole_float(self):
        """Kontroluje, že whole float je při integer_only bezpečně převeden na int."""
        self.assertEqual(validate_number(7.0, 'x', integer_only=True), 7)

    def test_validate_number_integer_only_rejects_non_integer_float(self):
        """Zajišťuje odmítnutí desetinného čísla v integer režimu, aby nebyla ztracena přesnost."""
        self.assert_bad_request(validate_number, 7.5, 'x', integer_only=True, msg_contains='must be an integer')

    def test_validate_number_rejects_nan(self):
        """Ověřuje odmítnutí NaN hodnoty, která by v datech rozbíjela výpočty a porovnávání."""
        self.assert_bad_request(validate_number, math.nan, 'x', msg_contains='finite number')

    def test_validate_number_rejects_positive_infinity(self):
        """Kontroluje, že kladné nekonečno není povoleno, protože není reprezentovatelné v běžném JSON flow."""
        self.assert_bad_request(validate_number, math.inf, 'x', msg_contains='finite number')

    def test_validate_number_rejects_negative_infinity(self):
        """Kontroluje, že záporné nekonečno není povoleno z důvodu datové korektnosti."""
        self.assert_bad_request(validate_number, -math.inf, 'x', msg_contains='finite number')

    def test_validate_number_rejects_below_minimum(self):
        """Hlídá dolní hranici numerické validace, aby neprocházely zakázané záporné hodnoty."""
        self.assert_bad_request(validate_number, -1, 'x', minimum=0, msg_contains='at least 0')

    def test_validate_number_rejects_above_maximum(self):
        """Hlídá horní hranici numerické validace, aby šly omezit extrémní hodnoty."""
        self.assert_bad_request(validate_number, 11, 'x', maximum=10, msg_contains='at most 10')

    def test_validate_boost_type_accepts_none_and_known_values(self):
        """Ověřuje všechny povolené varianty boostType včetně null hodnoty."""
        self.assertIsNone(validate_boost_type(None))
        self.assertEqual(validate_boost_type('click'), 'click')
        self.assertEqual(validate_boost_type('pps'), 'pps')
        self.assertEqual(validate_boost_type('all'), 'all')

    def test_validate_boost_type_rejects_invalid_value(self):
        """Potvrzuje odmítnutí nepovoleného boostType, aby se držel kontrakt API."""
        with self.assertRaises(BadRequest):
            validate_boost_type('invalid')

    def test_validate_name_trims_whitespace(self):
        """Testuje ořez mezer u obecného názvu, aby uložená data byla čistá."""
        self.assertEqual(validate_name('  Pizza Lab  ', 'name'), 'Pizza Lab')

    def test_validate_name_rejects_empty_after_trim(self):
        """Zajišťuje, že název složený jen z mezer je odmítnut jako prázdný vstup."""
        self.assert_bad_request(validate_name, '   ', 'name', msg_contains='cannot be empty')

    def test_validate_name_rejects_non_string(self):
        """Ověřuje typovou kontrolu názvu, aby nedocházelo k ukládání čísel či jiných typů."""
        self.assert_bad_request(validate_name, 123, 'name', msg_contains='must be a string')

    def test_validate_name_rejects_too_long(self):
        """Kontroluje maximální délku názvu kvůli UI limitům a databázové konzistenci."""
        self.assert_bad_request(validate_name, 'x' * 31, 'name', msg_contains='at most 30 characters')

    def test_validate_name_rejects_numeric_only(self):
        """Brání názvu tvořenému pouze čísly, aby uživatelské jméno zůstalo čitelné."""
        self.assert_bad_request(validate_name, '123456', 'name', msg_contains='only numbers')

    def test_validate_nickname_rejects_numeric_only(self):
        """Specificky testuje, že přezdívka nesmí být jen čísla."""
        with self.assertRaises(BadRequest):
            validate_nickname('12345')

    def test_validate_nickname_trims_whitespace(self):
        """Ověřuje trimnutí přezdívky, aby se neukládaly náhodné okolní mezery."""
        self.assertEqual(validate_nickname('  Pepa123  '), 'Pepa123')

    def test_validate_nickname_rejects_too_short(self):
        """Hlídá minimální délku přezdívky kvůli použitelnosti a anti-spam pravidlům."""
        self.assert_bad_request(validate_nickname, 'ab', msg_contains='alespoň')

    def test_validate_nickname_rejects_too_long(self):
        """Hlídá maximální délku přezdívky, aby nepřetěžovala UI ani úložiště."""
        self.assert_bad_request(validate_nickname, 'x' * 31, msg_contains='nejvýše')

    def test_validate_password_accepts_boundary_lengths(self):
        """Testuje hraniční povolené délky hesla (minimum i maximum)."""
        self.assertEqual(validate_password('x' * 6), 'x' * 6)
        self.assertEqual(validate_password('x' * 128), 'x' * 128)

    def test_validate_password_rejects_too_short(self):
        """Ověřuje odmítnutí krátkého hesla kvůli základní bezpečnosti účtu."""
        self.assert_bad_request(validate_password, 'short', msg_contains='alespoň')

    def test_validate_password_rejects_too_long(self):
        """Ověřuje odmítnutí přehnaně dlouhého hesla dle definovaného limitu API."""
        self.assert_bad_request(validate_password, 'x' * 129, msg_contains='nejvýše')

    def test_validate_register_payload_accepts_valid_data(self):
        """Kontroluje validní registraci, aby endpoint správně propustil korektní payload."""
        result = validate_register_payload({'nickname': 'Pepa123', 'password': 'tajneheslo'})

        self.assertEqual(result['nickname'], 'Pepa123')
        self.assertEqual(result['password'], 'tajneheslo')

    def test_validate_register_payload_rejects_unknown_fields(self):
        """Ověřuje odmítnutí neznámých polí při registraci kvůli striktnímu API kontraktu."""
        self.assert_bad_request(
            validate_register_payload,
            {'nickname': 'Pepa123', 'password': 'tajneheslo', 'x': 1},
            msg_contains='Unknown fields'
        )

    def test_validate_register_payload_rejects_missing_fields(self):
        """Kontroluje, že registrace bez povinného pole spadne s validací."""
        self.assert_bad_request(validate_register_payload, {'nickname': 'Pepa123'}, msg_contains='Missing fields')

    def test_validate_login_payload_accepts_valid_data(self):
        """Ověřuje happy-path login payloadu, aby přihlášení fungovalo s validními vstupy."""
        result = validate_login_payload({'nickname': 'Pepa123', 'password': 'tajneheslo'})

        self.assertEqual(result['nickname'], 'Pepa123')
        self.assertEqual(result['password'], 'tajneheslo')

    def test_validate_login_payload_rejects_non_dict(self):
        """Hlídá, že login endpoint přijme jen JSON objekt a ne třeba řetězec."""
        self.assert_bad_request(validate_login_payload, 'bad', msg_contains='JSON object')

    def test_validate_leaderboard_payload_accepts_valid_list(self):
        """Kontroluje, že seznam leaderboard položek se správnou strukturou projde validací."""
        payload = [
            {'name': 'A', 'pps': 10, 'total': 200},
            {'name': 'B', 'pps': 5.5, 'total': 150.2},
        ]

        validated = validate_leaderboard_payload(payload)

        self.assertEqual(len(validated), 2)
        self.assertEqual(validated[0]['name'], 'A')
        self.assertEqual(validated[1]['pps'], 5.5)

    def test_validate_leaderboard_payload_rejects_non_list(self):
        """Ověřuje typovou kontrolu leaderboardu, který musí být seznam."""
        self.assert_bad_request(validate_leaderboard_payload, {}, msg_contains='JSON array')

    def test_validate_leaderboard_payload_rejects_more_than_ten_entries(self):
        """Testuje limit počtu položek leaderboardu, aby klient neposílal příliš velké payloady."""
        payload = [{'name': 'A', 'pps': 1, 'total': 1}] * 11
        self.assert_bad_request(validate_leaderboard_payload, payload, msg_contains='at most 10 entries')

    def test_validate_leaderboard_payload_rejects_unknown_entry_fields(self):
        """Zajišťuje, že položka leaderboardu nemá žádné nepovolené klíče."""
        payload = [{'name': 'A', 'pps': 1, 'total': 1, 'extra': 9}]
        self.assert_bad_request(validate_leaderboard_payload, payload, msg_contains='Unknown leaderboard fields')

    def test_validate_leaderboard_payload_rejects_missing_entry_fields(self):
        """Kontroluje, že každá položka leaderboardu obsahuje všechna povinná pole."""
        payload = [{'name': 'A', 'pps': 1}]
        self.assert_bad_request(validate_leaderboard_payload, payload, msg_contains='Missing leaderboard fields')

    def test_validate_leaderboard_payload_rejects_negative_values(self):
        """Ověřuje, že pps a total v leaderboardu nemohou být záporné."""
        payload = [{'name': 'A', 'pps': -1, 'total': 1}]
        self.assert_bad_request(validate_leaderboard_payload, payload, msg_contains='at least 0')

    def test_validate_last_login_date_accepts_none(self):
        """Testuje povolení null hodnoty pro datum posledního přihlášení."""
        self.assertIsNone(validate_last_login_date(None))

    def test_validate_last_login_date_accepts_valid_format(self):
        """Kontroluje, že datum v ISO formátu YYYY-MM-DD je validní."""
        self.assertEqual(validate_last_login_date('2026-03-22'), '2026-03-22')

    def test_validate_last_login_date_rejects_non_string(self):
        """Ověřuje, že datum musí být string (nebo null), ne číslo."""
        self.assert_bad_request(validate_last_login_date, 20260322, msg_contains='string or null')

    def test_validate_last_login_date_rejects_invalid_format(self):
        """Hlídá striktní formát data, aby backend pracoval s jednotným tvarem."""
        self.assert_bad_request(validate_last_login_date, '2026/03/22', msg_contains='YYYY-MM-DD')

    def test_validate_upgrades_accepts_valid_mapping(self):
        """Ověřuje validní mapu upgrade ID na bool příznaky nákupu."""
        result = validate_upgrades({'c1': True, 'p1': False})
        self.assertEqual(result, {'c1': True, 'p1': False})

    def test_validate_upgrades_rejects_non_dict(self):
        """Kontroluje, že upgrades jsou objekt a ne seznam nebo jiný typ."""
        self.assert_bad_request(validate_upgrades, [], msg_contains='must be an object')

    def test_validate_upgrades_rejects_unknown_id(self):
        """Zajišťuje odmítnutí neznámého upgrade ID kvůli ochraně před podvrženými daty."""
        self.assert_bad_request(validate_upgrades, {'z1': True}, msg_contains='Unknown upgrade id')

    def test_validate_upgrades_rejects_non_boolean_value(self):
        """Ověřuje, že hodnota upgradu musí být bool, nikoli číslo nebo text."""
        self.assert_bad_request(validate_upgrades, {'c1': 1}, msg_contains='must be true or false')

    def test_validate_earned_achievements_accepts_valid_mapping(self):
        """Kontroluje validní mapu achievement ID na bool, která reprezentuje získané úspěchy."""
        result = validate_earned_achievements({'a1': True, 'a2': False})
        self.assertEqual(result, {'a1': True, 'a2': False})

    def test_validate_earned_achievements_rejects_non_dict(self):
        """Ověřuje, že achievements musí být JSON objekt."""
        self.assert_bad_request(validate_earned_achievements, [], msg_contains='must be an object')

    def test_validate_earned_achievements_rejects_unknown_id(self):
        """Zabraňuje ukládání neznámých achievement ID, která aplikace nepodporuje."""
        self.assert_bad_request(validate_earned_achievements, {'a99': True}, msg_contains='Unknown achievement id')

    def test_validate_earned_achievements_rejects_non_boolean_value(self):
        """Hlídá, že hodnoty achievementů jsou jen true/false a ne textové náhrady."""
        self.assert_bad_request(
            validate_earned_achievements,
            {'a1': 'yes'},
            msg_contains='must be true or false'
        )

    def test_validate_leaderboard_post_payload_requires_keys(self):
        """Ověřuje, že leaderboard POST payload obsahuje obě povinná pole pps i total."""
        with self.assertRaises(BadRequest):
            validate_leaderboard_post_payload({'pps': 10})

    def test_validate_leaderboard_post_payload_accepts_valid_data(self):
        """Kontroluje korektní payload pro odeslání score do leaderboardu."""
        result = validate_leaderboard_post_payload({'pps': 12.5, 'total': 500})
        self.assertEqual(result['pps'], 12.5)
        self.assertEqual(result['total'], 500)

    def test_validate_leaderboard_post_payload_rejects_unknown_fields(self):
        """Zajišťuje, že POST leaderboard nepřijme nepovolené klíče navíc."""
        self.assert_bad_request(
            validate_leaderboard_post_payload,
            {'pps': 1, 'total': 2, 'rank': 1},
            msg_contains='Unknown fields'
        )

    def test_validate_leaderboard_post_payload_rejects_negative_values(self):
        """Hlídá nezápornost leaderboard metrik v POST payloadu."""
        self.assert_bad_request(validate_leaderboard_post_payload, {'pps': -1, 'total': 2}, msg_contains='at least 0')

    def test_validate_change_password_payload_accepts_valid_data(self):
        """Ověřuje happy-path změny hesla, kdy jsou obě hesla ve správném formátu."""
        result = validate_change_password_payload({
            'old_password': 'abc12345',
            'new_password': 'newpass123',
        })

        self.assertEqual(result['old_password'], 'abc12345')
        self.assertEqual(result['new_password'], 'newpass123')

    def test_validate_change_password_payload_rejects_unknown_fields(self):
        """Kontroluje, že změna hesla odmítne neznámé pole a drží API kontrakt."""
        self.assert_bad_request(
            validate_change_password_payload,
            {'old_password': 'abc12345', 'new_password': 'newpass123', 'x': 1},
            msg_contains='Unknown fields'
        )

    def test_validate_change_password_payload_rejects_missing_fields(self):
        """Ověřuje povinnost poslat staré i nové heslo v jednom requestu."""
        self.assert_bad_request(
            validate_change_password_payload,
            {'old_password': 'abc12345'},
            msg_contains='Missing fields'
        )

    def test_validate_change_password_payload_rejects_short_new_password(self):
        """Hlídá minimální délku nového hesla při změně hesla."""
        self.assert_bad_request(
            validate_change_password_payload,
            {'old_password': 'abc12345', 'new_password': '123'},
            msg_contains='alespoň'
        )


if __name__ == '__main__':
    unittest.main()
