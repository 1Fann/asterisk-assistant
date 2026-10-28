#!/usr/bin/python3
"""Offline caller display-name formatting; never changes the dialable identity."""
import json
from pathlib import Path
import re
import signal
import sys

BUNDLE = Path(__file__).resolve().parent
for wheel in sorted(BUNDLE.glob('phonenumberslite-*.whl')):
    sys.path.insert(0, str(wheel))


def digits(text):
    return re.sub(r'[^0-9]', '', text)


def format_display(number, name='', region='CN'):
    """Return a numeric display name, or None when no safe change is possible.

    No country code means the configured home region, never a guessed foreign
    country. International 00 is recognized only if it is that region's IDD.
    Every original digit must survive formatting, including leading zeros.
    """
    number = number.strip()
    if len(number) > 64 or not re.fullmatch(r'\+?[0-9][0-9 ()\.\-]*', number):
        return None
    if len(digits(number)) <= 6:
        return None
    # Preserve actual names and nonmatching numeric identifiers.
    if name and (not re.fullmatch(r'\+?[0-9][0-9 ()\.\-]*', name.strip())
                 or digits(name) != digits(number)):
        return None
    import phonenumbers as phone
    region = region.upper()
    if region not in phone.SUPPORTED_REGIONS:
        return None
    try:
        parsed = phone.parse(number, region, keep_raw_input=True)
    except phone.NumberParseException:
        return None
    if not phone.is_possible_number(parsed):
        return None
    source = parsed.country_code_source
    if source == phone.CountryCodeSource.FROM_NUMBER_WITH_PLUS_SIGN:
        result = phone.format_number(parsed, phone.PhoneNumberFormat.INTERNATIONAL)
    elif source == phone.CountryCodeSource.FROM_NUMBER_WITH_IDD:
        international = phone.format_number(parsed, phone.PhoneNumberFormat.INTERNATIONAL)
        all_digits = digits(number)
        suffix = digits(international)
        if not all_digits.endswith(suffix):
            return None
        result = all_digits[:-len(suffix)] + ' ' + international.removeprefix('+')
    elif source == phone.CountryCodeSource.FROM_NUMBER_WITHOUT_PLUS_SIGN:
        result = phone.format_number(parsed, phone.PhoneNumberFormat.INTERNATIONAL).removeprefix('+')
    else:
        result = phone.format_number(parsed, phone.PhoneNumberFormat.NATIONAL)
    # Use the library's group boundaries, with spaces as the display separator.
    result = re.sub(r'[().\-]+', ' ', result)
    result = re.sub(r'\s+', ' ', result).strip()
    if digits(result) != digits(number) or not re.fullmatch(r'\+?[0-9 ]+', result):
        return None
    return result if result != name else None


def command(text):
    print(text, flush=True)
    reply = sys.stdin.readline(4096).rstrip('\r\n')
    if not reply.startswith('200 '):
        raise RuntimeError('AGI command failed')
    return reply


def main():
    env = {}
    for _ in range(128):
        line = sys.stdin.readline(4096).rstrip('\r\n')
        if not line:
            break
        key, _, value = line.partition(': ')
        env[key] = value
    pres = command('GET FULL VARIABLE ${CALLERID(num-pres)}')
    if not re.search(r'\(allowed(?:_[a-z_]+)?\)$', pres):
        return
    region = 'CN'
    settings = BUNDLE / 'settings.json'
    if settings.exists():
        region = json.loads(settings.read_text(encoding='utf-8')).get('default_region', 'CN')
    formatted = format_display(env.get('agi_callerid', ''),
                               env.get('agi_calleridname', ''), region)
    if formatted is not None:
        # The allowlist above excludes quotes, newlines and AGI/SIP syntax.
        command('SET VARIABLE CALLERID(name) "' + formatted + '"')


if __name__ == '__main__':
    try:
        # Fail open: any dependency/config error leaves the call unmodified.
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, lambda *_: sys.exit(0))
            signal.alarm(2)
        main()
    except Exception:
        pass  # Never log caller numbers, names, or AGI environment.
