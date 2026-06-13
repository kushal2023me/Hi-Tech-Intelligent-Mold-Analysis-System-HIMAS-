import streamlit as st
import tempfile

from dfm_engine import (
    analyze_step_file,
    generate_pdf,
    generate_visualization,
    convert_step_to_stl
)

st.markdown(
    """
    <h1 style='text-align:center;
    color:#0E76A8;'>
    🔧 Hi-Tech Intelligent Mold Analysis System (HIMAS)   
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style='text-align:center;
    font-size:18px;
    color:gray'>
    AI-Powered Moldability Analysis for Injection Molded Parts
    </div>
    """,
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload STEP File",
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

    st.write("Running Analysis...")

    result = analyze_step_file(temp_path)
    
    stl_path = temp_path.replace(
    ".step",
    ".stl"
    )

    convert_step_to_stl(
        temp_path,
        stl_path
    )
    
    

    st.write("Parting Points:", len(result["parting_points"]))
    st.write("Undercut Points:", len(result["undercut_points"]))
    st.write("Good Points:", len(result["good_points"]))
    st.write("Warning Points:", len(result["warning_points"]))
    st.write("Critical Points:", len(result["critical_points"]))


    image_path = generate_visualization(
        result,
        stl_path
    )

    st.subheader("DFM Visualization")

    st.image(
        image_path,
        caption="Blue=Parting, Orange=Undercut, Green=Good Draft, Yellow=Warning Draft, Red=Critical Draft"
    )

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
            label="Download DFM Report",
            data=file,
            file_name="DFM_Report.pdf",
            mime="application/pdf"
        )