import json
from bs4 import BeautifulSoup as BS
import helpers

SHMOT_TYPE_ID = 3
LUK_TYPE_ID = 92
TYPE_ID_TO_KIND_ID_TO_NAME = {
    SHMOT_TYPE_ID: (
        'шмот',
        {
            1: 'шлем',
            2: 'сапоги',
            5: 'наручи',
            6: 'поножи',
            7: 'плечи',
            10: 'меч',
            12: 'двурук',
            17: 'щит',
            20: 'броня',
            21: 'кольчуга',
            44: 'меч2',
            116: 'лук',  # ugly hack for presenting bow as armor
            183: 'клановый меч',
            184: 'клановый щит',
            185: 'клановый меч2',
            186: 'клановый двурук',
        },
    ),
    18: (
        'юва',
        {
            25: 'амулет',
            76: 'кольцо'
        },
    ),
    23: (
        'труд',
        {
            42: 'серп',
            41: 'кирка',
            51: 'удочка',
            44: 'туфил'
        }
    ),
    LUK_TYPE_ID: ()
}


def get_type_to_kind_and_id(art_alts):
    type_to_kind = {}
    for art_alt in art_alts:
        art_contents = art_alt.contents
        for art_content in art_contents:
            if art_content is None or not art_content.startswith('art_alt['):
                continue

            json_str = art_content.split(" = ")[1].rstrip(';')
            try:
                art_json = json.loads(json_str)
            except ValueError:
                continue

            if 'type_id' not in art_json:
                continue

            type_id = int(art_json['type_id'])
            if type_id not in TYPE_ID_TO_KIND_ID_TO_NAME:
                continue

            if type_id == LUK_TYPE_ID:
                type_id = SHMOT_TYPE_ID

            kind_id = int(art_json['kind_id'])
            if kind_id not in TYPE_ID_TO_KIND_ID_TO_NAME[type_id][1]:
                continue

            if type_id not in type_to_kind:
                type_to_kind[type_id] = []
            type_to_kind[type_id].append((kind_id, art_json["id"]))

    return type_to_kind


def get_block(validated_url):
    error, parse_result, user_html = helpers.get_open_user_html(validated_url)
    if error is not None:
        # artifacts block requires open user info
        return f'`{error}`\n'

    soup = BS(user_html, features="html.parser")

    # firstly try to find table with arts (it's td with id=userCanvas)
    user_table = soup.find('td', {'id': 'userCanvas'})
    if user_table is None:
        return '`Cannot find table with user artifacts`\n'

    type_to_kind_and_id = get_type_to_kind_and_id(user_table.findChildren('script', recursive=False))
    block = ''
    for type_id in sorted(type_to_kind_and_id):
        block += f'***{TYPE_ID_TO_KIND_ID_TO_NAME[type_id][0]}***\n'

        type_to_kind_and_id[type_id].sort(key=lambda kind_and_id_tup: kind_and_id_tup[0])
        for kind_and_id in type_to_kind_and_id[type_id]:
            art_kind_id = kind_and_id[0]
            art_id = kind_and_id[1]
            block += f'{TYPE_ID_TO_KIND_ID_TO_NAME[type_id][1][art_kind_id]}: '
            block += f'{parse_result.scheme}://{parse_result.netloc}/artifact_info.php?artifact_id={art_id}\n'

    return block
