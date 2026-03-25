# python -m unittest discover -s testing -p "test_*.py"
"""
TC04 – Hraniční případy uložení herního stavu (Save-Payload Edge Cases)
=======================================================================

Tento soubor pokrývá vyčerpávající testy hranic a kombinací pro validate_save_payload.
Každý test ověřuje přesně jedno pravidlo nebo hraniční hodnotu, aby byl výsledek
snadno čitelný a přesně lokalizovatelný v případě selhání.

Oblasti pokryté testy
---------------------
1.  Číselná pole – nulové, záporné, maximální a mimořádně velké hodnoty
2.  Celočíselná koerce – float hodnoty na hranici celého čísla
3.  Pole upgrades – všechna povolená ID (c1–c12, p1–p10)
4.  Pole earnedAchievements – všechna povolená ID (a1–a21)
5.  Pole boostType + boostMult + boostEnd – platné i neplatné kombinace
6.  Pole pizzeriaName – mezní délky, ořez mezer, čistě číselné hodnoty
7.  Pole lastLoginDate / lastSpinDate – formát ISO 8601, null vs. string
8.  Struktura payloadu – chybějící pole, nadbytečná pole, špatný typ kořene
"""

import math
import sys
import os
import unittest

# Přidáme kořenový adresář projektu do cesty pro import modulů
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from werkzeug.exceptions import BadRequest

from validation import validate_save_payload


# ---------------------------------------------------------------------------
# Pomocná funkce – vytvoří validní payload pro modifikaci v jednotlivých testech
# ---------------------------------------------------------------------------

def _valid():
    """Vrátí kompletní validní save payload se smysluplnými výchozími hodnotami."""
    return {
        'pizzeriaName': 'Testovací Pizzerie',
        'money': 0.0,
        'totalEarned': 0.0,
        'clickValue': 1,
        'upgrades': {},
        'lastSave': 1_700_000_000_000,
        'earnedAchievements': {},
        'totalClicks': 0,
        'streak': 0,
        'lastLoginDate': None,
        'prestigeLevel': 0,
        'lastSpinDate': None,
        'boostType': None,
        'boostMult': 1,
        'boostEnd': 0,
    }


class TC04_SavePayload_NumericFields(unittest.TestCase):
    """Testy hranic číselných polí v save payloadu."""

    def test_money_exact_zero_is_accepted(self):
        """money = 0 musí být povoleno – nový hráč začíná bez peněz."""
        p = _valid()
        p['money'] = 0
        result = validate_save_payload(p)
        self.assertEqual(result['money'], 0)

    def test_money_large_value_is_accepted(self):
        """money = 1e18 (kvintilion) musí projít – hra nemá strop hotovosti."""
        p = _valid()
        p['money'] = 1e18
        result = validate_save_payload(p)
        self.assertEqual(result['money'], 1e18)

    def test_money_negative_one_is_rejected(self):
        """money = -1 musí být odmítnuto – záporná hotovost nedává herní smysl."""
        p = _valid()
        p['money'] = -1
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('at least 0', str(ctx.exception))

    def test_money_negative_float_is_rejected(self):
        """money = -0.01 musí být odmítnuto i jako nepatrné záporné číslo."""
        p = _valid()
        p['money'] = -0.01
        with self.assertRaises(BadRequest):
            validate_save_payload(p)

    def test_total_earned_zero_is_accepted(self):
        """totalEarned = 0 odpovídá novému hráči a musí být platné."""
        p = _valid()
        p['totalEarned'] = 0
        result = validate_save_payload(p)
        self.assertEqual(result['totalEarned'], 0)

    def test_total_earned_prestige_threshold_value_is_accepted(self):
        """totalEarned = 1e9 (práh prestige) musí být uložitelné."""
        p = _valid()
        p['totalEarned'] = 1_000_000_000.0
        result = validate_save_payload(p)
        self.assertEqual(result['totalEarned'], 1_000_000_000.0)

    def test_click_value_minimum_one_is_accepted(self):
        """clickValue = 1 je výchozí a musí být platné."""
        p = _valid()
        p['clickValue'] = 1
        result = validate_save_payload(p)
        self.assertEqual(result['clickValue'], 1)

    def test_click_value_zero_is_rejected(self):
        """clickValue = 0 musí být odmítnuto – kliknutí nesmí vydělat nula euro."""
        p = _valid()
        p['clickValue'] = 0
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('at least 1', str(ctx.exception))

    def test_total_clicks_zero_is_accepted(self):
        """totalClicks = 0 odpovídá hráči, který ještě neklikal."""
        p = _valid()
        p['totalClicks'] = 0
        result = validate_save_payload(p)
        self.assertEqual(result['totalClicks'], 0)

    def test_total_clicks_large_value_is_accepted(self):
        """totalClicks = 10_000_000 musí být platné – oddaný hráč může klikat milionkrát."""
        p = _valid()
        p['totalClicks'] = 10_000_000
        result = validate_save_payload(p)
        self.assertEqual(result['totalClicks'], 10_000_000)

    def test_streak_zero_is_accepted(self):
        """streak = 0 je výchozí stav pro nového hráče."""
        p = _valid()
        p['streak'] = 0
        result = validate_save_payload(p)
        self.assertEqual(result['streak'], 0)

    def test_streak_large_value_is_accepted(self):
        """streak = 365 odpovídá hráči s ročním přihlašovacím rekordem."""
        p = _valid()
        p['streak'] = 365
        result = validate_save_payload(p)
        self.assertEqual(result['streak'], 365)

    def test_prestige_level_zero_is_accepted(self):
        """prestigeLevel = 0 je výchozí stav hráče bez prestige."""
        p = _valid()
        p['prestigeLevel'] = 0
        result = validate_save_payload(p)
        self.assertEqual(result['prestigeLevel'], 0)

    def test_prestige_level_ten_is_accepted(self):
        """prestigeLevel = 10 je doložitelný stav (achievement 'Pizzový bůh')."""
        p = _valid()
        p['prestigeLevel'] = 10
        result = validate_save_payload(p)
        self.assertEqual(result['prestigeLevel'], 10)

    def test_boost_mult_minimum_one_is_accepted(self):
        """boostMult = 1 odpovídá žádnému aktivnímu boostu nebo nulové výhody."""
        p = _valid()
        p['boostMult'] = 1
        result = validate_save_payload(p)
        self.assertEqual(result['boostMult'], 1)

    def test_boost_mult_maximum_ten_is_accepted(self):
        """boostMult = 10 je povolená horní hranice násobitele boostu."""
        p = _valid()
        p['boostMult'] = 10
        result = validate_save_payload(p)
        self.assertEqual(result['boostMult'], 10)

    def test_boost_mult_eleven_is_rejected(self):
        """boostMult = 11 překračuje horní hranici a musí být odmítnuto."""
        p = _valid()
        p['boostMult'] = 11
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('at most 10', str(ctx.exception))

    def test_boost_end_zero_is_accepted(self):
        """boostEnd = 0 signalizuje, že žádný boost není aktivní."""
        p = _valid()
        p['boostEnd'] = 0
        result = validate_save_payload(p)
        self.assertEqual(result['boostEnd'], 0)

    def test_nan_money_is_rejected(self):
        """money = NaN musí být odmítnuto – NaN rozbíjí porovnávání i výpočty."""
        p = _valid()
        p['money'] = math.nan
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('finite', str(ctx.exception))

    def test_infinity_total_earned_is_rejected(self):
        """totalEarned = Infinity musí být odmítnuto – nekonečno nelze uložit do DB."""
        p = _valid()
        p['totalEarned'] = math.inf
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('finite', str(ctx.exception))


class TC04_SavePayload_IntegerCoercion(unittest.TestCase):
    """Testy automatické koerce float → int pro celočíselná pole."""

    def test_last_save_whole_float_is_coerced(self):
        """lastSave = 1.7e12 (jako float) musí být převeden na int bez ztráty informace."""
        p = _valid()
        p['lastSave'] = 1_700_000_000_000.0
        result = validate_save_payload(p)
        self.assertIsInstance(result['lastSave'], int)
        self.assertEqual(result['lastSave'], 1_700_000_000_000)

    def test_total_clicks_whole_float_is_coerced(self):
        """totalClicks = 1000.0 (float bez desetinné části) musí být převeden na 1000."""
        p = _valid()
        p['totalClicks'] = 1000.0
        result = validate_save_payload(p)
        self.assertIsInstance(result['totalClicks'], int)
        self.assertEqual(result['totalClicks'], 1000)

    def test_streak_whole_float_is_coerced(self):
        """streak = 7.0 musí být koercováno na int 7."""
        p = _valid()
        p['streak'] = 7.0
        result = validate_save_payload(p)
        self.assertIsInstance(result['streak'], int)
        self.assertEqual(result['streak'], 7)

    def test_prestige_level_whole_float_is_coerced(self):
        """prestigeLevel = 3.0 musí být koercováno na int 3."""
        p = _valid()
        p['prestigeLevel'] = 3.0
        result = validate_save_payload(p)
        self.assertIsInstance(result['prestigeLevel'], int)
        self.assertEqual(result['prestigeLevel'], 3)

    def test_boost_end_whole_float_is_coerced(self):
        """boostEnd = 1.7e12 jako float musí být koercováno na int."""
        p = _valid()
        p['boostEnd'] = 1_700_000_000_000.0
        result = validate_save_payload(p)
        self.assertIsInstance(result['boostEnd'], int)

    def test_total_clicks_decimal_float_is_rejected(self):
        """totalClicks = 42.5 (desetinný float) musí být odmítnuto jako neplatné celé číslo."""
        p = _valid()
        p['totalClicks'] = 42.5
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('must be an integer', str(ctx.exception))

    def test_streak_decimal_float_is_rejected(self):
        """streak = 1.1 musí být odmítnuto – streak je vždy celé číslo."""
        p = _valid()
        p['streak'] = 1.1
        with self.assertRaises(BadRequest):
            validate_save_payload(p)


class TC04_SavePayload_UpgradeIDs(unittest.TestCase):
    """Testy všech povolených a zakázaných upgrade ID."""

    def _buy(self, upgrade_id):
        """Vrátí payload s jediným zakoupeným upgradem."""
        p = _valid()
        p['upgrades'] = {upgrade_id: True}
        return validate_save_payload(p)

    # Klikací upgrady c1–c12
    def test_upgrade_c1_is_accepted(self):
        """c1 'Lepší recept' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c1')['upgrades']['c1'])

    def test_upgrade_c2_is_accepted(self):
        """c2 'Tajná omáčka' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c2')['upgrades']['c2'])

    def test_upgrade_c3_is_accepted(self):
        """c3 'Speciální těsto' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c3')['upgrades']['c3'])

    def test_upgrade_c4_is_accepted(self):
        """c4 'Mistr pizzar' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c4')['upgrades']['c4'])

    def test_upgrade_c5_is_accepted(self):
        """c5 'Zlaté ruce' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c5')['upgrades']['c5'])

    def test_upgrade_c6_is_accepted(self):
        """c6 'Perfektní slice' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c6')['upgrades']['c6'])

    def test_upgrade_c7_is_accepted(self):
        """c7 'Mistrný řez' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c7')['upgrades']['c7'])

    def test_upgrade_c8_is_accepted(self):
        """c8 'Pizza guru' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c8')['upgrades']['c8'])

    def test_upgrade_c9_is_accepted(self):
        """c9 'Legenda ulice' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c9')['upgrades']['c9'])

    def test_upgrade_c10_is_accepted(self):
        """c10 'Diamantová pizza' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c10')['upgrades']['c10'])

    def test_upgrade_c11_is_accepted(self):
        """c11 'Šampanská kůrka' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c11')['upgrades']['c11'])

    def test_upgrade_c12_is_accepted(self):
        """c12 'Kosmická pizza' musí být platné upgrade ID."""
        self.assertTrue(self._buy('c12')['upgrades']['c12'])

    # PPS upgrady p1–p10
    def test_upgrade_p1_is_accepted(self):
        """p1 'Rychlejší trouba' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p1')['upgrades']['p1'])

    def test_upgrade_p2_is_accepted(self):
        """p2 'Optimalizace výroby' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p2')['upgrades']['p2'])

    def test_upgrade_p3_is_accepted(self):
        """p3 'Moderní vybavení' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p3')['upgrades']['p3'])

    def test_upgrade_p4_is_accepted(self):
        """p4 'AI asistent' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p4')['upgrades']['p4'])

    def test_upgrade_p5_is_accepted(self):
        """p5 'Robotická linka' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p5')['upgrades']['p5'])

    def test_upgrade_p6_is_accepted(self):
        """p6 'Kvantová pec' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p6')['upgrades']['p6'])

    def test_upgrade_p7_is_accepted(self):
        """p7 'Turbo ingredience' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p7')['upgrades']['p7'])

    def test_upgrade_p8_is_accepted(self):
        """p8 'Geneticky lepší mouka' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p8')['upgrades']['p8'])

    def test_upgrade_p9_is_accepted(self):
        """p9 'Globální síť pecí' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p9')['upgrades']['p9'])

    def test_upgrade_p10_is_accepted(self):
        """p10 'Vesmírná pizzerie' musí být platné upgrade ID."""
        self.assertTrue(self._buy('p10')['upgrades']['p10'])

    def test_all_22_upgrades_purchased_is_accepted(self):
        """Payload se všemi 22 nakoupenými upgrady musí projít – stav po dokončení hry."""
        p = _valid()
        all_ids = [f'c{i}' for i in range(1, 13)] + [f'p{i}' for i in range(1, 11)]
        p['upgrades'] = {uid: True for uid in all_ids}
        result = validate_save_payload(p)
        self.assertEqual(len(result['upgrades']), 22)

    def test_upgrade_c0_is_rejected(self):
        """c0 neexistuje v seznamu upgradů a musí být odmítnuto."""
        p = _valid()
        p['upgrades'] = {'c0': True}
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('Unknown upgrade id', str(ctx.exception))

    def test_upgrade_p11_is_rejected(self):
        """p11 neexistuje – hra má jen p1–p10 a podvrh musí být odmítnut."""
        p = _valid()
        p['upgrades'] = {'p11': True}
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('Unknown upgrade id', str(ctx.exception))

    def test_upgrade_value_string_is_rejected(self):
        """Hodnota upgradu jako řetězec ('true') nesmí projít validací – musí být bool."""
        p = _valid()
        p['upgrades'] = {'c1': 'true'}
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('must be true or false', str(ctx.exception))


class TC04_SavePayload_DateFields(unittest.TestCase):
    """Testy datových polí lastLoginDate a lastSpinDate."""

    def test_last_login_date_none_is_accepted(self):
        """lastLoginDate = None je výchozí stav pro nového hráče."""
        p = _valid()
        p['lastLoginDate'] = None
        result = validate_save_payload(p)
        self.assertIsNone(result['lastLoginDate'])

    def test_last_login_date_valid_iso_is_accepted(self):
        """lastLoginDate = '2026-03-25' v korektním ISO 8601 formátu musí projít."""
        p = _valid()
        p['lastLoginDate'] = '2026-03-25'
        result = validate_save_payload(p)
        self.assertEqual(result['lastLoginDate'], '2026-03-25')

    def test_last_login_date_wrong_separator_is_rejected(self):
        """lastLoginDate = '2026/03/25' s lomítky místo pomlček musí být odmítnuto."""
        p = _valid()
        p['lastLoginDate'] = '2026/03/25'
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('YYYY-MM-DD', str(ctx.exception))

    def test_last_login_date_dd_mm_yyyy_format_is_rejected(self):
        """lastLoginDate = '25-03-2026' (evropský formát) musí být odmítnuto."""
        p = _valid()
        p['lastLoginDate'] = '25-03-2026'
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('YYYY-MM-DD', str(ctx.exception))

    def test_last_login_date_integer_is_rejected(self):
        """lastLoginDate = 20260325 (číslo místo stringu) musí být odmítnuto."""
        p = _valid()
        p['lastLoginDate'] = 20260325
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('string or null', str(ctx.exception))

    def test_last_spin_date_none_is_accepted(self):
        """lastSpinDate = None je výchozí stav hráče, který ještě nepointoval kolečkem."""
        p = _valid()
        p['lastSpinDate'] = None
        result = validate_save_payload(p)
        self.assertIsNone(result['lastSpinDate'])

    def test_last_spin_date_today_is_accepted(self):
        """lastSpinDate = '2026-03-25' označující dnešní datum musí projít."""
        p = _valid()
        p['lastSpinDate'] = '2026-03-25'
        result = validate_save_payload(p)
        self.assertEqual(result['lastSpinDate'], '2026-03-25')


class TC04_SavePayload_PizzeriaNamField(unittest.TestCase):
    """Testy pole pizzeriaName – délka, typ, ořez, číselné hodnoty."""

    def test_name_exactly_30_chars_is_accepted(self):
        """pizzeriaName o délce přesně 30 znaků musí projít – je na hranici limitu."""
        p = _valid()
        p['pizzeriaName'] = 'A' * 30
        result = validate_save_payload(p)
        self.assertEqual(len(result['pizzeriaName']), 30)

    def test_name_31_chars_is_rejected(self):
        """pizzeriaName o délce 31 znaků překračuje limit a musí být odmítnuto."""
        p = _valid()
        p['pizzeriaName'] = 'A' * 31
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('at most 30 characters', str(ctx.exception))

    def test_name_with_leading_trailing_spaces_is_trimmed(self):
        """pizzeriaName '  Pepino  ' musí být ořezáno na 'Pepino'."""
        p = _valid()
        p['pizzeriaName'] = '  Pepino  '
        result = validate_save_payload(p)
        self.assertEqual(result['pizzeriaName'], 'Pepino')

    def test_name_only_digits_is_rejected(self):
        """pizzeriaName = '12345' tvořený jen číslicemi musí být odmítnuto."""
        p = _valid()
        p['pizzeriaName'] = '12345'
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('only numbers', str(ctx.exception))

    def test_name_whitespace_only_is_rejected(self):
        """pizzeriaName = '   ' (jen mezery) po ořezu je prázdný a musí být odmítnuto."""
        p = _valid()
        p['pizzeriaName'] = '   '
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('cannot be empty', str(ctx.exception))

    def test_name_integer_type_is_rejected(self):
        """pizzeriaName jako číslo (int) místo stringu musí být odmítnuto."""
        p = _valid()
        p['pizzeriaName'] = 42
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('must be a string', str(ctx.exception))


class TC04_SavePayload_Structure(unittest.TestCase):
    """Testy struktury payloadu – chybějící pole, nadbytečná pole, špatný typ kořene."""

    def test_valid_payload_returns_all_expected_keys(self):
        """Validní payload musí vrátit výsledek obsahující všechna očekávaná pole."""
        result = validate_save_payload(_valid())
        expected_keys = {
            'pizzeriaName', 'money', 'totalEarned', 'clickValue', 'upgrades',
            'lastSave', 'earnedAchievements', 'totalClicks', 'streak',
            'lastLoginDate', 'prestigeLevel', 'lastSpinDate',
            'boostType', 'boostMult', 'boostEnd',
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_list_root_is_rejected(self):
        """Save payload jako seznam místo objektu musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload([])
        self.assertIn('JSON object', str(ctx.exception))

    def test_string_root_is_rejected(self):
        """Save payload jako řetězec musí být odmítnuto."""
        with self.assertRaises(BadRequest):
            validate_save_payload('{"money":0}')

    def test_extra_field_is_rejected(self):
        """Payload s neznámým polem 'hack' musí být odmítnuto."""
        p = _valid()
        p['hack'] = 999
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('Unknown save fields', str(ctx.exception))

    def test_missing_field_money_is_rejected(self):
        """Payload bez povinného pole 'money' musí být odmítnuto."""
        p = _valid()
        del p['money']
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('Missing save fields', str(ctx.exception))

    def test_missing_field_upgrades_is_rejected(self):
        """Payload bez povinného pole 'upgrades' musí být odmítnuto."""
        p = _valid()
        del p['upgrades']
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('Missing save fields', str(ctx.exception))

    def test_boolean_root_is_rejected(self):
        """Payload jako boolean hodnota musí být odmítnuto."""
        with self.assertRaises(BadRequest):
            validate_save_payload(True)

    def test_empty_dict_is_rejected(self):
        """Prázdný objekt {} musí být odmítnuto kvůli chybějícím polím."""
        with self.assertRaises(BadRequest):
            validate_save_payload({})


if __name__ == '__main__':
    unittest.main()
