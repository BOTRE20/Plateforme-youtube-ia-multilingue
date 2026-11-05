# youtub-ai  youtube-tiktok.streamlit.app
import streamlit as st
import streamlit.components.v1 as components
import requests
import urllib.parse
import json
import re
import random
import time
import html
import os
import tempfile
import subprocess
import shutil
from deep_translator import GoogleTranslator

# Les bibliothèques lourdes (whisper, torch, transformers, gtts, soundfile, numpy)
# sont importées uniquement dans la page "Traducteur" pour que l'appli démarre vite.

st.set_page_config(
    page_title="YouTube-TikTok",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Style CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%); }

    .main-header {
        font-size: 3rem; font-weight: 700;
        background: linear-gradient(135deg, #FF0000, #000000);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 1rem; letter-spacing: -0.5px;
    }
    .sub-header { text-align: center; color: #6c757d; margin-bottom: 2rem; font-size: 1.2rem; }

    .video-card {
        background: white; border-radius: 16px; overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        margin-bottom: 0.5rem; position: relative;
    }
    .video-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.12); }
    .thumbnail-container { position: relative; width: 100%; padding-bottom: 56.25%; background: #000; overflow: hidden; }
    .video-thumbnail { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
    .duration-badge {
        position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.7);
        color: white; padding: 2px 8px; border-radius: 20px; font-size: 0.7rem;
        font-weight: 600; font-family: monospace;
    }
    .platform-badge {
        position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7);
        color: white; padding: 2px 8px; border-radius: 20px; font-size: 0.7rem; font-weight: 600;
    }
    .video-info { padding: 12px; }
    .video-title {
        font-weight: 600; font-size: 0.95rem; margin-bottom: 6px; line-height: 1.4;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
    }
    .video-channel { font-size: 0.8rem; color: #6c757d; margin-bottom: 4px; }
    .video-meta { font-size: 0.7rem; color: #adb5bd; }

    .stButton > button { border-radius: 30px !important; font-weight: 500 !important; transition: all 0.2s ease !important; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

    section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e9ecef; }

    .translation-badge { background: #4caf50; color: white; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; margin-left: 0.5rem; font-weight: 500; }
    .tiktok-badge { background: #000; color: #fff; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; margin-left: 0.5rem; }

    .download-btn, .download-btn-sos {
        width: 100%; padding: 0.5rem 1rem; border: none; border-radius: 30px;
        color: white; font-weight: 500; cursor: pointer;
    }
    .download-btn { background: #ff0000; }
    .download-btn-sos { background: #222; }

    @media (max-width: 768px) {
        .main-header { font-size: 2rem; }
        .sub-header { font-size: 1rem; }
    }
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
""", unsafe_allow_html=True)

# --- État de session ---
_defaults = {
    'page': 'accueil',
    'selected_video': None,
    'search_results': [],
    'search_error': None,
    'last_search_key': None,
    'favorites': [],
    'last_search': "",
    'translation_lang': "fr",
    'translated_title': None,
    'translated_description': None,
    'current_video_index': 0,
    'current_list_source': None,
    'trending_time_filter': 'week',
    'trending_cache': {},
    'rec_channel': None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

langues_traduction = {
    "Français": "fr", "Anglais": "en", "Chinois (simplifié)": "zh-CN", "Chinois (Taiwan)": "zh-TW",
    "Indonésien": "id", "Islandais": "is", "Italien": "it", "Hébreu": "iw", "Japonais": "ja",
    "Javanais": "jw", "Khmer": "km", "Kannada": "kn", "Coréen": "ko", "Latin": "la",
    "Lituanien": "lt", "Letton": "lv", "Malayalam": "ml", "Marathi": "mr", "Malais": "ms",
    "Haoussa": "ha", "Yoruba": "yo", "Ewe": "ee", "Akan": "ak", "Shona": "sn", "Swahili": "sw",
    "Afrikaans": "af", "Amharique": "am", "Arabe": "ar", "Bulgare": "bg", "Bengali": "bn",
    "Bosnien": "bs", "Catalan": "ca", "Tchèque": "cs", "Gallois": "cy", "Danois": "da",
    "Allemand": "de", "Grec": "el", "Espagnol": "es", "Estonien": "et", "Basque": "eu",
    "Finnois": "fi", "Galicien": "gl", "Gujarati": "gu", "Hindi": "hi", "Croate": "hr",
    "Hongrois": "hu", "Birman": "my", "Népalais": "ne", "Néerlandais": "nl", "Norvégien": "no",
    "Pendjabi": "pa", "Polonais": "pl", "Portugais (Brésil)": "pt", "Roumain": "ro",
    "Russe": "ru", "Cinghalais": "si", "Slovaque": "sk", "Albanais": "sq", "Serbe": "sr",
    "Soundanais": "su", "Suédois": "sv", "Tamoul": "ta", "Telugu": "te", "Thaï": "th",
    "Filipino": "tl", "Turc": "tr", "Ukrainien": "uk", "Ourdou": "ur", "Vietnamien": "vi",
}
langues_tts = langues_traduction.copy()
hf_tts_models = {
    "Ewe": "facebook/mms-tts-ewe",
    "Shona": "facebook/mms-tts-sna",
    "Yoruba": "facebook/mms-tts-yor",
    "Akan": "facebook/mms-tts-aka",
}
hf_languages = set(hf_tts_models.keys())


#  UTILITAIRES TTS / WHISPER (imports paresseux) 

@st.cache_resource
def load_hf_tts_model(model_name):
    from transformers import pipeline
    return pipeline("text-to-speech", model=model_name, device=-1)


@st.cache_resource
def load_whisper_model(name="small"):
    import whisper
    return whisper.load_model(name)


@st.cache_data
def get_gtts_supported_langs():
    from gtts.lang import tts_langs
    return tts_langs()


# =====================  TRADUCTION  =====================

HEADERS_TRAD = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def _decouper(texte, n):
    """Découpe un texte en morceaux de n caractères max (de préférence aux fins de phrases)."""
    phrases = re.split(r'(?<=[.!?])\s+', texte)
    morceaux, courant = [], ""
    for p in phrases:
        while len(p) > n:
            if courant:
                morceaux.append(courant.strip())
                courant = ""
            morceaux.append(p[:n])
            p = p[n:]
        if len(courant) + len(p) + 1 <= n:
            courant += p + " "
        else:
            if courant.strip():
                morceaux.append(courant.strip())
            courant = p + " "
    if courant.strip():
        morceaux.append(courant.strip())
    return morceaux


def _trad_google_officiel(texte, cible, source):
    try:
        cle = st.secrets["GOOGLE_TRANSLATE_API_KEY"]
    except Exception:
        raise RuntimeError("pas de clé GOOGLE_TRANSLATE_API_KEY")
    sortie = []
    for m in _decouper(texte, 4500):
        data = {"q": m, "target": cible, "format": "text", "key": cle}
        if source != "auto":
            data["source"] = source
        r = requests.post("https://translation.googleapis.com/language/translate/v2", data=data, timeout=20)
        r.raise_for_status()
        sortie.append(r.json()["data"]["translations"][0]["translatedText"])
    return " ".join(sortie)


def _trad_google_deep(texte, cible, source):
    sortie = []
    for m in _decouper(texte, 4500):
        sortie.append(GoogleTranslator(source=source, target=cible).translate(m))
        time.sleep(0.3)
    return " ".join(s for s in sortie if s)


def _trad_google_gtx(texte, cible, source):
    sortie = []
    for m in _decouper(texte, 1500):
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": source, "tl": cible, "dt": "t", "q": m},
            headers=HEADERS_TRAD, timeout=15)
        r.raise_for_status()
        sortie.append("".join(seg[0] for seg in r.json()[0] if seg[0]))
        time.sleep(0.4)
    return " ".join(sortie)


LINGVA_INSTANCES = [
    "https://lingva.ml",
    "https://lingva.thedaviddelta.com",
    "https://translate.plausibility.cloud",
]


def _trad_lingva(texte, cible, source):
    corr = {"zh-CN": "zh", "zh-TW": "zh_HANT"}
    cible, source = corr.get(cible, cible), corr.get(source, source)
    derniere = None
    for base in LINGVA_INSTANCES:
        try:
            sortie = []
            for m in _decouper(texte, 900):
                url = f"{base}/api/v1/{source}/{cible}/{urllib.parse.quote(m, safe='')}"
                r = requests.get(url, headers=HEADERS_TRAD, timeout=20)
                r.raise_for_status()
                sortie.append(r.json()["translation"])
                time.sleep(0.3)
            return " ".join(sortie)
        except Exception as e:
            derniere = e
    raise RuntimeError(f"toutes les instances Lingva ont échoué ({derniere})")


def _trad_mymemory(texte, cible, source):
    corr = {"iw": "he", "jw": "jv"}
    cible, source = corr.get(cible, cible), corr.get(source, source)
    src = "Autodetect" if source == "auto" else source
    sortie = []
    for m in _decouper(texte, 450):
        r = requests.get("https://api.mymemory.translated.net/get",
                         params={"q": m, "langpair": f"{src}|{cible}"},
                         headers=HEADERS_TRAD, timeout=15)
        r.raise_for_status()
        j = r.json()
        t = j.get("responseData", {}).get("translatedText", "")
        if str(j.get("responseStatus")) != "200" or "MYMEMORY WARNING" in t:
            raise RuntimeError(t or "réponse invalide")
        sortie.append(t)
        time.sleep(0.3)
    return " ".join(sortie)


MOTEURS_TRADUCTION = [
    ("Google (API officielle)", _trad_google_officiel),
    ("Google", _trad_google_deep),
    ("Google (direct)", _trad_google_gtx),
    ("Lingva", _trad_lingva),
    ("MyMemory", _trad_mymemory),
]


@st.cache_data(show_spinner=False, ttl=3600)
def _traduire_cache(texte, langue_cible, source):
    erreurs = []
    for nom, fonction in MOTEURS_TRADUCTION:
        try:
            resultat = fonction(texte, langue_cible, source)
            if resultat and resultat.strip():
                return resultat
            erreurs.append(f"{nom} : résultat vide")
        except Exception as e:
            erreurs.append(f"{nom} : {str(e)[:120]}")
    raise RuntimeError("Tous les moteurs de traduction ont échoué.\n- " + "\n- ".join(erreurs))


def traduire_texte(texte, langue_cible, source='auto'):
    if not texte or texte.strip() == "":
        return texte
    try:
        return _traduire_cache(texte, langue_cible, source)
    except Exception as e:
        st.warning(f"Erreur de traduction : {e}")
        return texte


def traduire_texte_long(texte, langue_cible, source='auto', max_chars=4500):
    if not texte:
        return ""
    if len(texte) <= max_chars:
        return traduire_texte(texte, langue_cible, source)

    morceaux = _decouper(texte, max_chars)
    parts = []
    barre = st.progress(0, text="Traduction du texte...")
    for i, morceau in enumerate(morceaux):
        parts.append(traduire_texte(morceau, langue_cible, source))
        barre.progress((i + 1) / len(morceaux), text=f"Traduction : partie {i+1}/{len(morceaux)}")
        time.sleep(0.5)
    barre.empty()
    return " ".join(parts)


def generer_parole_par_morceaux(pipeline_tts, texte, taille_morceau=200):
    """Génère la parole morceau par morceau pour éviter une allocation mémoire trop grande."""
    import numpy as np

    morceaux = _decouper(texte, taille_morceau)
    if not morceaux:
        raise ValueError("Aucun morceau de texte à traiter.")

    parties_audio, freq = [], None
    barre = st.progress(0, text="Génération audio par morceaux...")
    for i, morceau in enumerate(morceaux):
        try:
            sortie = pipeline_tts(morceau)
            audio = sortie.get("audio")
            sr = sortie.get("sampling_rate", 16000)
            if audio is None:
                st.warning("Échec de la synthèse pour un morceau (ignoré).")
                continue
            audio = np.squeeze(np.array(audio, dtype=np.float32))
            parties_audio.append(audio)
            if freq is None:
                freq = sr
        except Exception as e:
            st.warning(f"Erreur sur un morceau : {e}")
            continue
        barre.progress((i + 1) / len(morceaux), text=f"Morceau {i+1}/{len(morceaux)}")
    barre.empty()

    if not parties_audio:
        raise RuntimeError("Aucun audio n'a pu être généré.")
    return np.concatenate(parties_audio), freq


# =====================  RECHERCHE VIDÉOS  =====================

def search_youtube_videos(query, max_results=15, time_filter=None):
    if not query or query.strip() == "":
        query = "popular videos"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        if time_filter:
            filter_params = {'today': 'EgIIAg%3D%3D', 'week': 'EgQIBDAB'}
            if time_filter in filter_params:
                url += f"&sp={filter_params[time_filter]}"

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        videos = []
        json_data = None
        for pattern in [r'var ytInitialData = ({.*?});</script>', r'ytInitialData\s*=\s*({.*?});']:
            match = re.search(pattern, response.text, re.DOTALL)
            if match:
                try:
                    json_data = json.loads(match.group(1))
                    break
                except Exception:
                    continue

        if json_data:
            try:
                sections = (json_data.get('contents', {})
                            .get('twoColumnSearchResultsRenderer', {})
                            .get('primaryContents', {})
                            .get('sectionListRenderer', {})
                            .get('contents', []))
                for item in sections:
                    for video_item in item.get('itemSectionRenderer', {}).get('contents', []):
                        vr = video_item.get('videoRenderer', {})
                        if not vr:
                            continue
                        video_id = vr.get('videoId')
                        title = vr.get('title', {}).get('runs', [{}])[0].get('text', '')
                        channel = vr.get('ownerText', {}).get('runs', [{}])[0].get('text', '')
                        duration = vr.get('lengthText', {}).get('simpleText', '')
                        thumbs = vr.get('thumbnail', {}).get('thumbnails', [])
                        thumb = thumbs[0].get('url', '') if thumbs else f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'
                        views = vr.get('viewCountText', {}).get('simpleText', '')
                        published = vr.get('publishedTimeText', {}).get('simpleText', '')
                        if video_id and title:
                            videos.append({
                                'id': video_id, 'title': title, 'channel': channel,
                                'duration': duration, 'thumbnail': thumb,
                                'url': f'https://www.youtube.com/watch?v={video_id}',
                                'views': views, 'published': published, 'platform': 'youtube'
                            })
                        if len(videos) >= max_results:
                            return videos
            except Exception:
                pass

        if not videos:
            pattern = r'"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"'
            for video_id, title in re.findall(pattern, response.text)[:max_results]:
                videos.append({
                    'id': video_id, 'title': title.replace('\\"', '"').replace('\\\\', '\\'),
                    'channel': 'YouTube', 'duration': '',
                    'thumbnail': f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg',
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'views': '', 'published': '', 'platform': 'youtube'
                })
        return videos[:max_results]
    except Exception:
        return []


def get_trending_videos(max_results=15, time_filter='week'):
    """Tendances avec cache de 10 min en session (évite de re-scraper à chaque clic)."""
    cache = st.session_state.trending_cache
    cle = (time_filter, max_results)
    if cle in cache and time.time() - cache[cle][0] < 600:
        return cache[cle][1]
    videos = search_youtube_videos("trending", max_results, time_filter=time_filter)
    if videos:
        cache[cle] = (time.time(), videos)
    return videos


def search_tiktok_videos(query, max_results=15):
    """Retourne (liste_de_videos, message_erreur). L'API tikwm attend un POST."""
    url = "https://www.tikwm.com/api/feed/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Referer": "https://www.tikwm.com/",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = {"keywords": query, "count": max_results, "cursor": 0, "web": 1, "hd": 1}

    erreur = None
    for _ in range(3):  # limite de 1 requête/seconde côté API
        try:
            resp = requests.post(url, data=data, headers=headers, timeout=15)
            resp.raise_for_status()
            j = resp.json()

            if j.get("code") == 0:
                videos = []
                for item in (j.get("data") or {}).get("videos") or []:
                    vid = str(item.get("video_id") or item.get("id") or "")
                    if not vid:
                        continue
                    secondes = int(item.get("duration") or 0)
                    auteur = item.get("author") or {}
                    play = item.get("play") or f"https://www.tikwm.com/video/media/play/{vid}.mp4"
                    if play.startswith("/"):
                        play = "https://www.tikwm.com" + play
                    cover = item.get("cover") or item.get("origin_cover") or ""
                    if cover.startswith("/"):
                        cover = "https://www.tikwm.com" + cover
                    videos.append({
                        'id': vid,
                        'title': item.get('title') or 'Sans titre',
                        'channel': auteur.get('nickname') or auteur.get('unique_id') or 'Inconnu',
                        'duration': f"{secondes // 60}:{secondes % 60:02d}",
                        'thumbnail': cover,
                        'url': play,
                        'views': f"{int(item.get('play_count') or 0):,} vues".replace(",", " "),
                        'published': '',
                        'platform': 'tiktok'
                    })
                if videos:
                    return videos[:max_results], None
                return [], "Aucune vidéo retournée par l'API."

            erreur = j.get("msg") or f"code {j.get('code')}"
            time.sleep(1.5)
        except Exception as e:
            erreur = str(e)
            time.sleep(1.5)

    return [], erreur


# =====================  AFFICHAGE  =====================

def afficher_video(video):
    platform = video.get('platform', 'youtube')
    if platform == 'youtube':
        embed_url = f"https://www.youtube.com/embed/{video['id']}?autoplay=1&rel=0"
        components.html(
            f'<iframe width="100%" height="400" src="{embed_url}" frameborder="0" '
            f'allow="autoplay; encrypted-media" allowfullscreen></iframe>', height=415)
    else:
        # TikTok : lecture directe du fichier mp4 fourni par l'API
        st.video(video['url'])


def ouvrir_video(video, source=None, index=0):
    st.session_state.selected_video = video
    st.session_state.page = 'lecture'
    st.session_state.translated_title = None
    st.session_state.translated_description = None
    st.session_state.current_list_source = source
    st.session_state.current_video_index = index


def display_video_grid(videos, cols=3, source='search'):
    if not videos:
        st.info("Aucune vidéo à afficher.")
        return

    for row_idx in range(0, len(videos), cols):
        columns = st.columns(cols)
        for col_idx, video in enumerate(videos[row_idx:row_idx + cols]):
            global_idx = row_idx + col_idx
            platform = video.get('platform', 'youtube')
            with columns[col_idx]:
                icon = '<i class="fab fa-youtube"></i>' if platform == 'youtube' else '<i class="fab fa-tiktok"></i>'
                titre = html.escape(video['title'][:70] + ('...' if len(video['title']) > 70 else ''))
                chaine = html.escape(video['channel'][:40] + ('...' if len(video['channel']) > 40 else ''))
                meta = html.escape(f"{video.get('views', '')} • {video.get('published', '')}".strip(" •"))
                thumb = html.escape(video['thumbnail'], quote=True)

                st.markdown(f"""
                <div class="video-card">
                    <div class="thumbnail-container">
                        <img src="{thumb}" class="video-thumbnail" loading="lazy">
                        <div class="duration-badge">{html.escape(video.get('duration', ''))}</div>
                        <div class="platform-badge">{icon}</div>
                    </div>
                    <div class="video-info">
                        <div class="video-title">{titre}</div>
                        <div class="video-channel">{chaine}</div>
                        <div class="video-meta">{meta}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                key_base = f"{source}_{platform}_{video['id']}_{global_idx}"
                b1, b2 = st.columns([3, 1])
                with b1:
                    if st.button("Regarder", key=f"play_{key_base}", use_container_width=True):
                        ouvrir_video(video, source=source, index=global_idx)
                        st.rerun()
                with b2:
                    is_fav = any(f['id'] == video['id'] and f.get('platform') == platform
                                 for f in st.session_state.favorites)
                    if st.button("★" if is_fav else "☆", key=f"fav_{key_base}", use_container_width=True):
                        if is_fav:
                            st.session_state.favorites = [
                                f for f in st.session_state.favorites
                                if not (f['id'] == video['id'] and f.get('platform') == platform)]
                        else:
                            st.session_state.favorites.append(video)
                        st.rerun()


# =====================  BARRE LATÉRALE  =====================

with st.sidebar:
    st.markdown('<div style="font-size:1.5rem;font-weight:700;color:#FF0000;text-align:center;'
                'padding:1rem;margin-bottom:1rem;"> Media Fusion</div>', unsafe_allow_html=True)

    for label, page in [(" Accueil", 'accueil'), (" Rechercher", 'recherche'),
                        ("Favoris", 'favoris'), (" Traducteur vidéo IA", 'traducteur')]:
        if st.button(label, use_container_width=True, key=f"nav_{page}"):
            st.session_state.page = page
            st.rerun()

    st.markdown("---")
    st.markdown(f"** Favoris :** {len(st.session_state.favorites)}")

    if st.session_state.selected_video:
        st.markdown("---")
        st.markdown("** En cours :**")
        st.markdown(f"*{st.session_state.selected_video['title'][:50]}...*")
        if st.button("↩ Reprendre", use_container_width=True, key="nav_resume"):
            st.session_state.page = 'lecture'
            st.rerun()


# =====================  PAGES  =====================

page = st.session_state.page

if page == 'accueil':
    st.markdown('<div class="main-header">Media Fusion</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">YouTube & TikTok • Traduction & Doublage IA</div>', unsafe_allow_html=True)

    time_filter_labels = {'today': "Aujourd'hui", 'week': 'Cette semaine'}
    selected_filter = st.radio(
        "Filtre tendances",
        options=list(time_filter_labels.keys()),
        format_func=lambda x: time_filter_labels[x],
        horizontal=True,
        index=list(time_filter_labels.keys()).index(st.session_state.trending_time_filter)
    )
    if selected_filter != st.session_state.trending_time_filter:
        st.session_state.trending_time_filter = selected_filter
        st.rerun()

    with st.spinner("Chargement des vidéos tendances..."):
        trending = get_trending_videos(15, time_filter=st.session_state.trending_time_filter)

    if trending:
        display_video_grid(trending, source='accueil')
    else:
        st.warning("Impossible de charger les tendances. Voici quelques suggestions :")
        demo_videos = [
            {'id': 'dQw4w9WgXcQ', 'title': 'Rick Astley - Never Gonna Give You Up', 'channel': 'Rick Astley',
             'thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
             'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'views': '1,5 Md de vues',
             'published': 'il y a 12 ans', 'platform': 'youtube', 'duration': '3:33'},
            {'id': 'kJQP7kiw5Fk', 'title': 'Luis Fonsi - Despacito ft. Daddy Yankee', 'channel': 'Luis Fonsi',
             'thumbnail': 'https://img.youtube.com/vi/kJQP7kiw5Fk/hqdefault.jpg',
             'url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk', 'views': '7,8 Md de vues',
             'published': 'il y a 6 ans', 'platform': 'youtube', 'duration': '4:42'},
            {'id': 'JGwWNGJdvx8', 'title': 'Ed Sheeran - Shape of You', 'channel': 'Ed Sheeran',
             'thumbnail': 'https://img.youtube.com/vi/JGwWNGJdvx8/hqdefault.jpg',
             'url': 'https://www.youtube.com/watch?v=JGwWNGJdvx8', 'views': '5,8 Md de vues',
             'published': 'il y a 6 ans', 'platform': 'youtube', 'duration': '4:24'},
        ]
        display_video_grid(demo_videos, cols=3, source='demo')

    yt_favs = [v for v in st.session_state.favorites if v.get('platform') == 'youtube']
    if yt_favs:
        st.markdown("---")
        st.markdown("##  Recommandé pour vous")
        fav_channels = list({v['channel'] for v in yt_favs})
        if st.session_state.rec_channel not in fav_channels:
            st.session_state.rec_channel = random.choice(fav_channels)
        rec_key = ("rec", st.session_state.rec_channel)
        if rec_key not in st.session_state.trending_cache:
            vids = search_youtube_videos(st.session_state.rec_channel, 6)
            if vids:
                st.session_state.trending_cache[rec_key] = (time.time(), vids)
        rec_videos = st.session_state.trending_cache.get(rec_key, (0, []))[1]
        if rec_videos:
            display_video_grid(rec_videos, cols=3, source='reco')

elif page == 'recherche':
    st.markdown("## 🔍 Recherche multi-plateformes")

    plateforme = st.radio("Choisissez la plateforme :", options=["YouTube", "TikTok"], horizontal=True)
    search_query = st.text_input("Rechercher des vidéos :", placeholder="Entrez des mots-clés...",
                                 value=st.session_state.last_search)

    if search_query:
        st.session_state.last_search = search_query
        cle = (plateforme, search_query)

        # On ne relance la recherche que si la requête change (évite la limite de débit de l'API)
        if st.session_state.last_search_key != cle:
            with st.spinner("Recherche en cours..."):
                if plateforme == "YouTube":
                    results, erreur = search_youtube_videos(search_query, 15), None
                    if not results:
                        erreur = "YouTube n'a retourné aucun résultat."
                else:
                    results, erreur = search_tiktok_videos(search_query, 15)
            st.session_state.search_results = results
            st.session_state.search_error = erreur
            # on ne mémorise que les succès pour pouvoir réessayer en cas d'échec
            st.session_state.last_search_key = cle if results else None

        results = st.session_state.search_results
        if results:
            st.markdown(f"### Résultats pour '{search_query}' sur {plateforme}")
            display_video_grid(results, cols=3, source='search')
        else:
            st.warning("Aucun résultat trouvé.")
            if st.session_state.search_error:
                st.caption(f"Détail technique : {st.session_state.search_error}")
    else:
        st.info("Entrez un mot-clé pour commencer la recherche.")

elif page == 'favoris':
    st.markdown("##  Mes favoris")
    if st.session_state.favorites:
        display_video_grid(st.session_state.favorites, cols=3, source='favorites')
    else:
        st.info("Vous n'avez pas encore de vidéos favorites. Ajoutez-en en cliquant sur ☆.")
        st.markdown("###  Suggestions")
        with st.spinner("Chargement..."):
            suggestions = get_trending_videos(6)
        if suggestions:
            display_video_grid(suggestions, cols=3, source='sugg_fav')

elif page == 'lecture' and st.session_state.selected_video:
    video = st.session_state.selected_video
    platform = video.get('platform', 'youtube')

    col1, col2 = st.columns([2, 1])

    with col1:
        afficher_video(video)

        badge = " YouTube" if platform == 'youtube' else "🎵 TikTok"
        titre = html.escape(st.session_state.translated_title or video['title'])
        traduit = "<span class='translation-badge'>Traduit</span>" if st.session_state.translated_title else ""
        st.markdown(f"## {titre} {traduit}<span class='tiktok-badge'>{badge}</span>", unsafe_allow_html=True)
        st.markdown(f"**{video['channel']}** • {video.get('views', '')} • {video.get('published', '')}")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            is_fav = any(f['id'] == video['id'] and f.get('platform') == platform for f in st.session_state.favorites)
            if is_fav:
                if st.button(" Retirer des favoris", use_container_width=True, key="fav_toggle"):
                    st.session_state.favorites = [f for f in st.session_state.favorites
                                                  if not (f['id'] == video['id'] and f.get('platform') == platform)]
                    st.rerun()
            else:
                if st.button(" Ajouter aux favoris", use_container_width=True, key="fav_toggle"):
                    st.session_state.favorites.append(video)
                    st.rerun()
        with col_b:
            if st.button(" Partager", use_container_width=True, key="share"):
                st.info(f"Lien : {video['url']}")
        with col_c:
            if st.button("Accueil", use_container_width=True, key="home_btn"):
                st.session_state.page = 'accueil'
                st.session_state.selected_video = None
                st.rerun()

        # Navigation précédent / suivant dans la liste d'origine (résultats de recherche ou favoris)
        src = st.session_state.current_list_source
        liste = (st.session_state.search_results if src == 'search'
                 else st.session_state.favorites if src == 'favorites' else [])
        idx = st.session_state.current_video_index
        if liste and 0 <= idx < len(liste) and liste[idx]['id'] == video['id']:
            n1, n2, n3 = st.columns([1, 2, 1])
            with n1:
                if idx > 0 and st.button("⏮ Précédent", key="prev_vid", use_container_width=True):
                    ouvrir_video(liste[idx - 1], source=src, index=idx - 1)
                    st.rerun()
            with n2:
                st.markdown(f"<div style='text-align:center;padding:10px;'>{idx + 1} / {len(liste)}</div>",
                            unsafe_allow_html=True)
            with n3:
                if idx < len(liste) - 1 and st.button("Suivant ⏭", key="next_vid", use_container_width=True):
                    ouvrir_video(liste[idx + 1], source=src, index=idx + 1)
                    st.rerun()

        with st.expander("⬇ Télécharger cette vidéo"):
            if platform == 'youtube':
                st.markdown("**Y2mate** (YouTube)")
                y2mate_url = f"https://www-y2mate.com/fr22/search/?query={urllib.parse.quote(video['url'])}"
                sos_url = video['url'].replace('youtube.com', 'sosyoutube.com')
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown(f'<a href="{y2mate_url}" target="_blank"><button class="download-btn">🎬 Ouvrir Y2mate</button></a>',
                                unsafe_allow_html=True)
                with d2:
                    st.markdown(f'<a href="{sos_url}" target="_blank"><button class="download-btn-sos">⚡ Astuce SOS</button></a>',
                                unsafe_allow_html=True)
            else:
                st.markdown("**Téléchargement TikTok**")
                st.markdown(f"[⬇ Lien direct de la vidéo (mp4)]({video['url']})")
                enc = urllib.parse.quote(video['url'])
                t1, t2 = st.columns(2)
                with t1:
                    st.markdown(f'<a href="https://snaptik.app/fr?url={enc}" target="_blank"><button class="download-btn">📱 SnapTik</button></a>',
                                unsafe_allow_html=True)
                with t2:
                    st.markdown(f'<a href="https://ssstik.io/fr?url={enc}" target="_blank"><button class="download-btn-sos">🎵 SSSTik</button></a>',
                                unsafe_allow_html=True)

    with col2:
        st.markdown("###  Traduction du titre")
        noms = list(langues_traduction.keys())
        codes = list(langues_traduction.values())
        idx_langue = codes.index(st.session_state.translation_lang) if st.session_state.translation_lang in codes else 0
        langue_nom = st.selectbox("Langue cible :", options=noms, index=idx_langue)
        nouvelle_langue = langues_traduction[langue_nom]

        if st.button(" Traduire le titre", use_container_width=True, key="do_translate"):
            st.session_state.translation_lang = nouvelle_langue
            with st.spinner("Traduction en cours..."):
                st.session_state.translated_title = traduire_texte(video['title'], nouvelle_langue)
            st.rerun()

        if st.button("↺ Réinitialiser la traduction", key="reset_translate"):
            st.session_state.translated_title = None
            st.session_state.translated_description = None
            st.rerun()

        st.markdown("### Suggestions")
        suggestions = [v for v in st.session_state.search_results
                       if v['id'] != video['id'] and v.get('platform') == platform][:5]
        if not suggestions and platform == 'youtube':
            channel_videos = search_youtube_videos(video['channel'], 6)
            suggestions = [v for v in channel_videos if v['id'] != video['id']][:5]

        if suggestions:
            for sug in suggestions:
                c_thumb, c_info, c_btn = st.columns([1, 3, 1])
                with c_thumb:
                    if sug.get('thumbnail'):
                        st.image(sug['thumbnail'], use_container_width=True)
                with c_info:
                    st.markdown(f"**{sug['title'][:50]}{'...' if len(sug['title']) > 50 else ''}**")
                    st.caption(sug['channel'][:30])
                with c_btn:
                    if st.button(" ", key=f"watch_{sug['platform']}_{sug['id']}", use_container_width=True):
                        ouvrir_video(sug, source=None, index=0)
                        st.rerun()
        else:
            st.info("Aucune suggestion pour le moment.")

elif page == 'traducteur':
    st.markdown("##  Traduction automatique de vidéo")
    st.write("Téléversez une vidéo de moins de 6 minutes et choisissez la langue de doublage.")

    if not shutil.which("ffmpeg"):
        st.error("ffmpeg n'est pas installé sur le système (ajoutez `ffmpeg` dans packages.txt). "
                 "La traduction vidéo est impossible.")
        st.stop()

    try:
        import soundfile as sf
        from gtts import gTTS
        import whisper  # noqa: F401
    except ImportError as e:
        st.error(f"Bibliothèque manquante : {e}. Vérifiez requirements.txt "
                 "(openai-whisper, gTTS, soundfile, transformers, torch, numpy).")
        st.stop()

    video_file = st.file_uploader(" Upload vidéo", type=["mp4", "mov", "avi", "mkv"])
    selected_language = st.selectbox("🎙 Langue cible du doublage", options=list(langues_tts.keys()))
    target_language_code = langues_tts[selected_language]

    if video_file:
        st.video(video_file)

        if st.button("🎧 Traduire la vidéo", type="primary"):
            with st.spinner("Traitement en cours... Cela peut prendre plusieurs minutes."):
                temp_dir = tempfile.mkdtemp()
                input_video = os.path.join(temp_dir, "video.mp4")
                translated_audio = os.path.join(temp_dir, "audio_translated.mp3")
                output_video = os.path.join(temp_dir, "video_finale.mp4")

                with open(input_video, "wb") as f:
                    f.write(video_file.getbuffer())

                # 1. Transcription
                try:
                    model = load_whisper_model("small")
                    result = model.transcribe(input_video)
                    text = result["text"]
                except Exception as e:
                    st.error(f"Erreur lors de la transcription : {e}")
                    st.stop()

                if not text.strip():
                    st.error("Aucune parole détectée dans la vidéo.")
                    st.stop()

                # 2. Traduction
                translated_text = traduire_texte_long(text, target_language_code)

                # 3. Synthèse vocale
                try:
                    if selected_language in hf_languages:
                        tts_pipeline = load_hf_tts_model(hf_tts_models[selected_language])
                        audio_array, sampling_rate = generer_parole_par_morceaux(tts_pipeline, translated_text)
                        audio_file_for_ffmpeg = os.path.join(temp_dir, "audio_translated.wav")
                        sf.write(audio_file_for_ffmpeg, audio_array, sampling_rate, format='WAV')
                    else:
                        supported = get_gtts_supported_langs()
                        if target_language_code not in supported:
                            st.warning(f"La langue '{selected_language}' n'est pas supportée par gTTS. "
                                       "Utilisation de l'anglais à la place.")
                            target_language_code = 'en'
                        gTTS(text=translated_text, lang=target_language_code).save(translated_audio)
                        audio_file_for_ffmpeg = translated_audio
                except Exception as e:
                    st.error(f"Erreur lors de la synthèse vocale : {e}")
                    st.stop()

                # 4. Assemblage
                try:
                    subprocess.run([
                        "ffmpeg", "-y",
                        "-i", input_video, "-i", audio_file_for_ffmpeg,
                        "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
                        "-shortest", output_video
                    ], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    st.error(f"Erreur lors de l'assemblage vidéo :\n{e.stderr}")
                    st.stop()

                st.success("Vidéo traduite avec succès !")
                with st.expander(" Texte original / traduit"):
                    st.markdown("**Original :**")
                    st.write(text)
                    st.markdown("**Traduit :**")
                    st.write(translated_text)
                st.video(output_video)

                with open(output_video, "rb") as f:
                    st.download_button("⬇ Télécharger la vidéo traduite", f,
                                       file_name="video_traduite.mp4", mime="video/mp4")

# --- Pied de page ---
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#6c757d;padding:1rem;'>"
    "MediaFusion • YouTube & TikTok • Traduction IA (80 langues) • Doublage (Ewe, Yoruba, Shona, Akan inclus)"
    "</div>"
    "<div style='text-align:center;color:#007bff;padding:1rem;'>By BOTRE LARE Aboudou</div>",
    unsafe_allow_html=True
)