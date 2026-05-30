import streamlit as st
import streamlit.components.v1 as components

# 1. Page Configuration for Full Width
st.set_page_config(
    page_title="Vanta Background",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def vanta_full_screen():
    vanta_html = """
    <style>
        /* Ensure the iframe itself doesn't have scrollbars or margins */
        body, html {
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #0e1117;
        }
        #vanta-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
        }
    </style>

    <div id="vanta-bg"></div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.dots.min.js"></script>

    <script>
        VANTA.DOTS({
          el: "#vanta-bg",
          mouseControls: true,
          touchControls: true,
          gyroControls: false,
          minHeight: 200.00,
          minWidth: 200.00,
          scale: 1.00,
          scaleMobile: 1.00,
          color: 0x2e6ff2,       /* Primary Dot Color */
          color2: 0x5d89f0,      /* Secondary Highlight */
          backgroundColor: 0x0e1117,
          size: 4.50,            /* Larger dots for better visual */
          spacing: 35.00,
          showLines: false
        })
    </script>
    """
    # We use a height of 1000 to ensure the component has space to render,
    # but the CSS inside 'vanta_html' fixes it to the viewport regardless.
    return components.html(vanta_html, height=2000)


# 2. Kill all Streamlit UI Padding/Header/Footer
st.markdown("""
    <style>
    /* Hide Streamlit's Header, Footer, and Toolbar */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Remove padding from the main container */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Make the app background transparent */
    .stApp {
        background: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Render the background
vanta_full_screen()