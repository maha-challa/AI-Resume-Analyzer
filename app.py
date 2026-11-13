import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from analyzer import extract_text_from_pdf, analyze_resume
import db

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ai-resume-analyzer-secret-key-2026")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf"}

# Attempt initial database setup on startup
try:
    db.init_db()
except Exception as init_err:
    print(f"Notice: Initial MySQL setup deferred or pending credentials: {init_err}")


def allowed_file(filename: str) -> bool:
    """Checks if the uploaded file has a valid .pdf extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    """Renders the main application page."""
    return render_template("index.html")


@app.route("/db-status", methods=["GET"])
def db_status():
    """Checks MySQL database connection status."""
    is_connected, msg = db.test_connection()
    return jsonify({
        "connected": is_connected,
        "message": msg
    })


@app.route("/history", methods=["GET"])
def get_history():
    """Returns all previous resume analysis records from MySQL."""
    try:
        records = db.get_all_analyses()
        return jsonify({
            "success": True,
            "analyses": records
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve history: {str(e)}"
        }), 500


@app.route("/history/<int:analysis_id>", methods=["GET"])
def get_history_detail(analysis_id: int):
    """Returns full details of a specific previous analysis."""
    try:
        record = db.get_analysis_by_id(analysis_id)
        if not record:
            return jsonify({
                "success": False,
                "error": "Record not found."
            }), 404
        return jsonify({
            "success": True,
            "analysis": record
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to load analysis details: {str(e)}"
        }), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Handles resume upload, PDF text extraction, skill matching,
    and automatic record persistence into the MySQL database.
    """
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
              "application/json" in request.headers.get("Accept", "")

    # 1. Validate file presence
    if "resume" not in request.files:
        error_msg = "Please upload a resume file."
        if is_ajax:
            return jsonify({"success": False, "error": error_msg}), 400
        return render_template("index.html", error=error_msg)

    file = request.files["resume"]

    if file.filename == "":
        error_msg = "No file selected. Please choose a PDF resume to upload."
        if is_ajax:
            return jsonify({"success": False, "error": error_msg}), 400
        return render_template("index.html", error=error_msg)

    if not allowed_file(file.filename):
        error_msg = "Invalid file type. Only PDF files (.pdf) are supported."
        if is_ajax:
            return jsonify({"success": False, "error": error_msg}), 400
        return render_template("index.html", error=error_msg)

    # 2. Validate job description
    job_description = request.form.get("job_description", "").strip()
    if not job_description:
        error_msg = "Please paste or enter a job description to compare against your resume."
        if is_ajax:
            return jsonify({"success": False, "error": error_msg}), 400
        return render_template("index.html", error=error_msg)

    # 3. Analyze PDF & Extract Skills
    try:
        resume_text = extract_text_from_pdf(file.stream)
        results = analyze_resume(resume_text, job_description)
        results["filename"] = secure_filename(file.filename)

        # 4. Save to MySQL database
        db_saved = False
        db_error_msg = None
        try:
            record_id = db.save_analysis(
                filename=results["filename"],
                job_description=job_description,
                match_percentage=results["match_percentage"],
                matched_skills=results["matched_skills"],
                missing_skills=results["missing_skills"],
                suggestions=results["suggestions"]
            )
            results["saved_to_db"] = True
            results["record_id"] = record_id
        except Exception as dbe:
            results["saved_to_db"] = False
            results["db_error"] = str(dbe)
            print(f"Warning: Database save skipped/failed: {dbe}")

        if is_ajax:
            return jsonify({"success": True, "data": results})

        return render_template("index.html", results=results, job_description=job_description)

    except ValueError as ve:
        error_msg = str(ve)
        if is_ajax:
            return jsonify({"success": False, "error": error_msg}), 400
        return render_template("index.html", error=error_msg, job_description=job_description)

    except Exception as e:
        error_msg = f"An unexpected error occurred during analysis: {str(e)}"
        if is_ajax:
            return jsonify({"success": False, "error": error_msg}), 500
        return render_template("index.html", error=error_msg, job_description=job_description)


if __name__ == "__main__":
    # Support dynamic cloud hosting port (e.g. Render, Railway, Heroku)
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug)
