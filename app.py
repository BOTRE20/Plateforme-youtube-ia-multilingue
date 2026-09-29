# youtub-ai  youtube-tiktok.streamlit.app
import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import re
import random
from datetime import datetime
from deep_translator import GoogleTranslator
import os

import tempfile
import math
import subprocess
import shutil
import whisper
from gtts import gTTS
from gtts.lang import tts_langs
from transformers import pipeline
import torch
import numpy as np
import soundfile as sf

# Configuration de la page
st.set_page_config(
    page_title="YouTube-TikTok",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Lecture des paramètres URL pour un clic direct sur une vidéo ---
if "video_id" in st.query_params:
    try:
        video = {
            "id": st.query_params["video_id"],
            "platform": st.query_params.get("platform", "youtube"),
            "title": st.query_params.get("title", ""),
            "channel": st.query_params.get("channel", ""),
            "duration": st.query_params.get("duration", ""),
            "thumbnail": st.query_params.get("thumbnail", ""),
            "url": st.query_params.get("url", ""),
            "views": st.query_params.get("views", ""),
            "published": st.query_params.get("published", ""),
        }
        # Décodage des caractères spéciaux
        for key in ["title", "channel", "duration", "thumbnail", "url", "views", "published"]:
            if key in video:
                video[key] = urllib.parse.unquote(video[key])

        st.session_state.selected_video = video
        st.session_state.page = "lecture"
        st.query_params.clear()
    except Exception as e:
        st.warning(f"Erreur lors de la lecture de l'URL : {e}")

# --- Style CSS modernisé ---
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Couleur de fond principale */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%);
    }

    /* En-tête principal */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF0000, #000000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        text-align: center;
        color: #6c757d;
        margin-bottom: 2rem;
        font-size: 1.2rem;
        font-weight: 400;
    }

    /* Cartes vidéo modernes */
    .video-card {
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        cursor: pointer;
        margin-bottom: 1rem;
        position: relative;
    }
    .video-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    .thumbnail-container {
        position: relative;
        width: 100%;
        padding-bottom: 56.25%; /* ratio 16:9 */
        background: #000;
        overflow: hidden;
    }
    .video-thumbnail {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.3s ease;
    }
    .video-card:hover .video-thumbnail {
        transform: scale(1.05);
    }
    .duration-badge {
        position: absolute;
        bottom: 8px;
        right: 8px;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(4px);
        color: white;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        font-family: monospace;
    }
    .platform-badge {
        position: absolute;
        top: 8px;
        left: 8px;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(4px);
        color: white;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .video-info {
        padding: 12px;
    }
    .video-title {
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 6px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        line-height: 1.4;
    }
    .video-channel {
        font-size: 0.8rem;
        color: #6c757d;
        margin-bottom: 4px;
    }
    .video-meta {
        font-size: 0.7rem;
        color: #adb5bd;
    }

    /* Boutons modernes */
    .stButton > button {
        border-radius: 30px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Barre latérale */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF0000, #000000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .sidebar-button {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 16px;
        border-radius: 12px;
        transition: background 0.2s;
        cursor: pointer;
    }
    .sidebar-button:hover {
        background: #f8f9fa;
    }

    /* Badges */
    .translation-badge {
        background: #4caf50;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        margin-left: 0.5rem;
        font-weight: 500;
    }
    .tiktok-badge {
        background: #000;
        color: #fff;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        margin-left: 0.5rem;
    }

    /* Expander personnalisé */
    .streamlit-expanderHeader {
        font-weight: 600;
        background-color: #f8f9fa;
        border-radius: 12px;
    }

    /* Suggestions horizontales */
    .suggestion-card {
        display: flex;
        margin-bottom: 12px;
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: transform 0.2s;
        cursor: pointer;
    }
    .suggestion-card:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .suggestion-thumb {
        width: 120px;
        height: 68px;
        object-fit: cover;
    }
    .suggestion-info {
        padding: 8px 12px;
        flex: 1;
    }
    .suggestion-title {
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .suggestion-channel {
        font-size: 0.7rem;
        color: #6c757d;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .main-header { font-size: 2rem; }
        .sub-header { font-size: 1rem; }
    }
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
""", unsafe_allow_html=True)

# --- Initialisation de l'état de session ---
if 'page' not in st.session_state:
    st.session_state.page = 'accueil'
if 'selected_video' not in st.session_state:
    st.session_state.selected_video = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'last_search' not in st.session_state:
    st.session_state.last_search = ""
if 'translation_lang' not in st.session_state:
    st.session_state.translation_lang = "fr"
if 'translated_title' not in st.session_state:
    st.session_state.translated_title = None
if 'translated_description' not in st.session_state:
    st.session_state.translated_description = None
if 'current_video_index' not in st.session_state:
    st.session_state.current_video_index = 0
if 'current_list_source' not in st.session_state:
    st.session_state.current_list_source = None
if 'trending_time_filter' not in st.session_state:
    st.session_state.trending_time_filter = 'week'

langues_traduction = {
    "Français": "fr",
    "Haoussa": "ha",
    "Yoruba": "yo",
    "Ewe": "ee",
    "Akan": "ak",
    "Shona": "sn",
    "Swahili": "sw",
    "Afrikaans": "af",
    "Amharique": "am",
    "Arabe": "ar",
    "Bulgare": "bg",
    "Bengali": "bn",
    "Bosnien": "bs",
    "Catalan": "ca",
    "Tchèque": "cs",
    "Gallois": "cy",
    "Danois": "da",
    "Allemand": "de",
    "Grec": "el",
    "Anglais": "en",
    "Espagnol": "es",
    "Estonien": "et",
    "Basque": "eu",
    "Finnois": "fi",
    "Galicien": "gl",
    "Gujarati": "gu",
    "Hindi": "hi",
    "Croate": "hr",
    "Hongrois": "hu",
    "Indonésien": "id",
    "Islandais": "is",
    "Italien": "it",
    "Hébreu": "iw",
    "Japonais": "ja",
    "Javanais": "jw",
    "Khmer": "km",
    "Kannada": "kn",
    "Coréen": "ko",
    "Latin": "la",
    "Lituanien": "lt",
    "Letton": "lv",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Malais": "ms",
    "Birman": "my",
    "Népalais": "ne",
    "Néerlandais": "nl",
    "Norvégien": "no",
    "Pendjabi": "pa",
    "Polonais": "pl",
    "Portugais (Brésil)": "pt",
    "Roumain": "ro",
    "Russe": "ru",
    "Cinghalais": "si",
    "Slovaque": "sk",
    "Albanais": "sq",
    "Serbe": "sr",
    "Soundanais": "su",
    "Suédois": "sv",
    "Tamoul": "ta",
    "Telugu": "te",
    "Thaï": "th",
    "Filipino": "tl",
    "Turc": "tr",
    "Ukrainien": "uk",
    "Ourdou": "ur",
    "Vietnamien": "vi",
    "Chinois (simplifié)": "zh-CN",
    "Chinois (Taiwan)": "zh-TW",
}
langues_tts = langues_traduction.copy()  # même liste pour la synthèse vocale
hf_tts_models = {
    "Ewe": "facebook/mms-tts-ewe",
    "Shona": "facebook/mms-tts-sna",
    "Yoruba": "facebook/mms-tts-yor",
    "Akan": "facebook/mms-tts-aka"
}
hf_languages = set(hf_tts_models.keys())

# --- Fonctions utilitaires ---

@st.cache_resource
def load_hf_tts_model(model_name):
    return pipeline("text-to-speech", model=model_name, device=-1, torch_dtype="auto")

@st.cache_data
def get_gtts_supported_langs():
    return tts_langs()

def traduire_texte(texte, langue_cible, source='auto'):
    if not texte or texte.strip() == "":
        return texte
    try:
        translator = GoogleTranslator(source=source, target=langue_cible)
        return translator.translate(texte)
    except Exception as e:
        st.warning(f"Erreur de traduction : {e}")
        return texte

def traduire_texte_long(texte, langue_cible, source='auto', max_chars=5000):
    if not texte:
        return ""
    if len(texte) <= max_chars:
        return traduire_texte(texte, langue_cible, source)

    sentences = re.split(r'(?<=[.!?])\s+', texte)
    translated_parts = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                translated_parts.append(traduire_texte(current_chunk.strip(), langue_cible, source))
            current_chunk = sentence + " "
    if current_chunk:
        translated_parts.append(traduire_texte(current_chunk.strip(), langue_cible, source))

    return " ".join(translated_parts)

# --- Fonction de génération vocale par morceaux (correction mémoire) ---
def generer_parole_par_morceaux(pipeline_tts, texte, taille_morceau=200):
    """
    Génère la parole en découpant le texte en petits morceaux pour éviter
    une allocation mémoire trop importante.
    Retourne (audio_array, frequence_echantillonnage).
    """
    phrases = re.split(r'(?<=[.!?])\s+', texte)
    morceaux = []
    morceau_courant = ""

    for phrase in phrases:
        if len(morceau_courant) + len(phrase) + 1 <= taille_morceau:
            morceau_courant += phrase + " "
        else:
            if morceau_courant:
                morceaux.append(morceau_courant.strip())
            morceau_courant = phrase + " "
    if morceau_courant:
        morceaux.append(morceau_courant.strip())

    if not morceaux:
        raise ValueError("Aucun morceau de texte à traiter.")

    parties_audio = []
    freq = None

    progress_bar = st.progress(0, text="Génération audio par morceaux...")
    for i, morceau in enumerate(morceaux):
        try:
            sortie = pipeline_tts(morceau)
            audio = sortie.get("audio")
            sr = sortie.get("sampling_rate", 16000)
            if audio is None:
                st.warning(f"Échec de la synthèse pour un morceau (ignoré).")
                continue
            audio = np.array(audio, dtype=np.float32)
            audio = np.squeeze(audio)  # garantit un tableau 1D
            parties_audio.append(audio)
            if freq is None:
                freq = sr
        except Exception as e:
            st.warning(f"Erreur sur un morceau : {e}")
            continue
        progress_bar.progress((i + 1) / len(morceaux), text=f"Morceau {i+1}/{len(morceaux)}")
    progress_bar.empty()

    if not parties_audio:
        raise RuntimeError("Aucun audio n'a pu être généré.")

    audio_final = np.concatenate(parties_audio)
    return audio_final, freq

def search_youtube_videos(query, max_results=15, time_filter=None):
    if not query or query.strip() == "":
        query = "popular videos"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        if time_filter:
            filter_params = {'today': 'EgIIAg%3D%3D', 'week': 'EgQIBDAB'}
            if time_filter in filter_params:
                url += f"&sp={filter_params[time_filter]}"

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        videos = []
        patterns = [
            r'var ytInitialData = ({.*?});</script>',
            r'ytInitialData\s*=\s*({.*?});'
        ]
        json_data = None
        for pattern in patterns:
            match = re.search(pattern, response.text, re.DOTALL)
            if match:
                try:
                    json_data = json.loads(match.group(1))
                    break
                except:
                    continue

        if json_data:
            try:
                contents = json_data.get('contents', {})
                two_column = contents.get('twoColumnSearchResultsRenderer', {})
                primary = two_column.get('primaryContents', {})
                section = primary.get('sectionListRenderer', {})
                contents_list = section.get('contents', [])
                for item in contents_list:
                    item_renderer = item.get('itemSectionRenderer', {})
                    contents2 = item_renderer.get('contents', [])
                    for video_item in contents2:
                        video_renderer = video_item.get('videoRenderer', {})
                        if video_renderer:
                            video_id = video_renderer.get('videoId')
                            title = video_renderer.get('title', {}).get('runs', [{}])[0].get('text', '')
                            channel = video_renderer.get('ownerText', {}).get('runs', [{}])[0].get('text', '')
                            duration = video_renderer.get('lengthText', {}).get('simpleText', '')
                            thumbnails = video_renderer.get('thumbnail', {}).get('thumbnails', [])
                            thumbnail_url = thumbnails[0].get('url', '') if thumbnails else f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'
                            views = video_renderer.get('viewCountText', {}).get('simpleText', '')
                            published = video_renderer.get('publishedTimeText', {}).get('simpleText', '')
                            if video_id and title:
                                videos.append({
                                    'id': video_id, 'title': title, 'channel': channel,
                                    'duration': duration, 'thumbnail': thumbnail_url,
                                    'url': f'https://www.youtube.com/watch?v={video_id}',
                                    'views': views, 'published': published, 'platform': 'youtube'
                                })
                            if len(videos) >= max_results:
                                return videos
            except Exception as e:
                pass

        if not videos:
            video_pattern = r'"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"'
            matches = re.findall(video_pattern, response.text)
            for match in matches[:max_results]:
                video_id, title = match
                videos.append({
                    'id': video_id, 'title': title.replace('\\"', '"').replace('\\\\', '\\'),
                    'channel': 'YouTube', 'duration': '',
                    'thumbnail': f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg',
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'views': '', 'published': '', 'platform': 'youtube'
                })
        return videos[:max_results]
    except Exception as e:
        return []

def get_trending_videos(max_results=15, time_filter='week'):
    return search_youtube_videos("trending", max_results, time_filter=time_filter)

def search_tiktok_videos(query, max_results=15):
    try:
        url = "https://www.tikwm.com/api/feed/search"
        params = {"keywords": query, "count": max_results, "cursor": 0, "web": 1}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                videos = []
                for item in data.get("data", {}).get("videos", []):
                    video_url = f"https://www.tikwm.com/video/media/play/{item['video_id']}.mp4"
                    videos.append({
                        'id': item['video_id'],
                        'title': item.get('title', 'Sans titre'),
                        'channel': item.get('author', {}).get('nickname', 'Inconnu'),
                        'duration': f"{item.get('duration', 0)} s",
                        'thumbnail': item.get('cover', ''),
                        'url': video_url,
                        'views': f"{item.get('play_count', 0)} vues",
                        'published': '',
                        'platform': 'tiktok'
                    })
                return videos[:max_results]
            else:
                return []
        else:
            return []
    except Exception as e:
        return []

def afficher_video(video):
    platform = video.get('platform', 'youtube')
    video_id = video['id']
    if platform == 'youtube':
        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"
        html_code = f'<iframe width="100%" height="400" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>'
        st.components.v1.html(html_code, height=415)
    elif platform == 'tiktok':
        embed_url = f"https://www.tiktok.com/embed/v2/{video_id}?autoplay=1"
        html_code = f'<iframe width="100%" height="700" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>'
        st.components.v1.html(html_code, height=715)
    else:
        st.video(video['url'])

def display_video_grid(videos, cols=3, source='search'):
    if not videos:
        st.info("Aucune vidéo à afficher.")
        return

    rows = [videos[i:i+cols] for i in range(0, len(videos), cols)]
    for row_idx, row in enumerate(rows):
        columns = st.columns(cols)
        for col_idx, video in enumerate(row):
            with columns[col_idx]:
                # Construction de l'URL de la vidéo
                params = {
                    "video_id": video['id'],
                    "platform": video.get('platform', 'youtube'),
                    "title": video['title'],
                    "channel": video['channel'],
                    "duration": video.get('duration', ''),
                    "thumbnail": video['thumbnail'],
                    "url": video['url'],
                    "views": video.get('views', ''),
                    "published": video.get('published', '')
                }
                encoded_params = {k: urllib.parse.quote(str(v)) for k, v in params.items()}
                url_params = "&".join([f"{k}={v}" for k, v in encoded_params.items()])
                video_url = f"?{url_params}"

                # Icône de plateforme
                platform_icon = '<i class="fab fa-youtube"></i>' if video.get('platform') == 'youtube' else '<i class="fab fa-tiktok"></i>'

                # Affichage de la carte avec lien
                st.markdown(f"""
                <a href="{video_url}" style="text-decoration: none; color: inherit;">
                    <div class="video-card">
                        <div class="thumbnail-container">
                            <img src="{video['thumbnail']}" class="video-thumbnail" loading="lazy">
                            <div class="duration-badge">{video.get('duration', '')}</div>
                            <div class="platform-badge">{platform_icon}</div>
                        </div>
                        <div class="video-info">
                            <div class="video-title">{video['title'][:70]}{'...' if len(video['title']) > 70 else ''}</div>
                            <div class="video-channel">{video['channel'][:40]}{'...' if len(video['channel']) > 40 else ''}</div>
                            <div class="video-meta">{video.get('views', '')} • {video.get('published', '')}</div>
                        </div>
                    </div>
                </a>
                """, unsafe_allow_html=True)

                # Étoile de favoris
                is_fav = any(f['id'] == video['id'] and f.get('platform') == video.get('platform') for f in st.session_state.favorites)
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if is_fav:
                        if st.button("★", key=f"fav_{video['id']}_{video['platform']}_{row_idx}_{col_idx}", use_container_width=True):
                            st.session_state.favorites = [f for f in st.session_state.favorites if not (f['id'] == video['id'] and f.get('platform') == video.get('platform'))]
                            st.rerun()
                    else:
                        if st.button("☆", key=f"fav_{video['id']}_{video['platform']}_{row_idx}_{col_idx}", use_container_width=True):
                            st.session_state.favorites.append(video)
                            st.rerun()

# --- Barre latérale modernisée ---
with st.sidebar:
    st.markdown('<div style="font-size: 1.5rem; font-weight: 700; color: #FF0000; text-align: center; padding: 1rem; margin-bottom: 1rem;"> Media Fusion</div>', unsafe_allow_html=True)

    # Navigation avec icônes
    if st.button("🏠 Accueil", use_container_width=True):
        st.session_state.page = 'accueil'
        st.session_state.selected_video = None
        st.rerun()
    if st.button("🔍 Rechercher", use_container_width=True):
        st.session_state.page = 'recherche'
        st.session_state.selected_video = None
        st.rerun()
    if st.button("❤️ Favoris", use_container_width=True):
        st.session_state.page = 'favoris'
        st.session_state.selected_video = None
        st.rerun()
    if st.button("🎧 Traducteur vidéo IA", use_container_width=True):
        st.session_state.page = 'traducteur'
        st.session_state.selected_video = None
        st.rerun()

    st.markdown("---")
    st.markdown(f"**⭐ Favoris :** {len(st.session_state.favorites)}")

    if st.session_state.selected_video:
        st.markdown("---")
        st.markdown("**📺 En cours :**")
        st.markdown(f"*{st.session_state.selected_video['title'][:50]}...*")
        if st.button("⏯️ Reprendre", use_container_width=True):
            st.session_state.page = 'lecture'
            st.rerun()

# --- Gestion des pages ---
if st.session_state.page == 'accueil':
    st.markdown('<div class="main-header">Media Fusion</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">YouTube & TikTok .Traduction & Doublage IA</div>', unsafe_allow_html=True)

    time_filter_labels = {'today': 'Aujourd\'hui', 'week': 'Cette semaine'}
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
            {
                'id': 'dQw4w9WgXcQ', 'title': 'Rick Astley - Never Gonna Give You Up',
                'channel': 'Rick Astley', 'thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'views': '1,5 Md de vues',
                'published': 'il y a 12 ans', 'platform': 'youtube', 'duration': '3:33'
            },
            {
                'id': 'kJQP7kiw5Fk', 'title': 'Luis Fonsi - Despacito ft. Daddy Yankee',
                'channel': 'Luis Fonsi', 'thumbnail': 'https://img.youtube.com/vi/kJQP7kiw5Fk/hqdefault.jpg',
                'url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk', 'views': '7,8 Md de vues',
                'published': 'il y a 6 ans', 'platform': 'youtube', 'duration': '4:42'
            },
            {
                'id': 'JGwWNGJdvx8', 'title': 'Ed Sheeran - Shape of You',
                'channel': 'Ed Sheeran', 'thumbnail': 'https://img.youtube.com/vi/JGwWNGJdvx8/hqdefault.jpg',
                'url': 'https://www.youtube.com/watch?v=JGwWNGJdvx8', 'views': '5,8 Md de vues',
                'published': 'il y a 6 ans', 'platform': 'youtube', 'duration': '4:24'
            }
        ]
        display_video_grid(demo_videos[:6], cols=3, source='accueil')

    if st.session_state.favorites:
        st.markdown("---")
        st.markdown("## ✨ Recommandé pour vous")
        fav_channels = list(set([v['channel'] for v in st.session_state.favorites]))
        if fav_channels:
            random_channel = random.choice(fav_channels)
            rec_videos = search_youtube_videos(random_channel, 6)
            if rec_videos:
                display_video_grid(rec_videos, cols=3, source='accueil')

elif st.session_state.page == 'recherche':
    st.markdown("## 🔎 Recherche multi-plateformes")

    plateforme = st.radio(
        "Choisissez la plateforme :",
        options=["YouTube", "TikTok"],
        horizontal=True
    )

    search_query = st.text_input("Rechercher des vidéos :", placeholder="Entrez des mots-clés...", value=st.session_state.last_search)

    if search_query:
        st.session_state.last_search = search_query
        with st.spinner("Recherche en cours..."):
            if plateforme == "YouTube":
                results = search_youtube_videos(search_query, 15)
            else:
                results = search_tiktok_videos(search_query, 15)
            st.session_state.search_results = results

        if results:
            st.markdown(f"### Résultats pour '{search_query}' sur {plateforme}")
            display_video_grid(results, cols=3, source='search')
        else:
            st.warning("Aucun résultat trouvé.")
    else:
        st.info("Entrez un mot-clé pour commencer la recherche.")

elif st.session_state.page == 'favoris':
    st.markdown("## ❤️ Mes favoris")

    if st.session_state.favorites:
        display_video_grid(st.session_state.favorites, cols=3, source='favorites')
    else:
        st.info("Vous n'avez pas encore de vidéos favorites. Ajoutez-en en cliquant sur ☆ Ajouter.")
        st.markdown("### 🎬 Suggestions")
        with st.spinner("Chargement..."):
            suggestions = get_trending_videos(6)
        if suggestions:
            display_video_grid(suggestions, cols=3, source='accueil')

elif st.session_state.page == 'lecture' and st.session_state.selected_video:
    video = st.session_state.selected_video
    platform = video.get('platform', 'youtube')

    if 'last_video_id' not in st.session_state or st.session_state.last_video_id != video['id']:
        st.session_state.last_video_id = video['id']
        st.session_state.translated_title = None
        st.session_state.translated_description = None

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.spinner("Chargement de la vidéo..."):
            afficher_video(video)

        badge = "📺 YouTube" if platform == 'youtube' else "🎵 TikTok"
        titre_affiche = video['title']
        if st.session_state.translated_title:
            titre_affiche = st.session_state.translated_title
            st.markdown(f"## {titre_affiche} <span class='translation-badge'>Traduit</span> <span class='tiktok-badge'>{badge}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"## {titre_affiche} <span class='tiktok-badge'>{badge}</span>", unsafe_allow_html=True)

        st.markdown(f"**{video['channel']}** • {video.get('views', '')} • {video.get('published', '')}")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            is_fav = any(f['id'] == video['id'] and f.get('platform') == platform for f in st.session_state.favorites)
            if is_fav:
                if st.button("★ Retirer des favoris", use_container_width=True):
                    st.session_state.favorites = [f for f in st.session_state.favorites if not (f['id'] == video['id'] and f.get('platform') == platform)]
                    st.rerun()
            else:
                if st.button("☆ Ajouter aux favoris", use_container_width=True):
                    st.session_state.favorites.append(video)
                    st.rerun()
        with col_b:
            if st.button("🔄 Partager", use_container_width=True):
                st.info(f"Lien : {video['url']}")
        with col_c:
            if platform == 'tiktok' and st.session_state.current_list_source == 'search' and st.session_state.search_results:
                current_idx = st.session_state.current_video_index
                if current_idx < len(st.session_state.search_results) - 1:
                    if st.button("⏩ Suivant", use_container_width=True):
                        st.session_state.current_video_index = current_idx + 1
                        st.session_state.selected_video = st.session_state.search_results[current_idx + 1]
                        st.rerun()
                else:
                    st.button(" Suivant (fin)", disabled=True, use_container_width=True)
            else:
                if st.button("🏠 Accueil", use_container_width=True):
                    st.session_state.page = 'accueil'
                    st.session_state.selected_video = None
                    st.rerun()

        if platform == 'tiktok' and st.session_state.current_list_source == 'search':
            search_results = st.session_state.search_results
            current_idx = st.session_state.current_video_index
            if search_results:
                nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
                with nav_col1:
                    if current_idx > 0:
                        if st.button("⬆️ Précédent", key="prev_tiktok", use_container_width=True):
                            st.session_state.current_video_index = current_idx - 1
                            st.session_state.selected_video = search_results[current_idx - 1]
                            st.rerun()
                with nav_col2:
                    st.markdown(f"<div style='text-align: center; padding:10px;'>{current_idx+1} / {len(search_results)}</div>", unsafe_allow_html=True)
                with nav_col3:
                    if current_idx < len(search_results) - 1:
                        if st.button("⬇️ Suivant", key="next_tiktok", use_container_width=True):
                            st.session_state.current_video_index = current_idx + 1
                            st.session_state.selected_video = search_results[current_idx + 1]
                            st.rerun()

        with st.expander("⬇️ Télécharger cette vidéo"):
            if platform == 'youtube':
                st.markdown("**Y2mate** (YouTube)")
                video_url_encoded = urllib.parse.quote(video['url'])
                y2mate_url = f"https://www-y2mate.com/fr22/search/?query={video_url_encoded}"
                sos_url = video['url'].replace('youtube.com', 'sosyoutube.com')
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown(f'<a href="{y2mate_url}" target="_blank"><button class="download-btn">🎬 Ouvrir Y2mate</button></a>', unsafe_allow_html=True)
                with col_d2:
                    st.markdown(f'<a href="{sos_url}" target="_blank"><button class="download-btn-sos">⚡ Astuce SOS</button></a>', unsafe_allow_html=True)
            elif platform == 'tiktok':
                st.markdown("**Téléchargeurs TikTok**")
                video_url_encoded = urllib.parse.quote(video['url'])
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    snaptik_url = f"https://snaptik.app/fr?url={video_url_encoded}"
                    st.markdown(f'<a href="{snaptik_url}" target="_blank"><button class="download-btn">📱 SnapTik</button></a>', unsafe_allow_html=True)
                with col_t2:
                    ssstik_url = f"https://ssstik.io/fr?url={video_url_encoded}"
                    st.markdown(f'<a href="{ssstik_url}" target="_blank"><button class="download-btn-sos">🎵 SSSTik</button></a>', unsafe_allow_html=True)

        st.markdown("---")

    with col2:
        st.markdown("### 🌐 Traduction du titre")
        langue_nom = st.selectbox(
            "Langue cible :",
            options=list(langues_traduction.keys()),
            index=list(langues_traduction.values()).index(st.session_state.translation_lang) if st.session_state.translation_lang in langues_traduction.values() else 0
        )
        nouvelle_langue = langues_traduction[langue_nom]

        if nouvelle_langue != st.session_state.translation_lang:
            st.session_state.translation_lang = nouvelle_langue
            with st.spinner("Traduction en cours..."):
                st.session_state.translated_title = traduire_texte(video['title'], nouvelle_langue)
                desc_text = f"Chaîne : {video['channel']}. Durée : {video.get('duration', 'Non spécifiée')}. Regardez cette vidéo."
                st.session_state.translated_description = traduire_texte(desc_text, nouvelle_langue)
            st.rerun()

        if st.button("🔄 Réinitialiser la traduction"):
            st.session_state.translated_title = None
            st.session_state.translated_description = None
            st.rerun()

        st.markdown("### 📺 Suggestions")
        suggestions = []
        if platform == 'youtube':
            if st.session_state.search_results:
                suggestions = [v for v in st.session_state.search_results if v['id'] != video['id'] and v.get('platform') == 'youtube'][:5]
            if not suggestions:
                channel_videos = search_youtube_videos(video['channel'], 6)
                suggestions = [v for v in channel_videos if v['id'] != video['id']][:5]

        if suggestions:
            for sug in suggestions:
                with st.container():
                    col_thumb, col_info, col_btn = st.columns([1, 3, 1])
                    with col_thumb:
                        st.image(sug['thumbnail'], width=100, use_container_width=True)
                    with col_info:
                        st.markdown(f"**{sug['title'][:50]}{'...' if len(sug['title']) > 50 else ''}**")
                        st.caption(sug['channel'][:30])
                    with col_btn:
                        if st.button("▶️ Watch", key=f"watch_{sug['id']}", use_container_width=True):
                            st.session_state.selected_video = sug
                            st.session_state.page = 'lecture'
                            st.session_state.translated_title = None
                            st.session_state.translated_description = None
                            st.rerun()
        else:
            st.info("Aucune suggestion pour le moment.")

elif st.session_state.page == 'traducteur':
    st.markdown("## 🎙️ Traduction automatique de vidéo")
    st.write("Téléchargez une vidéo et choisissez la langue de doublage.")

    # Vérifier que ffmpeg est disponible
    if not shutil.which("ffmpeg"):
        st.error("❌ ffmpeg n'est pas installé sur le système. La traduction vidéo est impossible.")
        st.stop()

    video_file = st.file_uploader("📂 Upload vidéo", type=["mp4", "mov", "avi", "mkv"])
    selected_language = st.selectbox("🌍 Langue cible du doublage (80 langues disponibles)", options=list(langues_tts.keys()))
    target_language_code = langues_tts[selected_language]

    if video_file:
        st.video(video_file)

        if st.button("🎧 Traduire la vidéo", type="primary"):
            with st.spinner("Traitement en cours... Cette opération peut prendre plusieurs minutes."):
                temp_dir = tempfile.mkdtemp()
                input_video = os.path.join(temp_dir, "video.mp4")
                translated_audio = os.path.join(temp_dir, "audio_translated.mp3")
                output_video = os.path.join(temp_dir, "video_finale.mp4")

                with open(input_video, "wb") as f:
                    f.write(video_file.read())

                # Transcription directe avec Whisper (pas besoin d'extraire l'audio séparément)
                try:
                    model = whisper.load_model("small")
                    result = model.transcribe(input_video)
                    text = result["text"]
                except Exception as e:
                    st.error(f"Erreur lors de la transcription : {e}")
                    st.stop()

                # Traduction
                translated_text = traduire_texte_long(text, target_language_code)

                # Synthèse vocale
                try:
                    if selected_language in hf_languages:
                        model_name = hf_tts_models[selected_language]
                        tts_pipeline = load_hf_tts_model(model_name)
                        audio_array, sampling_rate = generer_parole_par_morceaux(tts_pipeline, translated_text)
                        translated_audio_wav = os.path.join(temp_dir, "audio_translated.wav")
                        sf.write(translated_audio_wav, audio_array, sampling_rate, format='WAV')
                        audio_file_for_ffmpeg = translated_audio_wav
                    else:
                        # Vérifier si la langue est supportée par gTTS
                        supported = get_gtts_supported_langs()
                        if target_language_code not in supported:
                            st.warning(f"⚠️ La langue '{selected_language}' n'est pas supportée par gTTS. Utilisation de l'anglais (en) à la place.")
                            target_language_code = 'en'
                        tts = gTTS(text=translated_text, lang=target_language_code)
                        tts.save(translated_audio)
                        audio_file_for_ffmpeg = translated_audio
                except Exception as e:
                    st.error(f"Erreur lors de la synthèse vocale : {e}")
                    st.stop()

                # Assemblage final avec ffmpeg
                try:
                    subprocess.run([
                        "ffmpeg",
                        "-y",  # écraser sans demander
                        "-i", input_video,
                        "-i", audio_file_for_ffmpeg,
                        "-c:v", "copy",
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-shortest",
                        output_video
                    ], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    st.error(f"Erreur lors de l'assemblage vidéo :\n{e.stderr}")
                    st.stop()

                st.success("✅ Vidéo traduite avec succès !")
                st.video(output_video)

                with open(output_video, "rb") as f:
                    st.download_button(
                        "⬇️ Télécharger la vidéo traduite",
                        f,
                        file_name="video_traduite.mp4",
                        mime="video/mp4"
                    )

# --- Pied de page ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6c757d; padding: 1rem;'>"
    "🎬 MediaFusion • YouTube & TikTok • Traduction IA (80 langues) • Doublage (Ewe, Yoruba, Shona, Akan inclus)"
    "</div>",
    unsafe_allow_html=True
)