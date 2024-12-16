import helpers


def get_block(validated_url):
    parse_result, user_html = helpers.get_parse_result_and_html(validated_url)

    error, nick = helpers.get_nick(user_html)
    if error is not None:
        return f'`{error}`\n'

    nick = nick.replace(' ', '+')
    return f'[Тень]({parse_result.scheme}://{parse_result.netloc}/companion_info.php?nick={nick})\n'
