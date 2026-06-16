import streamlit as st

st.set_page_config(
    page_title="Hi-Tech Intelligent Mold Analysis System (HIMAS)",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)
import tempfile
import time

from dfm_engine import (
    analyze_step_file,
    generate_pdf,
    generate_plotly_visualization,
    convert_step_to_stl
)

col1, col2 = st.columns([1, 8])

with col1:
    st.markdown(
        "<h1 style='font-size:70px;'>🧩</h1>",
        unsafe_allow_html=True
    )

with col2:

    st.title("Hi-Tech Intelligent Mold Analysis System (HIMAS)")

    st.caption(
        "AI-Powered Moldability Analysis for Injection Molded Parts"
    )

    st.caption(
        "Developed by- **Kushal R**"
    )

st.divider()

st.subheader("📂 Upload CAD Model")

uploaded_file = st.file_uploader(
    "Choose a STEP file",
    type=["step", "stp"]
)

if uploaded_file:

    st.success("STEP File Uploaded Successfully")

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".step"
    ) as tmp:

        tmp.write(uploaded_file.read())
        temp_path = tmp.name

    st.info("Running DFM Analysis...")

    progress = st.progress(0)

    progress.progress(10)

    analysis_start = time.time()

    result = analyze_step_file(temp_path)

    progress.progress(50)

    analysis_end = time.time()

    st.write(
        "Analysis Time:",
        round(analysis_end - analysis_start, 2),
        "seconds"
    )
    
    stl_path = temp_path.replace(
    ".step",
    ".stl"
    )

    convert_step_to_stl(
        temp_path,
        stl_path
    )

    progress.progress(80)
    
    fig = generate_plotly_visualization(
    stl_path
    )

    progress.progress(100)
    
    st.markdown(
        """
        <h2 style='color:#1E90FF'>
        🧩 Interactive 3D Viewer
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.write("Parting Points:", len(result["parting_points"]))
    st.write("Undercut Points:", len(result["undercut_points"]))
    st.write("Good Points:", len(result["good_points"]))
    st.write("Warning Points:", len(result["warning_points"]))
    st.write("Critical Points:", len(result["critical_points"]))


    
    

    st.markdown(
        """
        <h2 style='color:#FF6B35'>
        📊 Analysis Results
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "Optimal Mold Direction:",
        result["mold_direction"]
    )

    st.write(
        "Undercut Faces:",
        result["undercut_faces"]
    )

    st.write(
        "Undercut Regions:",
        result["undercut_regions"]
    )

    st.write(
        "Core Faces:",
        result["core_faces"]
    )

    st.write(
        "Cavity Faces:",
        result["cavity_faces"]
    )

    st.write(
        "Parting Faces:",
        result["parting_faces"]
    )
    
    st.markdown(
        """
        <h2 style='color:#2E8B57'>
        📈 Draft Analysis
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "Good Faces:",
        result["good_faces"]
    )

    st.write(
        "Warning Faces:",
        result["warning_faces"]
    )

    st.write(
        "Critical Faces:",
        result["critical_faces"]
    )

    st.write(
        "Average Draft Angle:",
        result["average_draft"],
        "degrees"
    )

    st.markdown(
        """
        <h2 style='color:#8A2BE2'>
        🎯 DFM Assessment
        </h2>
        """,
        unsafe_allow_html=True
    )    

    st.subheader(
        "DFM Assessment"
    )

    score = result["score"]

    rating = result["rating"]

    risk = result["risk_level"]

    if rating == "Excellent":

        st.success(
            f"🟢 {rating}"
        )

    elif rating == "Good":

        st.info(
            f"🔵 {rating}"
        )

    elif rating == "Moderate":

        st.warning(
            f"🟡 {rating}"
        )

    else:

        st.error(
            f"🔴 {rating}"
        )

    st.metric(
        "Manufacturability Score",
        score
    )

    st.write(
        "Risk Level:",
        risk
    )

    st.write(
        "Recommendation:",
        result["recommendation"]
    )

    # Generate PDF
    pdf_file = generate_pdf(result)

    # Download Button
    with open(pdf_file, "rb") as file:

        st.download_button(
            label="Download HIMAS Report",
            data=file,
            file_name="HIMAS_Report.pdf",
            mime="application/pdf"
        )