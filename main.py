import warnings
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from crewai import Agent, Task, Crew
import streamlit as st
from langchain_openai import ChatOpenAI

warnings.filterwarnings('ignore')
load_dotenv()

# Fonction de connexion
def login(username, password):
    # Remplacez ceci par la vérification réelle des identifiants
    if username == "admin" and password == "aze123":
        return True
    return False

# Fonction pour afficher la page de connexion
def show_login_page():
    st.set_page_config(page_title="Connexion - Blog Post Writer", page_icon=":lock:", layout="centered")
    
    st.markdown("""
        <style>
        .login-container {
            background-color: #f4f4f9;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            margin: 0 auto;
        }
        .login-title {
            color: #4CAF50;
            text-align: center;
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        .login-input {
            margin-bottom: 1rem;
        }
        .login-button {
            background-color: #4CAF50;
            color: white;
            border-radius: 4px;
            padding: 0.5rem;
            font-size: 1rem;
        }
        .login-button:hover {
            background-color: #45a049;
        }
        .footer-text {
            margin-top: 1rem;
            font-size: 0.875rem;
            color: #888;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Connexion</h2>', unsafe_allow_html=True)

    username = st.text_input("Username", className="login-input")
    password = st.text_input("Password", type="password", className="login-input")
    login_button = st.button("Se connecter", key="login_button", help="Cliquez pour vous connecter", className="login-button")

    if login_button:
        if login(username, password):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Identifiants incorrects. Veuillez réessayer.")

    st.markdown('<div class="footer-text">Développé par DIGITAR</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Fonction pour afficher la page principale
def show_main_page():
    # Configuration de la page
    st.set_page_config(page_title="DIGITAR Blog Post Writer", page_icon="📝", layout="centered")
    st.title("DIGITAR BLOG POST WRITER")
    st.markdown("""
    <style>
        .stApp {
            background-color: #2E3B4E;
            color: white;
        }
        .main {
            background-color: #2E3B4E;
            color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .title {
            font-size: 2.5rem;
            color: #FFD700;
            text-align: center;
        }
        .description {
            font-size: 1.2rem;
            color: #FFD700;
            text-align: center;
            margin-bottom: 2rem;
        }
        .input-text {
            background-color: #1F2937;
            color: white;
        }
        .stButton button {
            background-color: green;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            font-size: 1rem;
            border-radius: 5px;
            cursor: pointer;
        }
        .stButton button:hover {
            background-color: #FFC700;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title">DIGITAR BLOG POST WRITER</div>', unsafe_allow_html=True)
    st.markdown('<div class="description">Cette application vous guide à travers le processus de planification, rédaction et édition d\'un article de blog sur un sujet spécifié.</div>', unsafe_allow_html=True)

    # Section de la barre latérale pour la clé de l'API et le modèle de langage
    st.sidebar.title("Configuration")
    api_key = st.sidebar.text_input("Entrez votre clé API:", type="password")
    model_option = st.sidebar.selectbox("Choisissez le modèle de langage:", ("Groq", "OpenAI"))

    # Initialiser st.session_state pour la configuration
    if 'configuration_validated' not in st.session_state:
        st.session_state.configuration_validated = False
    if 'llm' not in st.session_state:
        st.session_state.llm = None

    # Ajouter un bouton pour valider la configuration de l'API et du modèle
    if st.sidebar.button("Valider la configuration"):
        if api_key and model_option:
            if model_option == "Groq":
                st.session_state.llm = ChatGroq(api_key=api_key)
            elif model_option == "OpenAI":
                st.session_state.llm = ChatOpenAI(api_key=api_key)
            st.session_state.configuration_validated = True
            st.sidebar.success("Configuration validée avec succès!")
        else:
            st.sidebar.error("Veuillez entrer votre clé API et choisir un modèle de langage.")

    # Vérifiez que l'utilisateur a validé la configuration avant de permettre le démarrage du workflow
    if st.session_state.configuration_validated and st.session_state.llm:
        llm = st.session_state.llm

        # Entrée pour le sujet
        topic = st.text_input("Entrez le sujet pour l'article de blog:", "Intelligence Artificielle", key="input-text")

        # Définir les agents
        planner = Agent(
            role="Planificateur de Contenu",
            goal="Planifier un contenu engageant et factuellement précis sur le sujet {topic}",
            backstory="Vous travaillez sur la planification d'un article de blog sur le sujet : {topic}. Vous collectez des informations pour aider le public à apprendre quelque chose et à prendre des décisions éclairées. Votre travail sert de base pour que le Rédacteur de Contenu puisse écrire un article sur ce sujet.",
            allow_delegation=False,
            verbose=True,
            llm=llm
        )

        writer = Agent(
            role="Rédacteur de Contenu",
            goal="Écrire un article d'opinion perspicace et factuellement précis sur le sujet : {topic}",
            backstory="Vous travaillez sur la rédaction d'un nouvel article d'opinion sur le sujet : {topic}. Vous basez votre rédaction sur le travail du Planificateur de Contenu, qui fournit un plan et un contexte pertinent sur le sujet. Vous suivez les principaux objectifs et la direction du plan, tels que fournis par le Planificateur de Contenu. Vous fournissez également des idées objectives et impartiales et les soutenez avec les informations fournies par le Planificateur de Contenu. Vous reconnaissez dans votre article d'opinion lorsque vos déclarations sont des opinions par opposition à des déclarations objectives.",
            allow_delegation=False,
            verbose=True,
            llm=llm
        )

        editor = Agent(
            role="Éditeur",
            goal="Éditer un article de blog donné pour l'aligner avec le style rédactionnel de l'organisation.",
            backstory="Vous êtes un éditeur qui reçoit un article de blog du Rédacteur de Contenu. Votre objectif est de revoir l'article de blog pour vous assurer qu'il suit les meilleures pratiques journalistiques, qu'il offre des points de vue équilibrés lorsqu'il présente des opinions ou des assertions, et qu'il évite également les sujets ou opinions controversés majeurs lorsque cela est possible.",
            allow_delegation=False,
            verbose=True,
            llm=llm
        )

        # Définir les tâches
        plan = Task(
            description=(
                "1. Prioriser les dernières tendances, les acteurs clés et les actualités notables sur le sujet {topic}.\n"
                "2. Identifier le public cible, en tenant compte de ses intérêts et de ses points de douleur.\n"
                "3. Développer un plan de contenu détaillé comprenant une introduction, des points clés et un appel à l'action.\n"
                "4. Inclure des mots-clés SEO et des données ou sources pertinentes."
            ),
            expected_output="Un document de plan de contenu complet avec un plan, une analyse du public, des mots-clés SEO et des ressources.",
            agent=planner
        )

        write = Task(
            description=(
                "1. Utiliser le plan de contenu pour rédiger un article de blog convaincant sur le sujet {topic}.\n"
                "2. Incorporer naturellement les mots-clés SEO.\n"
                "3. Les sections/Sous-titres sont correctement nommés de manière engageante.\n"
                "4. Écrire un article de blog complet avec une introduction, un corps et une conclusion."
            ),
            expected_output="Un article de blog complet avec introduction, corps et conclusion.",
            agent=writer
        )

        edit = Task(
            description=(
                "1. Revoir et affiner l'article de blog fourni par le Rédacteur de Contenu.\n"
                "2. Assurer l'exactitude des informations, l'engagement du contenu et l'adéquation avec le style de l'organisation.\n"
                "3. Rechercher des informations supplémentaires si nécessaire pour améliorer le contenu.\n"
                "4. Éviter les controverses majeures et garantir un ton équilibré."
            ),
            expected_output="Une version révisée de l'article de blog prête pour publication.",
            agent=editor
        )

        # Affichage des tâches
        st.header("Planifier, Écrire et Éditer un Article de Blog")
        st.subheader(f"Sujet : {topic}")

        st.write("### Étape 1: Planification")
        st.write(plan.description.format(topic=topic))

        st.write("### Étape 2: Rédaction")
        st.write(write.description.format(topic=topic))

        st.write("### Étape 3: Édition")
        st.write(edit.description.format(topic=topic))

# Vérifiez si l'utilisateur est connecté, sinon afficher la page de connexion
if 'logged_in' not in st.session_state:
    show_login_page()
else:
    show_main_page()
