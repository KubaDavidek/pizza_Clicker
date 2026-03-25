# python -m unittest discover -s testing -p "test_*.py"
"""
TC06 – Systém achievementů (odměn za splnění podmínek)
=======================================================

Tento soubor pokrývá kompletní testování validace achievementů: všechna
platná ID (a1–a21), prázdné stavy, plně splněné sady, smíšené hodnoty
a všechny neplatné vstupy.

Oblasti pokryté testy
---------------------
1.  Každé jednotlivé achievement ID (a1–a21) – platné přijetí
2.  Prázdná mapa achievementů – výchozí stav nového hráče
3.  Všechna ID najednou (plná mapa) – stav po 100% dokončení
4.  Hodnoty True vs. False pro každý achievement
5.  Neznámá ID (a0, a22, a99, neplatný formát)
6.  Špatný typ hodnoty (řetězec, číslo, None)
7.  Špatný typ samotného pole achievementů (seznam, řetězec)
8.  Kombinace achievement ID s herními podmínkami odpovídajícími jejich popisům
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from werkzeug.exceptions import BadRequest

from validation import validate_earned_achievements, validate_save_payload


# ---------------------------------------------------------------------------
# Pomocné funkce
# ---------------------------------------------------------------------------

def _save_with_achievements(achievements: dict) -> dict:
    """Vrátí kompletní save payload s danými achievements."""
    return {
        'pizzeriaName': 'Achievement Lab',
        'money': 0,
        'totalEarned': 0,
        'clickValue': 1,
        'upgrades': {},
        'lastSave': 1_700_000_000_000,
        'earnedAchievements': achievements,
        'totalClicks': 0,
        'streak': 0,
        'lastLoginDate': None,
        'prestigeLevel': 0,
        'lastSpinDate': None,
        'boostType': None,
        'boostMult': 1,
        'boostEnd': 0,
    }


# Popis všech 21 achievementů pro dokumentaci
ACHIEVEMENT_DESCRIPTIONS = {
    'a1':  'První krok – kliknout 1× na pizzu',
    'a2':  'Tisícář – vydělat 1 000 € celkem',
    'a3':  'Nakupuji! – koupit 1 upgrade',
    'a4':  'Klikací stroj – 1 000 kliknutí celkem',
    'a5':  'Sto tisíc! – vydělat 100 000 € celkem',
    'a6':  'Technik – koupit 5 upgradů',
    'a7':  'Průmyslník – vydělat 10 000 000 € celkem',
    'a8':  'Pizza maniak – 10 000 kliknutí celkem',
    'a9':  'Miliardář – vydělat 1 000 000 000 € celkem',
    'a10': 'Sběratel – koupit 10 upgradů',
    'a11': 'Klikací legenda – 100 000 kliknutí celkem',
    'a12': 'Biliardář – vydělat 1 000 000 000 000 € celkem',
    'a13': 'Rychlá pizzerie – dosáhnout 1 000 €/s PPS',
    'a14': 'Perfekcionista – koupit všech 22 upgradů',
    'a15': 'Král pizzy – vydělat 1 000 000 000 000 000 € celkem',
    'a16': 'Pravidelník – 3 dny streak',
    'a17': 'Věrný zákazník – 7 dní streak',
    'a18': 'Pizzový fanatik – 30 dní streak',
    'a19': 'Nový začátek – dosáhnout prestige úrovně 1',
    'a20': 'Veterán – dosáhnout prestige úrovně 5',
    'a21': 'Pizzový bůh – dosáhnout prestige úrovně 10',
}


# ---------------------------------------------------------------------------
# Testy každého jednotlivého achievement ID
# ---------------------------------------------------------------------------

class TC06_IndividualAchievementIDs(unittest.TestCase):
    """Ověřuje, že každé ze 21 achievement ID je individuálně akceptováno."""

    def _assert_single_achievement_accepted(self, ach_id):
        result = validate_earned_achievements({ach_id: True})
        self.assertTrue(result[ach_id])

    def test_a1_prvni_krok_is_accepted(self):
        """a1 'První krok' – nejzákladnější achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a1')

    def test_a2_tisicár_is_accepted(self):
        """a2 'Tisícář' – první finanční milestone musí být platné ID."""
        self._assert_single_achievement_accepted('a2')

    def test_a3_nakupuji_is_accepted(self):
        """a3 'Nakupuji!' – první upgrade achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a3')

    def test_a4_klikaci_stroj_is_accepted(self):
        """a4 'Klikací stroj' – tisíc kliků achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a4')

    def test_a5_sto_tisic_is_accepted(self):
        """a5 'Sto tisíc!' – 100K€ achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a5')

    def test_a6_technik_is_accepted(self):
        """a6 'Technik' – 5 upgradů achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a6')

    def test_a7_prumyslnik_is_accepted(self):
        """a7 'Průmyslník' – 10M€ achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a7')

    def test_a8_pizza_maniak_is_accepted(self):
        """a8 'Pizza maniak' – 10K kliků achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a8')

    def test_a9_miliardár_is_accepted(self):
        """a9 'Miliardář' – 1B€ achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a9')

    def test_a10_sberatel_is_accepted(self):
        """a10 'Sběratel' – 10 upgradů achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a10')

    def test_a11_klikaci_legenda_is_accepted(self):
        """a11 'Klikací legenda' – 100K kliků achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a11')

    def test_a12_biliardár_is_accepted(self):
        """a12 'Biliardář' – 1T€ achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a12')

    def test_a13_rychla_pizzerie_is_accepted(self):
        """a13 'Rychlá pizzerie' – 1K€/s PPS achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a13')

    def test_a14_perfekcionista_is_accepted(self):
        """a14 'Perfekcionista' – všech 22 upgradů achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a14')

    def test_a15_kral_pizzy_is_accepted(self):
        """a15 'Král pizzy' – 1Q€ achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a15')

    def test_a16_pravidelnik_is_accepted(self):
        """a16 'Pravidelník' – 3 dny streak achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a16')

    def test_a17_verny_zakaznik_is_accepted(self):
        """a17 'Věrný zákazník' – 7 dní streak achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a17')

    def test_a18_pizzovy_fanatik_is_accepted(self):
        """a18 'Pizzový fanatik' – 30 dní streak achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a18')

    def test_a19_novy_zacatek_is_accepted(self):
        """a19 'Nový začátek' – prestige level 1 achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a19')

    def test_a20_veteran_is_accepted(self):
        """a20 'Veterán' – prestige level 5 achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a20')

    def test_a21_pizzovy_buh_is_accepted(self):
        """a21 'Pizzový bůh' – prestige level 10 achievement musí být platné ID."""
        self._assert_single_achievement_accepted('a21')


# ---------------------------------------------------------------------------
# Testy množinových stavů achievementů
# ---------------------------------------------------------------------------

class TC06_AchievementSetStates(unittest.TestCase):
    """Testy pro prázdnou, plnou a smíšenou mapu achievementů."""

    def test_empty_achievements_is_accepted(self):
        """Prázdná mapa {} je výchozí stav nového hráče a musí projít."""
        result = validate_earned_achievements({})
        self.assertEqual(result, {})

    def test_all_21_achievements_true_is_accepted(self):
        """Všechna ID a1–a21 nastavena na True (plné dokončení) musí projít."""
        all_true = {f'a{i}': True for i in range(1, 22)}
        result = validate_earned_achievements(all_true)
        self.assertEqual(len(result), 21)
        for ach_id, val in result.items():
            self.assertTrue(val, f'{ach_id} musí být True')

    def test_all_21_achievements_false_is_accepted(self):
        """Všechna ID a1–a21 nastavena na False (žádné nesplněno) musí projít."""
        all_false = {f'a{i}': False for i in range(1, 22)}
        result = validate_earned_achievements(all_false)
        self.assertEqual(len(result), 21)
        for val in result.values():
            self.assertFalse(val)

    def test_mixed_achievements_is_accepted(self):
        """Smíšená mapa (část True, část False) musí projít validací."""
        mixed = {f'a{i}': (i % 2 == 0) for i in range(1, 22)}
        result = validate_earned_achievements(mixed)
        self.assertEqual(len(result), 21)
        self.assertTrue(result['a2'])
        self.assertFalse(result['a1'])

    def test_first_click_achievements_progression(self):
        """Logická progrese: a1 True, a4 False (1 klik, ale méně než 1000) musí projít."""
        progression = {'a1': True, 'a4': False}
        result = validate_earned_achievements(progression)
        self.assertTrue(result['a1'])
        self.assertFalse(result['a4'])

    def test_streak_achievements_seven_day_earned(self):
        """Hráč s 7 dny streaku musí mít a16 True, a17 True, a18 False – musí projít."""
        streak_state = {'a16': True, 'a17': True, 'a18': False}
        result = validate_earned_achievements(streak_state)
        self.assertTrue(result['a16'])
        self.assertTrue(result['a17'])
        self.assertFalse(result['a18'])

    def test_prestige_achievements_level_five_earned(self):
        """Hráč na prestige 5 musí mít a19 True, a20 True, a21 False – musí projít."""
        prestige_state = {'a19': True, 'a20': True, 'a21': False}
        result = validate_earned_achievements(prestige_state)
        self.assertTrue(result['a19'])
        self.assertTrue(result['a20'])
        self.assertFalse(result['a21'])

    def test_achievements_in_save_payload_accepted(self):
        """Mapa achievementů jako součást celého save payloadu musí projít."""
        achievements = {'a1': True, 'a2': True, 'a3': True}
        result = validate_save_payload(_save_with_achievements(achievements))
        self.assertEqual(len(result['earnedAchievements']), 3)
        self.assertTrue(result['earnedAchievements']['a1'])


# ---------------------------------------------------------------------------
# Testy neplatných achievement ID
# ---------------------------------------------------------------------------

class TC06_InvalidAchievementIDs(unittest.TestCase):
    """Testy odmítnutí neplatných, neexistujících nebo špatně formátovaných ID."""

    def test_a0_does_not_exist_is_rejected(self):
        """a0 neexistuje (ID začínají od a1) a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'a0': True})
        self.assertIn('Unknown achievement id', str(ctx.exception))

    def test_a22_does_not_exist_is_rejected(self):
        """a22 neexistuje (ID končí u a21) a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'a22': True})
        self.assertIn('Unknown achievement id', str(ctx.exception))

    def test_a99_is_rejected(self):
        """a99 je zcela fiktivní ID a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'a99': True})
        self.assertIn('Unknown achievement id', str(ctx.exception))

    def test_uppercase_A1_is_rejected(self):
        """'A1' (velké písmeno) je jiné ID než 'a1' a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'A1': True})
        self.assertIn('Unknown achievement id', str(ctx.exception))

    def test_achievement_id_without_prefix_is_rejected(self):
        """'1' bez prefixu 'a' musí být odmítnuto jako neznámé ID."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'1': True})
        self.assertIn('Unknown achievement id', str(ctx.exception))

    def test_arbitrary_string_id_is_rejected(self):
        """'achievement_first_click' jako ID ve špatném formátu musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'achievement_first_click': True})
        self.assertIn('Unknown achievement id', str(ctx.exception))


# ---------------------------------------------------------------------------
# Testy neplatných typů hodnot achievementů
# ---------------------------------------------------------------------------

class TC06_InvalidAchievementValues(unittest.TestCase):
    """Testy odmítnutí neplatných typů hodnot (non-boolean)."""

    def test_string_true_value_is_rejected(self):
        """Hodnota 'true' jako řetězec místo bool True musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'a1': 'true'})
        self.assertIn('must be true or false', str(ctx.exception))

    def test_integer_1_value_is_rejected(self):
        """Hodnota 1 (int) místo bool True musí být odmítnuta – int není bool."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'a1': 1})
        self.assertIn('must be true or false', str(ctx.exception))

    def test_integer_0_value_is_rejected(self):
        """Hodnota 0 (int) místo bool False musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'a1': 0})
        self.assertIn('must be true or false', str(ctx.exception))

    def test_none_value_is_rejected(self):
        """Hodnota None místo bool musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'a1': None})
        self.assertIn('must be true or false', str(ctx.exception))

    def test_list_value_is_rejected(self):
        """Hodnota [] jako seznam místo bool musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements({'a1': []})
        self.assertIn('must be true or false', str(ctx.exception))


# ---------------------------------------------------------------------------
# Testy neplatného typu samotného pole earnedAchievements
# ---------------------------------------------------------------------------

class TC06_InvalidAchievementsFieldType(unittest.TestCase):
    """Testy odmítnutí, když earnedAchievements není objekt."""

    def test_list_root_is_rejected(self):
        """earnedAchievements jako seznam musí být odmítnuto – musí být objekt."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements([])
        self.assertIn('must be an object', str(ctx.exception))

    def test_string_root_is_rejected(self):
        """earnedAchievements jako řetězec musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements('{}')
        self.assertIn('must be an object', str(ctx.exception))

    def test_none_root_is_rejected(self):
        """earnedAchievements = None musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements(None)
        self.assertIn('must be an object', str(ctx.exception))

    def test_integer_root_is_rejected(self):
        """earnedAchievements jako číslo musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_earned_achievements(42)
        self.assertIn('must be an object', str(ctx.exception))

    def test_achievements_in_save_payload_as_list_is_rejected(self):
        """earnedAchievements jako seznam v save payloadu musí být odmítnuto."""
        p = _save_with_achievements({'a1': True})
        p['earnedAchievements'] = ['a1']
        with self.assertRaises(BadRequest):
            validate_save_payload(p)


if __name__ == '__main__':
    unittest.main()
