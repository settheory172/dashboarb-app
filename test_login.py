from streamlit.testing.v1 import AppTest

def test_no_interaction():
    at = AppTest.from_file("login.py")
    # 1. Explicitly set the state before running the app
    at.session_state["logged_in"] = False
    at.session_state["username"] = ""
    at.session_state["login_attempts"] = 0
    # 2. Run the app with that pre-existing state
    at.run()
    # 3. Assert your app's behavior under this state
    assert at.session_state["logged_in"] == False
    assert at.session_state["username"] == ""
    assert at.session_state["login_attempts"] == 0

def test_logout():
    at = AppTest.from_file("login.py")
    at.run()
    at.session_state["logged_in"] = False
    at.session_state["username"] = ""

def test_login():
    at = AppTest.from_file("login.py")
    # 1. Mock st.secrets so the dictionary lookup doesn't crash
    at.secrets["credentials"] = {"my_user": "my_secure_password"}
    
    # 2. Initialize necessary session state defaults if needed
    at.session_state["login_attempts"] = 0
    
    # 3. Run the app to render the inputs and buttons
    at.run()
    # 4. Fill in the text inputs (adjust labels or indices to match your app)
    # Assuming text inputs exist for username and password
    at.text_input[0].set_value("my_user")
    at.text_input[1].set_value("my_secure_password")
    # 5. Find and click the submit button
    # If it's a form, you might submit the form, or click the button:
    at.button[0].click().run()
    # 6. Assert success state and messages
    assert at.session_state["logged_in"] is True
    assert at.session_state["username"] == "my_user"
    assert at.session_state['login_attempts'] == 0
    #assert len(at.success) > 0
    
  
   
   
