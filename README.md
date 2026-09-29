#  Media Fusion (YouTube-TikTok)

Application Streamlit pour **rechercher et regarder des vidéos YouTube et TikTok**, **traduire leurs titres** et **doubler automatiquement des vidéos** dans plus de 80 langues, dont des langues africaines (Éwé, Yoruba, Shona, Akan).

 Démo : 
---

##  Fonctionnalités

-  **Accueil** : vidéos tendances YouTube (filtre « Aujourd'hui » / « Cette semaine »)
-  **Recherche multi-plateformes** : YouTube et TikTok
-  **Lecteur intégré** : lecture via iframe, navigation précédent/suivant pour TikTok
-  **Favoris** : ajout/retrait, recommandations basées sur les chaînes favorites
-  **Traduction du titre** dans plus de 75 langues (Google Translate via `deep-translator`)
-  Traducteur vidéo I :
  1. Transcription de la parole avec Whisper (modèle `small`)
  2. Traduction du texte dans la langue choisie
  3. Synthèse vocale avec gTTS (la plupart des langues) ou **Meta MMS-TTS** via Hugging Face (Éwé, Yoruba, Shona, Akan)
  4. Remplacement de la piste audio avec ffmpeg
  5. Lecture et téléchargement de la vidéo doublée
- ⬇ **Liens de téléchargement** vers des services externes (Y2mate, SnapTik, SSSTik)
- Lien direct vers une vidéo via les paramètres d'URL

---

## Technologies

| Rôle | Bibliothèque |
|---|---|
| Interface | Streamlit |
| Scraping / API | requests, BeautifulSoup |
| Traduction | deep-translator |
| Transcription | openai-whisper |
| Synthèse vocale | gTTS, transformers (MMS-TTS), torch |
| Audio | soundfile, numpy |
| Montage | ffmpeg |

---

##  Installation locale

### 1. Prérequis

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) installé et accessible dans le `PATH`
- libsndfile (nécessaire à `soundfile` sous Linux)

```bash
# Ubuntu / Debian
sudo apt install ffmpeg libsndfile1

# macOS
brew install ffmpeg libsndfile
```

### 2. Cloner et installer

```bash
git clone https://github.com/<ton-compte>/<ton-repo>.git
cd <ton-repo>
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Lancer

```bash
streamlit run app.py
```

L'application est disponible sur http://localhost:8501

---

##  requirements.txt

```txt
streamlit
requests
beautifulsoup4
deep-translator
openai-whisper
gTTS
transformers
torch
numpy
soundfile
```

##  Déploiement sur Streamlit Cloud

Ajoute un fichier `packages.txt` à la racine pour installer les dépendances système :

```txt
ffmpeg
libsndfile1
```

>  Whisper et les modèles MMS-TTS sont gourmands en mémoire. Sur l'offre gratuite de Streamlit Cloud, les vidéos longues peuvent provoquer un dépassement de mémoire. Privilégie des vidéos courtes.

---

##  Utilisation

1. Accueil / Recherche : choisis YouTube ou TikTok, saisis des mots-clés et clique sur une vidéo.
2. Lecture: regarde la vidéo, traduis son titre, ajoute-la aux favoris.
3. Traducteur vidéo IA : importe un fichier (`mp4`, `mov`, `avi`, `mkv`), choisis la langue de doublage, puis clique sur **Traduire la vidéo**. Le traitement peut durer plusieurs minutes.

---

##  Limites connues

- La recherche YouTube repose sur l'analyse du HTML de la page (`ytInitialData`) : elle peut cesser de fonctionner si YouTube modifie sa structure.
- La recherche TikTok utilise l'API non officielle **tikwm.com**, dont la disponibilité n'est pas garantie.
- Le doublage génère une voix unique sur toute la durée : pas de synchronisation avec les paroles d'origine ni de gestion de plusieurs locuteurs.
- Certaines langues de la liste ne sont pas prises en charge par gTTS : l'anglais est alors utilisé par défaut.
- Les liens de téléchargement mènent vers des sites tiers, sans lien avec ce projet.

##  Avertissement légal

Ce projet est fourni à des fins éducatives. Respecte les conditions d'utilisation de YouTube et TikTok ainsi que les droits d'auteur des contenus. Ne télécharge, ne traduis et ne redistribue que des vidéos dont tu as le droit de te servir.

## Licence

MIT (ou la licence de ton choix)