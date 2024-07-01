
import streamlit as st
import pyodbc

# Interface utilisateur pour les informations de connexion
st.title('Configuration de la connexion SQL Server')
server = st.text_input('Nom du serveur SQL Server (ex: localhost\\SQLEXPRESS)', value='localhost\\SQLEXPRESS')
database = st.text_input('Nom de la base de données')
username = st.text_input('Nom d\'utilisateur SQL Server (optionnel)')
password = st.text_input('Mot de passe SQL Server (optionnel)', type='password')

# Fonction pour se connecter à la base de données
def get_db_connection(server, database, username=None, password=None):
    if not server or not database:
        st.warning('Veuillez entrer le nom du serveur et le nom de la base de données.')
        return None

    driver = '{ODBC Driver 17 for SQL Server}'
    if username and password:
        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    else:
        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'

    try:
        st.info(f"Tentative de connexion à {server}/{database}...")
        conn = pyodbc.connect(connection_string)
        st.success(f"Connexion réussie à {server}/{database}")
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[1]
        st.error(f"Échec de la connexion : {sqlstate}")
        return None

# Fonction pour exécuter une requête SQL
def execute_query(query, conn):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except pyodbc.Error as ex:
        sqlstate = ex.args[1]
        st.error(f"Erreur SQL : {sqlstate}")
        return []

# Interface utilisateur Streamlit
st.title('Application Streamlit avec SQL Server')

# Test de connexion
if st.button('Tester la connexion'):
    conn = get_db_connection(server, database, username, password)
    if conn:
        conn.close()

# Afficher les données de la table produits
if st.button('Afficher les produits'):
    conn = get_db_connection(server, database, username, password)
    if conn:
        query = "SELECT * FROM produits"
        results = execute_query(query, conn)
        if results:
            for row in results:
                st.write(row)
        else:
            st.warning('Aucun résultat trouvé.')
        conn.close()

# Ajouter un nouveau produit
st.subheader('Ajouter un nouveau produit')
new_name = st.text_input('Nom du produit')
new_category = st.number_input('ID de la catégorie', min_value=1)
new_supplier = st.number_input('ID du fournisseur', min_value=1)
new_price = st.number_input('Prix', min_value=0.0)

if st.button('Ajouter le produit'):
    conn = get_db_connection(server, database, username, password)
    if conn:
        cursor = conn.cursor()
        insert_query = f"INSERT INTO produits (nom, categorie_id, fournisseur_id, prix) VALUES ('{new_name}', {new_category}, {new_supplier}, {new_price})"
        try:
            cursor.execute(insert_query)
            conn.commit()
            st.success('Produit ajouté avec succès')
        except pyodbc.Error as ex:
            sqlstate = ex.args[1]
            st.error(f"Erreur lors de l'ajout du produit : {sqlstate}")
        finally:
            conn.close()

# Lancer l'application Streamlit
if __name__ == '__main__':
    st.write('Bienvenue sur l\'application Streamlit avec SQL Server')






