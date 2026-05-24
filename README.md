Markdown
# KhadaMat_AI 🇲🇦🤖

**KhadaMat_AI** est un assistant administratif intelligent et multilingue conçu pour simplifier, centraliser et guider les citoyens marocains dans leurs démarches administratives. Grâce à l'Intelligence Artificielle Générative, au Traitement Automatique du Langage Naturel (NLP) et à des technologies de reconnaissance/synthèse vocale, l'application rend l'information administrative accessible à tous.

---

## 🚀 Fonctionnalités Clés

* **Compréhension Multilingue :** Support natif de l'Arabe standard, du Darija marocain et du Français.
* **Assistant IA Administratif :** Réponses précises basées sur un jeu de données structuré des procédures administratives marocaines.
* **Intégration Audio (TTS & STT) :** Fonctionnalités de synthèse vocale (Text-to-Speech) et de reconnaissance vocale pour interagir à l'oral (idéal pour l'accessibilité).
* **Extraction de Documents (OCR) :** Capacité d'analyse et d'extraction de texte à partir de documents officiels pour pré-remplir ou vérifier des informations.

---

## 🛠️ Technologies Utilisées

* **Backend :** Python, FastAPI / Flask
* **Modèles d'IA & LLMs :** Modèles open-source (via Ollama / Mistral / LLaMA) adaptés aux spécificités locales.
* **Traitement Audio :** Outils et scripts de Speech-to-Text et Text-to-Speech (`reproduce_tts.py`).
* **Base de données / Données :** Dataset markdown structuré (`morocco_admin_dataset.md`).

---

## 📂 Structure du Projet

```text
├── backend/                  # Code source de la logique serveur
├── app.py                    # Point d'entrée principal de l'application
├── morocco_admin_dataset.md  # Base de connaissances des procédures administratives
├── reproduce_tts.py          # Script de test/reproduction pour la synthèse vocale
├── debug_sr.py               # Script de débogage pour la reconnaissance vocale
└── .gitignore                # Fichiers et dossiers à ignorer par Git
⚙️ Installation et Configuration
Préréquis
Python 3.10+

Ollama (avec le modèle local configuré)

1. Cloner le dépôt
Bash
git clone [https://github.com/kholoud-sandi/KhadaMat_AI.git](https://github.com/kholoud-sandi/KhadaMat_AI.git)
cd KhadaMat_AI
2. Configurer l'environnement virtuel
Bash
python -m venv venv
# Sur Windows
venv\Scripts\activate
# Sur macOS/Linux
source venv/bin/activate
3. Installer les dépendances
(Assurez-vous de générer un fichier requirements.txt ou installez les modules principaux)

Bash
pip install -r requirements.txt
4. Lancer l'application
Bash
python app.py
