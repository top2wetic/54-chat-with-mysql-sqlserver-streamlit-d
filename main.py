import streamlit as st
import urllib.parse
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import sqlalchemy.exc

from sqlalchemy import create_engine

# Fonction pour initialiser la base de données en fonction du type
def init_database(db_type: str, user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    try:
        if db_type == "MySQL":
            db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
        elif db_type == "PostgreSQL":
            db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        elif db_type == "SQL Server":
            driver = 'ODBC Driver 17 for SQL Server'
            if user and password:
                driver = '{ODBC Driver 17 for SQL Server}'
                params = urllib.parse.quote_plus(f"DRIVER={driver};SERVER={host};DATABASE={database};UID={user};PWD={password}")
                db_uri = f"mssql+pyodbc:///?odbc_connect={params}"
            else:
                db_uri = f"mssql+pyodbc://{host}/{database}?trusted_connection=yes&driver={driver}"
            return SQLDatabase.from_uri(db_uri)
        else:
            raise ValueError("Unsupported database type")
        
        return SQLDatabase.from_uri(db_uri)
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        return None

def get_llm_chain(db, llm_type, api_key, model=None):
    default_model = "gpt-4-0125-preview"
  
    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.

    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}

    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.

    For example:
    Question: which 3 artists have the most tracks?
    SQL Query: SELECT `ArtistId`, COUNT(*) as track_count FROM `Track` GROUP BY `ArtistId` ORDER BY track_count DESC LIMIT 3;
    Question: Name 10 artists
    SQL Query: SELECT `Name` FROM `Artist` LIMIT 10;

    Your turn:

    Question: {question}
    SQL Query:
    """

    prompt = ChatPromptTemplate.from_template(template)
    
    try:
        if llm_type == "OpenAI":
            llm = ChatOpenAI(api_key=api_key, model=model or default_model) 
        elif llm_type == "Groq":
            llm = ChatGroq(api_key=api_key)
        else:
            raise ValueError("Unsupported LLM type")

        def get_schema(_):
            return db.get_table_info()

        return (
            RunnablePassthrough.assign(schema=get_schema)
            | prompt
            | llm
            | StrOutputParser()
        )
    except Exception as e:
        st.error(f"Failed to initialize LLM chain: {str(e)}")
        return None

def get_response(user_query: str, db: SQLDatabase, chat_history: list, llm_type: str, api_key: str, model: str = None):
    sql_chain = get_llm_chain(db, llm_type, api_key, model)
    if sql_chain is None:
        return "Failed to initialize LLM chain. Check your LLM settings."

    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, question, sql query, and sql response, write a natural language response.
    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL Response: {response}
    """

    prompt = ChatPromptTemplate.from_template(template)
    
    try:
        if llm_type == "OpenAI":
            llm = ChatOpenAI(api_key=api_key)
        elif llm_type == "Groq":
            llm = ChatGroq(api_key=api_key)
        else:
            raise ValueError("Unsupported LLM type")

        chain = (
            RunnablePassthrough.assign(query=sql_chain).assign(
                schema=lambda _: db.get_table_info(),
                response=lambda vars: db.run(vars["query"]),
            )
            | prompt
            | llm
            | StrOutputParser()
        )

        return chain.invoke({
            "question": user_query,
            "chat_history": chat_history,
        })
    except sqlalchemy.exc.ProgrammingError as pe:
        return f"SQL error: {str(pe)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def show_login_page():
    st.set_page_config(page_title="Login | DIGITAR", page_icon=":lock:", layout="centered")
    st.markdown("""
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background-color: #f0f2f6;
        }
        .login-box {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.2);
            max-width: 400px;
            width: 100%;
            text-align: center;
        }
        .login-header {
            margin-bottom: 20px;
        }
        .login-header h2 {
            color: #333;
        }
        .login-header p {
            color: #777;
            font-size: 14px;
        }
        .login-input {
            margin-bottom: 15px;
        }
        .login-button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 5px;
            cursor: pointer;
        }
        .login-button:hover {
            background-color: #0056b3;
        }
        .footer {
            margin-top: 20px;
            font-size: 12px;
            color: #999;
        }
        </style>
        <div class="login-container">
            <div class="login-box">
                <div class="login-header">
                    <h2>Login</h2>
                    <p>Welcome to Chat with Your Database<br>Developed by DIGITAR</p>
                </div>
                <div class="login-input">
                    <input type="text" placeholder="Enter your username" id="username" class="stTextInput">
                </div>
                <div class="login-input">
                    <input type="password" placeholder="Enter your password" id="password" class="stTextInput">
                </div>
                <button class="login-button" id="login-button">Log In</button>
                <div class="footer">
                    <p>Powered by <b>DIGITAR</b></p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Collect the inputs from the login form
    username = st.text_input("User", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    if st.button("Log In"):
        # Simple credential check (for demonstration purposes only)
        if username == "admin" and password == "aze123":
            st.session_state["logged_in"] = True
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

def show_main_page():
    load_dotenv()

    st.set_page_config(page_title="Chat with Your Database", page_icon=":speech_balloon:", layout="centered")

    st.markdown("""
        <style>
        .main {
            color: #ffffff;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background-color: #007bff;
            color: white;
        }
        .header .logout-button {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
        }
        .header .logout-button:hover {
            color: #0056b3;
        }
        </style>
        <div class="header">
            <h1>Chat with Your Database</h1>
            <button class="logout-button" title="Logout" onclick="window.location.href='/logout'">&#x1F512;</button>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Chat with the Database")
    st.write("Ask your database anything and get the response in natural language.")

    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.markdown(message.content)

    user_query = st.chat_input("Type a message...")
    if user_query is not None and user_query.strip() != "":
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        
        with st.chat_message("Human"):
            st.markdown(user_query)
            
        with st.chat_message("AI"):
            if "db" in st.session_state:
                if "api_key" in st.session_state and "llm_type" in st.session_state:
                    response = get_response(
                        user_query, 
                        st.session_state.db, 
                        st.session_state.chat_history, 
                        st.session_state.llm_type, 
                        st.session_state.api_key, 
                        st.session_state.model if st.session_state.model.strip() != "" else None
                    )
                else:
                    response = "Please configure the LLM settings first."
            else:
                response = "Please connect to a database first."
            st.markdown(response)
            
        st.session_state.chat_history.append(AIMessage(content=response))

    # Logout action for the button
    if st.experimental_get_query_params().get("logout", [None])[0]:
        st.session_state.logged_in = False
        st.experimental_rerun()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello! I'm a SQL assistant. Ask me anything about your database."),
    ]

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    show_main_page()
else:
    show_login_page()
