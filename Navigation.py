# navigation.py
import streamlit as st
from streamlit_option_menu import option_menu

def navbar():
    selected = option_menu(
        menu_title=None,
        options=["Area tecnica", "Listino", "Quotazioni"],
        icons=["tools", "bar-chart", "speedometer"],
        menu_icon="gear",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f0f2f6"},
            "icon": {"color": "white", "font-size": "15px" },
            "nav-link": {"font-size": "15px", "text-align": "center", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#d70019"},
        }
    )
    return selected
