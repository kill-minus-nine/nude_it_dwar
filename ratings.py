import helpers
from bs4 import BeautifulSoup as BS
import requests

race_to_scalp_key = {
    'Магмары': 'Убито людей',
    'Люди': 'Убито магмаров'
}

scalp_count_to_dragon = {
    10: 1, 35: 2, 85: 3, 160: 4, 260: 5, 460: 6, 760: 7, 1160: 8, 1660: 9, 2260: 10,
    3060: 11, 4060: 12, 5260: 13, 6660: 14, 8260: 15, 10260: 16, 12660: 17, 15460: 18, 18660: 19, 22260: 20,
    26460: 21, 31460: 22, 37260: 23, 43860: 24, 51260: 25, 60260: 26, 70860: 27, 83060: 28, 96860: 29, 112260: 30
}

lvl_to_dragon_threshold = {
    10: 3,
    15: 5
}

RATING_ID_SCALP = 17
RATING_ID_RR = 4
RATING_ID_EXP = 3
RATING_ID_DOBL = 2

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
    if race not in race_to_scalp_key:
        return None

    scalp_key = race_to_scalp_key[race]
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
    return next(v for k, v in scalp_count_to_dragon.items() if scalp_count < k) - 1


def get_val_from_rating(parse_result, nick, rating_id):
    rating_url = f'{parse_result.scheme}://{parse_result.netloc}/rating.php?rating_id={rating_id}'
    r = requests.post(rating_url, data={'nick': nick})
    soup = BS(r.text, features="html.parser")

    person_row = soup.find('tr', class_='bg_l3')
    if person_row is None:
        return 'Cannot find person in ratings. Maybe it\'s hidden.', None

    val_elem = person_row.find('td', attrs={'align': 'center'})
    if val_elem is None or len(val_elem.contents) != 1:
        return 'Cannot parse rating table', None

    return None, int(val_elem.contents[0].strip())


def get_block(validated_url):
    parse_result, user_html = helpers.get_parse_result_and_html(validated_url)

    error, nick = helpers.get_nick(user_html)
    if error is not None:
        return f'`{error}`\n'

    block = ''

    error, scalps_in_rating = get_val_from_rating(parse_result, nick, 17)
    if error is not None:
        return f'`{error}`\n'
    dragon_level = get_dragon_lvl_by_scalps(scalps_in_rating)
    block += f'***Уровень дракона: *** {dragon_level}\n'
    scalps_in_info = get_scalps_in_info(validated_url)
    if scalps_in_info is not None:
        dragon_with_scalps = get_dragon_lvl_by_scalps(scalps_in_rating + scalps_in_info)
        if dragon_with_scalps != dragon_level:
            block += f'***Уровень дракона если сдать скальпы: *** {dragon_with_scalps}\n'

    error, rr_in_rating = get_val_from_rating(parse_result, nick, 4)
    if error is not None:
        return f'`{error}`\n'

    block += f'***РР: *** {rr_in_rating}\n'

    return block
