import streamlit as st
import requests
from authlib.integrations.requests_client import OAuth2Session


# === LOGIN GOOGLE ===
def login(client_id, client_secret, redirect_uri, button=True):

    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"

    oauth = OAuth2Session(
         client_id
        ,client_secret
        ,scope = "openid email profile"
        ,redirect_uri = redirect_uri
    )

    uri, _ = oauth.create_authorization_url(authorize_url)
    
    if button:

        st.markdown("""
        <div style="display: flex; justify-content: center;">
        <img src="https://www.abcdacomunicacao.com.br/wp-content/uploads/Daki_logo.png" width="150">
        </div>
        <div style='text-align: center; padding-top: 100px;'>
        <h1>🔐 Login Necessário<br><br>
        <p style='font-size: 18px;'>Para continuar, por favor faça login com sua conta Google.</p>
        <p style='font-size: 18px;'>⚠️ Atenção: use apenas uma conta com domínio <b>@soudaki.com.</b></p>
        </div>
        """, unsafe_allow_html=True)
            

        st.markdown("""
            <style>
                .stLinkButtonCustom {{
                    display: flex;
                    justify-content: center;
                    margin-top: 1rem;
                }}

                .stLinkButtonCustom a {{
                    text-decoration: none;
                    background-color: #f0f0f5;
                    color: #333;
                    padding: 0.5rem 1.5rem;
                    border-radius: 8px;
                    font-weight: 600;
                    border: 1px solid #ccc;
                }}

                .stLinkButtonCustom a:hover {{
                    background-color: #e0e0e0;
                }}
            </style>
            <div class="stLinkButtonCustom">
                <a href="{0}" target="_self">Login com Google</a>
            </div>
        """.format(uri), unsafe_allow_html=True)

    return oauth

# == | == | == | == | == |




# === VERIFICAR TOKEN ===
def get_token(client_id, client_secret, redirect_uri, code):

    oauth = login(client_id, client_secret, redirect_uri, button=False)

    token_url = "https://oauth2.googleapis.com/token"
    token = oauth.fetch_token(token_url, code=code)
    
    return token

# == | == | == | == | == |




# === API REST COM TOKEN GERADA ===
def get_userinfo(token):

    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    headers = {"Authorization": f"Bearer {token['access_token']}"}
    userinfo = requests.get(userinfo_url, headers=headers).json()

    email = userinfo.get("email", "")
    user_valid = email.endswith("@soudaki.com")
    name = userinfo.get("name", "")
    photo = userinfo.get("picture", "")

    return user_valid, name, photo

# == | == | == | == | == |




# === DADOS USER ===
def display_user(name, photo):
    l1, l2 = st.columns([98,2])
    l1.markdown(f'<div style="text-align: right;">{name}</div><br><br>', unsafe_allow_html=True)
    l2.image(photo, width=40)

# == | == | == | == | == |