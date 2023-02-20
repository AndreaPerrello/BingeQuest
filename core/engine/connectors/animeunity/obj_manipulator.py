import json

from .classes import Anime, Episode, Related


def get_formatted_search_results(res_obj):
    # Per comodità se non è un array lo trasformo in array
    if not isinstance(res_obj, type([])):
        res_obj = [res_obj]
    anime_arr = []
    for anime_ob in res_obj:
        # Creo oggetto anime e assegno i campi
        anime = None
        anime = Anime(anime_ob['id'], anime_ob['title'], anime_ob['type'], anime_ob['episodes_length'])
        anime.status = anime_ob['status']
        anime.year = anime_ob['date']
        anime.slug = anime_ob['slug']
        anime.title_eng = anime_ob['title_eng']
        anime.cover_image = anime_ob['imageurl_cover']
        anime.thumbnail = anime_ob['imageurl']
        anime.episodes = []
        for ep in anime_ob['episodes']:
            # Creo oggetto episodio e assegno campi
            episode = Episode(ep['id'], ep['number'], ep['created_at'], ep['link'])
            # Aggiungo episodio alla lista dell'anime
            anime.episodes.append(episode)
        # Aggiungo anime alla lista
        if 'related' in anime_ob:
            anime.related = []
            for rel in anime_ob['related']:
                anime.related.append(Related(rel['id'], rel['type'], rel['title'], rel['slug']))
        anime_arr.append(anime)
    return order_search_res(anime_arr)


# Cerco anime per id
def get_selected_anime_obj_by_id(anime_arr, a_id=None):
    for res in anime_arr:
        if str(res.a_id) == a_id:
            return res
    return anime_arr[0]


def get_year(anime):
    return anime.year


def order_search_res(anime_list):
    anime_list.sort(key=get_year)
    return anime_list


if __name__ == "__main__":
    with open('./doc/test_dir/search_result_final.json') as f:
        search_res = json.load(f)

    anime_obj = get_formatted_search_results(search_res)
    print(anime_obj)
    print(order_search_res(anime_obj))

    print(get_selected_anime_obj_by_id(anime_obj, 743))
