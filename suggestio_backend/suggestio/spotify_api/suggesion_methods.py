from suggestio.spotify_api.spotify_api import SpotifyAPI


def list_of_tracks(data):
    uris = list()
    ind = 0
    tracks = data['tracks']

    name, link = str(), str()
    for i in tracks:
        artists = str()
        name = i["name"]
        for j in i["artists"]:
            artists += j['name'] + ", "
        artists = artists[:-2]
        link = i["external_urls"]['spotify']
        uris.append(i["uri"])
        ind += 1
        #print(name + " By " + artists + ": " + link)
    return uris


def jaccard(set_a: set, set_b: set) -> float:
    if len(set_a) != 0 and len(set_b) != 0:
        return len(set_a.intersection(set_b)) / len(set_a.union(set_b))
    else:
        return 0


def similar_artists(spotify_api: SpotifyAPI, artists: list) -> list:
    unique_artists = list(set(artists))
    list_sim = []

    for i in range(len(unique_artists)):
        if unique_artists[i] == "":
            continue
        if i + 1 > len(unique_artists):
            break

        sim = [unique_artists[i]]
        light_sim = []

        for j in range(i + 1, len(unique_artists)):
            if unique_artists[j] != "" and unique_artists[i] != "":
                id1, id2 = unique_artists[i], unique_artists[j]
                id1 = id1.split(":")[2]
                id2 = id2.split(":")[2]
                related1, related2 = spotify_api.related_artists(id1), spotify_api.related_artists(id2)
                l1 = []
                l2 = []
                for z in related1:
                    l1.append(z['artist'])
                for z in related2:
                        l2.append(z['artist'])
                setSim = jaccard(set(l1), set(l2))
                if setSim >= 0.3:
                    sim.append(unique_artists[j])
                    unique_artists[j] = ""
                elif setSim > 0.09:
                    light_sim.append(unique_artists[j])

        g1 = spotify_api.artist_genre(id1)

        for z in light_sim:
            item = z.split(":")[2]
            g2 = spotify_api.artist_genre(item)
            setg1 = set(g1)
            setg2 = set(g2)
            if jaccard(setg1, setg2) > 0.124:
                unique_artists[unique_artists.index(z)] = ""
                sim.append(z)

        list_sim.append(sim)

    # for i in list_sim:
    #     for j in i:
    #         if j != i[0]:
    #             print("     " + j)
    #         else:
    #             print(j)
    return list_sim

def average_audio_features(spotify_api: SpotifyAPI, data: list[dict]) -> dict:
    tracks_features = list()
    for i in data:
        i = i['track'].split(':')[2]
        try:
            json = spotify_api.audio_features(i)
            if 'error' not in json.keys():
                features_json = dict()
                features_json['energy'] = json["energy"]
                features_json['loud'] = json["loudness"]
                features_json["dance"] = json["danceability"]
                features_json["speech"] = json["speechiness"]
                features_json["valence"] = json["valence"]
                features_json["uri"] = json["uri"]
                tracks_features.append(features_json)
                #print(i + ' checked')
            else:
                #print(json['error'])
                break
        except Exception as e:
            raise e

    count = len(data)
    sum_features = {
        "energy": 0,
        'loud': 0,
        "dance": 0,
        "speech": 0,
        "valence": 0
    }
    for i in tracks_features:
        for key in i.keys():
            if key == "uri":
                continue
            sum_features[key] += i[key]

    aver_features = {
        "energy": 0,
        'loud': 0,
        "dance": 0,
        "speech": 0,
        "valence": 0
    }

    for key in sum_features.keys():
        try:
            aver_features[key] = sum_features[key] / count
        except Exception as e:
            #print(e)
            return dict()
    return aver_features

def playlist_recommendation_tracks(spotify_api: SpotifyAPI, data, sim_artists, aver_features, limit, market) -> list:
    full_uris = list()

    for artists in sim_artists:
        seed_tracks = str()
        seed_artists = str()
        tracks = []

        for track in data:
            if track['artist'] in artists:
                tracks.append(track)

        counter = 0
        for track in tracks:
            if counter != 5:
                item = track['track'].split(':')[2]
                seed_tracks += item + ','

                item1 = track['artist'].split(':')[2]
                seed_artists += item1 + ','

                counter += 1
            else:
                seed_tracks = seed_tracks[:-1]
                seed_artists = seed_artists[:-1]

                params = {
                    "seed_tracks": seed_tracks,
                    "seed_artist": seed_artists,
                    "target_danceability": aver_features['dance'],
                    "target_energy": aver_features['energy'],
                    "target_loudness": aver_features['loud'],
                    "target_speechiness": aver_features['speech'],
                    "target_valence": aver_features['valence'],
                    "limit": limit,
                    "market": market
                }

                rec_data = spotify_api.track_recommendation(params)
                uris = list_of_tracks(rec_data)
                full_uris.extend(list(set(uris).difference(set(full_uris))))

                counter = 0
                seed_tracks = str()
                seed_artists = str()

        if len(seed_tracks) != 0:
            seed_tracks = seed_tracks[:-1]
            seed_artists = seed_artists[:-1]

            params = {
                "seed_tracks": seed_tracks,
                "seed_artist": seed_artists,
                "target_danceability": aver_features['dance'],
                "target_energy": aver_features['energy'],
                "target_loudness": aver_features['loud'],
                "target_speechiness": aver_features['speech'],
                "target_valence": aver_features['valence'],
                "limit": "5",
                "market": "US"
            }

            rec_data = spotify_api.track_recommendation(params)
            uris = list_of_tracks(rec_data)
            full_uris.extend(list(set(uris).difference(set(full_uris))))

    return full_uris

def create_based_playlist(spotify_api: SpotifyAPI, playlist_id: str, name: str, public: bool =True,
                          desc: str = "", base_on_market: bool = False, limit: int = 5) -> str:

    user_data = spotify_api.user_info()
    user_id = user_data['id']

    market = "US"
    if base_on_market:
        market = user_data['country']

    data = spotify_api.playlist_tracks(playlist_id)

    artists = list()

    for i in data:
        artists.append(i['artist'])

    similars = similar_artists(spotify_api, artists)

    aver_features = average_audio_features(spotify_api, data)

    full_uris = playlist_recommendation_tracks(spotify_api, data, similars, aver_features, limit, market)

    return spotify_api.create_playlist(user_id, name, full_uris, public, desc)
