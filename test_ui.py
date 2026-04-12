import streamlit as st
from streamlit.testing.v1 import AppTest

def test_app():
    # just import the app and check if there's any errors
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception
    print("Test passed.")

test_app()
