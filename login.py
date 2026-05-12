import streamlit as st
import pandas as pd
import utils
import hmac


st.set_page_config(layout="wide")
# Initialization of session state variables and other variables
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False #user is logout so login is false
        
if 'username' not in st.session_state:
    st.session_state['username'] = ''#checks for password
    
if 'login_attempts' not in st.session_state:
    st.session_state['login_attempts'] = 0 #counter for number of attempts to login by user
    
MAX_ATTEMPTS = 3
    
#Define the login function
def login():
    st.title('Bienvenido al dashboard de IronTools')
    st.markdown(':orange-badge[Por favor ingrese credenciales para continuar]')
    
    #checks number of attemps and then stops page
    if st.session_state['login_attempts'] >= MAX_ATTEMPTS:
        st.error('Demasiados intentos. Por favor intente más tarde')
        st.stop()
    
    with st.form('login_form'):
        username = st.text_input('Usuario', autocomplete = 'off')
        password = st.text_input('clave', type='password', autocomplete = 'off')
        submit_button = st.form_submit_button('Entrar')
        
        if submit_button:#if submit_button has been clicked then excute this conditional
            try:
                #cheks if key exits in dictionary and then checks if password is equal to value of key and  
                # 1. .encode('utf-8'): Converts to bytes so hmac can handle non-ASCII (emojis/accents).
                # 2. compare_digest: Ensures the check takes the same time regardless of input, preventing hackers from "guessing" the password based on response speed.
                if username in st.secrets['credentials'] and hmac.compare_digest(st.secrets['credentials'][username].encode('utf-8'), password.encode('utf-8')):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['login_attempts'] = 0
                    st.success('Ingreso correcto!!')
                    st.rerun()
                            
                else:
                    st.session_state['login_attempts'] += 1
                    st.error(f'credenciales incorrectas o no ingresadas. Intentos remanentes: {MAX_ATTEMPTS - st.session_state.login_attempts}')
                    
            except KeyError:
                st.error('Revisar las configuraciones de claves o credenciales en la nube')
                     
# 3. Define the Logout Function to the same state when session_state is initialized
def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    #st.rerun()
    
if not st.session_state['logged_in']:
    login()
   
else:
    st.sidebar.title('Dashboard IronTools')
    role = next(iter(st.secrets['credentials'].keys()))#gets first item to apply logic as a main user
    
    if st.session_state['username'] == role:#shows information of main user once she is logged_in
        st.title(f'Bienvenida, {st.secrets['main_user']['first_name']} {st.secrets['main_user']['last_name']}!!!')
        st.sidebar.write(f'Correo: {st.secrets['main_user']['email']}')
        st.sidebar.write(f'role: {st.secrets['main_user']['role']}')
        st.success('Tienes acceso completo a los datos')
                 
        st.subheader("Total de facturas ($)")
        utils.prepare_data(role=role)
        utils.show_data(role = role)

    else:#shows information of another type of user once logged_in
        st.title(f'Hola, {st.secrets['user']['first_name']} {st.secrets['user']['last_name']}!!!')
        st.sidebar.write(f'Correo: {st.secrets['user']['email']}')
        st.sidebar.write(f'role: {st.secrets['user']['role']}')
        st.info(f'tienes acceso limitado')
        
        st.subheader("Porcentaje de facturas(%)")
        utils.prepare_data(role='')
        utils.show_data(role = '')
        
    st.sidebar.button('Salir', on_click = logout)