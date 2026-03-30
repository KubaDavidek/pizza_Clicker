# python -m unittest discover -s testing -p "test_*.py"
"""
TC08 – Uživatelský účet (autentizace, přezdívky, hesla, změna hesla)
=====================================================================

Tento soubor pokrývá kompletní testování validace uživatelského účtu:
přihlášení, registrace, pravidla pro přezdívky a hesla, změna hesla
a všechny krajní a hraniční případy vstupů.

Oblasti pokryté testy
---------------------
1.  validate_nickname – minimální délka (3), maximální délka (30), ořez,
    číselné přezdívky, typová kontrola
2.  validate_password – minimální délka (6), maximální délka (128),
    hraniční hodnoty, speciální znaky
3.  validate_register_payload – validní registrace, chybějící pole,
    nadbytečná pole, kombinace špatných vstupů
4.  validate_login_payload – validní přihlášení, špatný typ kořene,
    kombinace chyb
5.  validate_change_password_payload – validní změna hesla, chybějící
    pole, krátké nové heslo, nadbytečná pole
6.  Hranice délky přezdívky – přesně 3 znaky (minimum), přesně 30 znaků
    (maximum), 2 znaky (odmítnutí), 31 znaků (odmítnutí)
7.  Hranice délky hesla – přesně 6 znaků (minimum), přesně 128 znaků
    (maximum), 5 znaků (odmítnutí), 129 znaků (odmítnutí)
8.  Unicode a speciální znaky v přezdívkách a heslech
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from werkzeug.exceptions import BadRequest

from validation import (
    validate_nickname,
    validate_password,
    validate_register_payload,
    validate_login_payload,
    validate_change_password_payload,
)


# ---------------------------------------------------------------------------
# Testy validate_nickname
# ---------------------------------------------------------------------------

class TC08_Nickname_Boundaries(unittest.TestCase):
    """Testy hranic délky a typové kontroly přezdívky."""

    def test_nickname_exactly_3_chars_is_accepted(self):
        """Přezdívka přesně 3 znaků je na minimální hranici a musí projít."""
        result = validate_nickname('abc')
        self.assertEqual(result, 'abc')

    def test_nickname_exactly_30_chars_is_accepted(self):
        """Přezdívka přesně 30 znaků je na maximální hranici a musí projít."""
        name = 'A' * 30
        result = validate_nickname(name)
        self.assertEqual(result, name)

    def test_nickname_2_chars_is_rejected(self):
        """Přezdívka 2 znaky je pod minimem a musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_nickname('ab')
        self.assertIn('alespoň', str(ctx.exception))

    def test_nickname_31_chars_is_rejected(self):
        """Přezdívka 31 znaků přesahuje maximum a musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_nickname('A' * 31)
        self.assertIn('nejvýše', str(ctx.exception))

    def test_nickname_with_numbers_and_letters_is_accepted(self):
        """Přezdívka 'Pepa123' (čísla i písmena) musí projít – není jen číselná."""
        result = validate_nickname('Pepa123')
        self.assertEqual(result, 'Pepa123')

    def test_nickname_only_digits_is_rejected(self):
        """Přezdívka '12345' (jen číslice) musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_nickname('12345')
        self.assertIn('jen čísla', str(ctx.exception))

    def test_nickname_with_leading_trailing_spaces_is_trimmed(self):
        """Přezdívka '  Honza  ' musí být ořezána na 'Honza'."""
        result = validate_nickname('  Honza  ')
        self.assertEqual(result, 'Honza')

    def test_nickname_spaces_only_after_trim_is_rejected(self):
        """Přezdívka '   ' (jen mezery) po ořezu je pod minimem a musí být odmítnuta."""
        with self.assertRaises(BadRequest):
            validate_nickname('   ')

    def test_nickname_integer_type_is_rejected(self):
        """Přezdívka jako číslo (int) místo stringu musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_nickname(42)
        self.assertIn('must be a string', str(ctx.exception))

    def test_nickname_none_type_is_rejected(self):
        """Přezdívka = None místo stringu musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_nickname(None)
        self.assertIn('must be a string', str(ctx.exception))

    def test_nickname_list_type_is_rejected(self):
        """Přezdívka jako seznam musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_nickname(['Honza'])
        self.assertIn('must be a string', str(ctx.exception))

    def test_nickname_unicode_letters_is_accepted(self):
        """Přezdívka s diakritikou 'Žofka' (unicode) musí projít validací."""
        result = validate_nickname('Žofka')
        self.assertEqual(result, 'Žofka')

    def test_nickname_with_hyphen_is_accepted(self):
        """Přezdívka 'Jan-Pavel' s pomlčkou musí projít – není omezení na znakovou sadu."""
        result = validate_nickname('Jan-Pavel')
        self.assertEqual(result, 'Jan-Pavel')

    def test_nickname_exactly_3_chars_only_digits_is_rejected(self):
        """Přezdívka '999' (3 číslice = minimum délky, ale jen číslice) musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_nickname('999')
        self.assertIn('jen čísla', str(ctx.exception))


# ---------------------------------------------------------------------------
# Testy validate_password
# ---------------------------------------------------------------------------

class TC08_Password_Boundaries(unittest.TestCase):
    """Testy hranic délky a typové kontroly hesla."""

    def test_password_exactly_6_chars_is_accepted(self):
        """Heslo přesně 6 znaků je na minimální hranici a musí projít."""
        result = validate_password('x' * 6)
        self.assertEqual(result, 'xxxxxx')

    def test_password_exactly_128_chars_is_accepted(self):
        """Heslo přesně 128 znaků je na maximální hranici a musí projít."""
        result = validate_password('x' * 128)
        self.assertEqual(len(result), 128)

    def test_password_5_chars_is_rejected(self):
        """Heslo 5 znaků je pod minimem a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_password('x' * 5)
        self.assertIn('alespoň', str(ctx.exception))

    def test_password_129_chars_is_rejected(self):
        """Heslo 129 znaků přesahuje maximum a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_password('x' * 129)
        self.assertIn('nejvýše', str(ctx.exception))

    def test_password_7_chars_is_accepted(self):
        """Heslo 7 znaků je v povoleném rozsahu (6–128) a musí projít."""
        result = validate_password('abc1234')
        self.assertEqual(result, 'abc1234')

    def test_password_with_special_characters_is_accepted(self):
        """Heslo se speciálními znaky 'P@$$w0rd!' musí projít."""
        result = validate_password('P@$$w0rd!')
        self.assertEqual(result, 'P@$$w0rd!')

    def test_password_with_spaces_is_accepted(self):
        """Heslo s mezerami 'moje heslo 42' musí projít – mezery jsou povoleny."""
        result = validate_password('moje heslo 42')
        self.assertEqual(result, 'moje heslo 42')

    def test_password_with_unicode_is_accepted(self):
        """Heslo s unicode znaky 'hésló123' musí projít."""
        result = validate_password('hésló123')
        self.assertEqual(result, 'hésló123')

    def test_password_integer_type_is_rejected(self):
        """Heslo jako číslo (int) místo stringu musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_password(123456)
        self.assertIn('must be a string', str(ctx.exception))

    def test_password_none_type_is_rejected(self):
        """Heslo = None místo stringu musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_password(None)
        self.assertIn('must be a string', str(ctx.exception))

    def test_password_empty_string_is_rejected(self):
        """Prázdné heslo '' musí být odmítnuto (pod minimem 6 znaků)."""
        with self.assertRaises(BadRequest) as ctx:
            validate_password('')
        self.assertIn('alespoň', str(ctx.exception))


# ---------------------------------------------------------------------------
# Testy validate_register_payload
# ---------------------------------------------------------------------------

class TC08_RegisterPayload(unittest.TestCase):
    """Testy validace payloadu pro registraci."""

    def test_valid_registration_is_accepted(self):
        """Validní registrace s přezdívkou a heslem musí projít."""
        result = validate_register_payload({'nickname': 'Hráč123', 'password': 'bezpečné'})
        self.assertEqual(result['nickname'], 'Hráč123')
        self.assertEqual(result['password'], 'bezpečné')

    def test_registration_trimmed_nickname_is_accepted(self):
        """Registrace s přezdívkou s mezerami '  Pepa  ' musí ořezat na 'Pepa'."""
        result = validate_register_payload({'nickname': '  Pepa  ', 'password': 'heslo123'})
        self.assertEqual(result['nickname'], 'Pepa')

    def test_registration_missing_password_is_rejected(self):
        """Registrace bez hesla musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_register_payload({'nickname': 'Pepa123'})
        self.assertIn('Missing fields', str(ctx.exception))

    def test_registration_missing_nickname_is_rejected(self):
        """Registrace bez přezdívky musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_register_payload({'password': 'heslo123'})
        self.assertIn('Missing fields', str(ctx.exception))

    def test_registration_extra_field_is_rejected(self):
        """Registrace s nadbytečným polem 'email' musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_register_payload({'nickname': 'Pepa123', 'password': 'heslo123', 'email': 'p@p.cz'})
        self.assertIn('Unknown fields', str(ctx.exception))

    def test_registration_empty_dict_is_rejected(self):
        """Registrace s prázdným objektem musí být odmítnuta kvůli chybějícím polím."""
        with self.assertRaises(BadRequest) as ctx:
            validate_register_payload({})
        self.assertIn('Missing fields', str(ctx.exception))

    def test_registration_short_password_is_rejected(self):
        """Registrace s krátkým heslem (5 znaků) musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_register_payload({'nickname': 'Pepa123', 'password': 'short'})
        self.assertIn('alespoň', str(ctx.exception))

    def test_registration_numeric_only_nickname_is_rejected(self):
        """Registrace s přezdívkou z číslic musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_register_payload({'nickname': '12345', 'password': 'heslo123'})
        self.assertIn('jen čísla', str(ctx.exception))

    def test_registration_with_list_root_is_rejected(self):
        """Registrace se seznamem místo objektem musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_register_payload(['Pepa123', 'heslo123'])
        self.assertIn('JSON object', str(ctx.exception))

    def test_registration_boundary_nickname_3_chars(self):
        """Registrace s přezdívkou přesně 3 znaky musí projít."""
        result = validate_register_payload({'nickname': 'Abc', 'password': 'heslo123'})
        self.assertEqual(result['nickname'], 'Abc')

    def test_registration_boundary_password_6_chars(self):
        """Registrace s heslem přesně 6 znaků musí projít."""
        result = validate_register_payload({'nickname': 'Honza', 'password': 'abc123'})
        self.assertEqual(result['password'], 'abc123')


# ---------------------------------------------------------------------------
# Testy validate_login_payload
# ---------------------------------------------------------------------------

class TC08_LoginPayload(unittest.TestCase):
    """Testy validace payloadu pro přihlášení."""

    def test_valid_login_is_accepted(self):
        """Validní přihlášení s přezdívkou a heslem musí projít."""
        result = validate_login_payload({'nickname': 'Hráč123', 'password': 'heslo123'})
        self.assertEqual(result['nickname'], 'Hráč123')
        self.assertEqual(result['password'], 'heslo123')

    def test_login_missing_password_is_rejected(self):
        """Přihlášení bez hesla musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_login_payload({'nickname': 'Honza'})
        self.assertIn('Missing fields', str(ctx.exception))

    def test_login_missing_nickname_is_rejected(self):
        """Přihlášení bez přezdívky musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_login_payload({'password': 'heslo123'})
        self.assertIn('Missing fields', str(ctx.exception))

    def test_login_with_string_root_is_rejected(self):
        """Přihlášení se stringem místo objektem musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_login_payload('bad')
        self.assertIn('JSON object', str(ctx.exception))

    def test_login_with_none_root_is_rejected(self):
        """Přihlášení s None jako payload musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_login_payload(None)
        self.assertIn('JSON object', str(ctx.exception))

    def test_login_extra_field_is_rejected(self):
        """Přihlášení s nadbytečným polem musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_login_payload({'nickname': 'Honza', 'password': 'heslo123', 'remember': True})
        self.assertIn('Unknown fields', str(ctx.exception))

    def test_login_empty_dict_is_rejected(self):
        """Přihlášení s prázdným objektem musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_login_payload({})
        self.assertIn('Missing fields', str(ctx.exception))


# ---------------------------------------------------------------------------
# Testy validate_change_password_payload
# ---------------------------------------------------------------------------

class TC08_ChangePasswordPayload(unittest.TestCase):
    """Testy validace payloadu pro změnu hesla."""

    def test_valid_change_password_is_accepted(self):
        """Validní změna hesla se starým a novým heslem musí projít."""
        result = validate_change_password_payload({
            'old_password': 'staréheslo',
            'new_password': 'novéheslo123',
        })
        self.assertEqual(result['old_password'], 'staréheslo')
        self.assertEqual(result['new_password'], 'novéheslo123')

    def test_change_password_missing_old_is_rejected(self):
        """Změna hesla bez starého hesla musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_change_password_payload({'new_password': 'novéheslo123'})
        self.assertIn('Missing fields', str(ctx.exception))

    def test_change_password_missing_new_is_rejected(self):
        """Změna hesla bez nového hesla musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_change_password_payload({'old_password': 'staréheslo'})
        self.assertIn('Missing fields', str(ctx.exception))

    def test_change_password_short_new_is_rejected(self):
        """Nové heslo kratší než 6 znaků musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_change_password_payload({
                'old_password': 'staréheslo',
                'new_password': '123',
            })
        self.assertIn('alespoň', str(ctx.exception))

    def test_change_password_long_new_is_rejected(self):
        """Nové heslo delší než 128 znaků musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_change_password_payload({
                'old_password': 'staréheslo',
                'new_password': 'x' * 129,
            })
        self.assertIn('nejvýše', str(ctx.exception))

    def test_change_password_extra_field_is_rejected(self):
        """Změna hesla s nadbytečným polem 'token' musí být odmítnuta."""
        with self.assertRaises(BadRequest) as ctx:
            validate_change_password_payload({
                'old_password': 'staréheslo',
                'new_password': 'novéheslo123',
                'token': 'abc',
            })
        self.assertIn('Unknown fields', str(ctx.exception))

    def test_change_password_empty_dict_is_rejected(self):
        """Prázdný objekt při změně hesla musí být odmítnut."""
        with self.assertRaises(BadRequest) as ctx:
            validate_change_password_payload({})
        self.assertIn('Missing fields', str(ctx.exception))

    def test_change_password_old_boundary_6_chars(self):
        """Staré heslo přesně 6 znaků a nové heslo 7 znaků musí projít."""
        result = validate_change_password_payload({
            'old_password': 'abcdef',
            'new_password': 'abcdefg',
        })
        self.assertEqual(result['old_password'], 'abcdef')

    def test_change_password_same_old_and_new_is_accepted(self):
        """Změna hesla na stejné heslo musí projít validací – logiku zhodnotí server."""
        result = validate_change_password_payload({
            'old_password': 'stejnéheslo',
            'new_password': 'stejnéheslo',
        })
        self.assertEqual(result['old_password'], result['new_password'])

    def test_change_password_new_boundary_128_chars(self):
        """Nové heslo přesně 128 znaků je na maximální hranici a musí projít."""
        result = validate_change_password_payload({
            'old_password': 'staréheslo',
            'new_password': 'x' * 128,
        })
        self.assertEqual(len(result['new_password']), 128)


if __name__ == '__main__':
    unittest.main()
