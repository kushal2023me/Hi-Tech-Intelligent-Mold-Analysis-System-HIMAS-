import cadquery as cq
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from collections import Counter
from reportlab.pdfgen import canvas


def convert_step_to_stl(
    step_path,
    stl_path
):

    part = cq.importers.importStep(
        step_path
    )

    cq.exporters.export(
        part,
        stl_path
    )

    return stl_path


def analyze_step_file(step_path):

    # ==========================
    # STEP 1 : LOAD STEP FILE
    # ==========================

    part = cq.importers.importStep(step_path)

    shape = part.val()

    faces = shape.Faces()

    print("STEP Loaded Successfully")


    # ==========================
    # STEP 2 : EXTRACT NORMALS
    # ==========================

    face_normals = []

    for face in faces:

        umin, umax, vmin, vmax = face._uvBounds()

        u = (umin + umax) / 2
        v = (vmin + vmax) / 2

        result = face.normalAt(u, v)

        normal = result[0]

        face_normals.append(
            np.array([
                normal.x,
                normal.y,
                normal.z
            ])
        )

    # ==========================
    # PCA MOLD DIRECTION
    # ==========================

    face_centers = []

    for face in faces:

        center = face.Center()

        face_centers.append([
            center.x,
            center.y,
            center.z
        ])

    face_centers = np.array(face_centers)

    pca = PCA(n_components=3)

    pca.fit(face_centers)

    print("PCA Direction =", pca.components_[0])

    # ==========================
    # STEP 3 : FIND BEST MOLD
    # ==========================
    
    UNDERCUT_TOL = -0.15
    candidate_directions = {
        "+X": np.array([1,0,0]),
        "-X": np.array([-1,0,0]),
        "+Y": np.array([0,1,0]),
        "-Y": np.array([0,-1,0]),
        "+Z": np.array([0,0,1]),
        "-Z": np.array([0,0,-1])
    }
    
    results = {}

    for label, direction in candidate_directions.items():

        undercut_count = 0

        for normal in face_normals:

            dot = np.dot(normal, direction)

            if dot < UNDERCUT_TOL:
                undercut_count += 1

        results[label] = undercut_count

    best_direction = min(results, key=results.get)

    best_dir = candidate_directions[best_direction]
    

    # ==========================
    # STEP 4 : UNDERCUT FACES
    # ==========================
    undercut_area = 0

    total_area = 0
    undercut_faces = []

    for i, normal in enumerate(face_normals):
        face = faces[i]

        area = face.Area()

        total_area += area

        dot = np.dot(normal, best_dir)

        if dot < UNDERCUT_TOL:

            undercut_faces.append(i)

            undercut_area += area
    undercut_percentage = (
        undercut_area / total_area
    ) * 100
   

    # ==========================
    # STEP 5 : UNDERCUT REGIONS
    # ==========================

    undercut_points = []

    for face in faces:

        umin, umax, vmin, vmax = face._uvBounds()

        u = (umin + umax)/2
        v = (vmin + vmax)/2

        normal, _ = face.normalAt(u,v)

        center = face.Center()

        n = np.array([
            normal.x,
            normal.y,
            normal.z
        ])

        if np.dot(n, best_dir) < UNDERCUT_TOL:

            undercut_points.append([
                center.x,
                center.y,
                center.z
            ])

    undercut_points = np.array(undercut_points)

    clustering = DBSCAN(
        eps=15,
        min_samples=1
    ).fit(undercut_points)

    labels = clustering.labels_

    number_of_regions = len(set(labels))

    region_sizes = Counter(labels)


    # ==========================
    # STEP 6 : CORE / CAVITY
    # ==========================

    core_faces = []
    cavity_faces = []

    for i, normal in enumerate(face_normals):

        dot = np.dot(normal, best_dir)

        if dot >= 0:
            cavity_faces.append(i)
        else:
            core_faces.append(i)


    # ==========================
    # STEP 7 : PARTING FACES
    # ==========================

    parting_faces = []

    for i, normal in enumerate(face_normals):

        dot = np.dot(normal, best_dir)

        if abs(dot) < 0.05:
            parting_faces.append(i)

    parting_points = []

    for idx in parting_faces:

        face = faces[idx]

        center = face.Center()

        parting_points.append([
            center.x,
            center.y,
            center.z
        ])
    print("Parting Faces =", len(parting_faces))

    print("Parting Points =", len(parting_points))


    # ==========================
    # STEP 8 : PARTING POINTS
    # ==========================

    parting_points = []

    for idx in parting_faces:

        face = faces[idx]

        umin, umax, vmin, vmax = face._uvBounds()

        u = (umin + umax)/2
        v = (vmin + vmax)/2

        center = face.Center()

        parting_points.append([
            center.x,
            center.y,
            center.z
        ])


    # ==========================
    # STEP 9 : MAIN PARTING LINE
    # ==========================

    parting_points_np = np.array(parting_points)

    center = np.mean(parting_points_np, axis=0)

    pca = PCA(n_components=3)

    pca.fit(parting_points_np)

    main_direction = pca.components_[0]

    length = 100

    start_point = center - length * main_direction

    end_point = center + length * main_direction

    # ==========================
    # STEP 10 : DRAFT ANALYSIS
    # ==========================

    draft_angles = []

    good_faces = 0
    warning_faces = 0
    critical_faces = 0

    good_points = []

    warning_points = []

    critical_points = []

    for i, normal in enumerate(face_normals):

        dot = abs(np.dot(normal, best_dir))

        dot = np.clip(dot, -1.0, 1.0)

        angle = np.degrees(
            np.arccos(dot)
        )

        draft_angle = abs(90 - angle)

        draft_angles.append(draft_angle)

        face = faces[i]

        center = face.Center()

        point = [
            center.x,
            center.y,
            center.z
        ]

        if draft_angle > 3:

            good_faces += 1

            good_points.append(point)

        elif draft_angle > 1:

            warning_faces += 1

            warning_points.append(point)

        else:

            critical_faces += 1

            critical_points.append(point)

    print("draft_angles length =", len(draft_angles))

    average_draft = np.mean(draft_angles)

    print("average_draft =", average_draft)
    

    # ==========================
    # STEP 11 : SCORE
    # ==========================

    score = 100

    # Undercut Penalty
    score -= undercut_percentage * 0.6

    # Region Penalty
    score -= number_of_regions * 2

    # Draft Penalty
    if average_draft < 1:

        score -= 25

    elif average_draft < 3:

        score -= 10

    # Limit
    score = max(
        0,
        min(100, score)
    )

    if score >= 90:

        rating = "Excellent"

    elif score >= 75:

        rating = "Good"

    elif score >= 60:

        rating = "Moderate"

    else:

        rating = "Poor"

    if undercut_percentage < 5:

        risk_level = "Low"

    elif undercut_percentage < 15:

        risk_level = "Medium"

    else:

        risk_level = "High"

    recommendation = []

    if undercut_percentage > 10:

        recommendation.append(
            "Reduce undercuts or use sliders."
        )

    if average_draft < 3:

        recommendation.append(
            "Increase draft angle."
        )

    if len(recommendation) == 0:

        recommendation.append(
            "Design suitable for molding."
        )

    recommendation_text = " | ".join(
        recommendation
    )
    


    # ==========================
    # RETURN RESULTS
    # ==========================

    return {

    "mold_direction": best_direction,

    "undercut_faces": len(undercut_faces),

    "undercut_area": round(
        undercut_area,
        2
    ),

    "undercut_percentage": round(
        undercut_percentage,
        2
    ),

    "undercut_regions": number_of_regions,

    "undercut_points": undercut_points,

    "core_faces": len(core_faces),

    "cavity_faces": len(cavity_faces),

    "parting_faces": len(parting_faces),

    "parting_points": parting_points,

    "start_point": start_point,

    "end_point": end_point,
    
    "good_faces": good_faces,

    "warning_faces": warning_faces,

    "critical_faces": critical_faces,

    "average_draft": round(
        average_draft,
        2
    ), 
    
    "good_points": good_points,

    "warning_points": warning_points,

    "critical_points": critical_points,
    
    "score": round(score,2),
  
    "rating": rating,

    "risk_level": risk_level,

    "recommendation": recommendation_text,

    "region_sizes": region_sizes
}
from reportlab.pdfgen import canvas

def generate_pdf(result):

    pdf_path = "DFM_Report.pdf"

    pdf = canvas.Canvas(pdf_path)

    y = 800

    pdf.setFillColorRGB(
        0,
        0.3,
        0.7
    )

    pdf.setFont(
        "Helvetica-Bold",
        20
    )

    pdf.drawString(
        120,
        y,
        "DESIGN FOR MANUFACTURING REPORT"
    )

    y -= 40

    pdf.setFont("Helvetica-Bold",12)

    pdf.drawString(50,y,"Part Information")
    y -= 25

    pdf.setFont("Helvetica",11)

    pdf.drawString(
        70,
        y,
        f"Optimal Mold Direction : {result['mold_direction']}"
    )

    y -= 40

    pdf.setFont("Helvetica-Bold",12)

    pdf.drawString(
        50,
        y,
        "Manufacturability Summary"
    )

    y -= 25

    pdf.setFont("Helvetica",11)

    pdf.drawString(
        70,
        y,
        f"Undercut Faces : {result['undercut_faces']}"
    )

    y -= 20

    pdf.drawString(
        70,
        y,
        f"Undercut Regions : {result['undercut_regions']}"
    )

    y -= 20

    pdf.drawString(
        70,
        y,
        f"Parting Faces : {result['parting_faces']}"
    )

    y -= 40

    pdf.setFont("Helvetica-Bold",12)

    pdf.drawString(
        50,
        y,
        "Core / Cavity Analysis"
    )

    y -= 25

    pdf.setFont("Helvetica",11)

    pdf.drawString(
        70,
        y,
        f"Core Faces : {result['core_faces']}"
    )

    y -= 20

    pdf.drawString(
        70,
        y,
        f"Cavity Faces : {result['cavity_faces']}"
    )

    y -= 40

    pdf.setFont("Helvetica-Bold",12)

    pdf.drawString(
        50,
        y,
        "Parting Line"
    )

    y -= 25

    pdf.setFont("Helvetica",11)

    pdf.drawString(
        70,
        y,
        f"Start Point : {result['start_point']}"
    )

    y -= 20

    pdf.drawString(
        70,
        y,
        f"End Point : {result['end_point']}"
    )

    y -= 40

    score = result["score"]

    pdf.setFont("Helvetica-Bold",12)

    pdf.drawString(
        50,
        y,
        "Overall DFM Assessment"
    )

    y -= 25

    pdf.setFont("Helvetica",11)

    pdf.drawString(
        70,
        y,
        f"Score : {result['score']} / 100"
    )

    y -= 20

    pdf.drawString(
        70,
        y,
        f"Rating : {result['rating']}"
    )

    y -= 20

    pdf.drawString(
        70,
        y,
        f"Risk Level : {result['risk_level']}"
    )

    y -= 20

    pdf.drawString(
        70,
        y,
        f"Recommendation : {result['recommendation']}"
    )

    y -= 40

    pdf.setFillColorRGB(
        0.5,
        0.5,
        0.5
    )

    pdf.setFont(
        "Helvetica-Oblique",
        8
    )

    pdf.drawString(
        170,
        30,
        "Generated by DFM Intelligence Platform"
    )

    

    pdf.save()

    return pdf_path

def generate_visualization(
    result,
    stl_path
):

    return None
    #import os

    #os.environ["PYVISTA_OFF_SCREEN"] = "true"

    #import pyvista as pv
    #import numpy as np


    #pv.OFF_SCREEN = True

    #mesh = pv.read(
    #stl_path
    #)

    #plotter = pv.Plotter(off_screen=True)

# ==========================
# CAD MODEL
# ==========================

    plotter.add_mesh(
        mesh,
        color="lightgray",
        opacity=0.4
    )

# ==========================
# PARTING REGION
# ==========================

    if len(result["parting_points"]) > 0:

        parting_cloud = pv.PolyData(
            np.array(result["parting_points"])
        )

        plotter.add_mesh(
            parting_cloud,
            color="blue",
            point_size=25,
            render_points_as_spheres=True
        )

# ==========================
# UNDERCUT REGION
# ==========================

    if len(result["undercut_points"]) > 0:

        undercut_cloud = pv.PolyData(
            np.array(result["undercut_points"])
        )

        plotter.add_mesh(
            undercut_cloud,
            color="orange",
            point_size=25,
            render_points_as_spheres=True
        )

# ==========================
# GOOD DRAFT
# ==========================

    if len(result["good_points"]) > 0:

        good_cloud = pv.PolyData(
            np.array(result["good_points"])
        )

        plotter.add_mesh(
            good_cloud,
            color="green",
            point_size=12,
            render_points_as_spheres=True
        )

# ==========================
# WARNING DRAFT
# ==========================

    if len(result["warning_points"]) > 0:

        warning_cloud = pv.PolyData(
            np.array(result["warning_points"])
        )

        plotter.add_mesh(
            warning_cloud,
            color="yellow",
            point_size=14,
            render_points_as_spheres=True
        )

# ==========================
# CRITICAL DRAFT
# ==========================

    if len(result["critical_points"]) > 0:

        critical_cloud = pv.PolyData(
            np.array(result["critical_points"])
        )

        plotter.add_mesh(
            critical_cloud,
            color="red",
            point_size=14,
            render_points_as_spheres=True
        )

    plotter.add_axes()

    plotter.view_isometric()

    image_path = "visualization.png"

    plotter.screenshot(image_path)

    plotter.close()

    return image_path

