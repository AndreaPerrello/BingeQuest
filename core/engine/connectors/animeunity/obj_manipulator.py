from .classes import Anime, Episode, Related


def format_search_results(res_obj):
    if not isinstance(res_obj, type([])):
        res_obj = [res_obj]
    anime_arr = []
    for anime_ob in res_obj:
        anime = Anime(anime_ob['id'], anime_ob['title'], anime_ob['type'], anime_ob['episodes_length'])
        anime.status = anime_ob['status']
        anime.year = anime_ob['date']
        anime.slug = anime_ob['slug']
        anime.title_eng = anime_ob['title_eng']
        anime.cover_image = anime_ob['imageurl_cover']
        anime.thumbnail = anime_ob['imageurl']
        anime.episodes = []
        for ep in anime_ob['episodes']:
            episode = Episode(ep['id'], ep['number'], ep['created_at'], ep['link'])
            anime.episodes.append(episode)
        if 'related' in anime_ob:
            anime.related = []
            for rel in anime_ob['related']:
                anime.related.append(Related(rel['id'], rel['type'], rel['title'], rel['slug']))
        anime_arr.append(anime)
    return order_search_res(anime_arr)


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
