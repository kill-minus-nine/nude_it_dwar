import validators
import urllib.parse as up
import urllib.request as ur
from bs4 import BeautifulSoup as BS

SUPPORTED_HOSTNAMES = (
    'w1.dwar.ru',
    'w2.dwar.ru',
    'w1.dwar.mail.ru',
    'w2.dwar.mail.ru',
)


def get_nick(user_html):
    soup = BS(user_html, features="html.parser")

    header_with_nick = soup.find('div', attrs={'class': 'common-header'})
    if header_with_nick is None:
        return 'Cannot parse nick header', None

    nick_elem = header_with_nick.find('div', attrs={'class': 'h-txt'})
    if nick_elem is None:
        return 'Cannot parse nick element', None

    return None, nick_elem.contents[-1].strip()


def escape_string(str_arg):
    return up.quote(str_arg, safe='()/&=?:%+')


ESCAPED_MINOR = escape_string(' (ФЭО-Минор)')
ESCAPED_PRIME = escape_string(' (ФЭО-Прайм)')


def get_validated_user_url(url):
    url_parts = url.split('nick=')
    if len(url_parts) != 2:
        return 'Url doesn\'t contain nick part', None

    original_nick = url_parts[1]
    url = url.replace(original_nick, escape_string(original_nick))
    if not validators.url(url):
        return 'Not a valid url', None

    parse_result = up.urlparse(url)
    host_name = parse_result.netloc

    if host_name not in SUPPORTED_HOSTNAMES:
        return f'Supports only {SUPPORTED_HOSTNAMES} hostnames', None

    print(url)
    if url.endswith(ESCAPED_MINOR):
        url = f'{parse_result.scheme}://{parse_result.netloc.replace("w1", "w2")}{parse_result.path}?{parse_result.query.replace(ESCAPED_MINOR, "")}'
    elif url.endswith(ESCAPED_PRIME):
        url = f'{parse_result.scheme}://{parse_result.netloc.replace("w2", "w1")}{parse_result.path}?{parse_result.query.replace(ESCAPED_PRIME, "")}'

    return None, url


def get_parse_result_and_html(url):
    parse_result = up.urlparse(url)

    with ur.urlopen(url) as response:
        return parse_result, response.read()


def get_open_user_html(validated_url):
    parse_result, html = get_parse_result_and_html(validated_url)

    soup = BS(html, features="html.parser")

    play_info = soup.find('span', string='Игровая информация')
    if play_info is None:
        go_to_info_butt = soup.find('input', {'value': 'Перейти к игровой информации'})
        if go_to_info_butt is None:
            return 'Not a valid person url. Maybe it\'s hidden or there is no such player name.', None, None

        # e.g. location.href='location.href='user_info.php?nick=Милеста&amp;noredir=0f8eb5d8a96adf5516f35dfc621cb4d8';;
        on_click = go_to_info_butt["onclick"]
        href = on_click.split("=", 1)[1].split("'")[1]
        if href.startswith('http://'):
            url_to_info = href
        else:
            url_to_info = f'{parse_result.scheme}://{parse_result.netloc}/{href}'

        error, validated_url = get_validated_user_url(url_to_info)
        if error is not None:
            return error, None, None

        parse_result, html = get_parse_result_and_html(validated_url)

        soup = BS(html, features="html.parser")
        play_info = soup.find('span', string='Игровая информация')
        if play_info is None:
            return 'Cannot find player info', None, None

    return None, parse_result, html
