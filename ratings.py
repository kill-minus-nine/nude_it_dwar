import helpers
from bs4 import BeautifulSoup as BS
import requests

RACE_TO_SCALP_KEY = {
    'Магмары': 'Убито людей',
    'Люди': 'Убито магмаров'
}

SCALP_THRESHOLDS = [
    10, 35, 85, 160, 260, 460, 760, 1160, 1660, 2260, 3060, 4060, 5260, 6660, 8260, 10260, 12660, 15460, 18660, 22260,
    26460, 31460, 37260, 43860, 51260, 60260, 70860, 83060, 96860, 112260
]

LVL_TO_DRAGON_THRESHOLD = {
    10: 3,
    15: 5
}

EXP_THRESHOLDS = [
    0, 720, 4500, 21564, 90864, 198864, 401364, 806364, 1301364, 2100000, 3700000, 5200000, 8000000, 12000000, 17000000,
    22100000, 27300000, 35300000, 43950000, 53450000
]

DOBLA_THRESHOLDS = [
    0, 8000, 38000, 152000, 548000, 848000, 1248000, 1748000, 2348000, 3048000, 3848000, 5048000, 6848000, 9548000,
    13598000, 20000000, 29500000, 43500000, 65000000, 100000000
]

RATING_ID_SCALP = 17
RATING_ID_RR = 4
RATING_ID_EXP = 3
RATING_ID_DOBLA = 2


def get_scalps_in_info(validated_url):
    error, parse_result, user_html = helpers.get_open_user_html(validated_url)
    if error is not None:
        return None

    soup = BS(user_html, features="html.parser")
    race_key = soup.find('td', attrs={'class': 'brd2-top brd2-bt b'}, string='Раса')
    if race_key is None or race_key.parent is None:
        return None

    race_row = race_key.parent
    race_value = race_row.find('td', attrs={'class': 'brd2-top brd2-bt b redd'})
    if race_value is None or len(race_value.contents) != 1:
        return None

    race = race_value.contents[0].strip()
    if race not in RACE_TO_SCALP_KEY:
        return None

    scalp_key = RACE_TO_SCALP_KEY[race]
    scalp_key_elem = soup.find('td', attrs={'class': 'brd2-top brd2-bt b'}, string=scalp_key)
    if scalp_key_elem is None or scalp_key_elem.parent is None:
        return None

    scalp_row = scalp_key_elem.parent
    scalp_value_elem = scalp_row.find('td', attrs={'class': 'brd2-top brd2-bt b redd'})
    if scalp_value_elem is None or len(scalp_value_elem.contents) != 1:
        return None

    scalp_value_str = scalp_value_elem.contents[0].strip()
    if not scalp_value_str.isdigit():
        return None

    return int(scalp_value_str)


def get_dragon_lvl_by_scalps(scalp_count):
    for dragon_lvl, scalp_count_threshold in enumerate(SCALP_THRESHOLDS, start=1):
        if scalp_count_threshold > scalp_count:
            return dragon_lvl - 1

    return len(SCALP_THRESHOLDS)


def get_exp_percent_by_points(lvl, exp_points):
    if lvl >= len(EXP_THRESHOLDS):
        return 100

    return 100 * (exp_points - EXP_THRESHOLDS[lvl - 1]) / (EXP_THRESHOLDS[lvl] - EXP_THRESHOLDS[lvl - 1])


def get_dobla_percent_by_points(dobla_points):
    for zvanie, dobla_threshold in enumerate(DOBLA_THRESHOLDS):
        if dobla_threshold > dobla_points:
            return 100 * (dobla_points - DOBLA_THRESHOLDS[zvanie - 1]) / (
                    DOBLA_THRESHOLDS[zvanie] - DOBLA_THRESHOLDS[zvanie - 1])
    return 100


def get_row_from_rating(parse_result, nick, rating_id=None):
    rating_url = f'{parse_result.scheme}://{parse_result.netloc}/rating.php'
    if rating_id is not None:
        rating_url += f'?rating_id={rating_id}'
    r = requests.post(rating_url, data={'nick': nick}, verify=False)
    soup = BS(r.text, features="html.parser")

    person_row = soup.find('tr', class_='bg_l3')
    if person_row is None:
        return 'Cannot find person in ratings. Maybe it\'s hidden.', None

    return None, person_row


def get_val_from_rating(parse_result, nick, rating_id):
    err, person_row = get_row_from_rating(parse_result, nick, rating_id)
    if err is not None:
        return err, None

    val_elem = person_row.find('td', attrs={'align': 'center'})
    if val_elem is None or len(val_elem.contents) != 1:
        return 'Cannot parse rating table', None

    return None, int(val_elem.contents[0].strip())


def get_lvl(parse_result, nick):
    err, person_row = get_row_from_rating(parse_result, nick, None)
    if err is not None:
        return err, None

    nick_with_lvl_elem = person_row.find('b', attrs={'title': 'Персональное сообщение'})
    if nick_with_lvl_elem is None:
        return 'Cannot get person ceil from table', None

    if nick_with_lvl_elem is None or len(nick_with_lvl_elem.contents) != 1:
        return 'Cannot parse rating table', None

    nick_with_lvl = nick_with_lvl_elem.contents[0]
    return None, int(nick_with_lvl[nick_with_lvl.find("[") + 1: nick_with_lvl.find(']')])


def get_block(validated_url):
    parse_result, user_html = helpers.get_parse_result_and_html(validated_url)

    error, nick = helpers.get_nick(user_html)
    if error is not None:
        return f'`{error}`\n'

    error, lvl = get_lvl(parse_result, nick)
    if error is not None:
        return f'`{error}`\n'

    block = f'Лвл: {lvl}\n'

    error, scalps_in_rating = get_val_from_rating(parse_result, nick, RATING_ID_SCALP)
    if error is not None:
        return f'`{error}`\n'
    dragon_level = get_dragon_lvl_by_scalps(scalps_in_rating)
    block += f'Драк: {dragon_level}\n'
    scalps_in_info = get_scalps_in_info(validated_url)
    if scalps_in_info is not None:
        dragon_with_scalps = get_dragon_lvl_by_scalps(scalps_in_rating + scalps_in_info)
        if dragon_with_scalps != dragon_level:
            block += f'Драк скальп: {dragon_with_scalps}\n'

    error, rr_in_rating = get_val_from_rating(parse_result, nick, RATING_ID_RR)
    if error is not None:
        return f'`{error}`\n'
    block += f'РР: {rr_in_rating}\n'

    error, exp_in_rating = get_val_from_rating(parse_result, nick, RATING_ID_EXP)
    if error is not None:
        return f'`{error}`\n'
    block += f'Опыт: {round(get_exp_percent_by_points(lvl, exp_in_rating), 2)}%\n'

    error, dobla_in_rating = get_val_from_rating(parse_result, nick, RATING_ID_DOBLA)
    if error is not None:
        return f'`{error}`\n'
    block += f'Добла: {round(get_dobla_percent_by_points(dobla_in_rating), 2)}%\n'

    return block
