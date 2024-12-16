import json
from bs4 import BeautifulSoup as BS
import helpers

SHMOT_TYPE_ID = 3
LUK_TYPE_ID = 92
STYLE_TYPE_ID = 111
STYLE_WEAPON_TYPE_ID = 2

TYPE_ID_TO_KIND_ID_TO_NAME = {
    SHMOT_TYPE_ID: (
        'шмот',
        {
            1: 'шлем',
            2: 'сапог',
            5: 'руки',
            6: 'понож',
            7: 'плечи',
            10: 'меч',
            12: 'двурук',
            17: 'щит',
            20: 'броня',
            21: 'кольча',
            44: 'меч2',
            116: 'лук',  # ugly hack for presenting bow as armor
            183: 'клан меч',
            184: 'клан щит',
            185: 'клан меч2',
            186: 'клан двурук',
        },
    ),
    18: (
        'юва',
        {
            25: 'амуль',
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
    LUK_TYPE_ID: (),
    STYLE_TYPE_ID: (),
    STYLE_WEAPON_TYPE_ID: ()
}


def get_type_to_kinds(art_alts):
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

            style = False
            if type_id in (STYLE_TYPE_ID, STYLE_WEAPON_TYPE_ID):
                style = True
                for type_id_tmp, type_arr in TYPE_ID_TO_KIND_ID_TO_NAME.items():
                    if len(type_arr) == 2 and kind_id in type_arr[1]:
                        type_id = type_id_tmp

            if kind_id not in TYPE_ID_TO_KIND_ID_TO_NAME[type_id][1]:
                continue

            if type_id not in type_to_kind:
                type_to_kind[type_id] = []

            kind = None
            for kind_obj in type_to_kind[type_id]:
                if kind_obj['kind_id'] != kind_id:
                    continue
                if style:
                    if 'style_id' in kind_obj:
                        continue
                else:
                    if 'main_id' in kind_obj:
                        continue
                kind = kind_obj
            if kind is None:
                kind = {'kind_id': kind_id}
                type_to_kind[type_id].append(kind)

            if style:
                kind['style_id'] = art_json["id"]
            else:
                kind['main_id'] = art_json["id"]

    return type_to_kind


def get_block(validated_url):
    error, parse_result, user_html = helpers.get_open_user_html(validated_url)
    if error is not None:
        # artifacts block requires open user info
        return f'`{error}`\n'

    soup = BS(user_html, features="html.parser")

    # firstly try to find table with arts (it's td with id=userCanvas)
    user_table = soup.find('td', {'width': '1%', 'valign': 'top', 'align': 'center'})  # ugly, switch to regexp
    if user_table is None:
        return '`Cannot find table with user artifacts`\n'

    type_to_kinds = get_type_to_kinds(user_table.findChildren('script', recursive=False))
    block = ''
    for type_id in sorted(type_to_kinds):
        if block != '':
            block += '\n'

        for kind_obj in type_to_kinds[type_id]:

            if 'main_id' in kind_obj:
                block += f'[{TYPE_ID_TO_KIND_ID_TO_NAME[type_id][1][kind_obj["kind_id"]]}]({parse_result.scheme}://{parse_result.netloc}/artifact_info.php?artifact_id={kind_obj["main_id"]}) '
            if 'style_id' in kind_obj:
                block += f'([_{TYPE_ID_TO_KIND_ID_TO_NAME[type_id][1][kind_obj["kind_id"]]}_]({parse_result.scheme}://{parse_result.netloc}/artifact_info.php?artifact_id={kind_obj["style_id"]}))'
            block += '\n'
    return block
