import streamlit as st

def render():
    # Keep your CSS exactly as before
    st.markdown(
        """
        <style>
        .about-container { max-width: 900px; width: 100%; padding: 20px 18px; margin:auto; }
        .section {
            background: #ffffff;
            border: 1px solid #e6eef5;
            padding: 18px 22px;
            border-radius: 12px;
            margin-bottom: 18px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
        }
        .title { font-size: 1.25rem; font-weight: 700; color: #0b4f8a; margin-bottom: 8px; }
        .lead { font-size: 1rem; color:#1f2937; line-height: 1.55; }
        .metrics { display:flex; gap:14px; justify-content:center; margin-bottom:16px; margin-top:10px; }
        .metric-card {
            background:#f8fafc; border:1px solid #e6eef5; padding:12px 16px;
            border-radius:10px; min-width:170px; text-align:center;
        }
        .metric-label { font-size:0.86rem; color:#6b7280; }
        .metric-value { font-size:1rem; font-weight:700; color:#0b4f8a; }
        .tag {
            background:#eef6ff; color:#083e73; padding:6px 10px; border-radius:8px;
            margin:6px 6px 6px 0; font-size:0.86rem; display:inline-block;
        }
        .cta {
            background: linear-gradient(90deg,#0b6bd6,#06b6d4);
            color:white; padding:12px 20px; border-radius:10px;
            text-decoration:none; font-weight:600;
            display:inline-block;
        }
        .footer { color:#6b7280; text-align:center; margin-top:12px; font-size:0.92rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="about-container">', unsafe_allow_html=True)

    st.header("ℹ️ About the Project")

    # -------- PROJECT OVERVIEW --------
    st.markdown(
        """
        <div class="section">
            <div class="title">Project Overview</div>
            <div class="lead">
                This website was created by three students from 
                <strong>Sapienza University of Rome</strong> for the Smart Cities course.
                <br><br>
                The idea behind the project is simple: we wanted to build an 
                <strong>interactive map</strong> where people can share everyday 
                problems they notice in the city — things like noise, heat, smell,
                or unsafe walking and cycling routes.
                <br><br>
                Our goal is to show how citizen feedback can help us understand what
                people experience in their neighbourhoods and where improvements might be needed.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------- PROJECT AT A GLANCE --------
    st.markdown(
        "<div style='text-align:center; margin-top:6px; margin-bottom:6px;'><strong>📊 Project at a glance</strong></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Course</div>
                <div class="metric-value">Smart Cities</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Issue Types</div>
                <div class="metric-value">6 Categories</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Main Feature</div>
                <div class="metric-value">Interactive Map</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr />", unsafe_allow_html=True)

    # -------- PURPOSE --------
    st.markdown(
        """
        <div class="section">
            <div class="title">Purpose</div>
            <div class="lead">
                Cities are full of small problems that people notice every day. 
                Many of these issues never get reported, even though they affect comfort,
                safety, and quality of life.
                <br><br>
                This tool makes it easy for anyone to:
            </div>
            <ul class="lead">
                <li>Share issues they experience in the city</li>
                <li>Mark the exact location where the problem happens</li>
                <li>See what other people have reported</li>
                <li>Understand which areas might need attention</li>
            </ul>
            <div class="lead">
                By collecting simple reports from many users, we can get a clearer picture 
                of what is happening across the city and highlight places that may benefit 
                from improvements.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------- ISSUE CATEGORIES --------
    st.markdown(
        """
        <div class="section">
            <div class="title">Issue Categories</div>
            <div class="lead">Users can report issues under the following categories:</div>
            <br>
            <span class="tag">🌫 Air Quality</span>
            <span class="tag">🔊 Noise</span>
            <span class="tag">🔥 Heat</span>
            <span class="tag">🚶 Cycling / Walking</span>
            <span class="tag">👃 Odor</span>
            <span class="tag">📍 Other</span>
            <br><br>
            <div class="lead">
                These categories help us organise reports and see patterns, such as streets that feel too hot,
                places with strong smells, or areas where walking or cycling feels unsafe.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------- TECHNOLOGIES --------
    st.markdown(
        """
        <div class="section">
            <div class="title">Technologies Used</div>
            <div class="lead">
                The project was built using simple, easy-to-learn tools:
            </div>
            <ul class="lead">
                <li><strong>Streamlit</strong> for the website interface</li>
                <li><strong>Folium / Leaflet</strong> for the interactive map</li>
                <li><strong>SQLite</strong> to store reports</li>
                <li><strong>Pandas & NumPy</strong> for small data calculations</li>
            </ul>
            <div class="lead">
                Everything was designed to be lightweight and easy to extend in the future.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------- EXPANDER --------
    with st.expander("Data & Map Details"):
        st.write(
            """
            • Each report includes a category, location, time, and short description  
            • The map shows points, clusters, and heatmaps  
            • Reports can be grouped to see which issues appear most often  
            • This helps identify the areas where people report discomfort or problems  
            """
        )

    st.markdown("<hr />", unsafe_allow_html=True)

    # -------- CTA --------
    st.markdown(
        """
        <div style="text-align:center; margin-top:14px;">
            <a href="#report" class="cta">🗺 Go to the Map & Report an Issue</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="footer">© Sapienza University of Rome — Smart Cities Course</p>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)